import os
import json


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(
        self,
        dataset_path: str | None = None,
        dataset_csv_delimiter: str | None = None,
        output_path: str | None = None
    ):
        if self._initialized:
            return

        configFileName = 'config/config.json' if os.path.isfile('config/config.json') else 'config/config_template.json'
        with open(configFileName) as f:
            self.config = json.load(f)

        self.config['output_path'] = ""

        if dataset_path is not None:
            self.config['dataset']['path'] = dataset_path
        if dataset_csv_delimiter is not None:
            self.config['dataset']['csv_delimiter'] = dataset_csv_delimiter
        if output_path is not None:
            self.config['output_path'] = output_path

        self._initialized = True

    def get(self):
        return self.config
    