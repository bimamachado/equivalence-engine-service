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
