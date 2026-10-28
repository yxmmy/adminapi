import os
import sys
import json
from datetime import datetime, timezone

import requests

DOCKER = os.environ["DOCKER_API_URL"]
NETBOX = os.environ["NETBOX_URL"]
JETON = os.environ["NETBOX_TOKEN"]

session = requests.Session()

# Récupération de la liste des conteneurs.
try:
    reponse = session.get(
        DOCKER + "/containers/json",
        params={"all": "true"},
        timeout=5,
    )
    reponse.raise_for_status()
    conteneurs = reponse.json()
except requests.exceptions.RequestException as erreur:
    sys.exit(
        f"Erreur lors de la récupération des conteneurs Docker : {erreur}"
    )

inventaire = []

for conteneur in conteneurs:
    fiche = {
        "name": conteneur["Names"][0].lstrip("/"),
        "image": conteneur["Image"],
        "state": conteneur["State"],
        "cpu_percent": None,
        "memory_mo": None,
    }

    print(fiche["name"], fiche["image"], fiche["state"])

    if conteneur["State"] == "running":
        # Récupération des statistiques du conteneur.
        try:
            reponse_stats = session.get(
                DOCKER + "/containers/" + conteneur["Id"] + "/stats",
                params={"stream": "false"},
                timeout=10,
            )
            reponse_stats.raise_for_status()
            stats = reponse_stats.json()
        except requests.exceptions.RequestException as erreur:
            sys.exit(
                f"Erreur de lecture des statistiques de "
                f"{fiche['name']} : {erreur}"
            )

        memoire_mo = stats["memory_stats"]["usage"] / 1024 / 1024

        cpu = stats["cpu_stats"]
        avant = stats["precpu_stats"]

        delta_cpu = (
            cpu["cpu_usage"]["total_usage"]
            - avant["cpu_usage"]["total_usage"]
        )
        delta_systeme = (
            cpu["system_cpu_usage"]
            - avant.get("system_cpu_usage", 0)
        )

        pourcent_cpu = (
            delta_cpu / delta_systeme * cpu["online_cpus"] * 100
            if delta_systeme > 0
            else 0.0
        )

        fiche["cpu_percent"] = round(pourcent_cpu, 2)
        fiche["memory_mo"] = round(memoire_mo, 2)

        print("Mémoire utilisée :", fiche["memory_mo"], "Mo")
        print("CPU utilisé :", fiche["cpu_percent"], "%")

    inventaire.append(fiche)

# Récupération de la version et des types d’objets NetBox.
try:
    reponse_netbox = session.get(
        NETBOX.rstrip("/") + "/api/status/",
        headers={"Authorization": "Bearer " + JETON},
        timeout=5,
    )
    reponse_netbox.raise_for_status()
    statut_netbox = reponse_netbox.json()

    print("Version NetBox :", statut_netbox["netbox-version"])

    url_suivante = (
        NETBOX.rstrip("/") + "/api/core/object-types/?limit=50"
    )
    nombre_types = 0
    total_annonce = None

    while url_suivante:
        reponse_types = session.get(
            url_suivante,
            headers={"Authorization": "Bearer " + JETON},
            timeout=5,
        )
        reponse_types.raise_for_status()
        page = reponse_types.json()

        if total_annonce is None:
            total_annonce = page["count"]

        nombre_types += len(page["results"])
        url_suivante = page["next"]

except requests.exceptions.RequestException as erreur:
    sys.exit(
        f"Erreur lors de la récupération des informations NetBox : {erreur}"
    )

print("Total annoncé :", total_annonce)
print("Types d’objets comptés :", nombre_types)

# Enregistrement du relevé.
releve = {
    "date": datetime.now(timezone.utc).isoformat(),
    "containers": inventaire,
    "netbox": {
        "version": statut_netbox["netbox-version"],
        "object_types_count": nombre_types,
    },
}

with open("inventaire.json", "w", encoding="utf-8") as fichier:
    json.dump(releve, fichier, ensure_ascii=False, indent=2)

print("Inventaire enregistré :", len(inventaire), "conteneurs.")