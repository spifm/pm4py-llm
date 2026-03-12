import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from models.schemas import CourseInfo, DBInfo

class EventLogMetadataBuilder:
    def _build_metadata(
        self,
        dataset_path: str,
        row_count: int,
        db_info: DBInfo,
        course_info: CourseInfo,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = {
            "dataset_path": dataset_path,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "row_count": row_count,
            "database": {
                "name": db_info.name,
                "av": db_info.av,
                "year": db_info.year,
            },
            "course": {
                "id": course_info.id,
                "fullname": course_info.fullname,
                "shortname": course_info.shortname,
            },
        }

        if extra:
            metadata.update(extra)

        return metadata

    def _get_metadata_path(self, dataset_path: str) -> str:
        path = Path(dataset_path)
        return str(path.with_suffix(".meta.json"))
    
    def _build_db_info(self, dbname: str) -> DBInfo:
        m = re.search(r'_(av\d+)_(\d{2}_\d{2})_db$', dbname)

        db_av = m.group(1) if m else None
        db_year = m.group(2) if m else None
        return DBInfo(
            name=dbname,
            av=db_av if db_av else "unknown",
            year=db_year if db_year else "unknown",
        )

    def write_metadata(
        self,
        dataset_path: str,
        row_count: int,
        db_name: str,
        course_info: CourseInfo,
        extra: dict[str, Any] | None = None,
    ) -> str:
        metadata = self._build_metadata(
            dataset_path=dataset_path,
            row_count=row_count,
            db_info=self._build_db_info(db_name),
            course_info=course_info,
            extra=extra,
        )

        metadata_path = self._get_metadata_path(dataset_path)

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return metadata_path