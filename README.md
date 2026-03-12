# Cline On-Prem Starter Pack

This folder packages a small Cline starter set for an on-prem environment.

Included:

- Global or project-local Cline rules
- Two reusable workflows
- Six local-first skills:
  - `openproject`
  - `doc`
  - `pdf`
  - `spreadsheet`
  - `jupyter-notebook`
  - `outlook-mail-archive`

Excluded on purpose:

- `playwright`
- `hwpx`
- NotebookLM, Genspark, and other external-service-heavy skills

## Folder layout

- `Rules/`: install to Cline rules
- `Workflows/`: install to Cline workflows
- `skills/`: install to Cline skills
- `examples/`: environment examples for internal tools

## Install

Global install on Windows PowerShell:

```powershell
pwsh .\install.ps1 -Scope Global
```

Project-local install into a repo:

```powershell
pwsh .\install.ps1 -Scope Project -ProjectPath C:\path\to\repo
```

Global install on Linux with PowerShell 7:

```bash
pwsh ./install.ps1 -Scope Global
```

Project-local install on Linux with PowerShell 7:

```bash
pwsh ./install.ps1 -Scope Project -ProjectPath /path/to/repo
```

Manual install on Linux without PowerShell:

```bash
mkdir -p "$HOME/Documents/Cline/Rules" "$HOME/Documents/Cline/Workflows" "$HOME/.cline/skills"
cp -R Rules/. "$HOME/Documents/Cline/Rules/"
cp -R Workflows/. "$HOME/Documents/Cline/Workflows/"
cp -R skills/. "$HOME/.cline/skills/"
```

What the installer copies:

- Global rules: `~/Documents/Cline/Rules`
- Global workflows: `~/Documents/Cline/Workflows`
- Global skills: `~/.cline/skills`

Project mode copies to:

- `<repo>\.clinerules`
- `<repo>\.clinerules\workflows`
- `<repo>\.cline\skills`

On Linux, the same layout resolves to:

- `<repo>/.clinerules`
- `<repo>/.clinerules/workflows`
- `<repo>/.cline/skills`

The installer overwrites files with the same names, but it does not delete old files that are no longer present in this pack.

## OpenProject setup

Copy the example file and set your internal values:

```powershell
Copy-Item .\examples\openproject.env.example .\openproject.env
```

Set these variables in the shell or your company-approved secret manager:

- `OPENPROJECT_BASE_URL`
- `OPENPROJECT_API_KEY`

## Verify

After installation:

1. Restart or reload Cline.
2. Confirm the rules appear in Cline.
3. Confirm the skills appear in Cline.
4. For OpenProject, test:

```powershell
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

5. For Jupyter scaffolding, test:

```powershell
python "$HOME/.cline/skills/jupyter-notebook/scripts/new_notebook.py" --help
```

6. For Outlook archiving on Windows, test:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/list_outlook_folders.ps1" -MaxDepth 1
```

7. To export a small inbox sample:

```powershell
powershell -STA -File "$HOME/.cline/skills/outlook-mail-archive/scripts/export_outlook_mail.ps1" `
  -FolderPath Inbox `
  -OutputRoot "$HOME\Documents\mail-archive" `
  -MaxItems 5
```

## Outlook setup

This skill is Windows-only and expects:

- Desktop Outlook installed
- At least one mailbox profile already signed in
- Local permission to let Outlook COM read messages and save attachments

If the folder alias does not work because of a localized mailbox, run the folder listing command first and reuse the exact reported folder path.
If you invoke the scripts from PowerShell 7 or another host, call them through `powershell.exe -STA -File ...` so Outlook COM runs in the expected apartment model.

## Obsidian path setup

If your Obsidian vault location is not the default, set these variables in the shell or your approved environment loader:

```powershell
$env:OBSIDIAN_VAULT="C:\path\to\vault"
$env:OBSIDIAN_INBOX="C:\path\to\vault\00. Inbox"
```

The included rules and workflows prefer `OBSIDIAN_VAULT` and `OBSIDIAN_INBOX` when they are present, then fall back to `~/Obsidian_Vault` and `~/Obsidian_Vault/00. Inbox`.

## Encoding note for on-prem Windows

Some on-prem Windows environments still default Python console IO to `cp949`. If you see garbled Korean text or `UnicodeEncodeError`, prefer UTF-8 mode before running the bundled Python helpers:

```powershell
$env:PYTHONUTF8="1"
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

The bundled Python scripts also reconfigure `stdout` and `stderr` to UTF-8 where supported, but setting `PYTHONUTF8=1` is still the safest shell-level default.

## Notes

- The Obsidian rules are intentionally generic. Adjust the preferred vault path or template conventions for your team.
- The OpenProject skill is sanitized for internal reuse. It does not contain user-specific URLs or credentials.
