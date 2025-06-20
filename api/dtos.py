from pydantic import BaseModel
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    datasetPath: str
    datasetCsvDelimiter: Optional[str] = ","

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]
