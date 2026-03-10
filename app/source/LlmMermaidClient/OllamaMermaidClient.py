import requests
from .LlmMermaidClientInterface import LlmMermaidClientInterface
from typing import Dict, Any
import time

class OllamaMermaidClient(LlmMermaidClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['ollama']
        self.url = f"{config['api_url']}{config['api_endpoint']}"
        self.model_name = config['model_name']
        self.options = config.get('options', {})
        self.max_prompt_tokens = config.get('max_prompt_tokens', 0)
        self.think = config.get('think', False)


    def _exec_ollama_prompt(self, prompt: str, output_file: str, payload: dict, url: str) -> Dict [str, Any] | None:

        self.logger.debug(f"URL: {url}")

        max_len = 500
        prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
        self.logger.debug(f"Simplificated prompt (truncated to {max_len} chars): {prompt_preview}")

        try:
            t0_perf = time.perf_counter()
            response = requests.post(url, json=payload)
            response.raise_for_status()
            t1_perf = time.perf_counter()
        except requests.exceptions.RequestException as e:
            self.logger.exception(f"Error in Ollama request: {e}")
            raise

        self.logger.info(f"Response status code: {response.status_code}")
        self.logger.debug(f"Response content: {response.content}")
        json_response = response.json()

        if "message" in json_response:
            result = json_response["message"]["content"]
        elif "response" in json_response:
            result = json_response["response"]
        else:
            raise ValueError(f"Unexpected response format from Ollama API.")

        self.logger.debug(f"Response content result: {result}")

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        # Get metrics to return them
        return {
            "Input tokens": json_response.get("prompt_eval_count", 0),
            "Output tokens": json_response.get("eval_count", 0),
            "Total duration ms": round((t1_perf - t0_perf) * 1000.0, 4),
            "total_duration (from Ollama) ms": int(json_response.get("total_duration", 0) or 0) / 1_000_000,
            "load_duration ms": int(json_response.get("load_duration", 0) or 0) / 1_000_000,
            "prompt_eval_duration ms": int(json_response.get("prompt_eval_duration", 0) or 0) / 1_000_000,
            "eval_duration ms": int(json_response.get("eval_duration", 0) or 0) / 1_000_000,
        }


    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:

        payload = {
            "model": self.model_name,
            "stream": False,
            "options": self.options,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "prompt": prompt
        }

        if self.think is dict:
            k, v = next(iter(self.think.items()))
            payload[k] = v

        return self._exec_ollama_prompt(prompt, output_file, payload, self.url)
