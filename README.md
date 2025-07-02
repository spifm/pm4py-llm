# Introduction

This Python application uses [pm4py](https://pm4py.fit.fraunhofer.de/) to perform process mining on event logs from any csv/xes dataset and can generate various models: Petri net, DFG, BPMN and Temporal Profile. It uses configurations to filter logs and export models. The application integrates with a Large Language Model (LLM) to analyze the discovered models and provide insights. The results, including filtered logs and analysis, are saved to an output directory created with a timestamp. The application is dockerized and can be run in any environment.

# Requirements

- Docker

# Instructions


## Create .env file
Create a `.env` file in the root directory of the project to specify environment variables for the application. This file is used to configure the API token for secure access to the API endpoints. Use the .env.example file as a template:

```bash
cp .env.example .env
```

## Build the docker images and run the containers

```bash
docker compose up -d
```

Two containers will be created:
- `pm4py-llm-container`: the container that runs the Python application. It includes the necessary libraries and scripts to run the process mining application. The container will also run the API server to expose the functionalities of the application through a generic endpoint
- `api-container`: the container with the client API. In case of integration with other systems, this API can be used to communicate with the Python application

## Create a config file called config.json using the template to specify configuration parameters

```bash
cp app/config/config_template.json app/config/config.json
```

Then, edit the `app/config/config.json` file to specify the parameters for the application. The configuration file is explained in the next section.

## Run

The system can be run using a command or using an API endpoint.

The following permission change could be needed:

```bash
chmod 777 app/dataset/
chmod 777 app/output/
```

### Using the script main.py

```bash
docker exec -it pm4py-llm-app-container python3 main.py
```

### Using the API endpoint

The API is available at `http://localhost:8001` after the container `pm4py-llm-app-container` is started. The corresponding documentation is available at `http://localhost:8001/docs`.

## Stop the container

```bash
docker compose down
```

# API container

The API documentation is available at `http://localhost:8000/docs` after the container `pm4py-llm-api-container` is started. The documentation is generated using [FastAPI] and it provides information about the available endpoints, request and response formats, and examples of how to use the API.

# Configuration

The configuration file is located in the config folder. The file is called config.json and it contains the following parameters:
- `dataset.path`: path to the log file to be analyzed
- `dataset.csv_delimiter`: separator used in the CSV file (ignored if the file is not in CSV format)
- `dataset.columns`: list of columns to be used in the log file. The columns must be present in the log file:
    - `case_id` --> field for case identifier
    - `activity` --> field for activity name
    - `timestamp` --> field for timestamp of the activity
- `debug`: boolean to enable debug mode
- `filter.level`: filter level to be used. Possible values are:
    - `trace` --> to filter by trace attributes
    - `event` --> to filter by event attributes
- `filter.attr`: attribute to be used for filtering. The attribute must be present in the event or trace attributes such as `grade_outcome`, `grade_er`, `grade_final`, etc.
- `filter.export_formats`: list of export formats to be used. If empty, no export will be performed. Possible values are:
    - `csv` --> to export the filtered log in CSV format
    - `xes` --> to export the filtered log in XES format
- `discovery.petri_net`: configuration for discovering a Petri Net
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `infrequent_ratio`: ratio of infrequent activities to be removed from the Petri Net (0-100). If set to 0.00, no infrequent activities will be remove
- `discovery.bpmn`: configuration for discovering BPMN
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `infrequent_ratio`: ratio of infrequent activities to be removed from the BPMN (0-100). If set to 0.00, no infrequent activities will be removed
- `discovery.dfg`: configuration for discovering a DFG
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `performance-enabled`: boolean to enable/disable an additional performance analysis using true/false
- `discovery.temporal_profile`: boolean to enable/disable the discovery of the temporal profile using true/false
- `llm.llm_provider`: provider of the LLM model to be used. Possible values are:
    - `hugging_face` --> to use a model from Hugging Face
    - `ollama` --> to use a model from Ollama
- If hugging_face is selected as the LLM provider, the following parameters must be specified:
    - `llm.huggingface.hugging_face_api_key`: API key to use the Hugging Face API for the LLM model
    - `llm.huggingface.model_name`: name of the LLM model to use
    - `llm.huggingface.model_type`: type of the LLM model to use, possible values are:
        - `text-generation-inference` --> to use a text generation model
- If ollama is selected as the LLM provider, the following parameters must be specified:
    - `llm.ollama.api_url`: URL (including port) of the Ollama API to use the LLM model
    - `llm.ollama.api_endpoint`: endpoint of the Ollama API to use the LLM model
    - `llm.ollama.model_name`: name of the LLM model to use
- `llm.context`: context to be used for the LLM model
- `llm.petri_net`: configuration for analyzing an abstraction of Petri Net
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context
    - `max_tokens`: maximum number of tokens to be used in the analysis of the Petri Net
- `llm.dfg`: configuration for analyzing an abstraction of Petri Net. If empty, analysis will not be performed
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context
    - `max_tokens`: maximum number of tokens to be used in the analysis of the DFG
- `llm.temporal_profile`: configuration for analyzing an abstraction of Temporal Profile. If empty, analysis will not be performed
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context
    - `max_tokens`: maximum number of tokens to be used in the analysis of the DFG


# Additional utilities

## Random sample of the log

The application can generate a random sample of the log file indicated in the config file. The sample is generated using `random_sample_selection.py`, which is a script that must be run independently. When the script is run, the user is prompted to enter the number the number of cases to be sampled. The script will then generate a new log file with the sampled cases. The new log file will be saved in the output directory created with a timestamp. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app-container python3 utils/random_sample_selection.py
```

## Merge abstract dfgs to json

This script reads abstract DFG models from a directory structure, extracts user IDs and grades from folder names, and combines them into a single JSON file for later processing. The script is called `merge_abstract_dfgs_to_json.py` and it must be run independently. When the script is run, the user is prompted to enter the path to the base directory (e.g., output/my-dfg-folder) where the abstract DFGs are stored. The script will then generate a new json file with the merged abstract DFGs. The new log file will be saved in the output directory created with a timestamp. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app-container python3 utils/merge_abstract_dfgs_to_json.py
```

## DFG to PNG

This script reads a dfg model from a pm4py .dfg file and generates a PNG image of the model. The script is called `dfg_to_png.py` and it must be run independently. The dfg file path is directly set in the script. The script will then generate a new png file with the DFG model. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app-container python3 utils/dfg_to_png.py
```

## CSV to JSON conversion

This script converts a CSV file to a custom JSON format. The script is called `csv_to_json.py` and it must be run independently. The CSV file path is directly set in the script. The script will then generate a new json file with the converted data. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app-container python3 utils/csv_to_json.py
``` 