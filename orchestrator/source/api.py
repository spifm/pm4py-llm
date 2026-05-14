from fastapi import FastAPI, HTTPException, Query, status, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from models.schemas import *
from helpers.cache_results_helper import CacheResultsHelper
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import logging
import sys
from pathlib import Path


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
PM4PY_BASE_URL = os.getenv("PM4PY_BASE_URL", "http://pm4py-llm-app:8001")

if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set in environment variables")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not token or token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token" + API_TOKEN,
        )

app = FastAPI()

cache_results_helper = CacheResultsHelper()


SIMPLIFY_FILE = "dfg-generic-activities.json"

@app.get(
        "/",
        summary="Check API status",
        description="Returns a simple message to confirm the API container is up.",
        dependencies=[Depends(verify_token)]
)
def read_root():
    return {"message": "API container is running"}



@app.post(
    "/run-full-analysis",
    summary="Execute full analysis pipeline: process mining analysis, simplification, mind map, and return results",
    description=(
        "Runs the full pipeline: pm-analysis → simplify-dfg → get-analysis → create-mind-map\n\n"
        "**Required input:**\n"
        "- `dataset` (str): the dataset file (CSV format) to analyze.\n"
        "- `output_path` (str): Directory where the analysis results will be stored.\n"
        "\n**Optional input:**\n"
        "- `dataset_csv_delimiter` (Optional[str]): CSV delimiter used in the dataset.\n"
        "- `disable-mind_map` (Optional[bool]): Flag to disable mind map generation.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"dataset\": \"my_dataset.csv\",\n"
        "  \"dataset_csv_delimiter\": \",\",\n"
        "  \"output_path\": \"my-folder\",\n"
        "  \"disable-mind_map\": false\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"output_dir\": \"XXX\",\n"
        "  \"analysis\": \"XXX\",\n"
        "  \"dfg_images\": {\"svg\": \"XXX\", \"png\": \"XXX\"},\n"
        "  \"simplified_dfg_analysis\": \"XXX\",\n"
        "  \"simplified_dfg_images\": {\"svg\": \"XXX\", \"png\": \"XXX\"},\n"
        "  \"mind_map_file\": \"output/mind_map.mmd\"\n"
        "  \"mind_map_image_file\": \"output/mind_map.svg\"\n"
        "}\n"
        "\n**Notes**\n"
        "- If `disable-mind_map` is set to true, the response will not include `mind_map_file` and `mind_map_image_file` fields.\n"
        "```"
    ),
    dependencies=[Depends(verify_token)]
)
def full_analysis(
    request: FullAnalysisRequest = Body(..., description="Request body for full analysis")
):
    logger.debug(f"Running full analysis with request: {request}")

    # Step 1: Execute pm_analysis
    pm_analysis_request = PMAnalysisRequest(
        dataset=request.dataset,
        output_path=request.output_path
    )

    if request.dataset_csv_delimiter is not None:
        pm_analysis_request.dataset_csv_delimiter = request.dataset_csv_delimiter

    pm_result = pm_analysis(pm_analysis_request)

    logger.debug(f"Step 1 Completed: PM Analysis output: {pm_result}")

    if "error" in pm_result:
        return {"step": "pm-analysis", "error": pm_result["error"]}
    
    output_directory = pm_result["output_directory_name"]

    logger.debug(f"Starting Step 2: Simplify DFG in {output_directory}")
    
    # Step 2: Execute simplify_dfg_endpoint
    simplify_request = SimplifyDFGRequest(
        output_path = output_directory
    )

    simplify_result = simplify_dfg_endpoint(simplify_request)

    logger.debug(f"Step 2: Simplify DFG output: {simplify_result}")

    if "error" in simplify_result:
        return {"step": "simplify-dfg", "error": simplify_result["error"]}


    # Step 3: Execute get_analysis
    try:
        analysis_result = get_analysis(analysis_dir=output_directory)
        logger.debug(f"Step 3: Get Analysis output: {analysis_result}")
    except Exception as e:
        return {"step": "get-analysis", "error": str(e)}
    

    content = {
        "output_dir": output_directory,
        **json.loads(analysis_result.body),
    }
    
    # Step 4: Execute create_mind_map
    if not request.disable_mind_map:
        try:
            create_mind_map_request = CreateMindMapRequest(analysis_dir=output_directory)
            mind_map_result = create_mind_map(create_mind_map_request)
            logger.debug(f"Step 4: Create Mind Map output: {mind_map_result}")
            content.update(json.loads(mind_map_result.body))
        except Exception as e:
            return {"step": "create-mind-map", "error": str(e)}
    else:
        logger.info("Mind map generation is disabled for this analysis by request.")
    

    return JSONResponse(
        content=content
    )


@app.post(
    "/pm-analysis",
    summary="Run process mining analysis",
    description="This endpoint sends the analysis request to the PM4PY container, forwarding dataset configuration parameters.",
    dependencies=[Depends(verify_token)]
)
def pm_analysis(request: PMAnalysisRequest):
    url = f"{PM4PY_BASE_URL}/pm-analysis"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(url, json=request.model_dump(), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    

@app.post(
        "/store-dataset",
        summary="Store json dataset as CSV",
        description=(
            "This endpoint stores a JSON dataset as a CSV file in the PM4PY container.\n\n"
            "The request must include:\n"
            "- `filename`: the full path of the CSV file.\n"
            "- `data`: a JSON object where keys are column names and values are arrays of column values.\n\n"
            "**Example:**\n"
            "```json\n"
            "{\n"
            "  \"filename\": \"/dataset/my_dataset.csv\",\n"
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
    summary="Simplify a Directly-Follows Graph (DFG) using an LLM",
    description=(
        "Simplifies a Directly-Follows Graph (DFG) using a Large Language Model (LLM). "
        "This endpoint requires a **previous process mining analysis** that has generated a DFG file in PM4Py format.\n\n"
        "**Required input:**\n"
        "- `output_path` (str): Path where the DFG file to simplify is located.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"output_path\": \"my-folder\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Returns:**\n"
        "- `message`: Confirmation of successful simplification.\n"
        "- `output_analysis`: Path to the analysis file generated by the LLM.\n"
        "- `llm_simplified_dfg`: Path to the simplified DFG file generated by the LLM.\n"
        "- `simplified_dfg`: Path to the simplified DFG file.\n"
        "- `simplified_dfg_images`: Paths to the images representing the simplified DFG, keyed by format.\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"message\": \"DFG simplified successfully\",\n"
        "  \"output_analysis\": \"/output/simplified-dfg-analysis.txt\",\n"
        "  \"llm_simplified_dfg\": \"/output/llm-simplified-dfg.txt\",\n"
        "  \"simplified_dfg\": \"/output/simplified-dfg.dfg\",\n"
        "  \"simplified_dfg_images\": {\"svg\": \"/output/simplified-dfg.svg\", \"png\": \"/output/simplified-dfg.png\"}\n"
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


@app.post(
        "/create-mind-map",
        summary="Create a Mermaid mind map",
        description=(
            "Creates a Mermaid mind map based on the simplified analysis results.\n\n"
            "**Example response:**\n"
            "```json\n"
            "{\n"
            "  \"mind_map_file\": \"output/mind_map.mmd\",\n"
            "  \"mind_map_image_file\": \"output/mind_map.svg\",\n"
            "}\n"
            "```"
        ),
        dependencies=[Depends(verify_token)]
)
def create_mind_map(request: CreateMindMapRequest):

    url = f"{PM4PY_BASE_URL}/create-mind-map"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(url, json=request.model_dump(), headers=headers)
        response.raise_for_status()
        return JSONResponse(content=response.json())
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    

@app.get(
        "/get-analysis",
        summary="Get analysis results",
        description=(
            "Retrieves the analysis results for a given directory.\n\n"
            "It first checks if a cached version exists and is still valid. If so, it returns the cached data.\n"
            "If not, it fetches the data from the PM4PY container and caches it for future requests.\n\n"
            "**Example response:**\n"
            "```json\n"
            "{\n"
            "  \"analysis\": \"XXX\",\n"
            "  \"dfg_images\": {\"svg\": \"XXX\", \"png\": \"XXX\"},\n"
            "  \"simplified_dfg_analysis\": \"XXX\",\n"
            "  \"simplified_dfg_images\": {\"svg\": \"XXX\", \"png\": \"XXX\"}\n"
            "}\n"
            "```"
        ),
        dependencies=[Depends(verify_token)]
)
def get_analysis(analysis_dir: str = Query(
                                    alias="analysis_dir",
                                    description="Directory where the analysis results are stored"
                                    )
    ):
    # Check if the analysis is stored in a cache directory
    if cache_results_helper.is_enabled():
        cache, cache_file = cache_results_helper.read_from_cache(analysis_dir, simplified=False)
        if cache is not None:
            return JSONResponse(content=cache)

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

        if cache_results_helper.is_enabled():
            cache_results_helper.write_to_cache(cache_file, data)

        return JSONResponse(content=data)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis: {str(e)}")


@app.get(
        "/get-simplified-analysis",
        summary="Get simplified analysis results",
        description=(
            "Retrieves the simplified analysis results for a given directory.\n\n"
            "It first checks if a cached version exists and is still valid. If so, it returns the cached data.\n"
            "If not, it fetches the data from the PM4PY container and caches it for future requests.\n\n"
            "**Example response:**\n"
            "```json\n"
            "{\n"
            "  \"simplified_dfg_analysis\": \"XXX\",\n"
            "  \"simplified_dfg_images\": {\"svg\": \"XXX\", \"png\": \"XXX\"}\n"
            "}\n"
            "```"
        ),
        dependencies=[Depends(verify_token)]
)
def get_simplified_analysis(analysis_dir: str = Query(
                                    alias="analysis_dir",
                                    description="Directory where the analysis results are stored"
                                    )
    ):
    # Check if the simplified analysis is stored in a cache directory
    if cache_results_helper.is_enabled():
        cache, cache_file = cache_results_helper.read_from_cache(analysis_dir, simplified=True)
        if cache is not None:
            return JSONResponse(content=cache)

    # If not cached or cache is expired, fetch from PM4PY container
    url = f"{PM4PY_BASE_URL}/get-simplified-analysis"
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

        if cache_results_helper.is_enabled():
            cache_results_helper.write_to_cache(cache_file, data)

        return JSONResponse(content=data)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis: {str(e)}")
