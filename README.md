## Introduction

This Python application uses [pm4py](https://pm4py.fit.fraunhofer.de/) to perform process mining on event logs from any csv/xes dataset and can generate various models: Petri net, DFG, BPMN and Temporal Profile. It uses configurations to filter logs and export models. The application integrates with a Large Language Model (LLM) from Hugging Face to analyze the discovered models and provide insights. The results, including filtered logs and analysis, are saved to an output directory created with a timestamp. The application is dockerized and can be run in any environment.

## Requirements

- Docker

## Configuration

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
- `discovery.petri_net`: boolean to enable/disable the discovery of BPMN using true/false
- `discovery.bpmn`: boolean to enable/disable the discovery of BPMN using true/false
- `discovery.dfg`: boolean to enable/disable the discovery of DFG using true/false
- `discovery.temporal_profile`: boolean to enable/disable the discovery of the temporal profile using true/false
- `llm.hugging_face_api_key`: API key to use the Hugging Face API for the LLM model
- `llm.model_name`: name of the LLM model to use
- `llm.model_type`: type of the LLM model to use, possible values are:
    - `text-generation-inference` --> to use a text generation model
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


## Instructions

### Build the docker image and run the container

```bash
docker compose up -d
```

### Create a config file called config.json using the template to specify configuration parameters

```bash
cp config/config_template.json config/config.json
```

### Add a Hugging Face token in the config file

```json
{
    "llm": {
        "hugging_face_api_key": "your_hugging_face_api_key",
    ...
```

### Run the python script

```bash
docker exec -it pm4py-llm-container python3 main.py
```

### Stop the container

```bash
docker compose down
```

