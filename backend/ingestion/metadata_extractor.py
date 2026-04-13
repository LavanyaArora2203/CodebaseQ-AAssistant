import ast
from typing import List, Dict, Any


def extract_imports(tree: ast.AST) -> List[str]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return list(set(imports))


def extract_calls(node: ast.AST) -> List[str]:
    calls = []
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Call):
            if isinstance(subnode.func, ast.Name):
                calls.append(subnode.func.id)
            elif isinstance(subnode.func, ast.Attribute):
                calls.append(subnode.func.attr)
    return list(set(calls))


def extract_docstring(node: ast.AST) -> str:
    return ast.get_docstring(node) or ""


def extract_metadata(file_path: str, content: str) -> List[Dict[str, Any]]:
    """
    Parses a Python file and returns structured chunks
    with metadata per function, class, and method.
    """
    results = []

    try:
        tree = ast.parse(content)
        imports = extract_imports(tree)

        for node in tree.body:  # ✅ tree.body not ast.walk — avoids duplicates

            if isinstance(node, ast.FunctionDef):
                results.append({
                    "content": ast.get_source_segment(content, node),
                    "metadata": {
                        "file": file_path,
                        "function": node.name,
                        "class": None,
                        "type": "function",
                        "imports": imports,
                        "calls": extract_calls(node),
                        "docstring": extract_docstring(node)
                    }
                })

            elif isinstance(node, ast.ClassDef):
                results.append({
                    "content": ast.get_source_segment(content, node),
                    "metadata": {
                        "file": file_path,
                        "function": None,
                        "class": node.name,
                        "type": "class",
                        "imports": imports,
                        "calls": extract_calls(node),
                        "docstring": extract_docstring(node)
                    }
                })

                for subnode in node.body:  # ✅ methods inside class
                    if isinstance(subnode, ast.FunctionDef):
                        results.append({
                            "content": ast.get_source_segment(content, subnode),
                            "metadata": {
                                "file": file_path,
                                "function": subnode.name,
                                "class": node.name,
                                "type": "method",
                                "imports": imports,
                                "calls": extract_calls(subnode),
                                "docstring": extract_docstring(subnode)
                            }
                        })

    except Exception as e:
        print(f"[WARNING] Metadata extraction failed for {file_path}: {e}")

    return results