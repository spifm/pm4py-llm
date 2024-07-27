## Requirements

- Docker

## Configuration

The configuration file is located in the config folder. The file is called config.json and it contains the following parameters:
- `debug`: boolean to enable debug mode
- `filter.level`: filter level to be used. Possible values are:
    - `trace` --> to filter by trace attributes
    - `event` --> to filter by event attributes
- `filter.attr`: attribute to be used for filtering. The attribute must be present in the event or trace attributes such as `grade_outcome`, `grade_er`, `grade_final`, etc.
- `filter.export_formats`: list of export formats to be used. If empty, no export will be performed. Possible values are:
    - `csv` --> to export the filtered log in CSV format
    - `xes` --> to export the filtered log in XES format
- `discovery.bpmn`: 1 to enable the generation of the BPMN model, 0 to disable it
- `discovery.dfg`: 1 to enable the generation of the DFG, 0 to disable it
- `discovery.temporal_profile`: 1 to enable the generation of a temporal profile, 0 to disable it
- `llm.hugging_face_api_key`: API key to use the Hugging Face API for the LLM model
- `llm.model_name`: name of the LLM model to use
- `llm.petri_net`: configuration for analyzing an abstraction of Petri Net
    - `enabled`: 1 to enable the analysis, 0 to disable it
    - `max_tokens`: maximum number of tokens to be used in the analysis of the Petri Net
- `llm.dfg`: configuration for analyzing an abstraction of Petri Net. If empty, analysis will not be performed
    - `enabled`: 1 to enable the analysis, 0 to disable it
    - `max_tokens`: maximum number of tokens to be used in the analysis of the DFG


## Instructions

### Build the docker image and run the container

```bash
docker-compose up -d
```

### (OPTIONAL) Create a config file called config.json using the template to specify configuration parameters

```bash
cp config/config_template.json config/config.json
```

### Run the python script

```bash
docker exec -it pm4py_app python3 main.py
```

### Stop the container

```bash
docker-compose down
```

