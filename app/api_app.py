from fastapi import FastAPI, HTTPException
from lib.dtos import *
import subprocess
import os
from lib.store_dataset_as_csv import store_json_dataset_as_csv

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
                "--dataset-csv_delimiter", request.datasetCsvDelimiter,
                "--output_path", request.outputPath
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


@app.post("/store-dataset")
def run_script(request: DatasetToStoreRequest):
    try:
        output_path = store_json_dataset_as_csv(request.filename, request.data)
        return {"success": True, "file": output_path}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))