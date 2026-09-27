from fastapi import FastAPI
from app.api.routes.process import router as process_router

app = FastAPI(
    title="LOGVANTA",
    description="Adaptive security log preprocessing and normalization framework",
    version="0.1.0",
)

app.include_router(process_router)


@app.get("/")
def root():
    return {"project": "LOGVANTA", "status": "running", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
