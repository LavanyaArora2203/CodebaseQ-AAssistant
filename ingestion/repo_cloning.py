"""
Repository Cloning Module

Responsibilities:
- Clone Git repositories into a temporary sandbox directory.
- Supports shallow cloning (--depth=1).
- Easy to extend for GitHub OAuth / Personal Access Tokens.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class RepositoryCloneError(Exception):
    """Raised when repository cloning fails."""


class RepoCloner:
    """
    Clone Git repositories into a temporary directory.

    Example:
    --------
    >>> cloner = RepoCloner()
    >>> repo_path = cloner.clone("https://github.com/user/repo.git")
    >>> print(repo_path)
    """

    def __init__(self):
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.repo_path: Optional[Path] = None

    def clone(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        depth: int = 1,
    ) -> Path:
        """
        Clone a Git repository.

        Parameters
        ----------
        repo_url : str
            GitHub repository URL.

        branch : str | None
            Branch to clone.

        depth : int
            Shallow clone depth.

        Returns
        -------
        Path
            Local repository path.
        """

        self._temp_dir = tempfile.TemporaryDirectory(prefix="repo_ingestion_")
        destination = Path(self._temp_dir.name)

        logger.info("Cloning repository: %s", repo_url)

        try:
            clone_kwargs = {
                "to_path": str(destination),
                "depth": depth,
            }

            if branch:
                clone_kwargs["branch"] = branch

            Repo.clone_from(repo_url, **clone_kwargs)

            self.repo_path = destination

            logger.info("Repository cloned successfully.")
            logger.info("Location: %s", destination)

            return destination

        except GitCommandError as e:
            logger.exception("Git clone failed.")
            self.cleanup()
            raise RepositoryCloneError(str(e)) from e

        except Exception as e:
            logger.exception("Unexpected cloning error.")
            self.cleanup()
            raise RepositoryCloneError(str(e)) from e

    def cleanup(self):
        """
        Delete temporary cloned repository.
        """

        if self._temp_dir is not None:
            logger.info("Cleaning temporary repository...")
            self._temp_dir.cleanup()

        self.repo_path = None


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s"
    )

    url = "https://github.com/pallets/flask.git"

    cloner = RepoCloner()

    try:
        repo = cloner.clone(url)

        print(f"\nRepository cloned to:\n{repo}")

    finally:
        cloner.cleanup()