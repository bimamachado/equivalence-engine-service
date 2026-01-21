import uuid
from fastapi import APIRouter, Depends, Request, Form
from app.deps import require_role
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app import models

router = APIRouter(dependencies=[Depends(require_role("admin", "auditor"))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), decision: str | None = None):
    q = db.query(models.EquivalenceResult).order_by(models.EquivalenceResult.created_at.desc())
    if decision:
        q = q.filter(models.EquivalenceResult.decision == decision)
    rows = q.limit(200).all()
    return templates.TemplateResponse("list.html", {"request": request, "rows": rows})

@router.get("/dashboard/result/{rid}", response_class=HTMLResponse)
def result_detail(rid: str, request: Request, db: Session = Depends(get_db)):
    r = db.get(models.EquivalenceResult, rid)
    label = db.query(models.Label).filter(models.Label.result_id == rid).order_by(models.Label.created_at.desc()).first()
    return templates.TemplateResponse("detail.html", {"request": request, "r": r, "label": label})

@router.post("/dashboard/result/{rid}/label")
def set_label(rid: str, labeled_by: str = Form(...), label: str = Form(...), notes: str = Form(default=""), db: Session = Depends(get_db)):
    lid = str(uuid.uuid4())
    db.add(models.Label(id=lid, result_id=rid, labeled_by=labeled_by, label=label, notes=notes))
    db.commit()
    return RedirectResponse(url=f"/dashboard/result/{rid}", status_code=303)
