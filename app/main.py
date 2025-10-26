from fastapi import FastAPI
from .engine import Engine
from .storage import Storage
from .config import load_config

app = FastAPI(title="AI Trading Lab v2")
cfg = load_config()
storage = Storage("data/results.sqlite")
engine = Engine(cfg, storage)

@app.on_event("startup")
async def on_startup():
    await engine.start()

@app.on_event("shutdown")
async def on_shutdown():
    await engine.stop()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/status")
def status():
    return engine.status_snapshot()
