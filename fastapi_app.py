# fastapi_app.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

class ScriptRequest(BaseModel):
    script: str = "main.py"
    args: list[str] = []

@app.post("/run")
def run_script(req: ScriptRequest):
    script_path = os.path.join("/pm4py-llm", req.script)
    if not os.path.isfile(script_path):
        return {"error": f"Script not found: {script_path}"}

    try:
        # Run the script as a subprocess and capture the output
        result = subprocess.run(
            ["python3", script_path] + req.args,
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
