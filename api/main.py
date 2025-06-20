from fastapi import FastAPI, HTTPException
from dtos import *
import requests

app = FastAPI()

PM4PY_BASE_URL = "http://pm4py-llm-container:8001"

@app.get(
        "/",
        summary="Check API status",
        description="Returns a simple message to confirm the API container is up."
)
def read_root():
    return {"message": "API container is running"}

@app.post(
    "/run-pm-analysis",
    summary="Run process mining analysis",
    description="This endpoint sends the analysis request to the PM4PY container, forwarding dataset configuration parameters."
)
def run_pm_analysis(request: PMAnalysisRequest):
    url = f"{PM4PY_BASE_URL}/run"
    try:
        response = requests.post(url, json=request.model_dump())
        response.raise_for_status()
        return {"output": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@app.post(
        "/store-dataset",
        summary="Store json dataset as CSV",
        description=(
        "This endpoint stores a JSON dataset as a CSV file in the PM4PY container.\n\n"
        "The request must include:\n"
        "- `filename`: the name of the CSV file.\n"
        "- `data`: a JSON object where keys are column names and values are arrays of column values.\n\n"
        "**Example:**\n"
        "```json\n"
        "{\n"
        "  \"filename\": \"my_dataset.csv\",\n"
        "  \"data\": {\n"
        "    \"column1\": [\"value1\", \"value2\"],\n"
        "    \"column2\": [10, 20]\n"
        "  }\n"
        "}\n"
        "```"
    )
)
def store_dataset(request: DatasetToStoreRequest):
    url = f"{PM4PY_BASE_URL}/store-dataset"

    try:
    
        # Check if all columns have the same length
        lengths = [len(col) for col in request.data.values()]
        if len(set(lengths)) > 1:
            raise HTTPException(status_code=400, detail="All columns must have the same number of elements.")
        
        res = requests.post(url, json=request.model_dump())
        return res.json()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
