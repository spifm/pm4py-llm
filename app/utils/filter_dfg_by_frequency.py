import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path


DEFAULT_XES_CASE_ID_COLUMN = "case:concept:name"
DEFAULT_XES_ACTIVITY_COLUMN = "concept:name"
DEFAULT_XES_TIMESTAMP_COLUMN = "time:timestamp"

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover a DFG from a dataset and keep the most frequent transitions by ratio.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset filename or path inside the dataset directory.",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        required=True,
        help="Percentage of most frequent transitions to retain. Example: 20 keeps the top 20%%.",
    )
    parser.add_argument(
        "--case-id-column",
        help="Case identifier column. Required for CSV datasets.",
    )
    parser.add_argument(
        "--activity-column",
        help="Activity column. Required for CSV datasets.",
    )
    parser.add_argument(
        "--timestamp-column",
        help="Timestamp column. Required for CSV datasets.",
    )
    parser.add_argument(
        "--csv-delimiter",
        default=",",
        help="CSV delimiter. Default: ','. Only used for CSV datasets.",
    )
    parser.add_argument(
        "--dataset-dir",
        default="/dataset",
        help="Dataset directory. Default: /dataset.",
    )
    parser.add_argument(
        "--output-root",
        default="/output",
        help="Output root directory. Default: /output.",
    )
    return parser.parse_args()


def normalize_ratio_for_path(ratio: float) -> str:
    ratio_str = f"{ratio:g}"
    return ratio_str.replace(".", "_")


def resolve_dataset_path(dataset: str, dataset_dir: str) -> Path:
    dataset_root = Path(dataset_dir).resolve()
    dataset_path = Path(dataset)

    if dataset_path.is_absolute():
        resolved_path = dataset_path.resolve()
    else:
        resolved_path = (dataset_root / dataset_path).resolve()

    try:
        resolved_path.relative_to(dataset_root)
    except ValueError as exc:
        raise ValueError(f"Dataset must be inside the dataset directory: {dataset_root}") from exc

    if not resolved_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {resolved_path}")

    return resolved_path


def load_config() -> dict:
    app_dir = Path(__file__).resolve().parents[1]
    config_paths = [
        Path("config/config.json"),
        Path("config/config_template.json"),
        app_dir / "config/config.json",
        app_dir / "config/config_template.json",
    ]

    for config_path in config_paths:
        if config_path.is_file():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError("Could not find config/config.json or config/config_template.json")


def get_dfg_image_formats() -> list[str]:
    config = load_config()
    image_formats = config["discovery"]["dfg"]["image_formats"]
    return [image_format.lower().lstrip(".") for image_format in image_formats]


def read_log(
    dataset_path: Path,
    csv_delimiter: str,
    case_id_column: str | None,
    activity_column: str | None,
    timestamp_column: str | None,
):
    extension = dataset_path.suffix.lower()

    if extension == ".xes":
        import pm4py

        log = pm4py.read_xes(str(dataset_path))
        return (
            log,
            case_id_column or DEFAULT_XES_CASE_ID_COLUMN,
            activity_column or DEFAULT_XES_ACTIVITY_COLUMN,
            timestamp_column or DEFAULT_XES_TIMESTAMP_COLUMN,
        )

    if extension == ".csv":
        import pandas as pd
        import pm4py

        missing_columns = [
            name
            for name, value in {
                "--case-id-column": case_id_column,
                "--activity-column": activity_column,
                "--timestamp-column": timestamp_column,
            }.items()
            if value is None
        ]
        if missing_columns:
            raise ValueError(f"CSV datasets require: {', '.join(missing_columns)}")

        log_df = pd.read_csv(dataset_path, sep=csv_delimiter)
        log_df[timestamp_column] = pd.to_datetime(log_df[timestamp_column], errors="coerce")
        log = pm4py.format_dataframe(log_df, case_id_column, activity_column, timestamp_column)
        log[case_id_column] = log[case_id_column].astype(str)
        return log, case_id_column, activity_column, timestamp_column

    raise ValueError("Unsupported file extension, please provide a .xes or .csv file")


def discover_dfg(log, case_id_column: str, activity_column: str, timestamp_column: str):
    import pm4py

    return pm4py.discover_dfg(
        log,
        case_id_key=case_id_column,
        activity_key=activity_column,
        timestamp_key=timestamp_column,
    )


def filter_dfg_by_frequency(dfg: dict, ratio: float) -> tuple[dict, int]:
    if ratio <= 0 or ratio > 100:
        raise ValueError("Ratio must be greater than 0 and less than or equal to 100")

    transitions = sorted(
        dfg.items(),
        key=lambda item: (-int(item[1]), str(item[0][0]), str(item[0][1])),
    )

    if not transitions:
        raise ValueError("The discovered DFG has no transitions")

    minimum_retained_transitions = math.ceil(len(transitions) * ratio / 100.0)
    retained_transitions = transitions[:minimum_retained_transitions]

    return dict(retained_transitions), minimum_retained_transitions


def filter_start_end_activities(start_activities: dict, end_activities: dict, filtered_dfg: dict) -> tuple[dict, dict]:
    retained_activities = set()
    for src, tgt in filtered_dfg.keys():
        retained_activities.add(src)
        retained_activities.add(tgt)

    filtered_start_activities = {
        activity: freq
        for activity, freq in start_activities.items()
        if activity in retained_activities
    }
    filtered_end_activities = {
        activity: freq
        for activity, freq in end_activities.items()
        if activity in retained_activities
    }

    return filtered_start_activities, filtered_end_activities


def parse_pm4py_dfg(dfg_path: Path) -> tuple[int, list[tuple[int, int, int]]]:
    transitions = []

    with open(dfg_path, "r", encoding="utf-8") as f:
        num_activities = int(f.readline().strip())
        for _ in range(num_activities):
            f.readline()

        num_start = int(f.readline().strip())
        for _ in range(num_start):
            f.readline()

        num_end = int(f.readline().strip())
        for _ in range(num_end):
            f.readline()

        for line in f:
            line = line.strip()
            if not line:
                continue
            src_dest, freq_str = line.split("x")
            src_str, tgt_str = src_dest.split(">")
            transitions.append((int(src_str), int(tgt_str), int(freq_str)))

    return num_activities, transitions


def write_info(
    info_path: Path,
    dataset_path: Path,
    dataset_extension: str,
    csv_delimiter: str,
    case_id_column: str,
    activity_column: str,
    timestamp_column: str,
    ratio: float,
    minimum_retained_transitions: int,
    original_dfg_path: Path,
    filtered_dfg_path: Path,
    image_formats: list[str],
) -> None:
    orig_activities, orig_transitions = parse_pm4py_dfg(original_dfg_path)
    filtered_activities, filtered_transitions = parse_pm4py_dfg(filtered_dfg_path)

    num_orig_transitions = len(orig_transitions)
    num_filtered_transitions = len(filtered_transitions)
    total_freq_orig = sum(freq for _, _, freq in orig_transitions)
    total_freq_filtered = sum(freq for _, _, freq in filtered_transitions)

    activity_reduction = (
        (orig_activities - filtered_activities) / orig_activities * 100.0
        if orig_activities > 0
        else 0.0
    )
    transition_reduction = (
        (num_orig_transitions - num_filtered_transitions) / num_orig_transitions * 100.0
        if num_orig_transitions > 0
        else 0.0
    )
    trace_coverage = (
        (total_freq_filtered / total_freq_orig) * 100.0
        if total_freq_orig > 0
        else 0.0
    )

    with open(info_path, "w", encoding="utf-8") as info:
        info.write("=== Frequency Filtering Info ===\n\n")
        info.write(f"Dataset path: {dataset_path}\n")
        info.write(f"Dataset extension: {dataset_extension}\n")
        info.write(f"Case id column: {case_id_column}\n")
        info.write(f"Activity column: {activity_column}\n")
        info.write(f"Timestamp column: {timestamp_column}\n")
        if dataset_extension == ".csv":
            info.write(f"CSV delimiter: {csv_delimiter}\n")
        info.write(f"Requested retained transitions (%): {ratio:g}\n")
        info.write(f"Minimum retained transitions by ratio: {minimum_retained_transitions}\n")
        info.write(f"Retained transitions after deterministic cut: {num_filtered_transitions}\n")
        info.write(f"Image formats: {', '.join(image_formats)}\n")

        info.write("\n\n=== Simplification Info ===\n\n")
        info.write(f"Original DFG:  {original_dfg_path}\n")
        info.write(f"Filtered DFG:  {filtered_dfg_path}\n\n")

        info.write("Activities (nodes)\n")
        info.write(f"  - Original:  {orig_activities}\n")
        info.write(f"  - Filtered:  {filtered_activities}\n\n")

        info.write("Transitions (edges)\n")
        info.write(f"  - Original:  {num_orig_transitions}\n")
        info.write(f"  - Filtered:  {num_filtered_transitions}\n\n")

        info.write("Reduction with respect to the original model\n")
        info.write(f"  - Activity reduction (%):   {activity_reduction:.2f}\n")
        info.write(f"  - Transition reduction (%): {transition_reduction:.2f}\n\n")

        info.write("Approximate trace coverage\n")
        info.write(f"  - Total transition freq (original): {total_freq_orig}\n")
        info.write(f"  - Total transition freq (filtered): {total_freq_filtered}\n")
        info.write(f"  - Trace coverage (%):               {trace_coverage:.2f}\n")


def main() -> None:
    args = parse_args()

    import pm4py

    dataset_path = resolve_dataset_path(args.dataset, args.dataset_dir)
    image_formats = get_dfg_image_formats()

    log, case_id_column, activity_column, timestamp_column = read_log(
        dataset_path=dataset_path,
        csv_delimiter=args.csv_delimiter,
        case_id_column=args.case_id_column,
        activity_column=args.activity_column,
        timestamp_column=args.timestamp_column,
    )

    dfg, start_activities, end_activities = discover_dfg(
        log,
        case_id_column=case_id_column,
        activity_column=activity_column,
        timestamp_column=timestamp_column,
    )
    filtered_dfg, minimum_retained_transitions = filter_dfg_by_frequency(dfg, args.ratio)
    filtered_start_activities, filtered_end_activities = filter_start_end_activities(
        start_activities,
        end_activities,
        filtered_dfg,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ratio_for_path = normalize_ratio_for_path(args.ratio)
    output_dir = Path(args.output_root) / f"filter_dfg_by_frequency_{ratio_for_path}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    original_dfg_path = output_dir / "dfg.dfg"
    filtered_dfg_path = output_dir / "filtered-dfg.dfg"
    pm4py.write_dfg(dfg, start_activities, end_activities, str(original_dfg_path))
    pm4py.write_dfg(filtered_dfg, filtered_start_activities, filtered_end_activities, str(filtered_dfg_path))

    for image_format in image_formats:
        image_path = output_dir / f"filtered-dfg.{image_format}"
        pm4py.save_vis_dfg(
            filtered_dfg,
            filtered_start_activities,
            filtered_end_activities,
            file_path=str(image_path),
            bgcolor="white",
            rankdir="LR",
        )

    write_info(
        info_path=output_dir / "info.txt",
        dataset_path=dataset_path,
        dataset_extension=dataset_path.suffix.lower(),
        csv_delimiter=args.csv_delimiter,
        case_id_column=case_id_column,
        activity_column=activity_column,
        timestamp_column=timestamp_column,
        ratio=args.ratio,
        minimum_retained_transitions=minimum_retained_transitions,
        original_dfg_path=original_dfg_path,
        filtered_dfg_path=filtered_dfg_path,
        image_formats=image_formats,
    )

    print(f"Filtered DFG results stored in: {output_dir}")


if __name__ == "__main__":
    main()
