import json
import logging
import os

from source.core.dfg.dfg_frequency import frequency_threshold_for_ratio
from source.helpers.info_writer import InfoWriter

logger = logging.getLogger(__name__)


class DeterministicPreFilter:
    """Optional deterministic frequency pre-filter applied before the LLM.

    When a retention ratio is provided, the DFG is reduced to its most
    frequent transitions and that reduced DFG feeds the rest of the pipeline.
    When no ratio is given, the original DFG is returned untouched.
    """

    def __init__(self, dfg_filter, fn):
        self._dfg_filter = dfg_filter
        self._fn = fn

    def apply(self, json_dfg_file: str, ratio: float | None, input_dir: str) -> str:
        if ratio is None:
            return json_dfg_file

        logger.info(
            "Applying deterministic frequency filter (ratio=%s) before LLM simplification...",
            ratio,
        )
        with open(json_dfg_file, "r", encoding="utf-8") as f:
            transitions = json.load(f).get("transitions") or []
        freqs = [int(t.get("freq", 0)) for t in transitions]
        threshold = frequency_threshold_for_ratio(freqs, ratio)

        info_writer = InfoWriter(os.path.dirname(os.path.abspath(json_dfg_file)))
        info_writer.write("\n\n=== Deterministic Pre-Filter ===\n\n")
        info_writer.write(
            f"Deterministic frequency pre-filter | ratio={ratio}% | "
            f"frequency threshold >{threshold}\n"
        )

        filtered_dfg_file = self._fn.get_filename_path("dfg.json_filtered_by_freq", input_dir)
        self._dfg_filter.filter_json_dfg_by_frequency(
            json_dfg_path=json_dfg_file,
            json_output_path=filtered_dfg_file,
            frequency_threshold=threshold,
        )
        return filtered_dfg_file
