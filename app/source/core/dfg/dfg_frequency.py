import json
import logging
import math
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_min_transition_frequency(json_dfg_path: str) -> int | None:
    """
    Returns the minimum 'freq' among the transitions of a DFG JSON,
    or None if the file has no transitions.
    """
    try:
        with open(json_dfg_path, "r", encoding="utf-8") as f:
            dfg: Dict[str, Any] = json.load(f)
        transitions: List[Dict[str, Any]] = dfg.get("transitions", []) or []
    except Exception as e:
        logger.error("Error reading DFG JSON file: %s", e)
        raise

    if not transitions:
        return None

    return min(int(t.get("freq", 0)) for t in transitions)


def frequency_threshold_for_ratio(freqs: list[int], ratio: float) -> int:
    """
    Translate a retention ratio (top X% most frequent transitions) into an
    exact frequency threshold to be used with a `freq > threshold` filter.

    The threshold keeps the whole frequency tier at the cutoff (round up), so
    at least `ratio`% of the transitions are retained. When several transitions
    share the boundary frequency, all of them are kept.

    Args:
        freqs: transition frequencies.
        ratio: percentage in (0, 100].

    Returns:
        The frequency threshold; transitions with freq > threshold are kept.

    Raises:
        ValueError: if ratio is out of range or freqs is empty.
    """
    if ratio <= 0 or ratio > 100:
        raise ValueError("Ratio must be greater than 0 and less than or equal to 100")
    if not freqs:
        raise ValueError("Cannot compute a frequency threshold from an empty transition set")

    ordered = sorted((int(f) for f in freqs), reverse=True)
    target = math.ceil(len(ordered) * ratio / 100.0)
    boundary_freq = ordered[target - 1]
    return boundary_freq - 1
