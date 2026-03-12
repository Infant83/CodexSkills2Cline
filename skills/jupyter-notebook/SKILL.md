---
name: jupyter-notebook
description: Create, scaffold, or edit Jupyter notebooks (.ipynb) for experiments, exploratory analysis, or tutorials. Prefer the bundled templates and the helper script new_notebook.py to avoid raw notebook JSON mistakes.
---

# Jupyter Notebook

Use this skill to create clean, reproducible notebooks for two primary modes:

- experiments and exploratory analysis
- tutorials and teaching-oriented walkthroughs

## When to use

- Create a new notebook from scratch.
- Convert rough notes or scripts into a structured notebook.
- Refactor an existing notebook to be more reproducible and skimmable.
- Build experiments or tutorials that other people will re-run or read.

## Decision tree

- If the request is exploratory or hypothesis-driven, choose `experiment`.
- If the request is instructional or step-by-step, choose `tutorial`.
- If editing an existing notebook, preserve intent and improve structure.

## Quick start

If this skill is installed under DeepAgents, replace `~/.cline/skills` in the examples below with `~/.deepagents/skills`.

Use the bundled helper:

```bash
python "$HOME/.cline/skills/jupyter-notebook/scripts/new_notebook.py" \
  --kind experiment \
  --title "Compare prompt variants" \
  --out output/jupyter-notebook/compare-prompt-variants.ipynb
```

```bash
python "$HOME/.cline/skills/jupyter-notebook/scripts/new_notebook.py" \
  --kind tutorial \
  --title "Intro to embeddings" \
  --out output/jupyter-notebook/intro-to-embeddings.ipynb
```

## Workflow

1. Lock the intent and audience.
2. Scaffold from the helper instead of hand-authoring notebook JSON.
3. Fill the notebook with small, runnable steps.
4. Use `references/experiment-patterns.md` or `references/tutorial-patterns.md` as needed.
5. Validate top-to-bottom execution when the environment allows.
6. If execution is not possible, say so explicitly and describe local validation.

## Bundled resources

- Templates: `assets/experiment-template.ipynb`, `assets/tutorial-template.ipynb`
- Structure guidance: `references/notebook-structure.md`
- Final checklist: `references/quality-checklist.md`

## Dependencies

The scaffold script uses only the Python standard library.

Optional packages for local execution:

```bash
python -m pip install jupyterlab ipykernel
```
