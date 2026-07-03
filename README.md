# DevOps Engineer Homework

## Overview

The goal of this assignment is to evaluate how you approach a typical DevOps engineering task involving:

- Application development / scripting
- Containerization
- Kubernetes
- Helm
- Terraform
- CI/CD
- Code review

The repository contains intentionally incomplete and imperfect components.
Your task is to complete, improve and document the solution.

You are not expected to produce a perfect production-ready system. We are more interested in your engineering approach, decision-making and ability to balance quality with the time constraints.

Time limit: approximately **3 hours**

## Repository Contents

The repository contains:

- An incomplete application skeleton
- Terraform configuration requiring review and improvement
- An incomplete Helm chart
- An incomplete CI/CD pipeline

Your task is to complete and improve these components. Our goal is to understand your engineering approach, and we will build the upcoming technical interview on this project.

## Goal 1

Complete and improve the provided project.

The repository contains the following files:

- Incomplete application code
- Broken/incomplete terraform configuration
- Incomplete Helm Chart
- Incomplete Gitlab CI pipeline

### Requirements

#### Application

Implement a simple application in either:

- Go
- Python

The application must expose the following endpoints:

##### `GET /health`

**Response:**

```json
{
    "status": "ok"
}
```

##### `GET /version`

**Response:**

```json
{
    "version": "1.0.0"
}
```

##### `GET /env`

**Response:**

```json
{
    "environment": "<value from ENVIRONMENT variable>"
}
```

##### `POST /config`

**Request:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

**Response:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

##### `GET /config/{name}`

**Example:**

```bash
GET /config/database_url
```

**Response:**

```json
{
    "name": "database_url",
    "value": "postgres://example"
}
```

##### `DELETE /config/{name}`

**Response:**

```json
{
    "deleted": true
}
```

#### Containerization

- Create the necessary Dockerfile with minimal setup
- The image should:
  - build successfully
  - run locally
  - expose the application endpoint

#### Terraform

- Review and fix/complete the Terraform code
- The Terraform code contains several issues and areas for improvement
- In case you don't get time to implement changes describe what would you still improve and why
- Document any changes you make

#### Helm

- Review and fix/complete the Helm Chart
- The chart should deploy the application to Kubernetes
- Document any change you make

#### Gitlab CI

- Complete the pipeline so it becomes capable of building and deploying the application
- The pipeline should support the workflow required to build and deploy the application
- The pipeline should be logically complete and demonstrate how you would automate the process
- Add any other necessary jobs to the pipeline

#### Documentation

Update the project README with following information.

##### What You Changed

Describe the changes and the rationale behind it.

##### Assumptions

Describe the assumptions made while completing the assignment.

##### Known Limitations

Describe anything you intentionally omitted.

##### Production Improvements

Describe how you would evolve this solution for production use.

### Deliverables

- Source Code of the Go/Python application
- Dockerfile
- Terraform changes
- Helm changes
- CI pipeline changes
- README describing decisions, assumptions and user guide for the project.

### Notes

You are not expected to deploy to a cloud provider.
The solution should work with a local Kubernetes cluster such as:

- Kind
- Minikube
- K3d

### Timing

Timebox yourself to approximately **3 hours**. If you can't finish the work within the timebox, describe in the README.md what is left and how you would approach it.

## Goal 2

You get this half-baked project from one of your colleagues who is a Junior and asking for your guidance.

Provide a short code review in `REVIEW.md` where you address the **top 5 most important things** to fix so the colleague can move forward.

### Review Timing

Spend no more than **30 minutes** on review and feedback.

### Evaluation Criteria

We will evaluate:

- Code quality
- Terraform quality
- Kubernetes and Helm knowledge
- CI/CD design and implementation
- Documentation quality
- Code review quality
- Maintainability and operational thinking

### Use of AI

The use of AI-assisted tools is permitted. However, we encourage you to complete the assignment primarily based on your own knowledge, experience and reasoning. During the interview, we will discuss your implementation choices, trade-offs and decision-making process, so it is important that you fully understand and can explain every part of your solution.

------------------------------------------------------

# DevOps Engineer Homework

## Áttekintés

Ez a repo egy kisméretű, konfigurációkezelő HTTP szolgáltatást valósít meg, a hozzá tartozó Docker / Helm / Terraform / GitLab CI eszközlánccal együtt, hogy lokális Kubernetes clusterre (kind / minikube / k3d) legyen telepíthető. A kapott projekt egy szándékosan hiányos és hibás vázat tartalmazott (üres app mappa, hibás Helm chart, nem futtatható Terraform, placeholder CI pipeline), a feladat ennek befejezése és javítása volt.

## What You Changed

### Alkalmazás

Implementáltam mind a 6 kötelező endpointot egy Python-on és Flask-en alapuló alkalmazással:
- `GET /health`, `GET /version`, `GET /env` --> egyszerű, függőség nélküli lekérdezések
- `POST /config`, `GET /config/{name}`, `DELETE /config/{name}` --> egy in-memory dict-alapú config store CRUD műveletei

A config store-t `threading.Lock`-kal védtem, mert a gunicorn több workerrel/szállal fut, és konkurens írás/olvasás esetén egy sima dict elméletileg inkonzisztens állapotba kerülhetne.

Írtam 11 pytest tesztet, ami lefedi mind a 6 endpointot, plusz két hibaágat: hiányzó mező a POST body-ban (400), és nem létező kulcs GET/DELETE esetén (404).

**Tervezési döntés:** a `DELETE /config/{name}` 404-et ad vissza, ha a kulcs nem létezik, ahelyett hogy mindig `{"deleted": true}`-t adna. A HTTP DELETE idempotens *hatás* tekintetében, azaz a végállapot ugyanaz, akárhányszor küldöm el, de ez nem jelenti, hogy a *válasznak* is mindig azonosnak kell lennie. Egy erőforrás-alapú API-ban hasznos infó a hívónak, ha egy nem létező erőforrást próbált törölni.

### Dockerfile

`python:3.12-slim` a base image, a függőségek külön layerben telepítve az app kód előtt (build cache), nem-root felhasználó (`appuser`) alatt fut, `HEALTHCHECK` a `/health` endpointra, és `gunicorn`-nal indul. Azért nem a Flask fejlesztői szerverével, mert az nem production-safe.

A portot 8080-ra állítottam az eredeti 5000 helyett, mivel ez konténeres alkalmazásoknál gyakori konvenció, és elkerüli az 5000-es port esetleges ütközését más helyi szolgáltatásokkal (pl: macOS-en az AirPlay Receiver ezt a portot használja). A lényeg, hogy ez az érték a projekt minden rétegében, pl: Dockerfile, Helm chart, konzisztens maradjon.

### Helm chart

A kapott chart 3 konkrét, egymástól független hibát tartalmazott, amik miatt éles telepítés esetén a forgalom soha nem jutott volna el az alkalmazásig:

1. **`service.yaml` selector hiba:** a Service `app: myapps` selectorral kereste a podokat, miközben a Deployment a podokat `app: myapp` labellel látta el. A Service selector tartalmazott egy plusz s betűt, ami nem volt azonos a Deployment labellel. Emiatt a Service egyetlen podot sem talált volna, a `kubectl get endpoints` üres listát adott volna, minden kérés timeoutolt volna.
2. **Port-mismatch:** a Deployment `containerPort: 5000`-et definiált, miközben a Service `targetPort: 8080`-ra küldte volna a forgalmat. Mindkét érték most a `values.yaml` egyetlen, közös `service.targetPort` mezőjéből származik, hogy fizikailag ne tudjanak többé szétcsúszni.
3. **Törött Ingress backend:** az `ingress.yaml` egy `homeworks` nevű Service-re mutatott, ami nem létezett a chartban. Javítottam a tényleges `myapp` Service névre, és az Ingress-t feltételessé tettem, attól függően, hogy mi van a values.yaml fájlban, alapértelmezetten kikapcsolva (enabled: false), mert a feladat nem várt el konkrét ingress controllert, így nem generál felesleges, working nélküli resource-ot.

Ezen felül hozzáadtam:
- `templates/_helpers.tpl` szabványos naming/label helper függvényekkel, hogy a Service, Deployment és Ingress egy közös helyről nyerje a nevét, ne kézzel, három helyen kelljen szinkronban tartani.
- `livenessProbe` és `readinessProbe`, mindkettő a `/health` endpointra, enélkül egy beragadt vagy hibás pod továbbra is "Running" maradt volna és forgalmat kapott volna.
- `resources.requests`/`limits` a konténerhez, hogy egy hibás vagy memory-leakes pod ne tudja felzabálni az egész node erőforrását.

A javításokat egy lokális `kind` clusteren ténylegesen le is teszteltem, a pod `Running`/`Ready` állapotba került, és a `/health`, `/version`, `POST /config` végpontok is helyesen válaszoltak `kubectl port-forward`-on keresztül.

### Terraform

- `main.tf`: a namespace hardcode-olva volt `"production"`-re annak ellenére, hogy a `variables.tf` deklarált egy `namespace` változót, ezt javítottam, most `var.namespace`-t használ. A `helm_release` resource egyik `set` blokkjának `image.tag` értéke teljesen hiányzott, a másik idézőjel és `var.` nélküli, nem létező hivatkozásra mutatott: `value = prod`, mindkettőt valid Terraform hivatkozásra javítottam: `var.image_tag` és `var.environment` lett a helyes definíció. A chart elérési útja, a `../helm/homework` egy nem létező mappára mutatott, ezt a megfelelő path-ra, azaz `../helm`-re javítottam.
- `providers.tf`: hozzáadtam egy `required_providers` blokkot, ami rögzíti a `kubernetes` és `helm` providerek verzióját: `~> 2.30`, illetve `~> 2.14`. Enélkül minden `terraform init` a legfrissebb elérhető provider-verziót töltené le, ami két gépen, két különböző időpontban eltérő, akár inkompatibilis viselkedést eredményezhetne ugyanabból a kódból, és ez pont az ellenkezője annak, amit Infrastructure as Code-tól elvárunk.
- `outputs.tf`: üres volt, kitöltöttem a létrehozott namespace nevével, a Helm release nevével és állapotával, hogy egy CI pipeline-ból is látható legyen, mi történt egy `terraform apply` után.
- `variables.tf`: leírásokat és sensible default értékeket adtam a változóknak, hogy a modul a `.tfvars` fájl nélkül is futtatható legyen lokális teszteléskor.

A `terraform validate` sikeresen lefutott a javítások után.

### GitLab CI

A két `echo` placeholder job helyett egy 4 szakaszos pipeline-t hoztam létre: `lint → test → build → deploy`.

- **lint + test**: minden push-nál és merge requesten lefut, branch-független, hogy minél korábban, minél előbb elkapjuk a hibás kódot, a "fail fast" elv szerint, mielőtt az komolyabb fázisokba, image build vagy deploy szakaszba kerülne.
- **build**: csak a default branch-en fut, mert csak onnan deployolunk, ezért nincs értelme minden feature branch-hez image-et építeni és a registry-be push-olni.
- **deploy**: default branch-en fut, de manuális jóváhagyással. Ez nem mond ellent az automatizációnak, a *folyamat* maga, vagyis a tényleges telepítési lépések 100%-ban automatizáltak, csak a *triggerelés pillanata* marad emberi döntés, ami gyakori és indokolt gyakorlat production deploy-oknál.
- A deploy job egy `KUBE_CONFIG` nevű, base64-kódolt CI/CD variable-ből állítja elő a kubeconfig-ot futásidőben, így a hitelesítő adat soha nem kerül be a kódba vagy a git historyba.

## Assumptions

- Az in-memory config store elfogadható ehhez a feladathoz; nem volt elvárás perzisztens tárolásra.
- Nincs konkrét cloud deployment target, a megoldás lokális Kubernetes clusterhez, pl: kind/minikube/k3d applikációkhoz készült.
- A Docker registry a GitLab beépített Container Registry-je (`$CI_REGISTRY_IMAGE`), mivel nem volt megadva külső registry.
- A deploy CI job feltételez egy `KUBE_CONFIG` nevű, base64-kódolt CI/CD variable-t, amit a projekt Settings → CI/CD → Variables alatt kellene beállítani egy valós cluster-en történő futtatáshoz.
- Python/Flask választása Go helyett: a feladat mindkettőt megengedte, de mivel a Python-ban otthonosabban mozgok, így Pythonnal gyorsabban tudtam egy tesztelt, production-közeli megoldást leszállítani a rendelkezésre álló időkeretben.

## Known Limitations

- **A config store in-memory és nem megosztott.** Ezt ténylegesen reprodukáltam is egy lokális `kind` clusteren: egy `POST /config` után egy rá következő `GET /config/{name}` 404-et adott, mert a kérés egy másik gunicorn workerhez került, aminek saját, elkülönített memóriája van, és a gunicorn minden workert külön Python process-ként indít. Ehhez éles használatban egy külső, megosztott store (pl. Redis, Postgres) kellene.
- Nincs authentikáció vagy authorizáció egyik endpointon sem, beleértve a `/config` írási útvonalat.
- Nincs TLS konfigurálva az Ingress-en.
- Nincs image vulnerability scanning vagy SBOM generálás a pipeline-ban.
- Nincs Terraform remote state illetve locking beállítva, jelenleg a `terraform.tfstate` lokális marad, ami csapatmunkára nem alkalmas.
- A CI deploy job egyetlen, manuális, single-environment job, így nincs külön staging/production promóciós folyamat, mivel ez egy demo projekt, de egy éles rendszernél ez az elvárt, alapértelmezett megoldás.

## Production Improvements

Ha ez éles rendszerré válna, nagyjából ebben a sorrendben fejleszteném tovább:

1. **Külső config store**-t (pl: Redis/Postgres) használnék az in-memory dict helyett, hogy a horizontális skálázás és az újraindítások ne veszítsenek adatot.
2. **Terraform remote state**-t, locking-ot (pl. S3/GCS backend), és külön workspace-eket vagy `.tfvars` fájlokat alakítanék ki környezetenként.
3. **GitOps-alapú deploy**-t használnék (pl: ArgoCD/Flux) a CI-ból futtatott `helm upgrade` helyett, hogy a cluster állapota folyamatosan reconciled legyen, és a drift látható legyen.
4. **Secrets management**-et alakítanék ki, mert a `KUBE_CONFIG` CI variable rendben van egy házi feladathoz, de éles környezetben rövid életű hitelesítést (OIDC federáció) vagy dedikált secrets managert használnék.
5. **Observability**-t vezetnék be, hogy strukturált logolás, Prometheus metrikák, dashboardok és alertek legyenek, mivel jelenleg csak egy health check van.
6. **Image scanning**-et futtatnék (Trivy/Grype) mint pipeline gate a push előtt.
7. **HPA**-t, azaz Horizontal Pod Autoscaler-t használnék a replikák számának meghatározásához a CPU/memória vagy egyedi metrikák alapján, mivel a `replicaCount` jelenleg statikus.
8. **NetworkPolicy-k**-at és egy `PodDisruptionBudget`-et állítanék fel alapszintű izolációhoz és rezilienciához.
9. **Dev/staging/prod branch-alapú környezet-promóció**, mivel nagyobb szervezeteknél a kód fokozatosan halad végig környezeteken, jóváhagyással vagy automatikus teszteléssel lépésenként. Ennél a projektnél túlméretezett lett volna, de éles rendszernél ez lenne a következő lépés.
10. **TLS mindenhol**, például cert-manager az Ingress-hez, esetleg mTLS, ha a rendszer több szolgáltatásra bővül.

## Quickstart

```bash
# Build
cd app
docker build -t myapp:latest .

# Helm deploy lokális kind clusterre
kind create cluster --name myapp
kind load docker-image myapp:latest --name myapp
cd ../helm
helm upgrade --install myapp . \
  --namespace myapp --create-namespace \
  --set image.repository=myapp \
  --set image.tag=latest

# Ellenőrzés
kubectl -n myapp get pods
kubectl -n myapp port-forward svc/myapp 8080:80
curl localhost:8080/health
```

Terraform-mal (ugyanezt a chartot telepíti):

```bash
cd terraform
terraform init
terraform apply -var="image_tag=latest"
```
