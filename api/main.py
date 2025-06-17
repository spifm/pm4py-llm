from fastapi import FastAPI, Query
from dtos import *
import requests

app = FastAPI()

PM4PY_URL = "http://pm4py-llm-container:8001/run"

@app.get("/")
def read_root():
    return {"message": "API container is running"}

@app.post("/run-pm-analysis")
def run_pm_analysis(request: PMAnalysisRequest):
    try:
        response = requests.post(PM4PY_URL, json=request.dict())
        response.raise_for_status()
        return {"output": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
