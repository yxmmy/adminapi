import os
import json

import requests
from fastapi import FastAPI, HTTPException

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


@app.get(
    "/containers/{id}",
    summary="Consulter un conteneur géré",
    responses={
        404: {"description": "Conteneur inconnu ou non géré"},
    },
)
def obtenir_conteneur(id: str):
    reponse = requests.get(
        DOCKER + "/containers/" + id + "/json",
        timeout=5,
    )

    if reponse.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Conteneur introuvable",
        )

    reponse.raise_for_status()
    conteneur = reponse.json()

    labels = conteneur["Config"]["Labels"] or {}

    if labels.get("adminapi.managed") != "true":
        raise HTTPException(
            status_code=404,
            detail="Conteneur introuvable",
        )

    return {
        "id": conteneur["Id"],
        "name": conteneur["Name"].lstrip("/"),
        "image": conteneur["Config"]["Image"],
        "state": conteneur["State"]["Status"],
    }