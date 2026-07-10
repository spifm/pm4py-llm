from source.helpers.info_writer import InfoWriter
import logging
import json
import os
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

class DFGFilter:
    def filter_json_dfg_by_frequency(
        self,
        json_dfg_path: str,
        json_output_path: str,
        frequency_threshold: int,
    ) -> None:
        """
        Filters a DFG JSON (object with start_activities, end_activities, transitions)
        removing transitions with freq <= frequency_threshold.

        Then prunes start_activities/end_activities to keep only activities that still appear
        in the remaining transitions.

        Writes the filtered DFG to json_output_path.
        """
        try:
            with open(json_dfg_path, "r", encoding="utf-8") as f:
                dfg: Dict[str, Any] = json.load(f)

            start_acts: List[Dict[str, Any]] = dfg.get("start_activities", []) or []
            end_acts: List[Dict[str, Any]] = dfg.get("end_activities", []) or []
            transitions: List[Dict[str, Any]] = dfg.get("transitions", []) or []
        except Exception as e:
            logger.error("Error reading DFG JSON file: %s", e)
            raise

        # 1) Filter transitions by freq threshold
        filtered_transitions = [
            t for t in transitions
            if int(t.get("freq", 0)) > frequency_threshold
        ]

        # 2) Compute which activities remain after filtering
        used_activities: Set[str] = set()
        for t in filtered_transitions:
            src = t.get("src")
            tgt = t.get("tgt")
            if isinstance(src, str):
                used_activities.add(src)
            if isinstance(tgt, str):
                used_activities.add(tgt)

        # 3) Filter start/end activities based on remaining activities
        filtered_start = [a for a in start_acts if a.get("activity") in used_activities]
        filtered_end = [a for a in end_acts if a.get("activity") in used_activities]

        # Keep at least one start/end if they existed originally
        if not filtered_start and start_acts:
            filtered_start = [max(start_acts, key=lambda x: int(x.get("freq", 0)))]
        if not filtered_end and end_acts:
            filtered_end = [max(end_acts, key=lambda x: int(x.get("freq", 0)))]

        filtered_dfg = {
            "start_activities": filtered_start,
            "end_activities": filtered_end,
            "transitions": filtered_transitions,
        }

        with open(json_output_path, "w", encoding="utf-8") as out:
            json.dump(filtered_dfg, out, ensure_ascii=False, indent=2)

        logger.info(
            "Filtered DFG saved to %s | threshold=%s | transitions: %s -> %s | activities kept=%s",
            json_output_path,
            frequency_threshold,
            len(transitions),
            len(filtered_transitions),
            len(used_activities),
        )

        # Write in information file
        out_dir = os.path.dirname(os.path.abspath(json_dfg_path))
        info_writer = InfoWriter(out_dir)
        info_writer.write("\n\n=== Filtered Info ===\n\n")
        info_writer.write(
            f"Filtered DFG with freq >{frequency_threshold} | "
            f"transitions: {len(transitions)} -> {len(filtered_transitions)} | "
            f"activities kept={len(used_activities)}\n"
        )