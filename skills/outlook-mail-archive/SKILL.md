---
name: outlook-mail-archive
description: Automate desktop Outlook on Windows to inspect received mail, export message bodies, save attachments into separate folders, and build a local mail archive with bundled PowerShell helpers. Use when working with Outlook inboxes, shared mailboxes, or PST/OST stores without relying on cloud mail APIs.
---

# Outlook Mail Archive

## Quick start

- Use this skill on Windows with desktop Outlook installed and a signed-in profile.
- Prefer listing folders before exporting mail.
- Default to read-only export. Do not move, delete, or mark messages unless the user explicitly asks.
- Save each message into its own folder with metadata, body text, original `.msg`, and attachments.

## Folder discovery

List stores and folders first:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/list_outlook_folders.ps1" -MaxDepth 2
```

Use `-AsJson` when another tool should parse the result:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/list_outlook_folders.ps1" -MaxDepth 3 -AsJson
```

## Export mail

Export recent inbox messages into a structured archive:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/export_outlook_mail.ps1" `
  -FolderPath Inbox `
  -OutputRoot "$HOME\Documents\mail-archive" `
  -ReceivedSince "2026-03-01" `
  -MaxItems 50
```

Export a specific mailbox folder and include subfolders:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/export_outlook_mail.ps1" `
  -FolderPath "user@example.com\Inbox\Vendor" `
  -OutputRoot "C:\Archive\VendorMail" `
  -IncludeSubfolders `
  -SubjectContains "invoice"
```

## Output layout

Each exported message is stored under:

```text
<OutputRoot>\<yyyy>\<MM>\<dd>\<timestamp_subject_hash>\
```

Files created per message:

- `message.md` or `message.txt`
- `metadata.json`
- `original.msg`
- `attachments\...`

The export run also writes `manifest-<timestamp>.csv` at the output root.
Text exports are written as UTF-8, and human-opened text files such as `message.md` and `manifest-*.csv` are written with a UTF-8 BOM for better Windows editor and Excel compatibility.

## Folder path notes

- `Inbox`, `Sent`, `Drafts`, `Deleted`, and `Outbox` can be used as aliases for default Outlook folders.
- For mailbox-specific folders, prefer the full store path such as `Mailbox - Team\Inbox\Approvals`.
- Localized Outlook names vary. If a folder path fails, list folders first and reuse the reported path.
- When running from PowerShell 7 or another host, explicitly launch `powershell.exe -STA -File ...` to avoid Outlook COM apartment issues.

## Cautions

- Outlook COM automation can trigger a local security prompt on some systems. If that happens, keep Outlook open and approve access when appropriate.
- Export can be slow on very large folders. Start with `-ReceivedSince`, `-SubjectContains`, or a smaller `-MaxItems`.
- Shared mailboxes depend on what is already visible in the signed-in Outlook profile.
