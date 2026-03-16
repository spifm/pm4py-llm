from pathlib import Path
from models.schema import DataResultsInfo


class AnalysisInfoFieldNotFoundError(Exception):
    """Raised when a required field is not found in info.txt."""
    pass


class AnalysisInfoReader:
    def read_data_results(self, results_dir: str) -> DataResultsInfo:
        """
        Reads info.txt inside results_dir and extracts:
        - database.av
        - database.year
        - course.shortname

        Args:
            results_dir: Directory containing info.txt.

        Returns:
            DataResultsInfo with the extracted values.

        Raises:
            FileNotFoundError: If info.txt does not exist.
            AnalysisInfoFieldNotFoundError: If any required field is missing.
        """
        info_path = Path(results_dir) / "info.txt"

        if not info_path.exists():
            raise FileNotFoundError(f"info.txt not found: {info_path}")

        database_av = None
        database_year = None
        course_shortname = None

        with open(info_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()

                if stripped.startswith("database.av:"):
                    database_av = stripped.split(":", 1)[1].strip()

                elif stripped.startswith("database.year:"):
                    database_year = stripped.split(":", 1)[1].strip()

                elif stripped.startswith("course.shortname:"):
                    course_shortname = stripped.split(":", 1)[1].strip()

                if database_av and database_year and course_shortname:
                    break

        missing_fields = []
        if not database_av:
            missing_fields.append("database.av")
        if not database_year:
            missing_fields.append("database.year")
        if not course_shortname:
            missing_fields.append("course.shortname")

        if missing_fields:
            raise AnalysisInfoFieldNotFoundError(
                f"Missing required fields in {info_path}: {', '.join(missing_fields)}"
            )

        return DataResultsInfo(
            database_av=database_av,
            database_year=database_year,
            course_shortname=course_shortname,
        )