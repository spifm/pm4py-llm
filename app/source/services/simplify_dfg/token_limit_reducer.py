import logging

from source.core.dfg.dfg_frequency import get_min_transition_frequency
from source.helpers.info_writer import InfoWriter

logger = logging.getLogger(__name__)


class TokenLimitReducer:
    """Reduces a DFG until the simplification prompt fits the LLM context window.

    Each attempt removes the least frequent transition tier (filtering by the
    current minimum frequency) and re-evaluates the prompt token budget.
    """

    def __init__(self, dfg_simplifier, dfg_filter, fn, max_attempts: int = 3):
        self._dfg_simplifier = dfg_simplifier
        self._dfg_filter = dfg_filter
        self._fn = fn
        self._max_attempts = max_attempts

    def reduce(self, json_dfg_file: str, input_dir: str) -> str:
        json_dfg_to_simplify = json_dfg_file

        for i in range(self._max_attempts):
            if self._dfg_simplifier.eval_fit_json_prompt_tokens(json_dfg_to_simplify):
                logger.info("Prompt is within token limits, proceeding with simplification.")
                break

            try:
                # Start from the least frequent transitions: filter out the
                # current minimum frequency tier and re-evaluate on next pass.
                min_freq = get_min_transition_frequency(json_dfg_to_simplify)
                if min_freq is None:
                    logger.warning("No transitions left to filter; stopping reduction.")
                    break

                logger.info(
                    "Prompt exceeds token limits, attempting to simplify further "
                    "in try %s with frequency filter >%s.",
                    i + 1,
                    min_freq,
                )
                reduced_dfg_filename = self._fn.get_filename_path(
                    "dfg.json_generic_act_filtered_by_freq", input_dir
                )
                InfoWriter(input_dir).write(
                    "\n\n=== DFG Pre-filtered to fit LLM context window ===\n\n"
                    f"Prompt exceeded the LLM token/context window (attempt {i + 1}); "
                    f"applied frequency filter with threshold >{min_freq} to reduce the DFG.\n"
                    "Proceeding to filter the DFG...\n"
                )
                self._dfg_filter.filter_json_dfg_by_frequency(
                    json_dfg_path=json_dfg_to_simplify,
                    json_output_path=reduced_dfg_filename,
                    frequency_threshold=min_freq,
                )
                json_dfg_to_simplify = reduced_dfg_filename
            except Exception as e:
                logger.error(
                    "Error during DFG filtering attempt %s with frequency threshold >%s: %s",
                    i + 1,
                    min_freq,
                    e,
                )
                raise
        else:
            if not self._dfg_simplifier.eval_fit_json_prompt_tokens(json_dfg_to_simplify):
                logger.error("Prompt exceeds token limits after %s attempts.", self._max_attempts)

        return json_dfg_to_simplify
