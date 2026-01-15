from app.db import engine, Base
from app import models  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)
