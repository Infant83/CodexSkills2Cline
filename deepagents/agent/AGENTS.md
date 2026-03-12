# On-Prem DeepAgents Defaults

## Core behavior

- Default response language is Korean unless the user explicitly asks for another language.
- Treat repository contents, documents, notes, and exported artifacts as potentially sensitive.
- Keep work local-first in the on-prem environment.
- Do not send internal content to external services unless the user explicitly asks for it and the environment permits it.
- If a requested capability is unavailable in this environment, say so plainly and continue with the best local fallback.
- When quoting or citing internal material, preserve source paths and dates when available. Do not invent references.

## Skill routing

- Prefer installed shared skills for repeated, multi-step, failure-prone, or stateful tasks.
- Do not create one skill per UI button or per product mode.
- Create or keep a dedicated skill only when the workflow is reused, involves login/session/upload/download handling, has several easy-to-misexecute actions, or needs a stable output structure.
- For PDF or DOCX review that depends on rendered pages, diagrams, screenshots, tables, or other visual content, prefer the shared on-prem document vision skill instead of assuming the active model can inspect images reliably.

## Obsidian capture

Use these defaults when the user asks to save, capture, summarize, organize, or quote Obsidian notes.

### Vault defaults

- First check `OBSIDIAN_VAULT`. If it is set, treat that as the preferred vault path.
- First check `OBSIDIAN_INBOX`. If it is set, treat that as the default inbox path.
- If `OBSIDIAN_INBOX` is not set but `OBSIDIAN_VAULT` is set, use `<OBSIDIAN_VAULT>/00. Inbox`.
- If neither variable is set, use `~/Obsidian_Vault` and `~/Obsidian_Vault/00. Inbox`.

### Rule discovery order

Before saving, searching, or quoting from the vault, check these guidance files if they exist:

1. `00_README_시작하기*`
2. `AGENTS*`
3. `START_HERE*`
4. `90. Settings/*`
5. `Indexes/*`
6. `Templates/*`

If multiple vault documents conflict, prefer the most specific document for the target folder or note type.

### Capture defaults

When the user says things like "메모하자", "옵시디언 저장", or "정리해줘":

1. Prefer saving to the Obsidian vault instead of the current working directory.
2. Resolve the default destination from `OBSIDIAN_INBOX`, then `OBSIDIAN_VAULT/00. Inbox`, then `~/Obsidian_Vault/00. Inbox`.
3. Add YAML frontmatter with at least `type`, `author`, `date created`, `date modified`, `tags`, and `status`.
4. Apply the relevant template from the vault when available.
5. Use the `source/inbox` tag for new captures unless vault rules define something else.
6. Do not create ad-hoc folders unless the user or vault rules require them.

### Note quality and curation

- Add a short TL;DR.
- Include an actionable checklist when relevant.
- Preserve links and references when converting from chats.
- Preserve raw wording when the user asks to keep raw comments.
- Treat `00. Inbox` as capture-first, then curate later.
- Keep curation non-destructive by default.
- Do not delete original content without explicit confirmation.
- Prefer move-with-log or copy-then-confirm-delete when reorganizing notes.
