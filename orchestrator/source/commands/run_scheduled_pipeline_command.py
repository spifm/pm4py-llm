import argparse
import json
import logging
from pathlib import Path
from typing import Any
import os
import sys
import requests
from datetime import datetime


# ------ Configure logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def save_pipeline_result(result: dict, base_dir: str = "/app/source/tmp/pipeline-results") -> str:
    now = datetime.now()
    day_dir = Path(base_dir) / now.strftime("%Y%m%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    file_path = day_dir / f"pipeline_result_{now.strftime('%Y%m%d_%H%M%S')}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return str(file_path)


class RunScheduledPipelineCommand:
    def __init__(self, disable_mind_map: bool = False, deterministic_ratio: float | None = None):
        self.orchestrator_api_url = self._require_env("ORCHESTRATOR_API_URL").rstrip("/")
        self.moodle_data_service_url = self._require_env("MOODLE_DATA_SERVICE_URL").rstrip("/")
        self.results_publisher_url = self._require_env("RESULTS_PUBLISHER_URL").rstrip("/")

        self.bearer_token = self._require_env("API_TOKEN")
        self.timeout = int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "1800")) # 30 minutes default
        self.config_path = "/app/source/config/scheduled_courses.json"
        self.disable_mind_map = disable_mind_map
        self.deterministic_ratio = deterministic_ratio

    def execute(self) -> dict[str, Any]:
        courses = self._load_config(self.config_path)

        results: list[dict[str, Any]] = []

        for course in courses:
            if not course.get("enabled", True):
                logger.info("Skipping disabled course: %s", course.get("course_id"))
                continue

            course_id = course["course_id"]
            dbname = course.get("dbname")

            try:
                logger.info("Scheduled pipeline: Starting STEP 1 (export dataset) for course_id=%s", course_id)
                export_result = self._export_dataset(course_id, dbname)

                dataset = export_result["output_file"]
                course_info = export_result["course_info"]
                #output_path = f"{course_info['shortname']}_{datetime.now().strftime('%Y%m%d')}"
                output_path = f"{datetime.now().strftime('%Y%m%d')}/{course_info['shortname']}"
                logger.info("Scheduled pipeline: Starting STEP 2 (run analysis) for course.shortname=%s, output_path=%s",
                            course_info['shortname'], output_path
                )
                analysis_result = self._run_full_analysis(
                    dataset, output_path, self.disable_mind_map, self.deterministic_ratio
                )

                logger.info("Scheduled pipeline: Starting STEP 3 (publish results) for course.shortname=%s, output_dir=%s",
                            course_info['shortname'], analysis_result["output_dir"]
                )
                publish_result = self._publish_results(analysis_result["output_dir"])

                results.append(
                    {
                        "course_id": course_id,
                        "course.shortname": course_info["shortname"],
                        "course.fullname": course_info["fullname"],
                        "dbname": dbname,
                        "status": "success",
                        "dataset": dataset,
                        "results_directory": analysis_result["output_dir"],
                        "publish_result": publish_result["published_result"]["published_results_directory"],
                    }
                )

                logger.info("Pipeline completed successfully for course_id=%s, course.shortname=%s",
                            course_id, course_info["shortname"]
                )

            except requests.exceptions.RequestException as e:
                logger.exception("HTTP pipeline failed for course_id=%s", course_id)
                results.append(
                    {
                        "course_id": course_id,
                        "dbname": dbname,
                        "status": "error",
                        "error": str(e),
                    }
                )
            except Exception as e:
                logger.exception("Unexpected pipeline failure for course_id=%s", course_id)
                results.append(
                    {
                        "course_id": course_id,
                        "dbname": dbname,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return {
            "message": "Scheduled pipeline execution finished",
            "results": results,
        }

    def _load_config(self, config_path: str) -> list[dict[str, Any]]:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("The scheduled pipeline config must be a JSON list")

        return data

    def _get_headers(self) -> dict[str, str]:
        if not self.bearer_token:
            return {}
        return {"Authorization": f"Bearer {self.bearer_token}"}
    
    def _require_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    def _export_dataset(self, course_id: int, dbname: str) -> dict[str, Any]:
        payload = {
            "course_id": course_id,
            "dbname": dbname,
        }

        response = requests.post(
            f"{self.moodle_data_service_url}/export-event-log",
            json=payload,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _run_full_analysis(
        self,
        dataset: str,
        output_path: str,
        disable_mind_map: bool = False,
        deterministic_ratio: float | None = None,
    ) -> dict[str, Any]:
        payload = {
            "dataset": dataset,
            "output_path": output_path,
            "disable-mind_map": disable_mind_map,
            "deterministic_ratio": deterministic_ratio,
        }

        response = requests.post(
            f"{self.orchestrator_api_url}/run-full-analysis",
            json=payload,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _publish_results(self, results_directory: str) -> dict[str, Any]:
        payload = {
            "results_directory": results_directory,
        }

        response = requests.post(
            f"{self.results_publisher_url}/publish-results",
            json=payload,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the scheduled pipeline command")
    parser.add_argument(
        "--disable-mind_map",
        action="store_true",
        default=False,
        help="Disable mind map generation during full analysis",
    )
    parser.add_argument(
        "--deterministic_ratio",
        type=float,
        default=None,
        help=(
            "Optional deterministic frequency pre-filter ratio (0, 100]. When set, the DFG is "
            "reduced to the top N%% most frequent transitions before the LLM simplification."
        ),
    )
    args = parser.parse_args()

    result = RunScheduledPipelineCommand(
        disable_mind_map=args.disable_mind_map,
        deterministic_ratio=args.deterministic_ratio,
    ).execute()
    saved_path = save_pipeline_result(result)
    print(f"Pipeline result saved to: {saved_path}")
