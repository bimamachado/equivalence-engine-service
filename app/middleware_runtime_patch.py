import logging
try:
    import app.middlewares as mid
except Exception as e:
    logging.getLogger('middleware_debug').info(f'Could not import app.middlewares to patch: {e}')
else:
    if hasattr(mid, 
