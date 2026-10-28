\# TP1 — Exploration de l’API Docker



L’adresse de l’API est définie dans Git Bash :



```bash

D=http://127.0.0.1:2375

```



\## 1. Version de Docker



```bash

curl -s -w '\\nCode HTTP : %{http\_code}\\n' "$D/version"

```



Code obtenu : \*\*200\*\*. La commande affiche la version de Docker et les informations du moteur.



\## 2. Liste complète des conteneurs



```bash

curl -s -w '\\nCode HTTP : %{http\_code}\\n' "$D/containers/json?all=true"

```



Code obtenu : \*\*200\*\*. La commande liste tous les conteneurs, même ceux arrêtés ; j’en obtiens six.



\## 3. Liste filtrée par label



```bash

curl -s --get "$D/containers/json" \\

&#x20; --data-urlencode 'all=true' \\

&#x20; --data-urlencode 'filters={"label":\["adminapi.managed=true"]}' \\

&#x20; -w '\\nCode HTTP : %{http\_code}\\n'

```



Code obtenu : \*\*200\*\*. Le filtre renvoie uniquement `web1`, qui porte le label `adminapi.managed=true`.



\## 4. Détail de web1



```bash

curl -s -w '\\nCode HTTP : %{http\_code}\\n' "$D/containers/web1/json"

```



Code obtenu : \*\*200\*\*. La commande affiche les détails de `web1`, notamment son état `running` et son label.



\## 5. Premier arrêt de web1



```bash

curl -i -X POST "$D/containers/web1/stop"

```



Code obtenu : \*\*204\*\*. Le conteneur est arrêté et la réponse ne contient pas de corps.



\## 6. Deuxième arrêt de web1



```bash

curl -i -X POST "$D/containers/web1/stop"

```



Code obtenu : \*\*304\*\*. Le conteneur étant déjà arrêté, Docker ne modifie rien.



\## 7. Conteneur inexistant



```bash

curl -i "$D/containers/conteneur-inexistant-tp1/json"

```



Code obtenu : \*\*404\*\*. Aucun conteneur ne correspond au nom demandé.



# Exploration de l’API NetBox

L’adresse de l’API est définie dans Git Bash :

```bash
N=http://127.0.0.1:8080/api
```

## 8. Obtenir un token

```bash
curl -sS -X POST "$N/users/tokens/provision/" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  -w '\nCode HTTP : %{http_code}\n'
```

Code obtenu : **201**. Cette commande crée un token pour authentifier les appels suivants.

Le token complet est enregistré uniquement dans `.env`, qui est ignoré par Git.

## 9. Créer le type de cluster Docker

Après avoir chargé les variables de `.env`, je prépare l’en-tête d’authentification :

```bash
A="Authorization: Bearer $NETBOX_TOKEN"
```

Puis je crée le type de cluster :

```bash
curl -sS -X POST "$N/virtualization/cluster-types/" \
  -H "$A" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"name":"Docker","slug":"docker"}' \
  -w '\nCode HTTP : %{http_code}\n'
```

Code obtenu : **201**. Le type de cluster `Docker` a été créé ; son identifiant sert à l’étape suivante.

## 10. Créer le cluster docker-local

```bash
curl -sS -X POST "$N/virtualization/clusters/" \
  -H "$A" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"name":"docker-local","type":1}' \
  -w '\nCode HTTP : %{http_code}\n'
```

Code obtenu : **201**. Le cluster `docker-local` a été créé avec le type `Docker`.

J’ai vérifié sa présence dans l’interface NetBox.

