import os
import requests

DOCKER = os.environ["DOCKER_API_URL"]
session = requests.Session()
reponse = session.get(DOCKER + "/containers/json", params={"all": "true"}, timeout=5)

reponse.raise_for_status()
conteneurs = reponse.json()

for conteneur in conteneurs:
    print(conteneur["Names"][0], conteneur["Image"], conteneur["State"])
    if conteneur["State"] == "running":
        reponse_stats = session.get(
            DOCKER + "/containers/" + conteneur["Id"] + "/stats",
            params={"stream": "false"},
            timeout=10,
        )
        reponse_stats.raise_for_status()
        stats = reponse_stats.json()
        memoire_mo = stats["memory_stats"]["usage"] / 1024 / 1024
        print("Mémoire utilisée :", round(memoire_mo, 2), "Mo")
        cpu = stats["cpu_stats"]
        avant = stats["precpu_stats"]

        delta_cpu = cpu["cpu_usage"]["total_usage"] - avant["cpu_usage"]["total_usage"]
        delta_systeme = cpu["system_cpu_usage"] - avant.get("system_cpu_usage", 0)

        pourcent_cpu = (
            delta_cpu / delta_systeme * cpu["online_cpus"] * 100
            if delta_systeme > 0
            else 0.0
        )

        print("CPU utilisé :", round(pourcent_cpu, 2), "%")