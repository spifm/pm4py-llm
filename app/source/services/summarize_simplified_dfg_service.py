import os
import logging
from source.core.dfg.dfg_simplifier import DFGSimplifier
from source.helpers.filename_getter import Filename

logger = logging.getLogger(__name__)
output_dir = "/output"


class SummarizeSimplifiedDFGService:

    @staticmethod
    def summarize(analysis_dir: str) -> dict:
        """
        Generate a short, concise explanatory summary of a previously
        generated simplified DFG using an LLM.

        Requires that a `/simplify-dfg` run has already produced the simplified
        DFG in JSON format (with restored activity names) inside the given
        analysis directory.
        """
        fn = Filename()

        input_dir = os.path.join(output_dir, analysis_dir)
        if not os.path.isdir(input_dir):
            raise ValueError("Analysis directory not found.")

        simplified_dfg_file = fn.get_filename_path(
            "dfg.json_llm_restored_simplified", input_dir
        )
        if not os.path.exists(simplified_dfg_file):
            raise ValueError(
                "Simplified DFG not found. Run /simplify-dfg first."
            )

        output_summary = fn.get_filename_path("dfg.simplified_summary", input_dir)

        dfg_simplifier = DFGSimplifier()
        dfg_simplifier.summarize_simplified_dfg(simplified_dfg_file, output_summary)

        with open(output_summary, "r") as f:
            summary_text = f.read()

        return {
            "summary_file": output_summary,
            "summary": summary_text,
        }
