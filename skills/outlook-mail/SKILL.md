---
name: outlook-mail
description: Read, search, filter, extract, archive, draft, and send Outlook mail on Windows through a Python helper backed by desktop Outlook COM. Use when working with Outlook inboxes, shared mailboxes, PST/OST stores, message body extraction, attachment download, or controlled outbound mail actions.
---

# Outlook Mail

## Quick start

- Use this skill on Windows with classic desktop Outlook installed and a signed-in profile.
- If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/agent/skills`.
- The core logic is Python-based and requires `pywin32`.
- Default to read-only commands unless the user explicitly asks to draft or send mail.
- If the user asks to "write" an email but does not explicitly say to send it, create a draft instead of sending.
- Draft or send mail without extra recipient confirmation only when every recipient matches the detected self address `<username>@lgdisplay.com`.
- The default self address is derived from the current OS username. If that is wrong, set `OUTLOOK_MAIL_SELF_ADDRESS` before using `draft-message` or `send-message`.
- For any other `To`, `CC`, or `BCC` recipient, ask the user first and only proceed after explicit approval.

## Dependency

Install the Outlook Python bridge first:

```powershell
python -m pip install pywin32
```

## Wrapper

Use the bundled PowerShell wrapper for normal execution:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" --help
```

The wrapper sets UTF-8-friendly Python environment variables and forwards all arguments to the Python helper.

## Read and search mail

List available stores and folders:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" list-folders --max-depth 2
```

Search unread messages in the inbox from a specific sender:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" search-messages `
  --folder-path Inbox `
  --unread-only `
  --sender-contains "vendor@example.com" `
  --max-items 20
```

Search messages with attachments and structured JSON output:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" search-messages `
  --folder-path "Mailbox - Team\Inbox" `
  --has-attachments `
  --subject-contains "invoice" `
  --json
```

## Extract message content

Fetch one message body by `entry_id`:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" get-message `
  --entry-id "<entry-id>" `
  --body-format markdown
```

## Export messages and download attachments

Export matching messages, metadata, original `.msg`, and attachments:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" export-messages `
  --folder-path Inbox `
  --received-since "2026-03-01" `
  --output-root "$HOME\Documents\mail-archive" `
  --max-items 50
```

If attachment download is the main goal, filter first and export only matching messages:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" export-messages `
  --folder-path Inbox `
  --has-attachments `
  --attachment-name-contains ".pdf" `
  --output-root "C:\Archive\Attachments" `
  --max-items 20
```

## Draft and send mail

Create a draft for the detected default recipient:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" draft-message `
  --to "${env:USERNAME}@lgdisplay.com" `
  --subject "Follow-up" `
  --body "Please review the attached note." `
  --explicit-write-request
```

If the detected address is wrong for your mailbox alias, set an override first:

```powershell
$env:OUTLOOK_MAIL_SELF_ADDRESS="actual.user@lgdisplay.com"
```

Send mail only when the user explicitly asked to send now:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" send-message `
  --to "${env:USERNAME}@lgdisplay.com" `
  --subject "Approved update" `
  --body "The update is complete." `
  --explicit-write-request `
  --confirm-send
```

For any recipient outside the detected self address, ask the user first and then include an approval flag for each approved address:

```powershell
powershell -File "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.ps1" draft-message `
  --to user@example.com `
  --subject "Requested draft" `
  --body "Draft body" `
  --explicit-write-request `
  --allow-recipient user@example.com
```

## Output layout

`export-messages` stores each message under:

```text
<OutputRoot>\<yyyy>\<MM>\<dd>\<timestamp_subject_hash>\
```

Files created per message:

- `message.md` or `message.txt`
- `metadata.json`
- `original.msg`
- `attachments\...`

The export run also writes `manifest-<timestamp>.csv` at the output root.
Text exports are written as UTF-8, and human-opened text files such as `message.md`, `message.txt`, and `manifest-*.csv` are written with a UTF-8 BOM for better Windows editor and Excel compatibility.

## Cautions

- This skill depends on desktop Outlook COM, so it is Windows-only even if the repo is shared with DeepAgents on other platforms.
- Shared mailboxes depend on what is already visible in the signed-in Outlook profile.
- Outlook may show a security prompt on some systems when COM reads message data or attachments.
- Do not use `draft-message` or `send-message` unless the user explicitly requested a mail-writing action in the current turn.
