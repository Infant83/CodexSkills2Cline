#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


TEXT_RULES = {
    ".bat": {"bom": False, "label": "UTF-8"},
    ".cmd": {"bom": False, "label": "UTF-8"},
    ".csv": {"bom": False, "label": "UTF-8"},
    ".env": {"bom": False, "label": "UTF-8"},
    ".json": {"bom": False, "label": "UTF-8"},
    ".md": {"bom": False, "label": "UTF-8"},
    ".ps1": {"bom": True, "label": "UTF-8 with BOM"},
    ".psd1": {"bom": True, "label": "UTF-8 with BOM"},
    ".psm1": {"bom": True, "label": "UTF-8 with BOM"},
    ".py": {"bom": False, "label": "UTF-8"},
    ".txt": {"bom": False, "label": "UTF-8"},
    ".yaml": {"bom": False, "label": "UTF-8"},
    ".yml": {"bom": False, "label": "UTF-8"},
}

UTF8_BOM = b"\xef\xbb\xbf"


def iter_git_tracked_files(repo_root: Path):
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    for raw_path in result.stdout.split(b"\x00"):
        if not raw_path:
            continue
        yield repo_root / raw_path.decode("utf-8")


def iter_target_files(repo_root: Path, paths):
    if paths:
        for raw_path in paths:
            candidate = (repo_root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path)
            if candidate.is_dir():
                for child in candidate.rglob("*"):
                    if child.is_file() and child.suffix.lower() in TEXT_RULES:
                        yield child
            elif candidate.is_file() and candidate.suffix.lower() in TEXT_RULES:
                yield candidate
        return

    yield from iter_git_tracked_files(repo_root)


def check_file(path: Path):
    suffix = path.suffix.lower()
    rule = TEXT_RULES.get(suffix)
    if rule is None:
        return None

    data = path.read_bytes()
    has_bom = data.startswith(UTF8_BOM)

    try:
        if has_bom:
            data.decode("utf-8-sig")
        else:
            data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return f"{path}: invalid UTF-8 ({exc})"

    expected_bom = rule["bom"]
    if expected_bom and not has_bom:
        return f"{path}: expected {rule['label']}"
    if not expected_bom and has_bom:
        return f"{path}: unexpected UTF-8 BOM"

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate repository text files against the UTF-8 encoding policy."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional files or directories to check. Defaults to git-tracked files in the repo.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    failures = []
    seen = set()

    for path in iter_target_files(repo_root, args.paths):
        if path in seen:
            continue
        seen.add(path)

        failure = check_file(path)
        if failure:
            failures.append(failure)

    if failures:
        print("Encoding check failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Encoding check passed for {len(seen)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
