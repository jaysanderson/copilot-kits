"""Embed demo: a mock third-party page that hosts the ask widget. Add-only module; it
holds no credentials and makes no ARAG call. The widget itself calls /api/answer."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/embed", response_class=HTMLResponse)
async def embed_demo(request: Request):
    origin = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(request, "embed.html", {"origin": origin})
