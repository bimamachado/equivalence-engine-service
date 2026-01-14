from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import hashlib
import random

app = FastAPI()

class Req(BaseModel):
    texts: List[str]

@app.post("/embed")
def embed(req: Req):
    # Embedding fake determinístico baseado em hash.
    vectors = []
    for t in req.texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        rnd = random.Random(h)
        vectors.append([rnd.random() for _ in range(256)])
    return {"vectors": vectors}
