import logging
import os
from source.helpers.filename_getter import Filename

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