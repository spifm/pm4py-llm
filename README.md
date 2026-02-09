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

The following containers will be created:
- `pm4py-llm-app`: the container that runs the Python application. It includes the necessary libraries and scripts to run the process mining application. The container will also run the API server to expose the functionalities of the application through a generic endpoint
- `pm4py-llm-api`: the container with the client API. In case of integration with other systems, this API can be used to communicate with the Python application
- `pm4py-moodle-data-service`: the container that runs a Moodle data service. This service is used to fetch data from a Moodle instance
- `pm4py-moodle-data-service-worker`: the container that runs a worker for the Moodle data service. This worker is used to process tasks in a redis queue
- `pm4py-redis`: the container that runs a Redis server. This server is used as a message broker for the Moodle data service
- `pm4py-rq-dashboard`: the container that runs a dashboard for monitoring the Redis queues. This dashboard is used to monitor the tasks in the Redis queue


## Create a config file called config.json using the template to specify configuration parameters

```bash
cp app/config/config_template.json app/config/config.json
```

Then, edit the `app/config/config.json` file to specify the parameters for the application. The configuration file is explained in the next section.

## Run

The system can be run using an API endpoint.

The following permission change could be needed:

```bash
chmod 777 app/dataset/
chmod 777 app/output/
```

The API is available at `http://localhost:8001` after the container `pm4py-llm-app"` is started. The corresponding documentation is available at `http://localhost:8001/docs`.


## Stop the container

```bash
docker compose down
```

# API container

The API documentation is available at `http://localhost:8000/docs` after the container `pm4py-llm-api"` is started. The documentation is generated using [FastAPI] and it provides information about the available endpoints, request and response formats, and examples of how to use the API.

# Configuration

The configuration file is located in the config folder. The file is called config.json and it contains the following parameters:
- `dataset.columns`: list of columns to be used in the log file. The columns must be present in the log file:
    - `case_id` --> field for case identifier
    - `activity` --> field for activity name
    - `timestamp` --> field for timestamp of the activity
- `filter.level`: filter level to be used. Possible values are:
    - `trace` --> to filter by trace attributes
    - `event` --> to filter by event attributes
- `filter.attr`: attribute to be used for filtering. The attribute must be present in the event or trace attributes such as `grade_outcome`, `grade_er`, `grade_final`, etc.
- `filter.export_formats`: list of export formats to be used. If empty, no export will be performed. Possible values are:
    - `csv` --> to export the filtered log in CSV format
    - `xes` --> to export the filtered log in XES format
- `preprocess.enabled`: boolean to enable/disable the preprocessing of the log using true/false
- `preprocess.mapping_activity_json_path`: path to the JSON file containing the activity mapping to be used in the preprocessing step
- `discovery.petri_net`: configuration for discovering a Petri Net
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `infrequent_ratio`: ratio of infrequent activities to be removed from the Petri Net (0-100). If set to 0.00, no infrequent activities will be remove
- `discovery.bpmn`: configuration for discovering BPMN
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `infrequent_ratio`: ratio of infrequent activities to be removed from the BPMN (0-100). If set to 0.00, no infrequent activities will be removed
- `discovery.dfg`: configuration for discovering a DFG
    - `enabled`: boolean to enable/disable the discovery using true/false
    - `performance-enabled`: boolean to enable/disable an additional performance analysis using true/false
- `discovery.temporal_profile`: configuration for discovering a Temporal Profile
    - `enabled`: boolean to enable/disable the discovery of the temporal profile using true/false
- `llm.llm_provider`: provider of the LLM model to be used. Possible values are:
    - `hugging_face` --> to use a model from Hugging Face
    - `ollama` --> to use a model from Ollama
    - `openai` --> to use a model from OpenAI
- If hugging_face is selected as the LLM provider, the following parameters must be specified:
    - `llm.huggingface.hugging_face_api_key`: API key to use the Hugging Face API for the LLM model
    - `llm.huggingface.model_name`: name of the LLM model to use
    - `llm.huggingface.model_type`: type of the LLM model to use, possible values are:
        - `text-generation-inference` --> to use a text generation model
    - `llm.huggingface.max_tokens`: maximum number of tokens to be used in the analysis of the models
- If ollama is selected as the LLM provider, the following parameters must be specified:
    - `llm.ollama.api_url`: URL (including port) of the Ollama API to use the LLM model
    - `llm.ollama.api_endpoint`: endpoint of the Ollama API to use the LLM model
    - `llm.ollama.model_name`: name of the LLM model to use
    - `llm.ollama.options`: options to be used for the Ollama LLM model. Example:
        - options: {
              "temperature": 0.5
          }
        - An empty options object `{}` can be used to skip this option in ollama requests
    - `llm.ollama.max_prompt_tokens`: maximum number of tokens to be used inside the prompt for the request to the model. If not specified (or 0), no limit will be applied.
    - `llm.ollama.think`: reasoning thinking level for the Ollama model. Example values are:
        - `false` --> to skip this option in requests and use the default thinking effort of the model
        - `{"think": false}` --> to force the thinking effort to be disabled in the requests
        - `{"think": true}` --> to force the thinking effort to be enabled in the requests
        - `{"think": "high"}` --> to enable high thinking effort (if supported by the model, i.e. GPT-OSS models)
    - `llm.ollama.json_prompt_config`: configuration for DFG simplification prompts. If it does not exist, the main ollama configuration will be used. It contains the same parameters as the main ollama configuration.
- If openai is selected as the LLM provider, the following parameters must be specified:
    - `llm.openai.api_key`: API key to use the OpenAI API for the LLM model
    - `llm.openai.model_name`: name of the LLM model to use
    - `llm.openai.think`: reasoning effort level for the OpenAI model. Example values are:
        - `false` --> to skip this option in requests and use the default reasoning effort of the model
        - `{"effort": "low"}` --> to enable low reasoning effort
        - `{"effort": "medium"}` --> to enable medium reasoning effort
        - `{"effort": "high"}` --> to enable high reasoning effort
    - `llm.openai.max_tokens`: maximum number of tokens to be used in the analysis of the models
- If gemini is selected as the LLM provider, the following parameters must be specified:
    - `llm.gemini.api_key`: API key to use the Gemini API for the LLM model
    - `llm.gemini.model_name`: name of the LLM model to use
    - `llm.gemini.think`: reasoning thinking level for the Gemini model. Example values are:
        - `false` --> to skip this option in requests and use the default thinking effort of the model
        - `{"thinking_level": "high"}` --> to enable low thinking effort
- `llm.context`: context to be used for the LLM model
- `llm.petri_net`: configuration for analyzing an abstraction of Petri Net
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context
- `llm.dfg`: configuration for analyzing an abstraction of Petri Net. If empty, analysis will not be performed
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context
    - `simplify_dfg.enabled`: boolean to enable/disable the simplification of the DFG using true/false
    - `simplify_dfg.removing_transitions_ratio`: ratio of transitions to be removed from the original DFG (0-100) during the simplification process
    - `simplify_dfg.retaining_transitions_ratio`: ratio of transitions to be retained from the original DFG (0-100) during the simplification process
    - `simplify_dfg.simplification_context_prompt`: context prompt to be used for the simplification of the DFG
    - `simplify_dfg.simplification_instructions_prompt`: prompt joined with the context to be used for the simplification of the DFG
    - `simplify_dfg.simplification_analysis_prompt`: prompt joined with the context to be used to analyze the simplified DFG
- `llm.temporal_profile`: configuration for analyzing an abstraction of Temporal Profile. If empty, analysis will not be performed
    - `enabled`: boolean to enable/disable the analysis using true/false
    - `prompt`: prompt to be used for the analysis joined with the context


# Additional utilities

## Random sample of the log

The application can generate a random sample of the log file indicated in the config file. The sample is generated using `random_sample_selection.py`, which is a script that must be run independently. When the script is run, the user is prompted to enter the number the number of cases to be sampled. The script will then generate a new log file with the sampled cases. The new log file will be saved in the output directory created with a timestamp. Flags indicate the dataset path and the csv delimiter. An example of how to run the script is shown below:

```bash
docker exec -it pm4py-llm-app" python3 -m utils.random_sample_selection --dataset-path="dataset/dataset.csv" --dataset-csv_delimiter=","
```

## Merge abstract dfgs to json

This script reads abstract DFG models from a directory structure, extracts user IDs and grades from folder names, and combines them into a single JSON file for later processing. The script is called `merge_abstract_dfgs_to_json.py` and it must be run independently. When the script is run, the user is prompted to enter the path to the base directory (e.g., output/my-dfg-folder) where the abstract DFGs are stored. The script will then generate a new json file with the merged abstract DFGs. The new log file will be saved in the output directory created with a timestamp. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app" python3 -m utils.merge_abstract_dfgs_to_json
```

## DFG to PNG

This script reads a dfg model from a pm4py .dfg file and generates a PNG image of the model. The script is called `dfg_to_png.py` and it must be run independently. The dfg file path is directly set in the script. The script will then generate a new png file with the DFG model. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app" python3 -m utils.dfg_to_png
```

## CSV to JSON conversion

This script converts a CSV file to a custom JSON format. The script is called `csv_to_json.py` and it must be run independently. The CSV file path is directly set in the script. The script will then generate a new json file with the converted data. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app" python3 -m utils.csv_to_json
``` 

## XES to Histogram

This script generates histograms from XES log files. The script is called `xes_to_histogram.py` and it must be run independently. The XES file path is directly set in the script. The script will then generate histogram plots and data files. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app" python3 -m utils.xes_to_histogram
```

# Build training JSONL for LLM fine-tuning
This script builds a JSONL file for training a Large Language Model (LLM) using prompt-completion pairs based on Directly-Follows Graphs (DFGs). The script is called `build-train-jsonl.py` and it must be run independently. When the script is run, it reads a prompt template from a specified file and processes multiple example directories containing input and output JSON files representing DFGs. It replaces a placeholder in the prompt template with the content of the input JSON files and pairs it with the corresponding output JSON files to create training examples. The resulting prompt-completion pairs are saved in a JSONL file for LLM fine-tuning. The script can be run using the following command:

```bash
docker exec -it pm4py-llm-app python3 -m utils.build-train-jsonl \
  --base-dir llm-training \
  --prompt-file prompt.txt \
  --examples-dir training \
  --output-file train.jsonl \
  --input-filename dfg-generic-activities.json \
  --output-filename llm-simplified-dfg.json
```