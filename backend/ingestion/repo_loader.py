import os
import shutil
from git import Repo
from typing import List, Dict

# -----------------------------
# CONFIG
# -----------------------------
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go",
    ".rs", ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css"
}

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", "venv",
    "env", ".idea", ".vscode", "dist", "build"
}

MAX_FILE_SIZE_MB = 2


# -----------------------------
# CLONE REPO
# -----------------------------
import os
import stat
import shutil
from git import Repo
from typing import List, Dict

# -----------------------------
# WINDOWS FIX: force delete read-only files
# -----------------------------
def force_remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree on Windows read-only files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


# -----------------------------
# CLONE REPO
# -----------------------------
def clone_repo(repo_url: str, local_path: str = "repo") -> str:
    if os.path.exists(local_path):
        print(f"[INFO] Removing existing repo at {local_path}")
        shutil.rmtree(local_path, onerror=force_remove_readonly)  # ✅ fix

    print(f"[INFO] Cloning repo from {repo_url}")
    Repo.clone_from(repo_url, local_path)
    print("[INFO] Repo cloned successfully!")
    return local_path

# -----------------------------
# FILE FILTER
# -----------------------------
def is_valid_file(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1]
    if ext not in SUPPORTED_EXTENSIONS:
        return False
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False
    return True


# -----------------------------
# LOAD FILES
# -----------------------------
def load_repo(repo_path: str) -> List[Dict]:
    documents = []

    for root, dirs, files in os.walk(repo_path):          # ✅ indented inside function
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            file_path = os.path.join(root, file)

            if not is_valid_file(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if file.endswith(".py"):
                    # TODO: replace with real call once ast_chunker.py is built
                    # from backend.ingestion.ast_chunker import extract_python_metadata
                    # function_docs = extract_python_metadata(file_path, content)
                    # documents.extend(function_docs)
                    documents.append({
                        "content": content,
                        "metadata": {
                            "file": file_path,
                            "function": None,
                            "type": "python_file",
                            "imports": [],
                            "calls": [],
                            "docstring": ""
                        }
                    })
                else:
                    documents.append({
                        "content": content,
                        "metadata": {
                            "file": file_path,
                            "function": None,
                            "type": "file",
                            "imports": [],
                            "calls": [],
                            "docstring": ""
                        }
                    })

            except Exception as e:
                print(f"[WARNING] Skipping {file_path}: {e}")

    print(f"[INFO] Loaded {len(documents)} documents from repo")
    return documents                                       # ✅ inside function now


# -----------------------------
# MAIN FUNCTION (ENTRY POINT)
# -----------------------------
def load_github_repo(repo_url: str) -> List[Dict]:
    repo_path = clone_repo(repo_url)
    documents = load_repo(repo_path)
    return documents                                       # ✅ inside function now


# -----------------------------
# CLI USAGE
# -----------------------------
if __name__ == "__main__":
    repo_url = input("Enter GitHub Repo URL: ").strip()
    docs = load_github_repo(repo_url)

    print("\n[SAMPLE OUTPUT]")
    if docs:
        print("File:", docs[0]["metadata"]["file"])       # ✅ fixed key name (was "file_name")
        print("Preview:\n", docs[0]["content"][:500])