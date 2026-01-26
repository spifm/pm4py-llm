import argparse
import json
from pathlib import Path

INPUT_FILENAME = "input.json"
OUTPUT_FILENAME = "output.json"

def build_train_jsonl(
    base_dir: str,
    prompt_file: str,
    examples_dir: str,
    output_file: str,
    input_filename: str = INPUT_FILENAME,
    output_filename: str = OUTPUT_FILENAME,
    placeholder: str = "{{DFG_JSON}}",
) -> None:
    """
    Reads the prompt template and example files to create a JSONL training file with (input, output) pairs.
    Recorre los ejemplos en `examples_dir` y genera un train.jsonl con pares (input, output).

    Directory structure:

    llm-training/
        prompt.txt
        training/
          ex01/
            input.json
            output.json
          ex02/
            input.json
            output.json
          dir1/
            ex03/
              input.json
              output.json
          ...

    - `prompt.txt` must contain the placeholder {{DFG_JSON}} 
    where the input DFG JSON will be injected.
    """

    base_path = Path(base_dir)
    prompt_path = base_path / prompt_file
    examples_path = base_path / examples_dir
    output_path = base_path / output_file

    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    if not examples_path.is_dir():
        raise NotADirectoryError(f"Examples directory not found: {examples_path}")

    # Read prompt template
    prompt_template = prompt_path.read_text(encoding="utf-8")

    if placeholder not in prompt_template:
        raise ValueError(
            f"The placeholder '{placeholder}' was not found in the prompt file."
        )

    # Prepare output
    with output_path.open("w", encoding="utf-8") as out_f:
        num_examples = 0


        for in_path in sorted(examples_path.rglob(input_filename)):
            if not in_path.is_file():
                continue

            example_dir = in_path.parent
            out_json_path = example_dir / output_filename

            if not out_json_path.is_file():
                print(
                    f"[WARN] Skipping {example_dir}: "
                    f"missing {input_filename} or {output_filename}"
                )
                continue

            # Read input JSON (Original DFG)
            input_json_str = in_path.read_text(encoding="utf-8").strip()

            # Optional: validate that it is JSON, just in case
            try:
                _ = json.loads(input_json_str)
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid JSON in {in_path}: {e}. Skipping.")
                continue

            # Build the "input" field: prompt + JSON
            full_input = prompt_template.replace(placeholder, input_json_str)

            # Read simplified JSON (output)
            output_json_str = out_json_path.read_text(encoding="utf-8").strip()
            try:
                _ = json.loads(output_json_str)
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid JSON in {out_json_path}: {e}. Skipping.")
                continue

            record = {
                "input": full_input,
                "output": output_json_str,
            }

            # Use json.dumps to ensure it is properly escaped in a single line
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            num_examples += 1

        print(f"[INFO] Wrote {num_examples} examples to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build train.jsonl for DFG simplification fine-tuning."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="dfg-data",
        help="Base directory containing prompt.txt and examples/ (default: dfg-data)",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default="prompt.txt",
        help="Prompt template file name (default: prompt.txt)",
    )
    parser.add_argument(
        "--examples-dir",
        type=str,
        default="examples",
        help="Directory (inside base-dir) with one subdir per example (default: examples)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="train.jsonl",
        help="Output JSONL file name (relative to base-dir, default: train.jsonl)",
    )
    parser.add_argument(
        "--input-filename",
        type=str,
        default=INPUT_FILENAME,
        help="Name of the input JSON file inside each example dir (default: %s)" %INPUT_FILENAME,
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        default=OUTPUT_FILENAME,
        help="Name of the output JSON file inside each example dir (default: %s)" %OUTPUT_FILENAME,
    )
    parser.add_argument(
        "--placeholder",
        type=str,
        default="{{DFG_JSON}}",
        help="Placeholder in the prompt template to be replaced by the DFG JSON (default: {{DFG_JSON}})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_train_jsonl(
        base_dir=args.base_dir,
        prompt_file=args.prompt_file,
        examples_dir=args.examples_dir,
        output_file=args.output_file,
        input_filename=args.input_filename,
        output_filename=args.output_filename,
        placeholder=args.placeholder,
    )
