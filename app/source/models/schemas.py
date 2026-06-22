from pydantic import BaseModel
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    dataset: str
    dataset_csv_delimiter: str = ","
    output_path: Optional[str] = ""

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]

class SimplifyDFGRequest(BaseModel):
    output_path: str

class SummarizeSimplifiedDFGRequest(BaseModel):
    analysis_dir: str

class CreateMindMapRequest(BaseModel):
    analysis_dir: str