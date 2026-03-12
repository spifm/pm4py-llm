import argparse
import pm4py
from pathlib import Path


def dfg_to_image(input_path: str, output_path: str, *, bgcolor: str = "white", rankdir: str = "LR") -> None:
    input_p = Path(input_path)
    if not input_p.is_file():
        raise FileNotFoundError(f"Input DFG not found: {input_path}")

    output_p = Path(output_path)
    if str(output_p.parent) not in (".", ""):
        output_p.parent.mkdir(parents=True, exist_ok=True)

    dfg, start_activities, end_activities = pm4py.read_dfg(str(input_p))
    pm4py.save_vis_dfg(
        dfg,
        start_activities,
        end_activities,
        file_path=str(output_p),
        bgcolor=bgcolor,
        rankdir=rankdir,
    )

    print(f"DFG saved as image in: {output_p}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PM4Py .dfg file into an image.",
    )
    parser.add_argument(
        "input_path",
        help="Path to the input .dfg file",
    )
    parser.add_argument(
        "output_path",
        help="Path to the output image to create",
    )
    parser.add_argument(
        "--bgcolor",
        default="white",
        help="Background color for the visualization (default: white)",
    )
    parser.add_argument(
        "--rankdir",
        default="LR",
        help="Graph direction (default: LR)",
    )
    args = parser.parse_args()

    dfg_to_image(args.input_path, args.output_path, bgcolor=args.bgcolor, rankdir=args.rankdir)


if __name__ == "__main__":
    main()
