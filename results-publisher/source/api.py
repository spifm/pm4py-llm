from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
import logging
import sys
from services.publish_results_service import PublishResultsService
from models.schema import PublishResultsRequest, PublishResultsResponse


# ─── Config .env and logging ─────────────────────────────────

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set in environment variables")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


# ─── Security ────────────────────────────────────────────────


security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not token or token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )


# ─── FastAPI app ──────────────────────────────────────────────

app = FastAPI()

@app.get(
        "/",
        summary="Check API status",
        description="Returns a simple message to confirm the container is up.",
        dependencies=[Depends(verify_token)]
)
def read_root():
    return {"message": "Container is running"}

@app.post(
    "/publish-results",
    response_model=PublishResultsResponse,
    summary="Publish results from analysis to the production directory",
    description=(
        "Publishes analysis results to the production directory.\n\n"
        "**Required input:**\n"
        "- `results_directory` (str): Path to the directory containing the analysis results to publish.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"results_directory\": \"results/my_results\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"message\": \"Results published successfully\",\n"
        "  \"result\": {\n"
        "    \"results_directory\": \"XXX\",\n"
        "      \"files\": {\n"
        "        \"analysis\": \"XXX\",\n"
        "        \"summary\": \"XXX\",\n"
        "        \"image\": \"XXX\",\n"
        "      }\n"
        "  }\n"
        "  \"published_result\": {\n"
        "    \"published_results_directory\": \"XXX\",\n"
        "      \"files\": {\n"
        "        \"analysis\": \"XXX\",\n"
        "        \"summary\": \"XXX\",\n"
        "        \"image\": \"XXX\",\n"
        "      }\n"
        "  }\n"
        "}\n"
        "```"
        "\n\n"
        "**Notes**\n"
        "- The `summary` file is optional: if it is not present in the results directory, it is skipped (a warning is logged).\n"
    ),
    dependencies=[Depends(verify_token)],
)
def publish_results(request: PublishResultsRequest):
    results_directory = request.results_directory
    logger.info("Publishing results from directory: %s", results_directory)

    try:
        full_results_path = os.path.join("/output", results_directory)
        if not os.path.isdir(full_results_path):
            raise ValueError(f"Results directory '{full_results_path}' does not exist or is not a directory")

        publish_results_service = PublishResultsService()
        result, published_result = publish_results_service.publish_results(full_results_path)

        return PublishResultsResponse(
            message="Results published successfully",
            result=result,
            published_result=published_result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Unexpected error publishing results for directory=%s", results_directory)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error publishing results",
        )
