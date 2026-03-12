---
name: pdf
description: Work with PDF files when reading, creating, or reviewing documents where rendering and layout matter. Prefer local extraction for text PDFs, and when scanned pages, tables, diagrams, or layout-critical review require image understanding, use the shared on-prem document vision helper.
---

# PDF

## When to use

If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/agent/skills`.

- Read or review PDF content where layout matters.
- Create PDFs programmatically with reliable formatting.
- Validate final rendering before delivery.

## Workflow

1. Use `pdfplumber` or `pypdf` first for text-heavy PDFs and quick checks.
2. If the PDF is scanned, image-heavy, table-heavy, or layout-sensitive, route it through `onprem-document-vision` instead of assuming the base LLM can inspect rendered pages.
3. Use `reportlab` to generate new PDFs.
4. After each meaningful update, re-render pages and verify alignment, spacing, and legibility.

## Dependencies

Python packages:

```bash
python -m pip install reportlab pdfplumber pypdf pypdfium2 pillow
```

`pypdfium2` handles page rendering directly, so no separate Poppler install is required for the shared PDF review path.

## Rendering

If the active Cline model does not support vision well, use the shared on-prem vision helper:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\path\to\file.pdf" `
  --max-pages 5 `
  --markdown
```

## Quality expectations

- Keep typography, spacing, and hierarchy polished.
- Avoid clipped text, overlapping elements, broken tables, or unreadable glyphs.
- Do not deliver until the latest rendered pages are clean.
- If visual verification could not be completed through the on-prem vision helper, state that risk explicitly.
