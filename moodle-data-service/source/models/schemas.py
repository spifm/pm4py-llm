from pydantic import BaseModel
from typing import Optional

class ExportEventLogRequest(BaseModel):
    course_id: int
    dbname: Optional[str] = None
    dataset_name: Optional[str] = None

class CourseInfo(BaseModel):
    id: int
    fullname: str
    shortname: str

class DBInfo(BaseModel):
    name: str
    av: str
    year: str

class ExportEventLogResponse(BaseModel):
    message: str
    output_file: str
    rows_exported: int
    course_info: CourseInfo

class AsyncExportEventLogResponse(BaseModel):
    message: str
    job_id: str
    expected_output_file: str
    course_info: CourseInfo