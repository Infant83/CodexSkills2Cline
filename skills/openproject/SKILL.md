---
name: openproject
description: Work with internal OpenProject through the REST API using OPENPROJECT_BASE_URL and OPENPROJECT_API_KEY. Use when inspecting users, projects, statuses, types, work packages, or performing carefully scoped create and update operations.
---

# OpenProject

## Quick start

- If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/agent/skills`.
- Require `OPENPROJECT_BASE_URL` and `OPENPROJECT_API_KEY` before calling the API.
- Use the bundled helper at `$HOME/.cline/skills/openproject/scripts/openproject_api.py` for OpenProject access.
- Accept `OPENPROJECT_BASE_URL` as either the instance root or the `/api/v3` root. The helper normalizes both forms.
- Read first. If the user asks for a mutation, inspect the target resource before writing.

Example:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

## Common tasks

Identify the authenticated user:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" whoami
```

Inspect a specific user:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" get-user 5
```

Search users by login, name, or email:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" \
  search-users "user@example.com" \
  --limit 10
```

List projects, statuses, and project types:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" list-projects --limit 20
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" list-statuses --limit 50
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" list-types --project-id 1
```

List or inspect work packages:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" \
  list-work-packages \
  --project-id 1 \
  --state open \
  --limit 20

python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" get-work-package 3
```

Send a raw API request for unsupported operations:

```bash
python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" \
  request get /api/v3/work_packages/3

python "$HOME/.cline/skills/openproject/scripts/openproject_api.py" \
  request patch /api/v3/work_packages/3 \
  --json '{"lockVersion":1,"subject":"Updated subject"}'
```

## Write workflow

1. Read the target collection or resource first.
2. Confirm permissions from the response. Stop on `MissingPermission`.
3. For `PATCH`, fetch the current work package and include its current `lockVersion`.
4. For create requests, send the payload to the project-scoped collection and include at least `subject` plus `_links.type`.
5. Prefer the generic `request` command for writes unless the operation is already proven against the target instance.

## Attachment note

- Markdown attachments may be served without a `charset`. Korean text can appear garbled when the file opens inline in the browser.
- If inline readability matters, upload UTF-8 BOM bytes for the attachment.
- Do not rewrite the local source file unless the user asked for it.
- If inline readability matters more than raw Markdown, consider attaching PDF or HTML alongside the Markdown file.

## References

- Read `references/api-patterns.md` for custom `filters` payloads and raw create or update bodies.
