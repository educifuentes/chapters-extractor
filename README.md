# chapters-extractor

A command-line tool that extracts chapters from an EPUB file and converts them into a hierarchical table of contents.

## Requirements

- Python 3.7+
- ebooklib

## Installation (macOS)

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
pip3 install ebooklib
chmod +x chapters-extractor.py
sudo cp chapters-extractor.py /usr/local/bin/chapters-extractor
```

## Usage

```bash
chapters-extractor MyBook.epub
```