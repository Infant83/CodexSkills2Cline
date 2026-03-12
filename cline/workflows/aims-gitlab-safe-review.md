# AIMS GitLab Safe Review Workflow

Use this workflow when the user wants to inspect or act on the internal AIMS GitLab from a checked-out repository or through the GitLab API.

## Steps

1. Check prerequisites.
   - Confirm the task is about the internal AIMS GitLab, not public GitHub.
   - Confirm `GITLAB_TOKEN` is available for normal API work.
   - If admin or impersonated behavior is requested, confirm `GITLAB_ADMIN_TOKEN` is available.
   - Prefer `GITLAB_BASE_URL`. Accept `GITHUB_BASE_URL` only as a compatibility fallback.

2. Keep repository changes local and scoped.
   - Use local `git` commands for branch, fetch, rebase, status, commit, pull, and push.
   - Do not change global git config, global credentials, or remote URLs unless the user explicitly asks.

3. Read before write.
   - Inspect the project, merge request, approval state, or member list before taking action.
   - For merge request approvals, inspect merge status and conflict state first.

4. Use the lowest privilege needed.
   - Use `GITLAB_TOKEN` by default.
   - Use `GITLAB_ADMIN_TOKEN` only for admin-only tasks or when the user explicitly asks for elevated behavior.
   - Use `--sudo` only when the user explicitly asks to act as another user.

5. Stop on unresolved merge conditions.
   - If the merge request shows conflicts, unresolved discussions, or a transient merge status such as `checking` or `approvals_syncing`, stop and report instead of approving blindly.

6. Summarize the action.
   - Report which repository or merge request was inspected or changed.
   - Mention whether the normal token or admin token was used.
   - Call out any unresolved permission, policy, or conflict issue.
