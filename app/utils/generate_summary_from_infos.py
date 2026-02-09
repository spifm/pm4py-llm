"""
Build a CSV summary from LLM benchmark info.txt files.

Usage:
  python build_llm_benchmark_csv.py /path/to/results -o summary.csv

It recursively scans for files named "info.txt" under the given root directory,
parses required metrics, and writes a CSV with one row per info.txt.
"""

import argparse
import csv
import os
import re
from typing import Dict, Any, List
from pathlib import Path

HEADERS = [
    "provider",
    "model",
    "analysis_input_tokens",
    "analysis_output_tokens",
    "analysis_total_duraction_ms",
    "simplification_input_tokens",
    "simplification_output_tokens",
    "simplification_total_duraction_ms",
    "simplificated_analysis_input_tokens",
    "simplificated_analysis_output_tokens",
    "simplificated_analysis_total_duraction_ms",
    "activity_reduction",
    "activities_original",
    "activities_simplified",
    "transition_reduction",
    "transitions_original",
    "transitions_simplified",
    "trace_coverage",
]

# Regex patterns (robust to variable whitespace)
RE_PROVIDER = re.compile(r"^\s*-\s*Provider:\s*(.+?)\s*$")
RE_MODEL = re.compile(r"^\s*-\s*Model:\s*(.+?)\s*$")

RE_INPUT_TOKENS = re.compile(r"^\s*Input tokens:\s*([0-9]+)\s*$")
RE_OUTPUT_TOKENS = re.compile(r"^\s*Output tokens:\s*([0-9]+)\s*$")
RE_TOTAL_DURATION = re.compile(r"^\s*Total duration ms:\s*([0-9]+(?:\.[0-9]+)?)\s*$")

RE_ORIGINAL = re.compile(r"^\s*-\s*Original:\s*([0-9]+)\s*$")
RE_SIMPLIFIED = re.compile(r"^\s*-\s*Simplified:\s*([0-9]+)\s*$")

RE_ACTIVITY_REDUCTION = re.compile(r"^\s*-\s*Activity reduction\s*\(%\):\s*([0-9]+(?:\.[0-9]+)?)\s*$")
RE_TRANSITION_REDUCTION = re.compile(r"^\s*-\s*Transition reduction\s*\(%\):\s*([0-9]+(?:\.[0-9]+)?)\s*$")

RE_TRACE_COVERAGE = re.compile(r"^\s*-\s*Trace coverage\s*\(%\):\s*([0-9]+(?:\.[0-9]+)?)\s*$")


def parse_info_txt(path: str) -> Dict[str, Any]:
    """
    Parse one info.txt and return a dict with the CSV headers as keys.
    Missing fields are returned as empty strings.
    """
    row: Dict[str, Any] = {h: "" for h in HEADERS}

    provider_found = False
    model_found = False

    # We must take the 1st/2nd/3rd occurrences for token/time groups.
    input_tokens_vals: List[int] = []
    output_tokens_vals: List[int] = []
    duration_vals: List[float] = []

    # For activities and transitions, we need 1st and 2nd occurrences of "- Original:" and "- Simplified:"
    original_vals: List[int] = []
    simplified_vals: List[int] = []

    activity_reduction_found = False
    transition_reduction_found = False
    trace_coverage_found = False

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            # Provider / Model (first match only)
            if not provider_found:
                m = RE_PROVIDER.match(line)
                if m:
                    row["provider"] = m.group(1).strip()
                    provider_found = True
                    continue

            if not model_found:
                m = RE_MODEL.match(line)
                if m:
                    row["model"] = m.group(1).strip()
                    model_found = True
                    continue

            # Token + duration occurrences (we collect up to 3)
            m = RE_INPUT_TOKENS.match(line)
            if m and len(input_tokens_vals) < 3:
                input_tokens_vals.append(int(m.group(1)))
                continue

            m = RE_OUTPUT_TOKENS.match(line)
            if m and len(output_tokens_vals) < 3:
                output_tokens_vals.append(int(m.group(1)))
                continue

            m = RE_TOTAL_DURATION.match(line)
            if m and len(duration_vals) < 3:
                duration_vals.append(float(m.group(1)))
                continue

            # Activities / Transitions: first two "- Original:" and "- Simplified:"
            m = RE_ORIGINAL.match(line)
            if m and len(original_vals) < 2:
                original_vals.append(int(m.group(1)))
                continue

            m = RE_SIMPLIFIED.match(line)
            if m and len(simplified_vals) < 2:
                simplified_vals.append(int(m.group(1)))
                continue

            # Reductions and trace coverage (first match only each)
            if not activity_reduction_found:
                m = RE_ACTIVITY_REDUCTION.match(line)
                if m:
                    row["activity_reduction"] = float(m.group(1))
                    activity_reduction_found = True
                    continue

            if not transition_reduction_found:
                m = RE_TRANSITION_REDUCTION.match(line)
                if m:
                    row["transition_reduction"] = float(m.group(1))
                    transition_reduction_found = True
                    continue

            if not trace_coverage_found:
                m = RE_TRACE_COVERAGE.match(line)
                if m:
                    row["trace_coverage"] = float(m.group(1))
                    trace_coverage_found = True
                    continue

    # Map occurrences to CSV fields (only if we found enough)
    if len(input_tokens_vals) >= 1:
        row["analysis_input_tokens"] = input_tokens_vals[0]
    if len(output_tokens_vals) >= 1:
        row["analysis_output_tokens"] = output_tokens_vals[0]
    if len(duration_vals) >= 1:
        row["analysis_total_duraction_ms"] = duration_vals[0]

    if len(input_tokens_vals) >= 2:
        row["simplification_input_tokens"] = input_tokens_vals[1]
    if len(output_tokens_vals) >= 2:
        row["simplification_output_tokens"] = output_tokens_vals[1]
    if len(duration_vals) >= 2:
        row["simplification_total_duraction_ms"] = duration_vals[1]

    if len(input_tokens_vals) >= 3:
        row["simplificated_analysis_input_tokens"] = input_tokens_vals[2]
    if len(output_tokens_vals) >= 3:
        row["simplificated_analysis_output_tokens"] = output_tokens_vals[2]
    if len(duration_vals) >= 3:
        row["simplificated_analysis_total_duraction_ms"] = duration_vals[2]

    # Activities (nodes) and Transitions (edges)
    # Per your rules: first "- Original:" is activities_original, first "- Simplified:" is activities_simplified
    # second "- Original:" is transitions_original, second "- Simplified:" is transitions_simplified
    if len(original_vals) >= 1:
        row["activities_original"] = original_vals[0]
    if len(simplified_vals) >= 1:
        row["activities_simplified"] = simplified_vals[0]
    if len(original_vals) >= 2:
        row["transitions_original"] = original_vals[1]
    if len(simplified_vals) >= 2:
        row["transitions_simplified"] = simplified_vals[1]

    return row


def find_info_files(root_dir: str) -> list[str]:
    root = Path(root_dir)

    if not root.exists():
        raise SystemExit(f"Root dir does not exist: {root.resolve()}")
    if not root.is_dir():
        raise SystemExit(f"Root path is not a directory: {root.resolve()}")

    matches = []
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower().strip() == "info.txt":
            matches.append(str(p))

    matches.sort()
    return matches


def main():
    parser = argparse.ArgumentParser(description="Create a CSV summary from info.txt benchmark reports.")
    parser.add_argument("root_dir", help="Root directory containing benchmark subdirectories.")
    parser.add_argument("-o", "--output", default="llm_benchmark_summary.csv", help="Output CSV path.")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ',').")
    args = parser.parse_args()

    info_files = find_info_files(args.root_dir)
    if not info_files:
        raise SystemExit(f"No info.txt files found under: {args.root_dir}")

    rows: List[Dict[str, Any]] = []
    for p in info_files:
        try:
            rows.append(parse_info_txt(p))
        except Exception as e:
            # Keep going, but mark row as error if needed
            # (You can change this behavior to fail-fast if you prefer.)
            err_row = {h: "" for h in HEADERS}
            err_row["provider"] = "PARSE_ERROR"
            err_row["model"] = os.path.relpath(p, args.root_dir)
            rows.append(err_row)
            print(f"[WARN] Failed parsing {p}: {e}")

    # Write CSV
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS, delimiter=args.delimiter)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Written {len(rows)} rows to: {args.output}")


if __name__ == "__main__":
    main()
