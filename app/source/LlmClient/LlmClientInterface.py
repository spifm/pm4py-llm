from abc import ABC, abstractmethod
from typing import Any, Dict
from logging import Logger

class LlmClientInterface(ABC):
    def __init__(self, config: Dict[str, Any], logger: Logger):
        self.config = config
        self.logger = logger
        self._init_config()

    @abstractmethod
    def _init_config(self) -> None:
        ...

    @abstractmethod
    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        ...

    @abstractmethod
    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict[str, Any] | None:
        ...

    @abstractmethod
    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        ...
