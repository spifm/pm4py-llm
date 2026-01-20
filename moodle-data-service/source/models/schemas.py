from pydantic import BaseModel
from typing import Optional

class ExportEventLogRequest(BaseModel):
    course_id: int
    dataset_name: Optional[str] = None

class CourseInfo(BaseModel):
    id: int
    fullname: str
    shortname: str

class ExportEventLogResponse(BaseModel):
    message: str
    output_file: str
    rows_exported: int
    course: CourseInfo