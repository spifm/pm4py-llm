import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path

from source.core.dfg.dfg_filter import DFGFilter
from source.core.dfg.dfg_frequency import frequency_threshold_for_ratio
from source.core.dfg.dfg_transformer import DFGTransformer
from source.helpers.filename_getter import Filename
from source.helpers.info_writer import InfoWriter


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


def write_base_info(
    info_writer: InfoWriter,
    dataset_path: Path,
    dataset_extension: str,
    csv_delimiter: str,
    case_id_column: str,
    activity_column: str,
    timestamp_column: str,
    ratio: float,
    minimum_retained_transitions: int,
    image_formats: list[str],
) -> None:
    info_writer.write("=== Frequency Filtering Info ===\n\n")
    info_writer.write(f"Dataset path: {dataset_path}\n")
    info_writer.write(f"Dataset extension: {dataset_extension}\n")
    info_writer.write(f"Case id column: {case_id_column}\n")
    info_writer.write(f"Activity column: {activity_column}\n")
    info_writer.write(f"Timestamp column: {timestamp_column}\n")
    if dataset_extension == ".csv":
        info_writer.write(f"CSV delimiter: {csv_delimiter}\n")
    info_writer.write(f"Requested retained transitions (%): {ratio:g}\n")
    info_writer.write(f"Minimum retained transitions by ratio: {minimum_retained_transitions}\n")
    info_writer.write(f"Image formats: {', '.join(image_formats)}\n")


def write_simplification_info(
    info_writer: InfoWriter,
    original_dfg_path: Path,
    filtered_dfg_path: Path,
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

    info_writer.write("\n\n=== Simplification Info ===\n\n")
    info_writer.write(f"Original DFG:  {original_dfg_path}\n")
    info_writer.write(f"Filtered DFG:  {filtered_dfg_path}\n\n")

    info_writer.write("Activities (nodes)\n")
    info_writer.write(f"  - Original:  {orig_activities}\n")
    info_writer.write(f"  - Filtered:  {filtered_activities}\n\n")

    info_writer.write("Transitions (edges)\n")
    info_writer.write(f"  - Original:  {num_orig_transitions}\n")
    info_writer.write(f"  - Filtered:  {num_filtered_transitions}\n\n")

    info_writer.write("Reduction with respect to the original model\n")
    info_writer.write(f"  - Activity reduction (%):   {activity_reduction:.2f}\n")
    info_writer.write(f"  - Transition reduction (%): {transition_reduction:.2f}\n\n")

    info_writer.write("Approximate trace coverage\n")
    info_writer.write(f"  - Total transition freq (original): {total_freq_orig}\n")
    info_writer.write(f"  - Total transition freq (filtered): {total_freq_filtered}\n")
    info_writer.write(f"  - Trace coverage (%):               {trace_coverage:.2f}\n")


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

    if not dfg:
        raise ValueError("The discovered DFG has no transitions")

    freqs = [int(freq) for freq in dfg.values()]
    threshold = frequency_threshold_for_ratio(freqs, args.ratio)
    minimum_retained_transitions = math.ceil(len(freqs) * args.ratio / 100.0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ratio_for_path = normalize_ratio_for_path(args.ratio)
    output_dir = Path(args.output_root) / f"filter_dfg_by_frequency_{ratio_for_path}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    fn = Filename()
    transformer = DFGTransformer()
    dfg_filter = DFGFilter()
    info_writer = InfoWriter(str(output_dir))

    # 1) Store the original DFG in pm4py format and its JSON representation
    original_dfg_path = Path(fn.get_filename_path("dfg.raw", str(output_dir)))
    original_json_path = Path(fn.get_filename_path("dfg.json", str(output_dir)))
    pm4py.write_dfg(dfg, start_activities, end_activities, str(original_dfg_path))
    transformer.dfg_pm4py_to_json(str(original_dfg_path), str(original_json_path))

    # 2) Write the base filtering info (before the deterministic filter runs)
    write_base_info(
        info_writer=info_writer,
        dataset_path=dataset_path,
        dataset_extension=dataset_path.suffix.lower(),
        csv_delimiter=args.csv_delimiter,
        case_id_column=case_id_column,
        activity_column=activity_column,
        timestamp_column=timestamp_column,
        ratio=args.ratio,
        minimum_retained_transitions=minimum_retained_transitions,
        image_formats=image_formats,
    )

    # 3) Deterministic frequency filter on the JSON DFG
    #    (DFGFilter appends its own "=== Filtered Info ===" section to info.txt)
    filtered_json_path = Path(fn.get_filename_path("dfg.json_filtered_by_freq", str(output_dir)))
    dfg_filter.filter_json_dfg_by_frequency(
        json_dfg_path=str(original_json_path),
        json_output_path=str(filtered_json_path),
        frequency_threshold=threshold,
    )

    # 4) Convert the filtered JSON DFG back to pm4py format
    filtered_dfg_path = Path(fn.get_filename_path("dfg.raw_filtered_by_freq", str(output_dir)))
    transformer.dfg_named_json_to_pm4py(str(filtered_json_path), str(filtered_dfg_path))

    # 5) Render the filtered DFG images
    filtered_dfg, filtered_start_activities, filtered_end_activities = pm4py.read_dfg(
        str(filtered_dfg_path)
    )
    image_paths = fn.get_filename_paths_for_formats(
        "dfg.image_filtered_by_freq", str(output_dir), image_formats
    )
    for image_path in image_paths.values():
        pm4py.save_vis_dfg(
            filtered_dfg,
            filtered_start_activities,
            filtered_end_activities,
            file_path=image_path,
            bgcolor="white",
            rankdir="LR",
        )

    # 6) Append the simplification info (reduction stats) after the filtered info
    write_simplification_info(
        info_writer=info_writer,
        original_dfg_path=original_dfg_path,
        filtered_dfg_path=filtered_dfg_path,
    )

    print(f"Filtered DFG results stored in: {output_dir}")


if __name__ == "__main__":
    main()
