from app.config import settings
from app.db import engine
print('SETTINGS_DB=', settings.DATABASE_URL)
print('ENGINE_URL=', engine.url)
