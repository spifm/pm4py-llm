from pathlib import Path
import time
import os
import logging

logger = logging.getLogger(__name__)

output_dir = "/output"

class MakeOutputDir:
    @staticmethod
    def make_unique_dir(base_dir: str) -> str:
        try:
            if base_dir != "":
                base_output_directory = output_dir + "/" + base_dir
            else:
                base_output_directory = output_dir + "/" + str(int(time.time()))
            
            base_path = Path(base_output_directory)
            try:
                base_path.mkdir(parents=True, exist_ok=False)
                return str(base_path)
            except FileExistsError:
                pass

            i = 2
            while True:
                candidate = Path(f"{base_output_directory}_{i}")
                try:
                    candidate.mkdir(parents=True, exist_ok=False)
                    return str(candidate)
                except FileExistsError:
                    i += 1

        except Exception as e:
            logger.exception("Error creating output directory", exc_info=e)
            raise
        