import pm4py
from lib.Config import Config
import lib.llm as llm
import re
import logging

logger = logging.getLogger(__name__)

class DFGSimplifier:
    def __init__(self):
        self.config = self._load_config()


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