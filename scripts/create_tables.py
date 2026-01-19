from app.db import engine, Base
print('creating tables...')
Base.metadata.create_all(bind=engine)
print('done')
