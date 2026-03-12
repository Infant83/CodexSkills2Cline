---
name: aims-gitlab
description: Work with the internal AIMS GitLab for repository-local git operations and GitLab REST API tasks. Use when handling on-prem GitLab projects, branches, push/pull/commit workflows, merge requests, approval state, merge-request approvals, project membership, or admin-only GitLab actions with GITLAB_TOKEN and GITLAB_ADMIN_TOKEN.
---

# AIMS GitLab

## Quick start

- Use normal local `git` commands for repo operations such as `status`, `fetch`, `pull`, `checkout -b`, `commit`, and `push`.
- Do not change global git config, global credentials, or the user's remote configuration unless explicitly asked.
- Use the bundled helper at `$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py` for GitLab REST API work.
- Require `GITLAB_TOKEN` for normal API actions and `GITLAB_ADMIN_TOKEN` only for explicit admin actions.
- Prefer `GITLAB_BASE_URL` for the AIMS GitLab instance root. Accept `GITHUB_BASE_URL` only as a compatibility fallback when the environment already uses that name.
- Read the target project or merge request first before approving, changing, or escalating privileges.

Environment examples:

```powershell
$env:GITLAB_BASE_URL="https://aims.example.com"
$env:GITLAB_TOKEN="your-user-token"
$env:GITLAB_ADMIN_TOKEN="your-admin-token"
```

```bash
export GITLAB_BASE_URL="https://aims.example.com"
export GITLAB_TOKEN="your-user-token"
export GITLAB_ADMIN_TOKEN="your-admin-token"
```

## Local git operations

Use the repository's existing remote and local configuration:

```bash
git status --short
git remote -v
git fetch origin
git checkout -b feature/my-change
git add -A
git commit -m "Describe the change"
git push -u origin HEAD
```

Use `git` for:

- branch creation and switching
- local commits and rebases
- fetch, pull, and push
- conflict inspection inside the checked-out repository

Use the API helper for:

- project lookup
- merge request listing and inspection
- approval state
- approval or unapproval
- member lookup
- raw GitLab API requests

## Common API tasks

Identify the current GitLab user:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" whoami
```

List accessible projects:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  list-projects \
  --membership \
  --per-page 20
```

Inspect a project by numeric ID or `group/project` path:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  get-project group/subgroup/project
```

List merge requests for a project:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  list-merge-requests \
  --project group/project \
  --state opened \
  --scope all \
  --per-page 20
```

Inspect one merge request and its approval state:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  get-merge-request \
  --project group/project \
  --mr-iid 42

python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  get-mr-approval-state \
  --project group/project \
  --mr-iid 42
```

Approve a merge request only after inspection:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  approve-merge-request \
  --project group/project \
  --mr-iid 42
```

Use the admin token only when the action truly needs it:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  list-project-members \
  --project group/project \
  --admin
```

## Admin and approval workflow

1. Use `GITLAB_TOKEN` by default.
2. Switch to `--admin` only for admin-only actions or when the user explicitly asks to act with elevated rights.
3. Before approval, inspect the merge request and approval state.
4. Stop if the merge request reports conflicts or an unresolved merge status.
5. If acting as an administrator for another user, use `--sudo <username-or-id>` only when the user explicitly asks for that behavior.

If a merge request was created or updated very recently, check that `detailed_merge_status` is no longer `checking` or `approvals_syncing` before approving.

## Unsupported or less common operations

- Use the generic `request` command for endpoints not covered directly.
- Read `references/api-patterns.md` for raw endpoint examples, project-path encoding examples, and admin patterns.

Example:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request get /api/v4/projects/group%2Fproject/merge_requests/42/discussions \
  --admin
```
