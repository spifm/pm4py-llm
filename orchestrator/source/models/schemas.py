from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class PMAnalysisRequest(BaseModel):
    dataset: str
    dataset_csv_delimiter: Optional[str] = ","
    output_path: Optional[str] = ""

class DatasetToStoreRequest(BaseModel):
    filename: str
    data: Dict[str, List]

class SimplifyDFGRequest(BaseModel):
    output_path: str

class CreateMindMapRequest(BaseModel):
    analysis_dir: str

class FullAnalysisRequest(BaseModel):
    dataset: str
    dataset_csv_delimiter: Optional[str] = ","
    output_path: Optional[str] = ""
    disable_mind_map: Optional[bool] = Field(False, alias="disable-mind_map")
