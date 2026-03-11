from pydantic import BaseModel

class RenderRequest(BaseModel):
    diagram: str
    format: str = "svg"  # svg | png