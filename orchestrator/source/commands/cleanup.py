"""
Cleanup utility for old pipeline-results directories.

Removes subdirectories of /app/source/tmp/pipeline-results whose name is
exactly YYYYMMDD and whose date is <= the given cutoff date. Directories
with any other naming format are left untouched.

By default runs in dry-run mode (prints what would be deleted).
Pass --apply to actually delete.

Usage:
  python -m commands.cleanup 20251231
  python -m commands.cleanup 20251231 --apply
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


OUTPUT_ROOT = Path("/app/source/tmp/pipeline-results")
DATE_FORMAT = "%Y%m%d"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete pipeline-results subdirectories named YYYYMMDD whose date is on or before "
            "the given cutoff. Directories with any other name format are not touched."
        ),
    )
    parser.add_argument(
        "date",
        help="Cutoff date in YYYYMMDD format (inclusive). Directories on or before this date are deleted.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the directories. Without this flag, only a dry-run is performed.",
    )
    return parser.parse_args()


def parse_cutoff_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        print(f"Error: '{date_str}' is not a valid date in YYYYMMDD format.", file=sys.stderr)
        sys.exit(1)


def extract_folder_date(name: str) -> Optional[datetime]:
    """Return the date if the folder name is exactly YYYYMMDD, otherwise None."""
    if len(name) != 8 or not name.isdigit():
        return None
    try:
        return datetime.strptime(name, DATE_FORMAT)
    except ValueError:
        return None


def find_dirs_to_delete(cutoff: datetime) -> list:
    candidates = []
    for entry in sorted(OUTPUT_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        date = extract_folder_date(entry.name)
        if date is not None and date <= cutoff:
            candidates.append((entry, date))
    return candidates


def main() -> None:
    args = parse_args()

    if not OUTPUT_ROOT.is_dir():
        print(f"Error: pipeline-results root '{OUTPUT_ROOT}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    cutoff = parse_cutoff_date(args.date)
    candidates = find_dirs_to_delete(cutoff)

    if not candidates:
        print("No directories to delete.")
        return

    dry_run = not args.apply
    if dry_run:
        print(f"Dry-run mode: the following directories would be deleted (pass --apply to delete):\n")
    else:
        print(f"Deleting {len(candidates)} director{'y' if len(candidates) == 1 else 'ies'}:\n")

    deleted = 0
    errors = 0
    for path, date in candidates:
        label = date.strftime(DATE_FORMAT)
        if dry_run:
            print(f"  {path.name}  ({label})")
        else:
            try:
                shutil.rmtree(path)
                print(f"  Deleted: {path.name}  ({label})")
                deleted += 1
            except OSError as e:
                print(f"  Error deleting {path.name}: {e}", file=sys.stderr)
                errors += 1

    print()
    if dry_run:
        print(f"Summary: {len(candidates)} director{'y' if len(candidates) == 1 else 'ies'} would be deleted.")
    else:
        print(f"Summary: {deleted} deleted, {errors} errors.")


if __name__ == "__main__":
    main()
