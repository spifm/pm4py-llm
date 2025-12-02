from pydantic import BaseModel
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    script: Optional[str] = "main.py"
    datasetPath: str
    datasetCsvDelimiter: str = ","
    outputPath: Optional[str] = ""

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]

class SimplifyDFGRequest(BaseModel):
    outputPath: str
    prompt_context: Optional[List[str]] = None

