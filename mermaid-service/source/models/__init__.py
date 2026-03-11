from pydantic import BaseModel


class ExportEventLogRequest(BaseModel):
    course_id: int


class ExportEventLogResponse(BaseModel):
    message: str
    course_id: int
    output_file: str
    rows_exported: int
