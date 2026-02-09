import logging
import os
import json
from source.Filename import Filename

logger = logging.getLogger(__name__)

class InfoWriter:
    def __init__(self, file_directory: str):
        try:
            fn = Filename()
            self.file = os.path.join(file_directory, fn.get_filename("info"))
            logger.debug(f"Initializing info file at: {self.file}")
        except Exception as e:
            logger.error(f"Error initializating info file: {e}")
            raise
        
    def write(self, info: str):
        try:
            with open(self.file, 'a', encoding="utf-8") as f:
                f.write(info)
        except Exception as e:
            logger.error(f"Error writing info to {self.file}: {e}")
            raise

    def write_line(self, info: str):
        try:
            with open(self.file, 'a', encoding="utf-8") as f:
                f.write(info + "\n")
        except Exception as e:
            logger.error(f"Error writing info to {self.file}: {e}")
            raise

    def write_llm_config(self, llm_config: dict):
        self.write("LLM\n")
        self.write(f"  - Provider:    {llm_config['llm_provider']}\n")
        self.write(f"  - Model:       {llm_config[llm_config['llm_provider']]['model_name']}\n")
        think = llm_config[llm_config['llm_provider']].get('think', False)
        if think is False:
            self.write(f"  - Think:       Not specified (default value in LLM's API was used)\n")
        else:
            self.write(f"  - Think:       {json.dumps(think, ensure_ascii=False)}\n")

        options = llm_config[llm_config['llm_provider']].get('options', {})
        self.write(f"  - Options:     {json.dumps(options, ensure_ascii=False)}\n\n")