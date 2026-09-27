from fastapi import FastAPI

app = FastAPI(
    title="LOGVANTA",
    description="Adaptive Security Log Preprocessing Framework",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "project": "LOGVANTA",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }