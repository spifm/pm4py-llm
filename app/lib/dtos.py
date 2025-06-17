from pydantic import BaseModel
from typing import Optional

class PMAnalysisRequest(BaseModel):
    script: Optional[str] = "main.py"
    datasetPath: str
    datasetCsvDelimiter: str = ","