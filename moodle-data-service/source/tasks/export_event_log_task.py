
import os
import logging
from services.event_log_exporter import EventLogExporter

logger = logging.getLogger(__name__)

def export_event_log_task(event_log_exporter: EventLogExporter, course_id: int, dataset_name: str | None):
    """
    Background task to export the event log of a course.
    """
    try:
        logger.info(
            "Starting background export for course_id=%s, dataset_name=%s",
            course_id,
            dataset_name,
        )
        output_file, rows_exported, course_info = event_log_exporter.export_course_event_log(
            course_id=course_id,
            dataset_name=dataset_name,
        )
        logger.info(
            "Background export completed for course_id=%s. File=%s, rows=%s",
            course_id,
            output_file,
            rows_exported,
        )
    except Exception:
        logger.exception(
            "Background export failed for course_id=%s, dataset_name=%s",
            course_id,
            dataset_name,
        )
