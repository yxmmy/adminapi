from fastapi import FastAPI

app = FastAPI()


@app.get("/health", summary="Vérifier que l’API fonctionne")
def health():
    return {"status": "ok"}