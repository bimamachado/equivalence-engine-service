import logging

try:
    import app.middlewares as mid
except Exception as e:
    logging.getLogger('middleware_debug').info(
        f'Could not import app.middlewares to patch: {e}'
    )
else:
    # No runtime patch required for now. Log successful import.
    logging.getLogger('middleware_debug').info(
        'middleware_runtime_patch loaded; no runtime patches applied'
    )
