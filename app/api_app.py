from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from lib.dtos import *
from config.constants import *
from lib.api_lib.store_dataset_as_csv import store_json_dataset_as_csv
import subprocess
import os

security = HTTPBearer()

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token" + API_TOKEN,
        )

app = FastAPI()

@app.post("/run", dependencies=[Depends(verify_token)])
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


@app.post("/store-dataset", dependencies=[Depends(verify_token)])
def run_script(request: DatasetToStoreRequest):
    try:
        output_path = store_json_dataset_as_csv(request.filename, request.data)
        return {"success": True, "file": output_path}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get(
        "/get-analysis",
        summary="Get analysis results",
        description=("Retrieves the analysis results for a given output directory."),
        dependencies=[Depends(verify_token)]
)
def get_analysis(analysis_dir: str = Query(
                                    alias="analysis_dir",
                                    description="Directory where the analysis results are stored"
                                    )
    ):

    basepath = os.path.join(OUTPUT_PATH, analysis_dir)

    if not os.path.isdir(basepath):
        raise HTTPException(status_code=404, detail="Analysis directory not found")
    
    dfgBasepath = os.path.join(basepath, "dfg.png")
    dfgAnalysisBasepath = os.path.join(basepath, "dfg-analysis.txt")
    
    if not os.path.isfile(dfgBasepath) or not os.path.isfile(dfgAnalysisBasepath):
        raise HTTPException(status_code=404, detail=dfgBasepath + " or " + dfgAnalysisBasepath + " not found")

    try:
        with open(dfgAnalysisBasepath, "r") as f:
            dfgAnalysisText = f.read()
        with open(dfgBasepath, "rb") as f:
            dfgImageBytes = f.read()

        return {
            "text": dfgAnalysisText,
            "image": dfgImageBytes.hex()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))