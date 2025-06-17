from fastapi import FastAPI, Query
from lib.dtos import PMAnalysisRequest
import subprocess
import os

app = FastAPI()

@app.post("/run")
def run_script(request: PMAnalysisRequest):
    script_path = os.path.join("/app", request.script)
    if not os.path.isfile(script_path):
        return {"error": f"Script not found: {script_path}"}

    try:
        # Run the script as a subprocess and capture the output
        result = subprocess.run(
            [
                "python3",
                script_path,
                "--dataset-path", request.datasetPath,
                "--dataset-csv_delimiter", request.datasetCsvDelimiter
            ],
            capture_output=True,
            text=True,
            timeout=600
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}
