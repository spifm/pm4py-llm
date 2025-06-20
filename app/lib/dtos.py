from pydantic import BaseModel
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    script: Optional[str] = "main.py"
    datasetPath: str
    datasetCsvDelimiter: str = ","

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]