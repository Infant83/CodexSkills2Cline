# Obsidian Policy

Use these rules when the user asks to save, capture, summarize, organize, or quote Obsidian notes.

## Vault defaults

- Preferred vault path: `~/Obsidian_Vault`
- Default inbox path: `~/Obsidian_Vault/00. Inbox`

## Rule discovery order

Before saving, searching, or quoting from the vault, check these guidance files if they exist:

1. `00_README_시작하기*`
2. `AGENTS*`
3. `START_HERE*`
4. `90. Settings/*`
5. `Indexes/*`
6. `Templates/*`

If multiple vault documents conflict, prefer the most specific document for the target folder or note type.

## Capture defaults

When the user says things like "메모하자", "옵시디언 저장", or "정리해줘":

1. Prefer saving to the Obsidian vault instead of the current working directory.
2. If no destination rule is found, save to `00. Inbox`.
3. Add YAML frontmatter with at least:
   - `type`
   - `author`
   - `date created`
   - `date modified`
   - `tags`
   - `status`
4. Apply the relevant template from the vault when available.
5. Use the `source/inbox` tag for new captures unless vault rules define something else.
6. Do not create ad-hoc folders unless the user or vault rules require them.

## Note quality

- Add a short TL;DR.
- Include an actionable checklist when relevant.
- Preserve links and references when converting from chats.
- Preserve raw wording when the user asks to keep raw comments.

## Curation policy

- Treat `00. Inbox` as capture-first, then curate later.
- Keep curation non-destructive by default.
- Do not delete original content without explicit confirmation.
- Prefer move-with-log or copy-then-confirm-delete when reorganizing notes.
