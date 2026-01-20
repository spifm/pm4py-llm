from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
import logging
import sys
from db import MoodleDatabase
from services.event_log_exporter import EventLogExporter
from models.schemas import (
    ExportEventLogRequest,
    ExportEventLogResponse,
    CourseInfo,
)

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
            detail="Invalid or missing token" + API_TOKEN,
        )

# ─── Service instances ────────────────────────────────────────

db = MoodleDatabase.from_env()
output_dir = os.getenv("EXPORT_OUTPUT_DIR", "/data")
event_log_exporter = EventLogExporter(db=db, output_dir=output_dir)

# ─── FastAPI app ──────────────────────────────────────────────

app = FastAPI()

@app.get(
        "/",
        summary="Check API status",
        description="Returns a simple message to confirm the container is up.",
        dependencies=[Depends(verify_token)]
)
def read_root():
    return {"message": "Moodle exporter container is running"}

@app.post(
    "/export-event-log",
    response_model=ExportEventLogResponse,
    summary="Export Moodle event log for a course",
    description=(
        "Checks the course exists and exports its event log to a CSV file.\n\n"
        "**Required input:**\n"
        "- `course_id` (int): ID of the Moodle course to export the event log from.\n"
        "\n**Optional input:**\n"
        "- `dataset_name` (str): Name to use for the exported dataset file. If not provided, a default name will be used.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"course_id\": 123,\n"
        "  \"dataset_name\": \"my_dataset\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"message\": \"Event log exported successfully\",\n"
        "  \"output_file\": \"data/my_dataset.csv\",\n"
        "  \"rows_exported\": 100,\n"
        "  \"course\": {\n"
        "    \"id\": 123,\n"
        "    \"fullname\": \"Example Course\",\n"
        "    \"shortname\": \"EXC\"\n"
        "  }\n"
        "}\n"
        "```"
    ),
    dependencies=[Depends(verify_token)],
)
def export_event_log(request: ExportEventLogRequest):
    course_id = request.course_id
    dataset_name = request.dataset_name
    logger.info("Exporting event log for course_id=%s", course_id)

    try:
        output_file, rows_exported, course_info = event_log_exporter.export_course_event_log(
            course_id=course_id,
            dataset_name=dataset_name,
        )
        return ExportEventLogResponse(
            message="Event log exported successfully",
            output_file=output_file,
            rows_exported=rows_exported,
            course=CourseInfo(**course_info) # Type conversion dict -> Pydantic model
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Unexpected error exporting event log for course_id=%s", course_id)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error exporting event log",
        )