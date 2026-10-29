import os
import json

import requests
from fastapi import FastAPI

DOCKER = os.environ["DOCKER_API_URL"]

app = FastAPI()


@app.get("/health", summary="Vérifier que l’API fonctionne")
def health():
    return {"status": "ok"}


@app.get("/containers", summary="Lister les conteneurs gérés")
def lister_conteneurs():
    parametres = {
        "all": "true",
        "filters": json.dumps({
            "label": ["adminapi.managed=true"]
        }),
    }

    reponse = requests.get(
        DOCKER + "/containers/json",
        params=parametres,
        timeout=5,
    )
    reponse.raise_for_status()
    conteneurs = reponse.json()

    resultat = []

    for conteneur in conteneurs:
        fiche = {
            "id": conteneur["Id"],
            "name": conteneur["Names"][0].lstrip("/"),
            "image": conteneur["Image"],
            "state": conteneur["State"],
        }
        resultat.append(fiche)

    return resultat