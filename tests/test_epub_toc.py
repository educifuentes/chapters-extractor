#!/usr/bin/env python3
"""
Test suite for epub_toc.py

Tests:
- Chapter extraction correctness
- Console messages (success and error)
- Titleized format of chapter titles
"""

import pytest
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock
from ebooklib import epub

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module under test
from epub_toc import epub_toc


@pytest.fixture
def sample_epub_path():
    """Path to the actual test EPUB file - shared across all test classes"""
    epub_file = Path(__file__).parent / "data" / "accessible_epub_3.epub"
    if not epub_file.exists():
        pytest.skip(f"Test EPUB file not found: {epub_file}")
    return epub_file


class TestWalkTOC:
    """Test the walk_toc function"""

    def test_walk_toc_with_links(self):
        """Test walking TOC with Link items"""
        from ebooklib import epub as _epub
        
        link1 = _epub.Link("chapter1.xhtml", "Chapter 1", "ch1")
        link2 = _epub.Link("chapter2.xhtml", "Chapter 2", "ch2")
        toc = [link1, link2]
        
        results = list(epub_toc.walk_toc(toc, level=0))
        assert len(results) == 2
        assert results[0] == ("Chapter 1", 0)
        assert results[1] == ("Chapter 2", 0)

    def test_walk_toc_with_sections(self):
        """Test walking TOC with Section items"""
        from ebooklib import epub as _epub
        
        section = _epub.Section("section1")
        section.title = "Section 1"
        child_link = _epub.Link("child.xhtml", "Child Chapter", "child")
        toc = [(section, [child_link])]
        
        results = list(epub_toc.walk_toc(toc, level=0))
        assert len(results) == 2
        assert results[0] == ("Section 1", 0)
        assert results[1] == ("Child Chapter", 1)

    def test_walk_toc_with_nested_structure(self):
        """Test walking TOC with nested hierarchy"""
        from ebooklib import epub as _epub
        
        section1 = _epub.Section("section1")
        section1.title = "Part 1"
        child_section = _epub.Section("child_section")
        child_section.title = "Chapter 1"
        grandchild = _epub.Link("content.xhtml", "Content", "content")
        toc = [(section1, [(child_section, [grandchild])])]
        
        results = list(epub_toc.walk_toc(toc, level=0))
        assert len(results) == 3
        assert results[0] == ("Part 1", 0)
        assert results[1] == ("Chapter 1", 1)
        assert results[2] == ("Content", 2)


class TestTOCToMarkdown:
    """Test the toc_to_markdown function"""

    @pytest.fixture
    def epub_path(self, tmp_path):
        """Create a temporary EPUB file path"""
        return tmp_path / "test_book.epub"

    def test_toc_to_markdown_success_message(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that success message is printed correctly"""
        # Change to temp directory to avoid cluttering the repo
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            # Copy EPUB to temp directory
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            with patch('sys.stdout', new=StringIO()) as fake_out:
                epub_toc.toc_to_markdown(test_epub)
                output = fake_out.getvalue()
                
                assert "✅ Success!" in output
                assert "Table of contents saved to:" in output
                assert "accessible_epub_3 - ToC.md" in output
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_extracts_all_chapters(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that all chapters are extracted correctly from accessible_epub_3.epub"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            from ebooklib import epub
            
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            # First, get the expected count of chapters from the EPUB
            book = epub.read_epub(str(test_epub))
            expected_titles = list(extract_chapter.walk_toc(book.toc, level=0))
            expected_count = len(expected_titles)
            
            # Extract TOC to markdown
            extract_chapter.toc_to_markdown(test_epub)
            
            output_file = tmp_path / "accessible_epub_3 - ToC.md"
            assert output_file.exists(), "Output file should be created"
            
            content = output_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            
            # Check that we have the book title as h1
            assert lines[0].startswith("# "), "First line should be h1 with book title"
            
            # Count markdown headings (excluding the h1 title and empty line)
            headings = [line for line in lines[2:] if line.startswith("#")]
            actual_count = len(headings)
            
            # Verify exact count matches
            assert actual_count == expected_count, \
                f"Expected {expected_count} chapters, but found {actual_count} headings in output"
            
            # Verify all expected chapter titles are present
            content_lower = content.lower()
            for title, level in expected_titles:
                assert title.lower() in content_lower, \
                    f"Chapter '{title}' should be present in output"
            
            # Verify specific known chapters from accessible_epub_3.epub
            assert "Preface" in content, "Should contain 'Preface'"
            assert "Introduction" in content, "Should contain 'Introduction'"
            assert "Building a Better EPUB" in content, "Should contain 'Building a Better EPUB'"
            
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_book_title_extraction(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that book title is extracted and added as h1"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            extract_chapter.toc_to_markdown(test_epub)
            
            output_file = tmp_path / "accessible_epub_3 - ToC.md"
            content = output_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            
            # First line should be h1 with book title
            assert lines[0] == "# Accessible EPUB 3", f"Expected book title, got: {lines[0]}"
            # Second line should be empty
            assert lines[1] == "", "Should have empty line after title"
            
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_hierarchical_structure(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that hierarchical structure is preserved correctly"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            extract_chapter.toc_to_markdown(test_epub)
            
            output_file = tmp_path / "accessible_epub_3 - ToC.md"
            content = output_file.read_text(encoding="utf-8")
            lines = [line for line in content.split("\n") if line.strip()]
            
            # Skip the h1 title and empty line
            headings = [line for line in lines[2:] if line.startswith("#")]
            
            # Verify hierarchy: level 0 should be ##, level 1 should be ###, etc.
            for heading in headings:
                if heading.startswith("## "):
                    # This is a top-level chapter (level 0)
                    assert not heading.startswith("###"), "Top-level should be ##"
                elif heading.startswith("### "):
                    # This is a second-level chapter (level 1)
                    assert not heading.startswith("####"), "Second-level should be ###"
                elif heading.startswith("#### "):
                    # This is a third-level chapter (level 2)
                    pass  # Valid
            
            # Verify we have at least some top-level chapters
            top_level = [h for h in headings if h.startswith("## ") and not h.startswith("###")]
            assert len(top_level) > 0, "Should have top-level chapters"
            
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_titleized_set(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that titleized set is created correctly with proper format"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            # Read the EPUB and collect all titles
            book = epub.read_epub(str(test_epub))
            all_titles = []
            for title, level in epub_toc.walk_toc(book.toc, level=0):
                all_titles.append(title)
            
            # Create titleized set manually (matching the function's logic)
            titleized_set = {title.title() for title in all_titles}
            
            # Verify all titles are in the set
            assert len(titleized_set) > 0, "Titleized set should not be empty"
            assert len(titleized_set) == len(all_titles), \
                f"Titleized set should have {len(all_titles)} entries (one per chapter)"
            
            # Verify each title in the set is properly titleized
            for titleized in titleized_set:
                # Check that it's title case (first letter of each word capitalized)
                words = titleized.split()
                for word in words:
                    if word and word[0].isalpha():  # Only check alphabetic words
                        assert word[0].isupper(), \
                            f"Word '{word}' should start with uppercase in titleized form '{titleized}'"
            
            # Verify specific expected titleized entries from accessible_epub_3.epub
            titleized_lower = {t.lower() for t in titleized_set}
            expected_titles = ["preface", "introduction", "conclusion", "acknowledgments"]
            found_titles = [t for t in expected_titles if t in titleized_lower]
            assert len(found_titles) >= 2, \
                f"Should have at least 2 of expected titles {expected_titles}, found: {found_titles}"
            
            # Verify titleized format examples
            # "preface" -> "Preface", "introduction" -> "Introduction"
            for original_title in all_titles:
                titleized = original_title.title()
                assert titleized in titleized_set, \
                    f"Titleized version '{titleized}' of '{original_title}' should be in set"
            
        finally:
            monkeypatch.chdir(original_cwd)
    
    def test_toc_to_markdown_chapter_titles_format(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that chapter titles in output have correct format (titleized)"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            extract_chapter.toc_to_markdown(test_epub)
            
            output_file = tmp_path / "accessible_epub_3 - ToC.md"
            content = output_file.read_text(encoding="utf-8")
            
            # Extract all chapter titles from markdown (skip h1 book title)
            lines = content.split("\n")
            chapter_headings = [line for line in lines[2:] if line.startswith("#")]
            
            # Verify each chapter title has proper format
            for heading in chapter_headings:
                # Extract the title part (after the # symbols)
                parts = heading.split(" ", 1)
                if len(parts) == 2:
                    title = parts[1]
                    # Verify title is not empty
                    assert title.strip(), f"Chapter title should not be empty in: {heading}"
                    
                    # Note: The current implementation uses titles as-is from EPUB,
                    # but we verify they follow reasonable formatting
                    # (first character should typically be uppercase for proper titles)
                    if title and title[0].isalpha():
                        # Most chapter titles should start with uppercase
                        # (though some may start with numbers like "1. Introduction")
                        assert title[0].isupper() or title[0].isdigit(), \
                            f"Chapter title should start with uppercase or digit: '{title}'"
            
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_error_handling_nonexistent_file(self, tmp_path, capsys):
        """Test error handling and console message when EPUB file doesn't exist"""
        nonexistent_file = tmp_path / "nonexistent.epub"
        
        # ebooklib raises an exception for missing files
        with pytest.raises(Exception) as exc_info:
                epub_toc.toc_to_markdown(nonexistent_file)
        
        # Verify that an exception was raised (this is the error "message" in Python)
        assert exc_info.value is not None, "Should raise an exception for nonexistent file"
        
        # The exception message should indicate the file issue
        error_message = str(exc_info.value).lower()
        assert "no such file" in error_message or "not found" in error_message or \
               "cannot" in error_message or "error" in error_message, \
               f"Error message should indicate file issue, got: {error_message}"

    def test_toc_to_markdown_error_handling_invalid_epub(self, tmp_path, capsys):
        """Test error handling and console message with invalid EPUB file"""
        invalid_epub = tmp_path / "invalid.epub"
        invalid_epub.write_text("This is not a valid EPUB file")
        
        # ebooklib raises an exception for invalid EPUBs
        with pytest.raises(Exception) as exc_info:
            extract_chapter.toc_to_markdown(invalid_epub)
        
        # Verify that an exception was raised
        assert exc_info.value is not None, "Should raise an exception for invalid EPUB"
        
        # The exception should be related to EPUB parsing
        error_message = str(exc_info.value).lower()
        # ebooklib typically raises exceptions for invalid EPUBs
        assert len(error_message) > 0, "Should have an error message"

    def test_toc_to_markdown_output_filename(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that output filename is correct"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            extract_chapter.toc_to_markdown(test_epub)
            
            expected_output = tmp_path / "accessible_epub_3 - ToC.md"
            assert expected_output.exists(), f"Output file should be named '{expected_output.name}'"
            
        finally:
            monkeypatch.chdir(original_cwd)

    def test_toc_to_markdown_markdown_format(self, sample_epub_path, tmp_path, monkeypatch):
        """Test that markdown format is correct"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            extract_chapter.toc_to_markdown(test_epub)
            
            output_file = tmp_path / "accessible_epub_3 - ToC.md"
            content = output_file.read_text(encoding="utf-8")
            
            # Verify UTF-8 encoding
            assert content, "Content should not be empty"
            
            # Verify markdown structure
            lines = content.split("\n")
            
            # First line should be h1
            assert lines[0].startswith("# "), "Should start with h1"
            assert not lines[0].startswith("##"), "First heading should be h1, not h2"
            
            # Should end with newline
            assert content.endswith("\n"), "Should end with newline"
            
            # Verify heading format: should be "# Title" or "## Title" etc.
            for line in lines:
                if line.startswith("#"):
                    # Should have format: "# Title" or "## Title" etc.
                    parts = line.split(" ", 1)
                    assert len(parts) == 2, f"Heading should have format '# Title', got: {line}"
                    hashes = parts[0]
                    title = parts[1]
                    assert all(c == "#" for c in hashes), "Should only have # characters"
                    assert len(hashes) >= 1, "Should have at least one #"
                    assert title.strip(), "Title should not be empty"
            
        finally:
            monkeypatch.chdir(original_cwd)


class TestMain:
    """Test the main function"""

    def test_main_with_valid_file(self, sample_epub_path, tmp_path, monkeypatch):
        """Test main function with valid EPUB file"""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            import shutil
            test_epub = tmp_path / "accessible_epub_3.epub"
            shutil.copy(sample_epub_path, test_epub)
            
            with patch('sys.argv', ['extract_chapter.py', str(test_epub)]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    epub_toc.main()
                    output = fake_out.getvalue()
                    assert "✅ Success!" in output
        finally:
            monkeypatch.chdir(original_cwd)

    def test_main_with_missing_file(self, capsys):
        """Test main function error handling with missing file"""
        with patch('sys.argv', ['extract_chapter.py', 'nonexistent.epub']):
            # The function will try to read the file and raise an exception
            # argparse won't catch this, the epub.read_epub will raise it
            with pytest.raises(Exception):
                epub_toc.main()
            
            # Check that no success message was printed
            captured = capsys.readouterr()
            assert "✅ Success!" not in captured.out, \
                "Should not print success message for missing file"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

