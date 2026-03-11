---
name: spreadsheet
description: Work with spreadsheets such as .xlsx, .csv, and .tsv using openpyxl and pandas, especially when formulas, references, formatting, or structured analysis must be preserved and verified.
---

# Spreadsheet

## When to use

- Build new workbooks with formulas, formatting, and structured layouts.
- Read or analyze tabular data.
- Modify existing workbooks without breaking formulas or references.
- Visualize data with charts or well-structured tables.

## Workflow

1. Confirm the file type and goal: create, edit, analyze, or visualize.
2. Use `openpyxl` for `.xlsx` edits and `pandas` for analysis and CSV or TSV workflows.
3. If layout matters, render for visual review when tooling is available.
4. Validate formulas and references. `openpyxl` does not evaluate formulas.
5. Save outputs cleanly and keep filenames descriptive.

## Dependencies

Python packages:

```bash
python -m pip install openpyxl pandas
```

Optional:

```bash
python -m pip install matplotlib
```

Optional system tools for rendering:

```bash
# macOS
brew install libreoffice poppler

# Ubuntu or Debian
sudo apt-get install -y libreoffice poppler-utils
```

## Formula requirements

- Use formulas for derived values instead of hardcoding results.
- Prefer simple, readable formulas.
- Guard against `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, and `#NAME?`.
- Leave formulas intact and note that results calculate in Excel or Sheets.

## Formatting requirements

- Preserve existing formatting exactly when editing styled spreadsheets.
- Use clean number and date formats when creating new sheets.
- Keep headers distinct from data and avoid unnecessary borders everywhere.
- Make text, dates, currency, and percentages immediately readable.

## References

- See `references/examples/openpyxl/` for small example scripts.
