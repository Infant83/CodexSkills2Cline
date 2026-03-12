---
name: doc
description: Work with DOCX files when reading, creating, or editing documents where formatting and layout fidelity matter. Prefer python-docx for structure edits, use the bundled render_docx.py helper for rendering, and route image-heavy or layout-critical review through the shared on-prem document vision helper when the active model lacks vision.
---

# DOCX

## When to use

- Read or review DOCX content where layout matters.
- Create or edit DOCX files with professional formatting.
- Validate visual layout before delivery.

## Workflow

If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/agent/skills`.

1. Prefer visual review for layout, tables, diagrams, and pagination.
2. Use `python-docx` for edits and structured creation.
3. If the current Cline model cannot inspect images well enough, route rendered pages or the DOCX itself through `onprem-document-vision`.
4. Re-render and inspect after meaningful changes.
5. If visual review is not possible, extract text as a fallback and call out layout risk.

## Rendering helper

Bundled helper:

```bash
python "$HOME/.cline/skills/doc/scripts/render_docx.py" /path/to/file.docx --output_dir /tmp/docx_pages
```

The helper renders DOCX through LibreOffice and rasterizes the resulting PDF with `pypdfium2`.

If the active model lacks vision, use the shared on-prem document vision helper directly:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\path\to\file.docx" `
  --instructions "Extract visible text, explain diagrams, and call out layout issues." `
  --markdown
```

## Dependencies

Python packages:

```bash
python -m pip install python-docx pypdfium2 pillow
```

Required system tools for rendering:

```bash
# macOS
brew install libreoffice

# Ubuntu or Debian
sudo apt-get install -y libreoffice
```

## Quality expectations

- Deliver a polished document with consistent typography, spacing, margins, and hierarchy.
- Avoid clipped text, broken tables, unreadable characters, or placeholder styling.
- Re-render and inspect every page before final delivery when possible.
- If only text fallback was available, say that screenshots, diagrams, or layout-sensitive issues may remain.
