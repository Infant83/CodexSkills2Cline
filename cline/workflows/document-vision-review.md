# Document Vision Review Workflow

Use this workflow when the user asks to read, review, summarize, QA, or revise a PDF or DOCX whose meaning depends on rendered pages, images, tables, diagrams, or page layout.

## Steps

1. Decide whether plain text extraction is enough.
   - If the document is text-heavy and layout is not important, use normal extraction first.
   - If the document is scanned, image-heavy, table-heavy, screenshot-heavy, or layout-sensitive, use the on-prem document vision helper.

2. Use the shared vision helper.
   - Run `onprem-document-vision/scripts/document_vision_review.py`.
   - Use the default on-prem endpoint unless the environment overrides it.
   - Prefer `Llama-4-Scout` unless the user specifies another on-prem vision model.

3. Read before editing.
   - Review the helper output before making document changes or final claims.
   - Treat the helper output as the visual ground truth when the active model itself lacks vision.

4. Re-run after meaningful edits.
   - If the document changes in a way that affects layout, tables, or screenshots, re-render and run the helper again.

5. Report remaining risk.
   - If the helper could not be used, state that visual-only issues may remain.
   - If the helper saw uncertainty, surface that uncertainty instead of masking it.
