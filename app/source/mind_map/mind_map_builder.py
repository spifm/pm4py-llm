from source.Config import Config
from source.Filename import Filename
from source.LlmMermaidClient import llm_mermaid_factory
import os
import logging
from source.helpers.info_writer import InfoWriter

logger = logging.getLogger(__name__)

class MindMapBuilder:

    def __init__(self):
        self.config = self._load_config()
        self.fn = Filename()
        self.client = llm_mermaid_factory.create_llm_client(self.config, logger)

    def _load_config(self):
        """
        Initializes and returns the configuration instance.
        """
        config_instance = Config()
        config_instance.initialize()
        return config_instance.get()


    def build_mind_map(
        self,
        analysis: str,
        mind_map_path: str
    ) -> str:
        """
        Build a mind map from a DFG's analysis.

        Args:
            analysis: The text analysis of the DFG to be used as input for the mind map generation.
            mind_map_path: The path where the resulting mind map will be saved.

        Returns:
            The mind map data
        """

        logger.info("Starting mind map building process.")

        # Prepare the prompt by loading the template and replacing the placeholder with the analysis
        prompt = self.client.get_mermaid_prompt().replace("{{ANALYSIS_TEXT}}", analysis)

        # Execute the prompt using the LLM client and get the mind map data
        simplified_mind_map_path = self.fn.get_filename_path("mermaid.simplified_mind_map", mind_map_path)
        metrics = self.client.exec_prompt(
            prompt,
            simplified_mind_map_path
        )

        # Write the metrics to the info file
        output_dir = os.path.dirname(simplified_mind_map_path)
        info_writer = InfoWriter(output_dir)
        info_writer.write("\n\n=== (Simplified) Mind map LLM Request Metrics ===\n\n")
        for key, value in metrics.items():
            info_writer.write(f"{key}: {value}\n")

        # Read the generated mind map data from the file and return it
        #with open(simplified_mind_map_path, 'r', encoding='utf-8') as f:
        #    simplified_mind_map_data = f.read()

        return simplified_mind_map_path