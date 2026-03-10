from logging import Logger
from typing import Any, Dict
from .LlmMermaidClientInterface import LlmMermaidClientInterface
from .OllamaMermaidClient import OllamaMermaidClient

def create_llm_client(config: Dict[str, Any], logger: Logger) -> LlmMermaidClientInterface:
    provider = config["llm"]["llm_provider"]
    if provider == "ollama":
        return OllamaMermaidClient(config, logger)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
