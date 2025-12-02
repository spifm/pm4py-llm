import os
import json

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance


    def initialize(self, cliArgs=None):
        if self._initialized:
            return

        configFileName = 'config/config.json' if os.path.isfile('config/config.json') else 'config/config_template.json'
        with open(configFileName) as f:
            self.config = json.load(f)

        self.config['output_path'] = ""

        if cliArgs:
            if cliArgs.dataset_path:
                self.config['dataset']['path'] = cliArgs.dataset_path
            if cliArgs.dataset_csv_delimiter:
                self.config['dataset']['csv_delimiter'] = cliArgs.dataset_csv_delimiter
            if cliArgs.output_path:
                self.config['output_path'] = cliArgs.output_path

        self._initialized = True


    def get(self):
        return self.config
    