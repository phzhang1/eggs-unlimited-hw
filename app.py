from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Eggs Unlimited")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Keep at the end of the file to avoid catching API requests before routes are registered.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
