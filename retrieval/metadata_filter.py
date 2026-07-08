"""
metadata_filter.py

Creates metadata filters for vector search.

Supports:
- chunk_type
- extension
- directory
- module
- git recency
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List


class MetadataFilter:

    def __init__(self):
        pass

    ####################################################################
    # Build filter dictionary
    ####################################################################

    def build_filter(
        self,
        chunk_type: Optional[str] = None,
        extension: Optional[str] = None,
        directory: Optional[str] = None,
        module: Optional[str] = None,
        modified_within_days: Optional[int] = None
    ) -> Dict:

        filters = []

        if chunk_type:
            filters.append({
                "chunk_type": chunk_type
            })

        if extension:
            filters.append({
                "extension": extension
            })

        if directory:
            filters.append({
                "directory": directory
            })

        if module:
            filters.append({
                "module": module
            })

        if modified_within_days:

            cutoff = (
                datetime.utcnow()
                - timedelta(days=modified_within_days)
            ).isoformat()

            filters.append({
                "git_date": {
                    "$gte": cutoff
                }
            })

        if len(filters) == 0:
            return {}

        if len(filters) == 1:
            return filters[0]

        return {
            "$and": filters
        }

    ####################################################################
    # Infer filters from natural language
    ####################################################################

    def infer_from_query(self, query: str) -> Dict:

        q = query.lower()

        chunk_type = None
        extension = None
        directory = None
        module = None
        recent = None

        ###########################################################
        # Chunk Type
        ###########################################################

        if "function" in q:
            chunk_type = "function"

        elif "docstring" in q:
            chunk_type = "docstring"

        elif "comment" in q:
            chunk_type = "comment"

        elif "markdown" in q or "documentation" in q:
            chunk_type = "markdown"

        ###########################################################
        # Extension
        ###########################################################

        if "python" in q:
            extension = ".py"

        elif "javascript" in q:
            extension = ".js"

        elif "typescript" in q:
            extension = ".ts"

        elif "markdown" in q:
            extension = ".md"

        elif "json" in q:
            extension = ".json"

        elif "yaml" in q:
            extension = ".yaml"

        ###########################################################
        # Directory
        ###########################################################

        directories = [
            "src",
            "tests",
            "docs",
            "config",
            "api",
            "models",
            "services",
            "database",
            "frontend",
            "backend"
        ]

        for d in directories:
            if d in q:
                directory = d
                break

        ###########################################################
        # Module
        ###########################################################

        if "authentication" in q:
            module = "auth"

        elif "inventory" in q:
            module = "inventory"

        elif "finance" in q:
            module = "finance"

        elif "payment" in q:
            module = "payment"

        ###########################################################
        # Recency
        ###########################################################

        if "recent" in q:
            recent = 30

        elif "latest" in q:
            recent = 7

        elif "new" in q:
            recent = 14

        return self.build_filter(
            chunk_type=chunk_type,
            extension=extension,
            directory=directory,
            module=module,
            modified_within_days=recent
        )
    

    