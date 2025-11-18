#!/usr/bin/env python3
"""
epub_toc_to_markdown.py

Extract the hierarchical table of contents (TOC) from an EPUB file and save it
as a Markdown file named:

    "<EPUB filename> - ToC.md"

Hierarchy:
    Top-level entries → ## heading
    Second level     → ### heading
    Third level      → #### heading
    etc.

Usage:
    python epub_toc_to_markdown.py book.epub
"""

import argparse
from pathlib import Path
from ebooklib import epub


SCRIPT_NAME = "epub_toc_to_markdown"


def walk_toc(toc, level=0):
    """
    Recursively walk EPUB TOC.
    Yield tuples: (title, level)
    """
    from ebooklib import epub as _epub

    for item in toc:

        # Case 1: item is a simple link
        if isinstance(item, _epub.Link):
            if item.title:
                yield item.title.strip(), level

        # Case 2: item is a Section with children: (SectionObj, [children])
        elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], _epub.Section):
            section, children = item
            if getattr(section, "title", None):
                yield section.title.strip(), level

            # recurse into children
            for t, l in walk_toc(children, level + 1):
                yield t, l

        # Case 3: bare Section object (rare)
        elif isinstance(item, _epub.Section):
            if getattr(item, "title", None):
                yield item.title.strip(), level


def toc_to_markdown(epub_path: Path):
    book = epub.read_epub(str(epub_path))

    # Output filename based on EPUB filename (not metadata)
    base_name = epub_path.stem
    output_file = epub_path.with_name(f"{base_name} - ToC.md")

    md_lines = []

    for title, level in walk_toc(book.toc, level=0):
        heading_level = level + 2     # level 0 → ##, level 1 → ###, etc.
        hashes = "#" * heading_level
        md_lines.append(f"{hashes} {title}")

    output_file.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] TOC saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Extract EPUB ToC and save it as '<filename> - ToC.md' with hierarchical headings."
    )
    parser.add_argument("epub_file", help="Path to the EPUB file")

    args = parser.parse_args()
    toc_to_markdown(Path(args.epub_file))


if __name__ == "__main__":
    main()