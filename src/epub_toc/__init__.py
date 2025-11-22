"""
EPUB Table of Contents to Markdown converter.

This package provides functionality to extract the table of contents
from EPUB files and convert them to Markdown format.
"""

from epub_toc.epub_toc import toc_to_markdown, walk_toc

__all__ = ["toc_to_markdown", "walk_toc"]
__version__ = "0.1.0"

