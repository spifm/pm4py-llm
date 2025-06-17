from pydantic import BaseModel
from typing import Optional

class PMAnalysisRequest(BaseModel):
    datasetPath: str
    datasetCsvDelimiter: Optional[str] = ","
