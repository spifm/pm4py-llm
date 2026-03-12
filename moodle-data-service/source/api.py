from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
import logging
import sys
from db import MoodleDatabase
from services.event_log_exporter import EventLogExporter
from models.schemas import (
    ExportEventLogRequest,
    ExportEventLogResponse,
    AsyncExportEventLogResponse,
)
from tasks.export_event_log_task import export_event_log_task
import redis
from rq import Queue


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

DATASET_DIR = os.getenv("DATASET_DIR", "/dataset")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)
task_queue = Queue("default", connection=redis_conn)

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
        "- `dbname` (str): Name of the Moodle database to connect to. If not provided, the default from environment variables will be used.\n"
        "- `dataset_name` (str): Name to use for the exported dataset file without extension. If not provided, a default name will be used.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"course_id\": 123,\n"
        "  \"dbname\": \"my_dbname\"\n"
        "  \"dataset_name\": \"my_dataset\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"message\": \"Event log exported successfully\",\n"
        "  \"output_file\": \"/dataset/my_dataset.csv\",\n"
        "  \"rows_exported\": 100,\n"
        "  \"course_info\": {\n"
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
    dbname = request.dbname
    dataset_name = request.dataset_name
    logger.info("Exporting event log for course_id=%s", course_id)

    try:
        db = MoodleDatabase.from_env()
        if dbname:
            db.set_dbname(dbname)

        event_log_exporter = EventLogExporter(
            db=db,
            course_id=course_id,
            dataset_dir=DATASET_DIR,
            dataset_name=dataset_name
        )
        rows_exported = event_log_exporter.export_course_event_log()

        return ExportEventLogResponse(
            message="Event log exported successfully",
            output_file=event_log_exporter.get_dataset_path(),
            rows_exported=rows_exported,
            course_info=event_log_exporter.get_course_info(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Unexpected error exporting event log for course_id=%s", course_id)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error exporting event log",
        )


@app.post(
    "/async/export-event-log",
    response_model=AsyncExportEventLogResponse,
    summary="Asynchronously export Moodle event log for a course",
    description=(
        "Async endpoint to export the event log of a Moodle course in the background.\n\n"
        "**Required input:**\n"
        "- `course_id` (int): ID of the Moodle course to export the event log from.\n"
        "\n**Optional input:**\n"
        "- `dbname` (str): Name of the Moodle database to connect to. If not provided, the default from environment variables will be used.\n"
        "- `dataset_name` (str): Name to use for the exported dataset file without extension. If not provided, a default name will be used.\n"
        "**Example input:**\n"
        "```json\n"
        "{\n"
        "  \"course_id\": 123,\n"
        "  \"dbname\": \"my_dbname\"\n"
        "  \"dataset_name\": \"my_dataset\"\n"
        "}\n"
        "```"
        "\n\n"
        "**Example response:**\n"
        "```json\n"
        "{\n"
        "  \"message\": \"Event log export started\",\n"
        "  \"expected_output_file\": \"/dataset/my_dataset.csv\",\n"
        "  \"course_info\": {\n"
        "    \"id\": 123,\n"
        "    \"fullname\": \"Example Course\",\n"
        "    \"shortname\": \"EXC\"\n"
        "  }\n"
        "}\n"
        "```"
    ),
    dependencies=[Depends(verify_token)],
)
async def export_event_log_async(
    request: ExportEventLogRequest
):
    course_id = request.course_id
    dbname = request.dbname
    dataset_name = request.dataset_name
    logger.info("Received async export request for course_id=%s", course_id)

    # Check course exists and get its info
    try:
        db = MoodleDatabase.from_env()
        if dbname:
            db.set_dbname(dbname)

        event_log_exporter = EventLogExporter(
            db=db,
            course_id=course_id,
            dataset_dir=DATASET_DIR,
            dataset_name=dataset_name
        )

        course_info = event_log_exporter.get_course_info()
        if course_info is None:
            raise ValueError(f"Course with id {course_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Unexpected error while checking course_id=%s", course_id)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while checking course",
        )

    # Execute export task in background
    job = task_queue.enqueue(
        export_event_log_task,
        event_log_exporter=event_log_exporter,
    )

    return AsyncExportEventLogResponse(
        message="Event log export started",
        job_id=job.id,
        dataset_path=event_log_exporter.get_dataset_path(),
        course_info=course_info,
    )