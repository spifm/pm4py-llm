import os
import logging
from typing import Tuple, List, Any
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from db import MoodleDatabase
import csv
import re
from models.schemas import CourseInfo
from .event_log_metadata_builder import EventLogMetadataBuilder

logger = logging.getLogger(__name__)


class EventLogExporter:
    """
    Service that is responsible for:
        - Checking that the course exists.
        - Executing the logs query.
        - Writing the result to CSV.
    """

    def __init__(self, db: MoodleDatabase, output_dir: str):
        self.db = db
        self.output_dir = output_dir
        self.metadata_service = EventLogMetadataBuilder()
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize the dataset name to use it as a file name:
        - convert to lowercase
        - replace spaces with underscores
        - remove weird characters
        """
        name = name.strip().lower()
        name = name.replace(" ", "_")
        name = re.sub(r"[^a-z0-9_\-]", "", name)
        return name or "dataset"


    def _fetch_logs(self, course_id: int) -> Tuple[List[str], List[tuple]]:
        """
        Returns (columns, rows) of the event log of the course filtered only for students.
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                query = sql.SQL(
                    """
                    SELECT
                        log.eventname,
                        log.action,
                        log.userid,
                        log.component,
                        log.timecreated
                    FROM {log_table} AS log
                    JOIN {user_table} AS u
                        ON u.id = log.userid
                    JOIN {role_assignments_table} AS ra
                        ON ra.userid = u.id
                    JOIN {role_table} AS r
                        ON r.id = ra.roleid
                    JOIN {context_table} AS ctx
                        ON ctx.id = ra.contextid
                    WHERE log.courseid = %s
                    AND r.shortname = 'student'
                    AND ctx.instanceid = log.courseid
                    ORDER BY log.timecreated
                    """
                ).format(
                    log_table=sql.Identifier(f"{self.db.table_prefix}logstore_standard_log"),
                    user_table=sql.Identifier(f"{self.db.table_prefix}user"),
                    role_assignments_table=sql.Identifier(f"{self.db.table_prefix}role_assignments"),
                    role_table=sql.Identifier(f"{self.db.table_prefix}role"),
                    context_table=sql.Identifier(f"{self.db.table_prefix}context"),
                )

                cur.execute(query, (course_id,))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]

        return colnames, rows
    

    def get_course_info(self, course_id: int) -> CourseInfo | None:
        """
        Returns a `dict` course info (id, fullname, shortname)
        or None if the course does not exist.
        """
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = sql.SQL(
                    """
                    SELECT id, fullname, shortname
                    FROM {course_table}
                    WHERE id = %s
                    """
                ).format(
                    course_table=sql.Identifier(f"{self.db.table_prefix}course")
                )

                cur.execute(query, (course_id,))
                row = cur.fetchone()
                return CourseInfo(**row) if row else None
                # Type conversion dict -> Pydantic model


    def get_output_path(
        self,
        course_id: int,
        dataset_name: str | None = None,
    ) -> str:
        """
        Returns the expected dataset filename for a given course_id and optional dataset_name.
        """
        if dataset_name:
            safe_name = self._sanitize_filename(dataset_name)
        else:
            safe_name = f"dataset-{course_id}"
        return os.path.join(self.output_dir, f"{safe_name}.csv")


    def export_course_event_log(
        self,
        course_id: int,
        dataset_name: str | None = None,
    ) -> tuple[str, int, CourseInfo]:
        """
        Exports the event log of a course to CSV.
        If dataset_name is provided, it is used to name the file.
        Returns (file_path, number_of_rows, course_info).
        """
        course_info = self.get_course_info(course_id)
        if course_info is None:
            logger.warning("Course %s not found", course_id)
            raise ValueError(f"Course with id {course_id} not found")

        logger.info(
            "Exporting event log for course_id=%s (%s)",
            course_info.id,
            course_info.fullname,
        )

        colnames, rows = self._fetch_logs(course_id)

        output_path = self.get_output_path(
            course_id=course_id,
            dataset_name=dataset_name,
        )

        logger.info("Writing %s rows to %s", len(rows), output_path)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(
                f,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_ALL,
            )
            writer.writerow(colnames)
            writer.writerows(rows)


        self.metadata_service.write_metadata(
            dataset_path=output_path,
            row_count=len(rows),
            course_info=course_info,
        )

        return output_path, len(rows), course_info