from openai import OpenAI
from .LlmClientInterface import LlmClientInterface
from source.helpers.clean_json import CleanJson
from typing import Dict, Any
import time
import json

class VLLMClient(LlmClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['vllm']
        self.base_url = config['api_url']
        self.api_key = config.get('api_key', 'EMPTY')
        self.model_name = config['model_name']
        self.options = config.get('options', {})
        self.max_prompt_tokens = config.get('max_prompt_tokens', 0)
        self.think = config.get('think', False)

    def _client(self) -> OpenAI:
        return OpenAI(base_url=self.base_url, api_key=self.api_key)

    def exec_prompt(self, prompt: str, output_file: str) -> Dict[str, Any] | None:

        client = self._client()

        try:
            t0_perf = time.perf_counter()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **self.options,
            )
            t1_perf = time.perf_counter()
        except Exception as e:
            self.logger.error(f"Error during vLLM request: {e}")
            raise

        self.logger.debug(f"vLLM response: {response}")

        result = response.choices[0].message.content or ""

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        return self._metrics(response, t0_perf, t1_perf)

    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict[str, Any] | None:

        client = self._client()

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "dfg",
                "schema": self._get_dfg_json_schema(),
                "strict": True,
            },
        }

        try:
            t0_perf = time.perf_counter()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=response_format,
                **self.options,
            )
            t1_perf = time.perf_counter()
        except Exception as e:
            self.logger.error(f"Error during vLLM JSON request: {e}")
            raise

        self.logger.debug(f"vLLM JSON response: {response}")

        result = response.choices[0].message.content or ""

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        CleanJson.clean_json(output_file)

        return self._metrics(response, t0_perf, t1_perf)

    def _metrics(self, response, t0_perf: float, t1_perf: float) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        return {
            "Provider": "vLLM",
            "Model": self.model_name,
            "Think": (
                "Not specified (default value in LLM's API was used)"
                if self.think is False
                else json.dumps(self.think, ensure_ascii=False)
            ),
            "Options": json.dumps(self.options, ensure_ascii=False),
            "Input tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "Output tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "Total duration ms": round((t1_perf - t0_perf) * 1000.0, 4),
            "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
        }

    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        if self.max_prompt_tokens == 0:
            self.logger.warning("vLLM: Maximum prompt tokens for JSON not set; assuming no limit.")
            return True
        self.logger.warning("Token counting not implemented for VLLMClient; assuming within limit.")
        return True
