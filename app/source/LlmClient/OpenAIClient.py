from openai import OpenAI
from openai.types.responses import ResponseOutputMessage, ResponseOutputText
from .LlmClientInterface import LlmClientInterface
from typing import Dict, Any

class OpenAIClient(LlmClientInterface):

    def _init_config(self) -> None:
        config = self.config["llm"]['openai']
        self.model_name = config['model_name']
        self.reasoning = config['reasoning']
        self.api_key = config['openai_api_key']

    def exec_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:

        client = OpenAI(api_key=self.api_key)

        try:
            if self.reasoning:
                response = client.responses.create(
                    model=self.model_name,
                    input=prompt,
                    reasoning=self.reasoning
                )
            else:
                response = client.responses.create(
                    model=self.model_name,
                    input=prompt
                )

        except Exception as e:
            self.logger.error(f"Error during OpenAI request: {e}")
            raise

        self.logger.debug(f"OpenAI response: {response}")

        # Search for the output that is a message
        message_output = next(
            o for o in response.output 
            if isinstance(o, ResponseOutputMessage) or getattr(o, "type", "") == "message"
        )

        # Extract text chunks
        text_chunks = []
        for c in message_output.content:
            if isinstance(c, ResponseOutputText) or hasattr(c, "text"):
                text_chunks.append(c.text)

        result = "\n".join(text_chunks)

        with open(output_file, 'a') as f:
            f.write(result + "\n\n")
    
    def exec_json_prompt(self, prompt: str, output_file: str) -> Dict [str, Any] | None:
        return self.exec_prompt(prompt, output_file)
    
    
    def eval_max_tokens_for_json_prompt(self, prompt: str) -> bool:
        self.logger.warning("Token counting not implemented for OpenAIClient.")
        return True