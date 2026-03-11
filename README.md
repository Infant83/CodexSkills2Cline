# Cline On-Prem Starter Pack

This folder packages a small Cline starter set for an on-prem environment.

Included:

- Global or project-local Cline rules
- Two reusable workflows
- Five local-first skills:
  - `openproject`
  - `doc`
  - `pdf`
  - `spreadsheet`
  - `jupyter-notebook`

Excluded on purpose:

- `playwright`
- `hwpx`
- NotebookLM, Genspark, email, and other external-service-heavy skills

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

What the installer copies:

- Global rules: `~/Documents/Cline/Rules`
- Global workflows: `~/Documents/Cline/Workflows`
- Global skills: `~/.cline/skills`

Project mode copies to:

- `<repo>\.clinerules`
- `<repo>\.clinerules\workflows`
- `<repo>\.cline\skills`

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

## Obsidian path setup

If your Obsidian vault location is not the default, set these variables in the shell or your approved environment loader:

```powershell
$env:OBSIDIAN_VAULT="C:\path\to\vault"
$env:OBSIDIAN_INBOX="C:\path\to\vault\00. Inbox"
```

The included rules and workflows prefer `OBSIDIAN_VAULT` and `OBSIDIAN_INBOX` when they are present, then fall back to `~/Obsidian_Vault` and `~/Obsidian_Vault/00. Inbox`.

## Notes

- The Obsidian rules are intentionally generic. Adjust the preferred vault path or template conventions for your team.
- The OpenProject skill is sanitized for internal reuse. It does not contain user-specific URLs or credentials.
