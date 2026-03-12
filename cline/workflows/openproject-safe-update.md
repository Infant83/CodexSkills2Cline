# OpenProject Safe Update Workflow

Use this workflow when the user wants to inspect, create, or update OpenProject data through the internal API.

## Steps

1. Check prerequisites.
   - Confirm `OPENPROJECT_BASE_URL` and `OPENPROJECT_API_KEY` are available.
   - If either variable is missing, stop and tell the user to set it before continuing.
   - Use the installed helper script from the `openproject` skill.

2. Read first.
   - Inspect the target project, user, or work package before writing anything.
   - Stop and report permission errors instead of retrying blindly.

3. Prepare the write.
   - For updates, fetch the latest resource and copy its current `lockVersion`.
   - For creates, confirm the project and type context before sending the payload.

4. Send the smallest valid change.
   - Avoid unrelated field changes.
   - Prefer one scoped request over a broad rewrite.

5. Handle attachments carefully.
   - If the user needs a Markdown attachment to render cleanly in the OpenProject UI, upload UTF-8 BOM bytes.
   - Do not rewrite the local source file unless the user asks for it.

6. Report the outcome.
   - Summarize the request that was sent.
   - Include the target project or work package.
   - Mention permission issues, validation failures, or unresolved follow-up actions.
