import requests
from .LlmClientInterface import LlmClientInterface

class OllamaClient(LlmClientInterface):
    def exec_prompt(self, prompt: str, output_file: str) -> str | None:
        ollama_config = self.config["llm"]['ollama']
        url = f"{ollama_config['api_url']}{ollama_config['api_endpoint']}"

        payload = {
            "model": ollama_config['model_name'],
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": ollama_config['options']
        }

        max_len = 500
        self.logger.debug(f"URL: {url}")
        prompt_preview = prompt if len(prompt) <= max_len else prompt[:max_len] + "..."
        self.logger.debug(f"Simplificated prompt (truncated to {max_len} chars): {prompt_preview}")

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.exception(f"Error in Ollama request: {e}")
            return None

        self.logger.info(f"Response status code: {response.status_code}")
        self.logger.debug(f"Response content: {response.content}")

        result = response.json()["message"]["content"]

        self.logger.debug(f"Response content result: {result}")

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")

        return result
