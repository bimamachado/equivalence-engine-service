import app.middleware_runtime_patch
# Reuse the main application instance so container entrypoint exposes same routes
from app.main import app
