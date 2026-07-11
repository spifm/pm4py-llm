from fastapi import FastAPI, HTTPException, Query, status, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from models.schemas import *
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
            detail="Invalid or missing token",
        )

app = FastAPI()


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
        "Runs the full pipeline: pm-analysis → simplify-dfg → summarize-simplified-dfg → get-analysis-files → create-mind-map\n\n"
        "The response contains the **file paths** of the generated artifacts (analysis texts and images)\n\n"
        "**Required input:**\n"
        "- `dataset` (str): the dataset file (CSV format) to analyze.\n"
        "- `output_path` (str): Directory where the analysis results will be stored.\n"
        "\n**Optional input:**\n"
        "- `dataset_csv_delimiter` (Optional[str]): CSV delimiter used in the dataset.\n"
        "- `disable-mind_map` (Optional[bool]): Flag to disable mind map generation.\n"
        "- `disable-summary` (Optional[bool]): Flag to disable simplified DFG summary generation.\n"
        "- `deterministic_ratio` (Optional[float], range `(0, 100]`): when provided, applies a deterministic "
        "frequency pre-filter to the DFG before LLM simplification, retaining the top `deterministic_ratio`% "
        "most frequent transitions. Transitions in the same frequency tier at the cutoff are all kept or all "
        "discarded (no arbitrary tie-breaking). When omitted, the LLM simplification runs on the original DFG.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"dataset\": \"my_dataset.csv\",\n"
        "  \"dataset_csv_delimiter\": \",\",\n"
        "  \"output_path\": \"my-folder\",\n"
        "  \"disable-mind_map\": false,\n"
        "  \"disable-summary\": false,\n"
        "  \"deterministic_ratio\": 20\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"output_dir\": \"XXX\",\n"
        "  \"dfg_analysis\": \"/output/XXX/dfg-analysis.txt\",\n"
        "  \"dfg_images\": {\"svg\": \"/output/XXX/dfg.svg\", \"png\": \"/output/XXX/dfg.png\"},\n"
        "  \"simplified_dfg_analysis\": \"/output/XXX/simplified-dfg-analysis.txt\",\n"
        "  \"simplified_dfg_summary\": \"/output/XXX/simplified-dfg-summary.txt\",\n"
        "  \"simplified_dfg_images\": {\"svg\": \"/output/XXX/simplified-dfg.svg\", \"png\": \"/output/XXX/simplified-dfg.png\"},\n"
        "  \"mind_map_file\": \"output/mind_map.mmd\",\n"
        "  \"mind_map_image_file\": \"output/mind_map.svg\"\n"
        "}\n"
        "\n**Notes**\n"
        "- The response contains file paths, not file content.\n"
        "- If `disable-mind_map` is set to true, the response will not include `mind_map_file` and `mind_map_image_file` fields.\n"
        "- If `disable-summary` is set to true, the response will not include the `simplified_dfg_summary` field.\n"
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
        output_path = output_directory,
        deterministic_ratio = request.deterministic_ratio
    )

    simplify_result = simplify_dfg_endpoint(simplify_request)

    logger.debug(f"Step 2: Simplify DFG output: {simplify_result}")

    if "error" in simplify_result:
        return {"step": "simplify-dfg", "error": simplify_result["error"]}


    # Step 3: Execute summarize_simplified_dfg_endpoint
    if not request.disable_summary:
        logger.debug(f"Starting Step 3: Summarize simplified DFG in {output_directory}")
        summarize_request = SummarizeSimplifiedDFGRequest(
            analysis_dir=output_directory
        )
        summarize_result = summarize_simplified_dfg_endpoint(summarize_request)
        logger.debug(f"Step 3: Summarize simplified DFG output: {summarize_result}")

        if "error" in summarize_result:
            return {"step": "summarize-simplified-dfg", "error": summarize_result["error"]}
    else:
        logger.info("Simplified DFG summary generation is disabled for this analysis by request.")


    # Step 4: Collect analysis result file paths
    try:
        analysis_result = get_analysis_files(analysis_dir=output_directory)
        logger.debug(f"Step 4: Get Analysis files output: {analysis_result}")
    except Exception as e:
        return {"step": "get-analysis-files", "error": str(e)}
    

    content = {
        "output_dir": output_directory,
        **json.loads(analysis_result.body),
    }
    
    # Step 5: Execute create_mind_map
    if not request.disable_mind_map:
        try:
            create_mind_map_request = CreateMindMapRequest(analysis_dir=output_directory)
            mind_map_result = create_mind_map(create_mind_map_request)
            logger.debug(f"Step 5: Create Mind Map output: {mind_map_result}")
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
    "/summarize-simplified-dfg",
    summary="Generate a short explanatory summary of a simplified DFG using an LLM",
    description=(
        "Generates a short, concise explanatory summary (TL;DR) of a simplified "
        "Directly-Follows Graph (DFG) using a Large Language Model (LLM). "
        "This endpoint requires a **previous `/simplify-dfg` run**.\n\n"
        "**Required input:**\n"
        "- `analysis_dir` (str): Directory where the simplified DFG is located.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"analysis_dir\": \"my-folder\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Returns:**\n"
        "- `message`: Confirmation of successful summary generation.\n"
        "- `summary_file`: Path to the summary file generated by the LLM.\n"
        "- `summary`: The generated summary text.\n"
    ),
    dependencies=[Depends(verify_token)]
)
def summarize_simplified_dfg_endpoint(request: SummarizeSimplifiedDFGRequest):
    url = f"{PM4PY_BASE_URL}/summarize-simplified-dfg"
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
        "/get-analysis-files",
        summary="Get analysis result file paths",
        description=(
            "Retrieves the file paths of the analysis results for a given directory, "
            "instead of their content. Only files that actually exist on disk are included.\n\n"
            "**Example response:**\n"
            "```json\n"
            "{\n"
            "  \"dfg_analysis\": \"/output/my-folder/dfg-analysis.txt\",\n"
            "  \"dfg_images\": {\"svg\": \"/output/my-folder/dfg.svg\"},\n"
            "  \"simplified_dfg_analysis\": \"/output/my-folder/simplified-dfg-analysis.txt\",\n"
            "  \"simplified_dfg_summary\": \"/output/my-folder/simplified-dfg-summary.txt\",\n"
            "  \"simplified_dfg_images\": {\"svg\": \"/output/my-folder/simplified-dfg.svg\"}\n"
            "}\n"
            "```"
        ),
        dependencies=[Depends(verify_token)]
)
def get_analysis_files(analysis_dir: str = Query(
                                    alias="analysis_dir",
                                    description="Directory where the analysis results are stored"
                                    )
    ):
    url = f"{PM4PY_BASE_URL}/get-analysis-files"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(url, params={"analysis_dir": analysis_dir}, headers=headers)

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Unknown error")
            except Exception:
                detail = response.text or "Unknown error"
            raise HTTPException(status_code=response.status_code, detail=f"PM4PY error: {detail}")

        return JSONResponse(content=response.json())

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analysis files: {str(e)}")

