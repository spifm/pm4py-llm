## Requirements

- Docker

## Configuration

The configuration file is located in the config folder. The file is called config.json and it contains the following parameters:
- `debug`: boolean to enable debug mode
- `filter.level`: filter level to be used. Possible values are:
    - `trace` --> to filter by trace attributes: i.e. case:grade_er
    - `event` --> to filter by event attributes: i.e grade_outcome
- `filter.attr`: attribute to be used for filtering. The attribute must be present in the event or trace attributes


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

