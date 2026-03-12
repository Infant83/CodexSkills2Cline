# Workflow Routing

Use these rules to keep automation reusable and maintainable.

## Skill policy

- Do not create one skill per UI button or per product mode.
- Standardize on:
  - platform-core skills
  - workflow profiles
  - shared policies for logging, storage, and verification

Create a dedicated skill only when the workflow is repeated, multi-step, failure-prone, or needs a stable output structure.

## Heuristic for making a new skill

Create or keep a dedicated skill when at least one of these is true:

1. The workflow is likely to be reused three or more times.
2. The workflow involves login, session, upload, or download handling.
3. The workflow has several actions that are easy to mis-execute.
4. The output needs a consistent structure or audit trail.

## Workflow profile model

Normalize common requests into reusable profiles such as:

- `source-to-report`
- `meeting-to-minutes`
- `deck-revision`
- `fact-check-and-augment`
- `data-table-analysis`
- `document-conversion`
- `document-vision-review`
- `openproject-update`

Before execution, resolve these fields when relevant:

- task type
- preferred tool
- source files
- fact-check strictness
- style reference
- editable output format
- save-to-obsidian requirement
- revision vs. first-draft mode
