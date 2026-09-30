from fastapi import FastAPI

app = FastAPI(title="DeployWatch")


@app.get("/health")
def health():
    return {"status": "ok"}