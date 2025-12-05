import pm4py
from lib.Config import Config
from lib.Filename import Filename
import lib.llm as llm
import os
import logging

logger = logging.getLogger(__name__)

class DFGSimplifier:
    def __init__(self):
        self.config = self._load_config()
        self.fn = Filename()


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
    

    def get_simplification_prompt(self):
        """
        Returns the instructions for the simplification prompt for the simplifier.
        """
        return self.config['llm']['dfg']['simplify_dfg']['simplification_instructions_prompt']
    

    def get_analysis_prompt(self):
        """
        Returns the analysis prompt for the simplifier.
        """
        return self.config['llm']['dfg']['simplify_dfg']['simplification_analysis_prompt']
    

    def set_context_prompt(self, context_prompt):
        """
        Sets the context prompt for the simplifier.
        """
        self.config['llm']['dfg']['simplify_dfg']['simplification_context_prompt'] = context_prompt


    def simplify_dfg(self, dfg_file, output_file):
        """
        Simplifies the Directly-Follows Graph (DFG) using an LLM.
        """
        print("\n\n-------------------\nSimplifying DFG\n-------------------\n\n")
        dfg = self._read_dfg(dfg_file)
        prompt_context = "\n".join(self.get_context_prompt())
        prompt_instructions = "\n".join(self.get_simplification_prompt())
        prompt = f"{prompt_context}\n\n{prompt_instructions}\n\n{dfg}"
        max_len = 500
        prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
        logger.debug(f"Simplification prompt (truncated to {max_len} chars): {prompt_preview}")
        result = llm.exec_prompt(self.config['llm']['dfg'], prompt, output_file)
        return result
    

    def analyze_simplified_dfg(self, dfg_file, output_analysis):
        """
        Analyze simplified Directly-Follows Graph (DFG) using an LLM.
        """
        print("\n\n-------------------\nAnalyzing Simplified DFG\n-------------------\n\n")
               
        simplified_dfg = self._read_dfg(dfg_file)

        prompt_context = "\n".join(self.get_context_prompt())
        prompt_instructions = "\n".join(self.get_analysis_prompt())
        prompt = f"{prompt_context}{prompt_instructions}{simplified_dfg}"
        logger.debug(f"Analysis prompt: {prompt}")
        result = llm.exec_prompt(self.config['llm']['dfg'], prompt, output_analysis)
        return result

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

        # 5) Build output path
        out_dir = os.path.dirname(os.path.abspath(simplified_dfg_path))
        out_path = os.path.join(out_dir, self.fn.get_filename("info"))

        # 6) Write information file
        with open(out_path, "a", encoding="utf-8") as out:
            out.write("\n\n=== Simplification Info ===\n\n")
            out.write(f"Original DFG:    {original_dfg_path}\n")
            out.write(f"Simplified DFG:  {simplified_dfg_path}\n\n")

            out.write("Activities (nodes)\n")
            out.write(f"  - Original:     {orig_activities}\n")
            out.write(f"  - Simplified:   {simp_activities}\n\n")

            out.write("Transitions (edges)\n")
            out.write(f"  - Original:     {num_orig_transitions}\n")
            out.write(f"  - Simplified:   {num_simp_transitions}\n\n")

            out.write("Reduction with respect to the original model\n")
            out.write(f"  - Activity reduction (%):   {activity_reduction:.2f}\n")
            out.write(f"  - Transition reduction (%): {transition_reduction:.2f}\n\n")

            out.write("Approximate trace coverage\n")
            out.write(f"  - Total transition freq (original):   {total_freq_orig}\n")
            out.write(f"  - Total transition freq (simplified): {total_freq_simp}\n")
            out.write(f"  - Trace coverage (%):                 {trace_coverage:.2f}\n")