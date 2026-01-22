from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/test-ui", response_class=HTMLResponse)
def test_ui(request: Request):
    """Simple HTML test UI that posts to the evaluate API and shows the response."""
    return templates.TemplateResponse("test_ui.html", {"request": request})


@router.get("/doc")
def doc_shortcut():
    """Redirect `/doc` to FastAPI's Swagger UI at `/docs`."""
    return RedirectResponse(url="/docs")


@router.get("/index.html")
def index_redirect():
    """Redirect legacy /index.html requests to the test UI."""
    return RedirectResponse(url="/test-ui")


@router.get("/favicon.ico")
def favicon_redirect():
    """Redirect favicon requests to the test UI (or serve a static favicon if available)."""
    return RedirectResponse(url="/test-ui")
