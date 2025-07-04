from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dtos import *
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

security = HTTPBearer()

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

app = FastAPI()

PM4PY_BASE_URL = "http://pm4py-llm-app-container:8001"
CACHE_DIR = "./cache/"
CACHE_DURATION = timedelta(seconds=60 * 60 * 24)  # Cache duration in seconds (1 day)

@app.get(
        "/",
        summary="Check API status",
        description="Returns a simple message to confirm the API container is up.",
        dependencies=[Depends(verify_token)]
)
def read_root():
    return {"message": "API container is running"}

@app.post(
    "/run-pm-analysis",
    summary="Run process mining analysis",
    description="This endpoint sends the analysis request to the PM4PY container, forwarding dataset configuration parameters.",
    dependencies=[Depends(verify_token)]
)
def run_pm_analysis(request: PMAnalysisRequest):
    url = f"{PM4PY_BASE_URL}/run"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(url, json=request.model_dump(), headers=headers)
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
        ),
        dependencies=[Depends(verify_token)]
)
def store_dataset(request: DatasetToStoreRequest):
    url = f"{PM4PY_BASE_URL}/store-dataset"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
    
        # Check if all columns have the same length
        lengths = [len(col) for col in request.data.values()]
        if len(set(lengths)) > 1:
            raise HTTPException(status_code=400, detail="All columns must have the same number of elements.")
        
        res = requests.post(url, json=request.model_dump(), headers=headers)
        return res.json()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
        "/simplify-dfg",
        summary="Simplify DFG using LLM",
        description=("Simplifies a Directly-Follows Graph (DFG) using a Large Language Model (LLM). "
                     "The DFG file path is provided as a string, and the output is saved to a new file."
                     "The request must include:\n"
                     "- `dfg_file`: the full path name of the DFG file\n\n"
                     "**Example:**\n"
                     "```json\n"
                     "{\n"
                     "  \"dfg_file\": \"output/analysis_dir/dfg.dfg\",\n"
                     "}\n"
                     "```"
                    ),
        dependencies=[Depends(verify_token)]
)
def simplify_dfg_endpoint(request: SimplifyDFGRequest):
    url = f"{PM4PY_BASE_URL}/simplify-dfg"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(url, json=request.model_dump(), headers=headers)
        response.raise_for_status()
        return {"output": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.get(
        "/get-analysis",
        summary="Get analysis results",
        description=(
            "Retrieves the analysis results for a given filename.\n\n"
            "It first checks if a cached version exists and is still valid. If so, it returns the cached data.\n"
            "If not, it fetches the data from the PM4PY container and caches it for future requests."
        ),
        dependencies=[Depends(verify_token)]
)
def get_analysis(analysis_dir: str = Query(
                                    alias="analysis_dir",
                                    description="Directory where the analysis results are stored"
                                    )
    ):
    # Check if the analysis is stored in a cache directory
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{analysis_dir}.json")

    if os.path.isfile(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time < CACHE_DURATION:
             with open(cache_file, "r") as f:
                return JSONResponse(content=json.load(f))

    # If not cached or cache is expired, fetch from PM4PY container
    url = f"{PM4PY_BASE_URL}/get-analysis"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(url, params={"analysis_dir": analysis_dir}, headers=headers)

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Unknown error")
            except Exception:
                detail = response.text or "Unknown error"
            raise HTTPException(status_code=response.status_code, detail=f"PM4PY error: {detail}")

        data = response.json()

        with open(cache_file, "w") as f:
            json.dump(data, f)

        return JSONResponse(content=data)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis: {str(e)}")