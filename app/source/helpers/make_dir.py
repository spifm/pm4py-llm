from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)

output_dir = "/output"


class MakeOutputDir:
    @staticmethod
    def make_unique_dir(base_dir: str) -> tuple[str, str]:
        """
        Creates a unique output directory.

        Returns:
            tuple[str, str]:
                - full_output_path: full path of the created directory
                - final_dir_name: final directory name relative to output_dir
        """
        try:
            if base_dir != "":
                final_dir_name = base_dir
            else:
                final_dir_name = str(int(time.time()))

            base_path = Path(output_dir) / final_dir_name

            try:
                base_path.mkdir(parents=True, exist_ok=False)
                return str(base_path), final_dir_name
            except FileExistsError:
                pass

            i = 2
            while True:
                candidate_name = f"{final_dir_name}_{i}"
                candidate_path = Path(output_dir) / candidate_name
                try:
                    candidate_path.mkdir(parents=True, exist_ok=False)
                    return str(candidate_path), candidate_name
                except FileExistsError:
                    i += 1

        except Exception as e:
            logger.exception("Error creating output directory", exc_info=e)
            raise