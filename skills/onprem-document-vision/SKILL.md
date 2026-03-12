---
name: onprem-document-vision
description: Analyze rendered document pages with the on-prem OpenAI-compatible vision model when the active Cline or DeepAgents model cannot reliably inspect images. Use for image-heavy PDFs, scanned PDFs, DOCX files with screenshots or diagrams, layout-critical review, table or figure extraction from rendered pages, and any document task where plain text extraction is insufficient.
---

# On-Prem Document Vision

## Quick start

- Use this skill when the current assistant model cannot inspect images well enough for document review.
- Prefer this skill for scanned PDFs, screenshots inside DOCX, diagrams, tables, slide-like pages, and layout-sensitive review.
- The helper calls the on-prem OpenAI-compatible endpoint directly and returns Markdown or JSON that the non-vision model can continue reasoning over.
- Default model: `Llama-4-Scout`
- Default API root: `http://10.116.240.101:8030/openai`
- Authentication defaults to `OPENAI_API_KEY`

If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/agent/skills`.

## Environment

Optional overrides:

```powershell
$env:OPENAI_BASE_URL="http://10.116.240.101:8030/openai"
$env:OPENAI_MODEL_VISION="Llama-4-Scout"
$env:OPENAI_API_KEY="your-api-key"
```

```bash
export OPENAI_BASE_URL="http://10.116.240.101:8030/openai"
export OPENAI_MODEL_VISION="Llama-4-Scout"
export OPENAI_API_KEY="your-api-key"
```

## Main helper

Analyze a PDF directly:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\path\to\file.pdf"
```

Analyze only the first 5 pages and write Markdown:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\path\to\file.pdf" `
  --max-pages 5 `
  --markdown `
  --markdown-output "C:\temp\file-review.md"
```

Analyze a DOCX with custom instructions:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\path\to\file.docx" `
  --instructions "Extract the visible Korean text, explain diagrams, and identify layout risks."
```

Analyze already-rendered page images in a directory:

```powershell
python "$HOME/.cline/skills/onprem-document-vision/scripts/document_vision_review.py" `
  review "C:\temp\rendered-pages" `
  --pages "1-3,5"
```

## Workflow

1. Decide whether plain text extraction is enough.
2. If the document includes images, scans, tables, or layout-critical content, use this helper instead of relying on the base LLM.
3. Read the helper output before editing or summarizing the document.
4. After meaningful document edits, re-render and re-run the helper when visual fidelity still matters.

## Output

- Default stdout format: JSON
- `--markdown`: print Markdown to stdout
- `--json-output`: write JSON file
- `--markdown-output`: write Markdown file

The JSON result contains:

- source path
- input type
- selected model and API root
- analyzed pages
- per-page analysis text
- final document summary

## Notes

- PDF rendering uses `pypdfium2` and does not require a separate Poppler install.
- DOCX rendering reuses the shared `doc` skill renderer, which depends on LibreOffice plus the Python packages `pypdfium2` and `pillow`.
- If the helper fails because the vision endpoint or API key is missing, stop and fix the environment first.
- For endpoint compatibility notes and prompt patterns, read `references/vision-routing.md`.
