# AIMS GitLab API Patterns

Use these examples when the built-in helper subcommands are not enough.

## Base behavior

- The helper normalizes `GITLAB_BASE_URL` into `<base>/api/v4`.
- If `GITLAB_BASE_URL` is not set, it can fall back to `GITHUB_BASE_URL` for compatibility with older local environments.
- Project references can be numeric IDs or URL-encoded paths such as `group%2Fproject`.
- Authentication uses the `PRIVATE-TOKEN` header.

## Project patterns

Get a project by path:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request get /api/v4/projects/group%2Fproject
```

List members including inherited access:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request get /api/v4/projects/group%2Fproject/members/all \
  --admin
```

## Merge request patterns

List discussions:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request get /api/v4/projects/group%2Fproject/merge_requests/42/discussions
```

List changed versions:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request get /api/v4/projects/group%2Fproject/merge_requests/42/versions
```

Trigger rebase:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  request put /api/v4/projects/group%2Fproject/merge_requests/42/rebase \
  --admin
```

## Admin patterns

Act as another user with an admin token that has `sudo` scope:

```bash
python "$HOME/.cline/skills/aims-gitlab/scripts/aims_gitlab_api.py" \
  whoami \
  --admin \
  --sudo some.username
```

Use `--sudo` only when the user explicitly asks to act as another user.
