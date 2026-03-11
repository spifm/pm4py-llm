from source.Config import Config
from source.LlmMermaidClient import llm_mermaid_factory
import os
import logging
from source.helpers.info_writer import InfoWriter

logger = logging.getLogger(__name__)

class MindMapBuilder:

    def __init__(self):
        self.config = self._load_config()
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
        mind_map_file: str
    ) -> str:
        """
        Build a mind map from a DFG's analysis.

        Args:
            analysis: The text analysis of the DFG to be used as input for the mind map generation.
            mind_map_file: The file path where the resulting mind map will be saved.

        Returns:
            The mind map content
        """

        logger.info("Starting mind map building process.")

        # Prepare the prompt by loading the template and replacing the placeholder with the analysis
        prompt = self.client.get_mermaid_prompt().replace("{{ANALYSIS_TEXT}}", analysis)

        # Execute the prompt using the LLM client and get the mind map data
        metrics = self.client.exec_prompt(
            prompt,
            mind_map_file
        )

        # Write the metrics to the info file
        output_dir = os.path.dirname(mind_map_file)
        info_writer = InfoWriter(output_dir)
        info_writer.write("\n\n=== (Simplified) Mind map LLM Request Metrics ===\n\n")
        for key, value in metrics.items():
            info_writer.write(f"{key}: {value}\n")

        # Read the generated mind map file and return its content
        with open(mind_map_file, 'r', encoding='utf-8') as f:
            return f.read()