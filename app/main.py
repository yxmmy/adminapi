import os
import json
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DOCKER = os.environ["DOCKER_API_URL"]

app = FastAPI()


class CreationConteneur(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,30}$")
    image: Literal["nginx:alpine", "redis:alpine", "httpd:alpine"]


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


@app.post(
    "/containers",
    status_code=201,
    summary="Créer et démarrer un conteneur géré",
    responses={
        409: {"description": "Nom de conteneur déjà utilisé"},
        422: {"description": "Données de création invalides"},
    },
)
def creer_conteneur(donnees: CreationConteneur):
    creation = requests.post(
        DOCKER + "/containers/create",
        params={"name": donnees.name},
        json={
            "Image": donnees.image,
            "Labels": {
                "adminapi.managed": "true",
            },
        },
        timeout=10,
    )

    if creation.status_code == 409:
        raise HTTPException(
            status_code=409,
            detail="Ce nom de conteneur est déjà utilisé",
        )

    creation.raise_for_status()
    id_conteneur = creation.json()["Id"]

    demarrage = requests.post(
        DOCKER + "/containers/" + id_conteneur + "/start",
        timeout=10,
    )
    demarrage.raise_for_status()

    return obtenir_conteneur(id_conteneur)