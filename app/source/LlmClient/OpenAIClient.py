from openai import OpenAI
from openai.types.responses import ResponseOutputMessage, ResponseOutputText
from .LlmClientInterface import LlmClientInterface

class OpenAIClient(LlmClientInterface):

    def exec_prompt(self, prompt: str, output_file: str) -> str | None:

        openai_config = self.config["llm"]['openai']
        client = OpenAI(api_key=openai_config["openai_api_key"])

        try:
            if openai_config['reasoning']:
                response = client.responses.create(
                    model=openai_config['model_name'],
                    input=prompt,
                    reasoning=openai_config['reasoning']
                )
            else:
                response = client.responses.create(
                    model=openai_config['model_name'],
                    input=prompt
                )

        except Exception as e:
            self.logger.error(f"Error during OpenAI request: {e}")
            return None

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
        
        return result