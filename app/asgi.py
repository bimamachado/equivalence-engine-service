from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="Equivalence Engine Service")
app.include_router(routes.router)
