"""
Chunk Merger

Merge neighbouring semantic chunks until
a configurable token budget is reached.

Chunks are NEVER split.
Only whole chunks are merged.
"""

from __future__ import annotations

from copy import deepcopy

from models import CodeChunk


class ChunkMerger:

    def __init__(
        self,
        max_tokens: int = 300,
    ):
        self.max_tokens = max_tokens

    # ---------------------------------------------------------

    def estimate_tokens(
        self,
        text: str,
    ) -> int:
        """
        Very rough estimate.

        Replace with tiktoken later.
        """

        return max(1, len(text) // 4)

    # ---------------------------------------------------------

    def merge(
        self,
        chunks: list[CodeChunk],
    ) -> list[CodeChunk]:

        if not chunks:
            return []

        merged = []

        current = deepcopy(chunks[0])

        current.metadata.token_count = self.estimate_tokens(
            current.source_code
        )

        for nxt in chunks[1:]:

            nxt.metadata.token_count = self.estimate_tokens(
                nxt.source_code
            )

            if (
                current.metadata.token_count
                + nxt.metadata.token_count
                <= self.max_tokens
            ):

                current.source_code += "\n\n" + nxt.source_code

                current.metadata.end_line = nxt.metadata.end_line

                current.metadata.end_byte = nxt.metadata.end_byte

                current.metadata.token_count += (
                    nxt.metadata.token_count
                )

            else:

                merged.append(current)

                current = deepcopy(nxt)

        merged.append(current)

        return merged