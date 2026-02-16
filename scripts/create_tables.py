from app.db import engine, Base
# Import all models so they are registered with Base
from app import models  # noqa: F401
from app.audit import models as audit_models  # noqa: F401

print('creating tables...')
Base.metadata.create_all(bind=engine)
print('done')
