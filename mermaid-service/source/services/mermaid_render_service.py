import tempfile
import subprocess
import os
from exceptions.exceptions import MermaidRenderError

class MermaidRenderService:
    
    def render(self, mermaid_code, image_format) -> tuple[bytes, str]:
        '''
        Renders the given Mermaid code to the specified image format.
        Returns a tuple of (image data as bytes, media type string).
        Raises MermaidRenderError if rendering fails.
        '''
        suffix = ".mmd"
        output_suffix = f".{image_format}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as tmp_in:
            tmp_in.write(mermaid_code)
            input_path = tmp_in.name

        with tempfile.NamedTemporaryFile(suffix=output_suffix, delete=False) as tmp_out:
            output_path = tmp_out.name

        try:
            result = subprocess.run(
                [
                    "mmdc",
                    "-i", input_path,
                    "-o", output_path,
                    "-b", "transparent",
                    "-p", "/app/source/puppeteer-config.json"
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise MermaidRenderError(f"Mermaid rendering failed: {result.stderr}")

            with open(output_path, "rb") as f:
                data = f.read()

            media_type = "image/svg+xml" if image_format == "svg" else "image/png"

            return data, media_type

        finally:
            for path in (input_path, output_path):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
