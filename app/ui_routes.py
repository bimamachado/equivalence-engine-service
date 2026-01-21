from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/test-ui", response_class=HTMLResponse)
def test_ui(request: Request):
    """Simple HTML test UI that posts to the evaluate API and shows the response."""
    return templates.TemplateResponse("test_ui.html", {"request": request})
