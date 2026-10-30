import os
import json
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException, Response
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


@app.post(
    "/containers/{id}/stop",
    summary="Arrêter un conteneur géré",
    responses={
        404: {"description": "Conteneur inconnu ou non géré"},
        409: {"description": "Conteneur déjà arrêté"},
    },
)
def arreter_conteneur(id: str):
    conteneur = obtenir_conteneur(id)
    id_conteneur = conteneur["id"]

    arret = requests.post(
        DOCKER + "/containers/" + id_conteneur + "/stop",
        params={"t": 5},
        timeout=15,
    )

    if arret.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Conteneur introuvable",
        )

    if arret.status_code == 304:
        raise HTTPException(
            status_code=409,
            detail="Le conteneur est déjà arrêté",
        )

    arret.raise_for_status()

    return obtenir_conteneur(id_conteneur)


@app.post(
    "/containers/{id}/start",
    summary="Démarrer un conteneur géré",
    responses={
        404: {"description": "Conteneur inconnu ou non géré"},
        409: {"description": "Conteneur déjà démarré"},
    },
)
def demarrer_conteneur(id: str):
    conteneur = obtenir_conteneur(id)
    id_conteneur = conteneur["id"]

    demarrage = requests.post(
        DOCKER + "/containers/" + id_conteneur + "/start",
        timeout=10,
    )

    if demarrage.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Conteneur introuvable",
        )

    if demarrage.status_code == 304:
        raise HTTPException(
            status_code=409,
            detail="Le conteneur est déjà démarré",
        )

    demarrage.raise_for_status()

    return obtenir_conteneur(id_conteneur)


@app.delete(
    "/containers/{id}",
    status_code=204,
    response_class=Response,
    summary="Supprimer un conteneur géré",
    responses={
        404: {"description": "Conteneur inconnu ou non géré"},
    },
)
def supprimer_conteneur(id: str):
    # Vérifier le label avant toute suppression.
    conteneur = obtenir_conteneur(id)
    id_conteneur = conteneur["id"]

    suppression = requests.delete(
        DOCKER + "/containers/" + id_conteneur,
        params={"force": "true"},
        timeout=15,
    )

    if suppression.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Conteneur introuvable",
        )

    suppression.raise_for_status()

    return Response(status_code=204)