---
name: doc
description: Work with DOCX files when reading, creating, or editing documents where formatting and layout fidelity matter. Prefer python-docx for structure edits and use the bundled render_docx.py helper for visual checks.
---

# DOCX

## When to use

- Read or review DOCX content where layout matters.
- Create or edit DOCX files with professional formatting.
- Validate visual layout before delivery.

## Workflow

If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/skills`.

1. Prefer visual review for layout, tables, diagrams, and pagination.
2. Use `python-docx` for edits and structured creation.
3. Re-render and inspect after meaningful changes.
4. If visual review is not possible, extract text as a fallback and call out layout risk.

## Rendering helper

Bundled helper:

```bash
python "$HOME/.cline/skills/doc/scripts/render_docx.py" /path/to/file.docx --output_dir /tmp/docx_pages
```

If `soffice` and `pdftoppm` are available, DOCX can also be rendered through PDF first.

## Dependencies

Python packages:

```bash
python -m pip install python-docx pdf2image
```

Optional system tools for rendering:

```bash
# macOS
brew install libreoffice poppler

# Ubuntu or Debian
sudo apt-get install -y libreoffice poppler-utils
```

## Quality expectations

- Deliver a polished document with consistent typography, spacing, margins, and hierarchy.
- Avoid clipped text, broken tables, unreadable characters, or placeholder styling.
- Re-render and inspect every page before final delivery when possible.
