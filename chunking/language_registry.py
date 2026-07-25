"""
Language Registry

Responsible for:
- Providing Tree-sitter parsers for supported languages.
- Checking whether a language is supported.
"""

from __future__ import annotations

from tree_sitter import Parser
from tree_sitter_language_pack import get_language


class LanguageRegistry:
    """
    Loads and caches Tree-sitter parsers.
    """

    def __init__(self):
        self._parsers: dict[str, Parser] = {}

    def get_parser(self, language: str) -> Parser:
        """
        Returns a cached parser for the requested language.

        Parameters
        ----------
        language : str
            e.g. "python", "javascript", "java"

        Returns
        -------
        Parser
        """

        language = language.lower()

        if language in self._parsers:
            return self._parsers[language]

        try:
            ts_language = get_language(language)

        except Exception as e:
            raise ValueError(
                f"Tree-sitter grammar not available for '{language}'"
            ) from e

        parser = Parser(ts_language)

        self._parsers[language] = parser

        return parser

    def supports(self, language: str) -> bool:
        """
        Returns True if Tree-sitter supports the language.
        """

        try:
            get_language(language.lower())
            return True
        except Exception:
            return False