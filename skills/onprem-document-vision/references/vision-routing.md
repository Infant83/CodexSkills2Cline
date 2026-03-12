# On-Prem Document Vision Routing

Use the on-prem document vision helper when local text extraction is not enough.

## Good fit

- scanned PDFs
- image-only PDFs
- DOCX files with screenshots, diagrams, or SmartArt
- forms or reports where the layout itself carries meaning
- tables that are easier to read visually than from extracted text
- QA of final rendering after document edits

## Less useful

- text-only PDFs where `pdfplumber`, `pypdf`, or normal DOCX text extraction already captures the content cleanly
- cases where only a quick string search is needed

## Endpoint assumptions

- The helper uses an OpenAI-compatible chat completions request with image input.
- Default API root: `http://10.116.240.101:8030/openai`
- Default model: `Llama-4-Scout`
- Environment vars:
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL_VISION`
  - `OPENAI_API_KEY`

## Suggested prompt goals

Use prompts that help a non-vision assistant continue the task:

- Extract visible text that plain OCR would likely miss or confuse.
- Describe diagrams, flowcharts, screenshots, and tables in words.
- Call out uncertainty rather than guessing.
- Separate page-local observations from document-level conclusions.
