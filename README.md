# Cline / DeepAgents On-Prem Starter Pack

This repository is split into three layers:

- `skills/`: shared skills reused by both Cline and DeepAgents
- `cline/`: Cline-only rules and workflows
- `deepagents/`: DeepAgents-only defaults such as `AGENTS.md` and `config.toml`

The pack is designed for an on-prem environment. Shared skills stay self-contained, while agent-specific behavior is separated by client.

## Included

- Shared skills:
  - `openproject`
  - `doc`
  - `pdf`
  - `spreadsheet`
  - `jupyter-notebook`
  - `outlook-mail`
- Cline-only assets:
  - global rules
  - reusable workflows
- DeepAgents-only assets:
  - `AGENTS.md`
  - `config.toml`

Excluded on purpose:

- `playwright`
- `hwpx`
- NotebookLM, Genspark, and other external-service-heavy skills

## Repository layout

```text
skills/                  shared skills for both agents
cline/rules/             Cline-only rule files
cline/workflows/         Cline-only workflow files
deepagents/config.toml   DeepAgents model/provider defaults
deepagents/agent/AGENTS.md
                         DeepAgents always-on instructions
examples/                internal environment examples
scripts/                 repo maintenance helpers
```

## Install

The default installers install both Cline and DeepAgents together.
When installing shared skills, the installer replaces any existing skill directory with the same name before copying the new version.

### Windows

Recommended:

```powershell
.\install.cmd
```

PowerShell entry point with explicit execution-policy bypass:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Install only one side when needed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target Cline
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target DeepAgents
```

If you use a non-default DeepAgents agent name:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DeepAgentsAgentName my-agent
```

### Linux

Recommended:

```bash
bash ./install.sh
```

Install only one side when needed:

```bash
bash ./install.sh --target cline
```

```bash
bash ./install.sh --target deepagents
```

If you use a non-default DeepAgents agent name:

```bash
bash ./install.sh --deepagents-agent-name my-agent
```

## Installed locations

### Cline

Managed copies:

- `~/.cline/rules`
- `~/.cline/workflows`
- `~/.cline/skills`

Runtime sync targets:

- `~/Documents/Cline/Rules`
- `~/Documents/Cline/Workflows`

The installer keeps a managed copy under `~/.cline` and also syncs rules/workflows into the global Cline runtime directories.

### DeepAgents

Managed copies:

- `~/.deepagents/config.toml`
- `~/.deepagents/agent/AGENTS.md`
- `~/.deepagents/agent/skills`

The default DeepAgents agent name is `agent`. Override it with:

- PowerShell: `-DeepAgentsAgentName`
- Bash: `--deepagents-agent-name`

## DeepAgents config

`deepagents/config.toml` is intended to replace `~/.deepagents/config.toml`.

This pack configures:

- `default = "openai:Qwen3-Coder-480B-A35B-Instruct"`
- `recent = "openai:Qwen3-Codex-480B-A35B-Instruct"`
- the built-in `openai` provider pointed at the on-prem OpenAI-compatible endpoint `http://10.116.240.101:8030/openai`

Because the endpoint is OpenAI-compatible, the config uses the standard `openai:` provider prefix instead of a custom alias.
If the DeepAgents environment does not have the OpenAI provider dependency available, install `langchain-openai` in the same Python environment as `deepagents`.

## Verify

After installation:

1. Restart or reload both clients.
2. For Cline, confirm rules and workflows appear after the global sync.
3. For DeepAgents, confirm `~/.deepagents/config.toml`, `~/.deepagents/agent/AGENTS.md`, and `~/.deepagents/agent/skills` exist.
4. For OpenProject, test:

```powershell
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

5. For Jupyter scaffolding, test:

```powershell
python "$HOME/.cline/skills/jupyter-notebook/scripts/new_notebook.py" --help
```

6. For Python-first Outlook mail access on Windows:

```powershell
python -m pip install pywin32
python -X utf8 "$HOME/.cline/skills/outlook-mail/scripts/outlook_mail.py" list-folders --max-depth 1
```

If you are verifying the DeepAgents-installed copy, replace `~/.cline/skills` with `~/.deepagents/agent/skills`.

## Outlook setup

The Outlook skills are Windows-only and expect:

- desktop Outlook installed
- at least one mailbox profile already signed in
- local permission to let Outlook COM read messages and save attachments
- `pywin32` installed for the Python-first `outlook-mail` skill

If the folder alias does not work because of a localized mailbox, run the folder listing command first and reuse the exact reported folder path.
`outlook-mail` is Python-first and initializes COM inside Python, so run the `.py` entry point directly.

Outbound mail safety rules in `outlook-mail`:

- use `draft-message` or `send-message` only when the user explicitly asked for a mail-writing action in the current turn
- if the user asked to write mail but did not explicitly ask to send it, create a draft instead
- the only no-extra-approval recipient is the detected self address `<username>@lgdisplay.com`
- the installer prints the detected address after installation
- if the detected address is wrong, set `OUTLOOK_MAIL_SELF_ADDRESS` to the actual company address before using `outlook-mail`
- any other recipient must be explicitly approved before running the command with `--allow-recipient`

Override examples:

```powershell
$env:OUTLOOK_MAIL_SELF_ADDRESS="actual.user@lgdisplay.com"
```

```bash
export OUTLOOK_MAIL_SELF_ADDRESS="actual.user@lgdisplay.com"
```

## Obsidian defaults

The Cline rules and the DeepAgents `AGENTS.md` both apply the same Obsidian defaults:

- prefer `OBSIDIAN_VAULT` and `OBSIDIAN_INBOX` when they exist
- otherwise fall back to `~/Obsidian_Vault` and `~/Obsidian_Vault/00. Inbox`
- discover vault guidance in this order:
  - `00_README_시작하기*`
  - `AGENTS*`
  - `START_HERE*`
  - `90. Settings/*`
  - `Indexes/*`
  - `Templates/*`

## Encoding note for on-prem Windows

Some on-prem Windows environments still default Python console IO to `cp949`. If you see garbled Korean text or `UnicodeEncodeError`, prefer UTF-8 mode before running the bundled Python helpers:

```powershell
$env:PYTHONUTF8="1"
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

The bundled Python scripts also reconfigure `stdout` and `stderr` to UTF-8 where supported, but setting `PYTHONUTF8=1` is still the safest shell-level default.

Repository encoding policy:

- PowerShell source files (`*.ps1`, `*.psm1`, `*.psd1`) should be saved as `UTF-8 with BOM`
- shell scripts, Python, Markdown, JSON, TOML, YAML, `.env`, and other text source files should be saved as `UTF-8`
- the Python-first Outlook mail skill writes exported `message.md` or `message.txt` and `manifest-*.csv` as UTF-8 with BOM for better Windows compatibility
- `git clone`, `git pull`, Linux `cp`, `scp`, and `rsync` do not transcode encodings; they preserve the bytes already stored in the repo

Repository safeguards:

- [`.editorconfig`](C:\Users\angpa\myProjects\Daily_Work\Skills_convert\.editorconfig) defines editor save defaults
- [`check_text_encoding.py`](C:\Users\angpa\myProjects\Daily_Work\Skills_convert\scripts\check_text_encoding.py) validates tracked source files against the encoding policy

Verification:

```powershell
python .\scripts\check_text_encoding.py install.ps1 install.cmd install.sh deepagents\config.toml deepagents\agent\AGENTS.md skills
```

## Notes

- The pack intentionally keeps shared skills outside the agent-specific folders.
- Cline gets separate rules/workflows because it has first-class support for them.
- DeepAgents gets `AGENTS.md` plus shared skills instead of a separate workflow directory.
