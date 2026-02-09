import pm4py
from source.Config import Config
from source.Filename import Filename
from source.Llm import Llm
import os
import logging
import json
from typing import Any, Dict, List
import math
from source.helpers.info_writer import InfoWriter

logger = logging.getLogger(__name__)

class DFGSimplifier:
    def __init__(self):
        self.config = self._load_config()
        self.fn = Filename()
        self.llm = Llm()
        self.analysis_prompt = self.config['llm']['dfg']['simplify_dfg']['simplification_analysis_prompt']
        self.simplification_prompt = self.config['llm']['dfg']['simplify_dfg']['simplification_instructions_prompt']
        self.removing_transitions_ratio = self.config['llm']['dfg']['simplify_dfg'].get('removing_transitions_ratio', 50)
        self.retaining_transitions_ratio = self.config['llm']['dfg']['simplify_dfg'].get('retaining_transitions_ratio', 20)


    def _load_config(self):
        """
        Initializes and returns the configuration instance.
        """
        config_instance = Config()
        config_instance.initialize()
        return config_instance.get()


    def _read_dfg(self, dfg_file):
        """
        Reads the Directly-Follows Graph (DFG) from a file.
        """
        with open(dfg_file, 'r') as file:
            return file.read()
        

    def _map_activity_labels_to_indices(self, dfg_file_path):
        """
        Read the original DFG file and returns a dictionary mapping
        each activity label to its original index.
        """    
        mapping = {}
        with open(dfg_file_path, 'r') as f:
            num_activities = int(f.readline().strip())
            for idx in range(num_activities):
                label = f.readline().rstrip()
                mapping[label] = idx
        return mapping


    def get_context_prompt(self):
        """
        Returns the context prompt for the simplifier.
        """
        return self.config['llm']['dfg']['simplify_dfg']['simplification_context_prompt']

    def set_context_prompt(self, context_prompt):
        """
        Sets the context prompt for the simplifier.
        """
        self.config['llm']['dfg']['simplify_dfg']['simplification_context_prompt'] = context_prompt


    def _build_simplification_prompt(self, dfg_file):
        """
        Builds the full simplification prompt by combining the context prompt,
        instructions, ratios, and the DFG content.
        """
        dfg = self._read_dfg(dfg_file)
        prompt_context = "\n".join(self.get_context_prompt())
        prompt_instructions = "\n".join(self.simplification_prompt)
        prompt_instructions = prompt_instructions.replace(
            "{{removing_transitions_ratio}}",
            str(self.removing_transitions_ratio),
        ).replace(
            "{{retaining_transitions_ratio}}",
            str(self.retaining_transitions_ratio),
        )
        prompt = f"{prompt_context}\n\n{prompt_instructions}\n\n{dfg}"
        return prompt


    def eval_fit_json_prompt_tokens(self, dfg_file) -> bool:
        """
        Evaluates if the number of tokens in the context prompt fits the limits of the LLM.
        """
        prompt = self._build_simplification_prompt(dfg_file)

        return self.llm.client.eval_max_tokens_for_json_prompt(prompt)


    def simplify(self, dfg_file, output_file):
        """
        Simplifies the Directly-Follows Graph (DFG) using an LLM.
        """
        print("\n\n-------------------\nSimplifying DFG\n-------------------\n\n")
        try:
            prompt = self._build_simplification_prompt(dfg_file)
            max_len = 500
            prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
            logger.debug(f"Simplification prompt (truncated to {max_len} chars): {prompt_preview}")
            metrics = self.llm.client.exec_json_prompt(prompt, output_file)
            if metrics is not None:
                out_dir = os.path.dirname(os.path.abspath(output_file))
                info_writer = InfoWriter(out_dir)
                info_writer.write("\n\n=== Simplification LLM Request Metrics ===\n\n")
                for key, value in metrics.items():
                    info_writer.write(f"{key}: {value}\n")
                
        except Exception as e:
            logger.exception(f"Error simplifying DFG: {e}")
            raise
    

    def analyze_simplified_dfg(self, dfg_file, output_analysis):
        """
        Analyze simplified Directly-Follows Graph (DFG) using an LLM.
        """
        print("\n\n-------------------\nAnalyzing Simplified DFG\n-------------------\n\n")
        try:       
            simplified_dfg = self._read_dfg(dfg_file)
            prompt_context = "\n".join(self.get_context_prompt())
            prompt_instructions = "\n".join(self.analysis_prompt)
            prompt = f"{prompt_context}{prompt_instructions}{simplified_dfg}"
            logger.debug(f"Analysis prompt: {prompt}")
            metrics = self.llm.client.exec_prompt(prompt, output_analysis)
            if metrics is not None:
                out_dir = os.path.dirname(os.path.abspath(output_analysis))
                info_writer = InfoWriter(out_dir)
                info_writer.write("\n\n=== Simplified DFG Analysis LLM Request Metrics ===\n\n")
                for key, value in metrics.items():
                    info_writer.write(f"{key}: {value}\n")
        except Exception as e:
            logger.exception(f"Error analyzing simplified DFG: {e}")
            raise


    def convert_dfg_to_image(self, dfg_file, output_path):
        """
        Converts the DFG to a PNG image
        """
        logger.debug(f"Converting DFG from {dfg_file} to image {output_path}")
        
        dfg, start_activities, end_activities = pm4py.read_dfg(dfg_file)

        pm4py.save_vis_dfg(
            dfg,
            start_activities,
            end_activities,
            file_path=output_path,
            bgcolor="white",     # White background
            rankdir="LR"         # Directed graph from left to right
        )

    def _parse_pm4py_dfg(self, dfg_path: str):
        """
        Reads a DFG file in pm4py format and returns:
          - num_activities: number of activities (nodes)
          - transitions: list of transitions (src_idx, tgt_idx, freq)
        Assumes format:
          <num_activities>
          <activity_0>
          ...
          <activity_n-1>
          <num_start>
          <start_idx>x<freq>
          ...
          <num_end>
          <end_idx>x<freq>
          ...
          <src_idx>><tgt_idx>x<freq>
          ...
        """
        transitions = []

        with open(dfg_path, "r", encoding="utf-8") as f:
            # 1) Number of activities and list of labels
            num_activities = int(f.readline().strip())
            for _ in range(num_activities):
                _ = f.readline()  # ignoramos las etiquetas aquí

            # 2) Start activities
            num_start = int(f.readline().strip())
            for _ in range(num_start):
                _ = f.readline()

            # 3) End activities
            num_end = int(f.readline().strip())
            for _ in range(num_end):
                _ = f.readline()

            # 4) Transitions
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # format: "<src_idx>><tgt_idx>x<freq>"
                src_dest, freq_str = line.split("x")
                src_str, tgt_str = src_dest.split(">")
                src_idx = int(src_str)
                tgt_idx = int(tgt_str)
                freq = int(freq_str)
                transitions.append((src_idx, tgt_idx, freq))

        return num_activities, transitions
    

    def compute_simplification_info(self,
                                    original_dfg_path: str,
                                    simplified_dfg_path: str) -> None:
        """
        Compute simplification metrics between an original DFG and a
        simplified one (both in pm4py format) and generates a file
        'info-simplification.txt' in the directory of the simplified DFG.

        Metrics:
          - Activities: number of activities in the simplified DFG.
          - Transitions: number of transitions in the simplified DFG.
          - Activity reduction (%)
          - Transition reduction (%)
          - Trace coverage (%): approximate as
                (sum of transition frequencies in the simplified model) /
                (sum of transition frequencies in the original model) * 100
        """

        # 1) Read original DFG
        orig_activities, orig_transitions = self._parse_pm4py_dfg(original_dfg_path)
        num_orig_transitions = len(orig_transitions)
        total_freq_orig = sum(freq for _, _, freq in orig_transitions)

        # 2) Read simplified DFG
        simp_activities, simp_transitions = self._parse_pm4py_dfg(simplified_dfg_path)
        num_simp_transitions = len(simp_transitions)
        total_freq_simp = sum(freq for _, _, freq in simp_transitions)

        # 3) Reduction percentages
        if orig_activities > 0:
            activity_reduction = (
                (orig_activities - simp_activities) / orig_activities * 100.0
            )
        else:
            activity_reduction = 0.0

        if num_orig_transitions > 0:
            transition_reduction = (
                (num_orig_transitions - num_simp_transitions) / num_orig_transitions * 100.0
            )
        else:
            transition_reduction = 0.0

        # 4) Approximate trace coverage
        #    We use the proportion of transition frequency mass
        #    preserved by the simplified model.
        if total_freq_orig > 0:
            trace_coverage = (total_freq_simp / total_freq_orig) * 100.0
        else:
            trace_coverage = 0.0

        # 5) Write in information file
        out_dir = os.path.dirname(os.path.abspath(simplified_dfg_path))
        info_writer = InfoWriter(out_dir)
        info_writer.write("\n\n=== Simplification Info ===\n\n")
        info_writer.write(f"Original DFG:    {original_dfg_path}\n")
        info_writer.write(f"Simplified DFG:  {simplified_dfg_path}\n\n")

        info_writer.write_llm_config(self.config['llm'])

        info_writer.write("Activities (nodes)\n")
        info_writer.write(f"  - Original:    {orig_activities}\n")
        info_writer.write(f"  - Simplified:  {simp_activities}\n\n")

        info_writer.write("Transitions (edges)\n")
        info_writer.write(f"  - Original:    {num_orig_transitions}\n")
        info_writer.write(f"  - Simplified:  {num_simp_transitions}\n\n")
        info_writer.write("Reduction with respect to the original model\n")
        info_writer.write(f"  - Activity reduction (%):   {activity_reduction:.2f}\n")
        info_writer.write(f"  - Transition reduction (%): {transition_reduction:.2f}\n\n")

        info_writer.write("Approximate trace coverage\n")
        info_writer.write(f"  - Total transition freq (original):   {total_freq_orig}\n")
        info_writer.write(f"  - Total transition freq (simplified): {total_freq_simp}\n")
        info_writer.write(f"  - Trace coverage (%):                 {trace_coverage:.2f}\n")


    def update_transition_ratios(self, original_dfg_path: str, filtered_dfg_path: str) -> None:
        """
        Updates the removing and retaining transition ratios in the simplifier.
        """

        try:
            with open(original_dfg_path, "r", encoding="utf-8") as f:
                original_dfg: Dict[str, Any] = json.load(f)
                original_transitions: List[Dict[str, Any]] = original_dfg.get("transitions", []) or []
        except Exception as e:
            logger.error("Error reading original DFG JSON file: %s", e)
            raise

        try:
            with open(filtered_dfg_path, "r", encoding="utf-8") as f:
                filtered_dfg: Dict[str, Any] = json.load(f)
                filtered_transitions: List[Dict[str, Any]] = filtered_dfg.get("transitions", []) or []
        except Exception as e:
            logger.error("Error reading filtered DFG JSON file: %s", e)
            raise


        X = len(original_transitions)
        Y = len(filtered_transitions)

        # Edge cases
        if X == 0:
            logger.warning("Original DFG has 0 transitions. Keeping ratios as-is.")
            return

        if Y == 0:
            logger.warning(
                "Filtered DFG has 0 transitions. Setting ratios to 0 (nothing to retain/remove)."
            )
            self.removing_transitions_ratio = 0
            self.retaining_transitions_ratio = 0
            return

        # Ratios (as floats) from current config
        remove_pct = float(self.removing_transitions_ratio)   # e.g., 50
        retain_pct = float(self.retaining_transitions_ratio)  # e.g., 20

        # Absolute bounds implied by ORIGINAL rules (in #transitions)
        # Keep between [L, U]
        L = math.ceil(X * (retain_pct / 100.0))
        U = math.floor(X * (1.0 - remove_pct / 100.0))

        # Clip to what is feasible with filtered input (<= Y)
        Lp = min(Y, L)
        Up = min(Y, U)

        # Ensure feasibility: lower bound cannot exceed upper bound
        if Lp > Up:
            # With filtering, you cannot satisfy both original constraints; make them consistent.
            # We force Up = Lp (i.e., "keep exactly Lp" in worst case).
            Up = Lp

        # Convert absolute bounds back to percentages wrt FILTERED transitions Y
        retain_new = 100.0 * (Lp / Y)            # minimum to retain
        remove_new = 100.0 * (1.0 - (Up / Y))    # minimum to remove

        # Clamp to [0, 100]
        retain_new = max(0.0, min(100.0, retain_new))
        remove_new = max(0.0, min(100.0, remove_new))

        # Keep them as ints
        self.retaining_transitions_ratio = int(math.floor(retain_new))
        self.removing_transitions_ratio = int(math.ceil(remove_new))

        # Write in information file
        out_dir = os.path.dirname(os.path.abspath(filtered_dfg_path))
        info_writer = InfoWriter(out_dir)
        info_writer.write(
            "\n\n=== Updated Transitions' Ratios Due to Pre-filtering ===\n\n"
            f"Adjusted ratios after pre-filtering:\n"
            f"- Original Transitions={X} -> Filtered Transitions={Y}\n"
            f"- orig retain={retain_pct} remove={remove_pct}\n"
            f"- abs bounds:\n"
            f"  orig_min_keep={L} orig_max_keep={U} -> "
            f"filtered_min_keep={Lp} filtered_max_keep={Up}\n"
            f"- new retain={self.retaining_transitions_ratio}% remove={self.removing_transitions_ratio}%\n"
        )
        
        logger.info(
            "Adjusted ratios after pre-filtering: Original Transitions=%s -> Filtered Transitions=%s | "
            "orig retain=%s%% remove=%s%% | "
            "abs bounds orig_min_keep=%s orig_max_keep=%s -> filtered_min_keep=%s filtered_max_keep=%s | "
            "new retain=%s%% remove=%s%%",
            X, Y,
            retain_pct, remove_pct,
            L, U, Lp, Up,
            self.retaining_transitions_ratio, self.removing_transitions_ratio,
        )

