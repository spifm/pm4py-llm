from pydantic import BaseModel
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    datasetPath: str
    datasetCsvDelimiter: Optional[str] = ","
    outputPath: Optional[str] = ""

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]

class SimplifyDFGRequest(BaseModel):
    outputPath: str
    prompt_context: Optional[List[str]] = None

class FullAnalysisRequest(BaseModel):
    datasetPath: str
    datasetCsvDelimiter: Optional[str] = ","
    outputPath: Optional[str] = ""
    prompt_context: Optional[List[str]] = None