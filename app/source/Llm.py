import logging
import os
from source.Config import Config
from source.LlmClient import llm_factory
from source.helpers.info_writer import InfoWriter

class Llm:
    def __init__(self):
        try:
            self.config = Config().get()
            self.logger = logging.getLogger(__name__)
            self.client = llm_factory.create_llm_client(self.config, self.logger)
        except Exception as e:
            self.logger.error(f"Error initializing LLM client in class Llm: {e}")
            raise

    def analyze_petri_net(self, abstract_model: str, file_name: str) -> None:
        llm_ctx = "\n".join(self.config["llm"]["context"])
        self.logger.info("\n\n-------------------\nPetri net analysis\n-------------------\n\n")
        try:
            prompt = (
                f"{llm_ctx}\n\n"
                f"{self.config['llm']['petri_net']['prompt']}\n\n"
                f"{abstract_model}"
            )
            metrics = self.client.exec_prompt(prompt, file_name)
            if metrics is not None:
                out_dir = os.path.dirname(os.path.abspath(file_name))
                info_writer = InfoWriter(out_dir)
                info_writer.write("\n\n=== Petri Net Analysis LLM Request Metrics ===\n\n")
                for key, value in metrics.items():
                    info_writer.write(f"{key}: {value}\n")
        except Exception as e:
            self.logger.error(f"Error constructing Petri net analysis prompt: {e}")
            raise

    def analyze_dfg(self, abstract_model: str, file_name: str) -> None:
        self.logger.info("\n\n-------------\nDFG analysis\n------------\n\n")
        try:
            prompt = (
                f"{self.config['llm']['context']}\n\n"
                f"{self.config['llm']['dfg']['prompt']}\n\n"
                f"{abstract_model}"
            )
            self.logger.debug("Executing DFG analysis prompt.")
            metrics = self.client.exec_prompt(prompt, file_name)
            if metrics is not None:
                out_dir = os.path.dirname(os.path.abspath(file_name))
                info_writer = InfoWriter(out_dir)
                info_writer.write("\n\n=== DFG Analysis LLM Request Metrics ===\n\n")
                for key, value in metrics.items():
                    info_writer.write(f"{key}: {value}\n")
        except Exception as e:
            self.logger.error(f"Error constructing DFG analysis prompt: {e}")
            raise

    def analyze_temporal_profile(self, abstract_model: str, file_name: str) -> None:
        self.logger.info("\n\n---------------------\nTemporal profile analysis\n---------------------\n\n")
        try:
            prompt = (
                f"{self.config['llm']['context']}\n\n"
                f"{self.config['llm']['temporal_profile']['prompt']}\n\n"
                f"{abstract_model}"
            )
            metrics = self.client.exec_prompt(prompt, file_name)
            if metrics is not None:
                out_dir = os.path.dirname(os.path.abspath(file_name))
                info_writer = InfoWriter(out_dir)
                info_writer.write("\n\n=== Temporal Profile Analysis LLM Request Metrics ===\n\n")
                for key, value in metrics.items():
                    info_writer.write(f"{key}: {value}\n")
        except Exception as e:
            self.logger.error(f"Error constructing Temporal profile analysis prompt: {e}")
            raise
