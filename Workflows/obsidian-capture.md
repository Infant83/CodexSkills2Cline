# Obsidian Capture Workflow

Use this workflow when the user wants notes, summaries, chats, or rough material saved into Obsidian.

## Steps

1. Resolve the vault path.
   - Prefer `OBSIDIAN_VAULT` when it is set.
   - Otherwise use `~/Obsidian_Vault`.
   - If the vault has a more specific local rule, follow that instead.

2. Discover vault guidance before writing.
   - Check `00_README_시작하기*`, `AGENTS*`, `START_HERE*`, `90. Settings/*`, `Indexes/*`, and `Templates/*`.

3. Decide the destination.
   - If the user or vault rules provide a target folder, use it.
   - Otherwise use `OBSIDIAN_INBOX` when it is set.
   - If `OBSIDIAN_INBOX` is not set, use `<vault>/00. Inbox`.

4. Create or update the note.
   - Add YAML frontmatter with `type`, `author`, `date created`, `date modified`, `tags`, and `status`.
   - Apply the relevant vault template when available.
   - Add a short TL;DR.
   - Add an actionable checklist when relevant.
   - Preserve links, references, and raw wording if the user asked for it.

5. Keep curation safe.
   - Do not delete original text without confirmation.
   - Prefer move-with-log or copy-then-confirm-delete.

6. Report back.
   - Say where the note was saved.
   - Mention any template or naming rule applied.
   - Call out missing vault guidance if none was found.
