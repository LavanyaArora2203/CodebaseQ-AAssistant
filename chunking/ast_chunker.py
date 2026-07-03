#!/usr/bin/env python3
"""
ts_chunker.py

Build a real AST per file (via `tree_sitter` + `tree_sitter_python`) and walk
it to extract chunk candidates:

    - function definitions   (top-level, methods, and arbitrarily nested defs)
    - class definitions
    - docstrings              (module / class / function)
    - standalone comments     (contiguous '#' lines not trailing code)
    - markdown_section        (heading-delimited sections, for .md files)

Each chunk carries rich metadata:
    file_path, chunk_type, name, qualified_name, start_line, end_line,
    parent_class, parent_function, language

Edge cases handled:
    - Very long functions are split into overlapping parts. Each part
      repeats the function's signature (decorators + def line) so the
      indentation context is never lost, even mid-body.
    - Nested functions (def inside def) are extracted as their own chunks,
      in addition to remaining part of the enclosing function's source.
    - Decorators are attached to whichever def they precede, at any
      nesting depth.
    - Non-code files (.md) are chunked by heading instead, using a
      lightweight heading splitter that ignores '#' characters inside
      fenced code blocks.

Currently wired for Python (tree-sitter) and Markdown (heading split — no
tree-sitter grammar for markdown is used here; see MarkdownChunker).

Usage:
    python ts_chunker.py path/to/file.py
    python ts_chunker.py path/to/file.py --json
    python ts_chunker.py path/to/file.py --max-lines 80 --overlap 8
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

PY_LANGUAGE = Language(tspython.language())

# Functions/methods with more body lines than this get split into overlapping
# parts. Kept generous by default so normal-sized functions are untouched.
DEFAULT_MAX_FUNCTION_LINES = 100
DEFAULT_OVERLAP_LINES = 8


@dataclass
class Chunk:
    file_path: str
    chunk_type: str              # function | class | docstring | comment | markdown_section
    name: Optional[str]
    qualified_name: Optional[str]  # dotted path, e.g. "Widget.build.inner_helper"
    start_line: int              # 1-indexed, inclusive
    end_line: int                # 1-indexed, inclusive
    parent_class: Optional[str]    # nearest enclosing class, only if directly a method
    parent_function: Optional[str] # nearest enclosing function, only if directly nested
    language: str
    part_index: Optional[int] = None   # set when a long function was split
    total_parts: Optional[int] = None  # total number of parts for this function
    source: str = field(default="", repr=False)  # exact source text (extra, but handy downstream)


# --------------------------------------------------------------------------
# Python: tree-sitter based walker
# --------------------------------------------------------------------------

class PythonTSChunker:
    def __init__(self, path: Path, max_function_lines: int = DEFAULT_MAX_FUNCTION_LINES,
                 overlap_lines: int = DEFAULT_OVERLAP_LINES):
        self.path = path
        self.file_path = str(path)
        self.text = path.read_text(encoding="utf-8")
        self.source_bytes = self.text.encode("utf-8")
        self.lines = self.text.splitlines(keepends=True)
        self.max_function_lines = max_function_lines
        self.overlap_lines = overlap_lines
        parser = Parser(PY_LANGUAGE)
        self.tree = parser.parse(self.source_bytes)

    # ---- public API -------------------------------------------------------

    def extract(self) -> List[Chunk]:
        chunks = self._walk_body(
            self.tree.root_node,
            parent_class=None,
            parent_function=None,
            scope_path=[],
            owner_name=None,
            collect_docs_and_comments=True,
        )
        chunks.sort(key=lambda c: (c.start_line, c.part_index or 0))
        return chunks

    # ---- generic helpers ----------------------------------------------------

    def _node_text(self, node: Node) -> str:
        return self.source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    def _line_span(self, node: Node) -> tuple[int, int]:
        return node.start_point[0] + 1, node.end_point[0] + 1

    def _source_slice(self, start_line: int, end_line: int) -> str:
        return "".join(self.lines[start_line - 1:end_line])

    def _is_standalone_comment(self, node: Node) -> bool:
        """True if nothing but whitespace precedes this comment on its line."""
        row = node.start_point[0]
        col = node.start_point[1]
        line_text = self.lines[row]
        return line_text[:col].strip() == ""

    def _identifier_name(self, def_node: Node) -> Optional[str]:
        for child in def_node.children:
            if child.type == "identifier":
                return self._node_text(child)
        return None

    @staticmethod
    def _find_block(def_node: Node) -> Optional[Node]:
        for c in def_node.children:
            if c.type == "block":
                return c
        return None

    def _make_chunk(self, chunk_type, name, qualified_name, start_line, end_line,
                     parent_class, parent_function, source=None,
                     part_index=None, total_parts=None) -> Chunk:
        return Chunk(
            file_path=self.file_path,
            chunk_type=chunk_type,
            name=name,
            qualified_name=qualified_name,
            start_line=start_line,
            end_line=end_line,
            parent_class=parent_class,
            parent_function=parent_function,
            language="python",
            part_index=part_index,
            total_parts=total_parts,
            source=source if source is not None else self._source_slice(start_line, end_line),
        )

    # ---- long-function splitting -------------------------------------------

    def _emit_function_chunks(self, node: Node, start_line: int, end_line: int,
                               name: Optional[str], qualified_name: Optional[str],
                               parent_class: Optional[str], parent_function: Optional[str]) -> List[Chunk]:
        """
        Build one Chunk for a function, or several overlapping part-chunks if
        its body exceeds max_function_lines. Every part repeats the
        signature (decorators + def line) so indentation context and the
        function's identity are visible no matter which part you're reading.
        """
        block = self._find_block(node)
        if block is None:
            return [self._make_chunk("function", name, qualified_name, start_line, end_line,
                                      parent_class, parent_function)]

        # The line just before the block's first line is the last line of the
        # signature (decorators + "def ...(...):", however many lines that spans).
        header_end_line = block.start_point[0]        # 1-indexed line of the ':' / last signature line
        header_start_line = start_line
        body_start_line = header_end_line + 1
        body_end_line = end_line
        body_line_count = body_end_line - body_start_line + 1

        if body_line_count <= self.max_function_lines:
            return [self._make_chunk("function", name, qualified_name, start_line, end_line,
                                      parent_class, parent_function)]

        header_text = self._source_slice(header_start_line, header_end_line)

        # Build overlapping line-range slices across the body.
        slices: List[tuple[int, int]] = []
        pos = body_start_line
        step = max(1, self.max_function_lines - self.overlap_lines)
        while pos <= body_end_line:
            part_end = min(body_end_line, pos + self.max_function_lines - 1)
            slices.append((pos, part_end))
            if part_end == body_end_line:
                break
            pos += step

        total_parts = len(slices)
        chunks = []
        for i, (s, e) in enumerate(slices, start=1):
            body_text = self._source_slice(s, e)
            combined_source = header_text + body_text
            chunks.append(self._make_chunk(
                "function", name, qualified_name,
                start_line=s if i > 1 else header_start_line,
                end_line=e,
                parent_class=parent_class,
                parent_function=parent_function,
                source=combined_source,
                part_index=i,
                total_parts=total_parts,
            ))
        return chunks

    # ---- main recursive walk -----------------------------------------------

    def _walk_body(self, container: Node, parent_class: Optional[str], parent_function: Optional[str],
                    scope_path: List[str], owner_name: Optional[str],
                    collect_docs_and_comments: bool) -> List[Chunk]:
        """
        Walk the direct children of a module/class/function 'block' node.

        - parent_class: set when this body is directly a class body (methods
          get tagged with it).
        - parent_function: set when this body is directly a function body
          (nested defs get tagged with it).
        - scope_path: dotted-name breadcrumb of enclosing defs/classes, used
          to build qualified_name.
        - collect_docs_and_comments: False when recursing purely to find
          nested defs inside a function body — in that mode we skip
          docstring/comment extraction so the parent function's own prose
          stays embedded in its source rather than being split out.
        """
        chunks: List[Chunk] = []
        body = list(container.children)

        first_stmt_idx = None
        if collect_docs_and_comments:
            for i, child in enumerate(body):
                if child.type != "comment":
                    first_stmt_idx = i
                    break

        pending_comment_run: List[Node] = []

        def flush_comments():
            if not pending_comment_run:
                return
            start_line = pending_comment_run[0].start_point[0] + 1
            end_line = pending_comment_run[-1].end_point[0] + 1
            chunks.append(self._make_chunk("comment", None, None, start_line, end_line,
                                            parent_class, parent_function))
            pending_comment_run.clear()

        for i, child in enumerate(body):
            if child.type == "comment":
                if collect_docs_and_comments and self._is_standalone_comment(child):
                    pending_comment_run.append(child)
                continue
            else:
                flush_comments()

            if collect_docs_and_comments and i == first_stmt_idx and child.type == "expression_statement":
                string_child = child.children[0] if child.children else None
                if string_child is not None and string_child.type == "string":
                    start, end = self._line_span(child)
                    chunks.append(self._make_chunk("docstring", owner_name,
                                                     ".".join(scope_path) or None,
                                                     start, end, parent_class, parent_function))
                    continue

            node = child
            decorator_start = None
            if node.type == "decorated_definition":
                decorator_start = node.start_point[0] + 1
                for c in node.children:
                    if c.type in ("function_definition", "class_definition"):
                        node = c
                        break

            if node.type == "function_definition":
                name = self._identifier_name(node)
                start, end = self._line_span(node)
                if decorator_start is not None:
                    start = decorator_start
                qualified_name = ".".join(scope_path + [name]) if name else None

                chunks.extend(self._emit_function_chunks(
                    node, start, end, name, qualified_name, parent_class, parent_function
                ))

                # Recurse to find nested defs (edge case: nested functions).
                # We do NOT collect docs/comments here, so the rest of this
                # function's own body stays intact inside its own chunk(s).
                func_block = self._find_block(node)
                if func_block is not None and name is not None:
                    chunks.extend(self._walk_body(
                        func_block,
                        parent_class=None,
                        parent_function=name,
                        scope_path=scope_path + [name],
                        owner_name=None,
                        collect_docs_and_comments=False,
                    ))

            elif node.type == "class_definition":
                name = self._identifier_name(node)
                start, end = self._line_span(node)
                if decorator_start is not None:
                    start = decorator_start
                qualified_name = ".".join(scope_path + [name]) if name else None
                chunks.append(self._make_chunk("class", name, qualified_name, start, end,
                                                parent_class, parent_function))
                class_block = self._find_block(node)
                if class_block is not None and name is not None:
                    chunks.extend(self._walk_body(
                        class_block,
                        parent_class=name,
                        parent_function=None,
                        scope_path=scope_path + [name],
                        owner_name=name,
                        collect_docs_and_comments=True,
                    ))

        flush_comments()
        return chunks


# --------------------------------------------------------------------------
# Markdown: heading-based section splitter (no tree-sitter grammar)
# --------------------------------------------------------------------------

_MD_ATX_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_MD_FENCE_RE = re.compile(r"^\s*(```|~~~)")


class MarkdownChunker:
    """
    Splits a markdown file into sections by ATX heading ('# ...' .. '###### ...').

    Edge case handled: '#' characters inside fenced code blocks (``` or ~~~)
    are not mistaken for headings — a common bug in naive line-based
    splitters (e.g. a code sample containing a Python comment '# note' or a
    shell script with '#!/bin/bash' would otherwise be misread as a new
    section).
    """

    def __init__(self, path: Path):
        self.path = path
        self.file_path = str(path)
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def extract(self) -> List[Chunk]:
        headers = []  # (line_no 1-indexed, level, title)
        in_fence = False
        for i, line in enumerate(self.lines, start=1):
            if _MD_FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = _MD_ATX_HEADER_RE.match(line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                headers.append((i, level, title))

        if not headers:
            if self.lines:
                return [Chunk(
                    file_path=self.file_path,
                    chunk_type="markdown_section",
                    name=None,
                    qualified_name=None,
                    start_line=1,
                    end_line=len(self.lines),
                    parent_class=None,
                    parent_function=None,
                    language="markdown",
                    source="\n".join(self.lines),
                )]
            return []

        chunks = []
        # breadcrumb stack of (level, title) to build qualified_name, e.g.
        # "Installation.Requirements"
        stack: List[tuple[int, str]] = []
        for idx, (start_line, level, title) in enumerate(headers):
            end_line = headers[idx + 1][0] - 1 if idx + 1 < len(headers) else len(self.lines)

            while stack and stack[-1][0] >= level:
                stack.pop()
            qualified_name = ".".join([t for _, t in stack] + [title])
            stack.append((level, title))

            chunks.append(Chunk(
                file_path=self.file_path,
                chunk_type="markdown_section",
                name=title,
                qualified_name=qualified_name,
                start_line=start_line,
                end_line=end_line,
                parent_class=None,
                parent_function=None,
                language="markdown",
                source="\n".join(self.lines[start_line - 1:end_line]),
            ))
        return chunks


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------

def chunk_file(path: str | Path, max_function_lines: int = DEFAULT_MAX_FUNCTION_LINES,
               overlap_lines: int = DEFAULT_OVERLAP_LINES) -> List[Chunk]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".py":
        return PythonTSChunker(path, max_function_lines, overlap_lines).extract()
    if suffix == ".md":
        return MarkdownChunker(path).extract()
    raise ValueError(f"Unsupported file type for chunking: {path} (suffix '{suffix}')")


def main():
    parser = argparse.ArgumentParser(description="Extract chunk candidates with rich metadata from a source file.")
    parser.add_argument("file", help="Path to a .py or .md file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_FUNCTION_LINES,
                         help="Max body lines before a function is split (default: %(default)s)")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP_LINES,
                         help="Overlap lines between split function parts (default: %(default)s)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        raise SystemExit(f"Error: '{path}' is not a file")

    chunks = chunk_file(path, args.max_lines, args.overlap)

    if args.json:
        print(json.dumps([asdict(c) for c in chunks], indent=2))
        return

    for c in chunks:
        label = c.chunk_type
        if c.name:
            label += f" '{c.name}'"
        if c.parent_class:
            label += f" (method of {c.parent_class})"
        if c.parent_function:
            label += f" (nested in {c.parent_function})"
        if c.total_parts:
            label += f" [part {c.part_index}/{c.total_parts}]"
        print(f"\n[{label}] {c.file_path}:{c.start_line}-{c.end_line} lang={c.language}")
        print(c.source.rstrip())


if __name__ == "__main__":
    main()