import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from models.schemas import CourseInfo

class EventLogMetadataBuilder:
    def _build_metadata(
        self,
        dataset_path: str,
        row_count: int,
        course_info: CourseInfo,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = {
            "dataset_path": dataset_path,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "row_count": row_count,
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

    def write_metadata(
        self,
        dataset_path: str,
        row_count: int,
        course_info: CourseInfo,
        extra: dict[str, Any] | None = None,
    ) -> str:
        metadata = self._build_metadata(
            dataset_path=dataset_path,
            row_count=row_count,
            course_info=course_info,
            extra=extra,
        )

        metadata_path = self._get_metadata_path(dataset_path)

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return metadata_path