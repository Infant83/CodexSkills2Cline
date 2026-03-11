---
name: pdf
description: Work with PDF files when reading, creating, or reviewing documents where rendering and layout matter. Prefer visual checks by rendering pages and use Python tools such as reportlab, pdfplumber, and pypdf for generation and extraction.
---

# PDF

## When to use

- Read or review PDF content where layout matters.
- Create PDFs programmatically with reliable formatting.
- Validate final rendering before delivery.

## Workflow

1. Prefer visual review by rendering pages to PNG and inspecting them.
2. Use `reportlab` to generate new PDFs.
3. Use `pdfplumber` or `pypdf` for extraction and quick checks.
4. After each meaningful update, re-render pages and verify alignment, spacing, and legibility.

## Dependencies

Python packages:

```bash
python -m pip install reportlab pdfplumber pypdf
```

Optional system tools for rendering:

```bash
# macOS
brew install poppler

# Ubuntu or Debian
sudo apt-get install -y poppler-utils
```

## Rendering

```bash
pdftoppm -png input.pdf output_prefix
```

## Quality expectations

- Keep typography, spacing, and hierarchy polished.
- Avoid clipped text, overlapping elements, broken tables, or unreadable glyphs.
- Do not deliver until the latest rendered pages are clean.
