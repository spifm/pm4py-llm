## Requirements

- Docker

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

