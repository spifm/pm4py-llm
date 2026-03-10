from abc import ABC, abstractmethod
from typing import Any, Dict
from logging import Logger
from source.helpers.load_prompt_template import PromptLoader

class LlmMermaidClientInterface(ABC):
    def __init__(self, config: Dict[str, Any], logger: Logger):
        self.config = config
        self.logger = logger
        self._init_config()

        prompt_loader = PromptLoader()
        self.mermaid_prompt = prompt_loader.load_template(self.config["mermaid"]["prompt"])

    @abstractmethod
    def _init_config(self) -> None:
        ...

    @abstractmethod
    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        ...

    def get_mermaid_prompt(self) -> str:
        return self.mermaid_prompt
