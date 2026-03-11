from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from dotenv import load_dotenv
import logging
import os
import sys
from models.schemas import RenderRequest
from exceptions.exceptions import MermaidRenderError
from services.mermaid_render_service import MermaidRenderService


# ─── Config .env and logging ─────────────────────────────────

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set in environment variables")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


# ─── Security ────────────────────────────────────────────────


security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not token or token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token" + API_TOKEN,
        )


# ─── Endpoints ──────────────────────────────────────────────

app = FastAPI()


@app.post(
        "/render",
        summary="Render a Mermaid diagram",
        description="Accepts a Mermaid diagram definition and returns the rendered image in the specified format.",
        response_description="The rendered diagram as an image file.",
        dependencies=[Depends(verify_token)]
)
def render_mermaid(request: RenderRequest):

    logger.info("Received render request with format: %s", request.format)

    image_format = request.format.lower()
    if image_format not in {"svg", "png"}:
        raise HTTPException(status_code=400, detail="format must be 'svg' or 'png'")
    
    logger.debug("Rendering Mermaid diagram:\n%s", request.diagram)

    try:
        service = MermaidRenderService()
        data, media_type = service.render(request.diagram, request.format)
        return Response(content=data, media_type=media_type)
    except MermaidRenderError as e:
        raise HTTPException(status_code=500, detail=str(e))