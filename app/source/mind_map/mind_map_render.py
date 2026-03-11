import os
import logging
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MindMapRender:

    def __init__(self):
        load_dotenv()
        self.mermaid_api_url = os.getenv("MERMAID_API_URL", "http://pm4py-mermaid-service:8003")
        self.mermaid_api_token = os.getenv("API_TOKEN", "")

    def render_image(
        self,
        mind_map: str,
        image_format: str,
    ) -> bytes:
        '''
        Builds an image from the given mind map string, using the Mermaid API.
        The image format can be specified (e.g., "png", "svg").
        Returns the generated image content as bytes.
        '''

        logger.info("Starting mind map rendering process.")

        payload = {
            "diagram": mind_map,
            "format": image_format
        }

        try:

            headers = {
                "Authorization": f"Bearer {self.mermaid_api_token}"
            }
            response = requests.post(
                f"{self.mermaid_api_url}/render",
                json=payload,
                headers=headers,
                timeout=120
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_detail = response.text if e.response is not None else str(e)
            logger.error(f"HTTP error while rendering mind map: {error_detail}")
            raise RuntimeError(f"Mermaid rendering failed: {error_detail}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error while calling Mermaid service: {e}")
            raise RuntimeError(f"Could not connect to Mermaid service: {e}") from e

        return response.content
    
    
    def store_image(self, mind_map: bytes, output_file: str) -> None:
        '''
        Stores the given mind map in a file at the specified path (output_file).
        Returns the path to the stored mind map file.
        '''
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        try:
            with open(output_file, "wb") as f:
                f.write(mind_map)
        except OSError as e:
            logger.error(f"Error writing mind map to {output_file}: {e}")
            raise RuntimeError(f"Could not save mind map to {output_file}: {e}") from e

        logger.info("Mind map stored successfully.")
        logger.debug(f"Mind map saved to: {output_file}")
