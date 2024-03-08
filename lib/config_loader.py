import os.path
import json

# Load configuration
def load_config():
    configFileName = 'config/config.json' if os.path.isfile('config/config.json') else 'config/config_template.json'
    with open(configFileName) as f:
        config = json.load(f)
    return config