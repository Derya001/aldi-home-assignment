# Code Review

Átnéztem a projektet, de mielőtt továbbmennénk vele van benne 5 dolog, amit mindenképp javítanunk kell. Mielőtt ez akár egy teszt clusterre is kikerülne, nézzük végig őket sorban.

## 1. A Helm chart resource-ai nincsenek összekötve egymással

A `service.yaml`, a `deployment.yaml` és az `ingress.yaml` mindegyike egymástól függetlenül tartalmazza a saját nevét, portját és selectorát, és pont ez okoz három különálló, de egy tőről fakadó problémát:

- A `service.yaml` selectorában `app: myapps` van egy extra "s" betű, miközben a `deployment.yaml`-ben a podok `app: myapp` labelt kaptak. Emiatt a Service **egyetlen podot sem találna** ha most lefuttatnád a `kubectl get endpoints` parancsot, csak egy üres listát kapnál vissza, és minden kérés timeoutolna.
- A Deployment részben `containerPort: 5000` van, szóval az 5000-as porton figyel, a Service viszont `targetPort: 8080`-ra küldené a forgalmat. Még ha a selector jó lenne is, a forgalom akkor is rossz portra menne a podon belül.
- Az `ingress.yaml` egy `homeworks` nevű Service-re mutat, de ilyen nevű Service sehol nincs a chartban, csak `myapp` nevű van. Minden Ingress-en keresztüli kérés 404/502-t adna.

Mindhárom probléma abból fakad, hogy a resource-ok neve és portja nem egyetlen közös helyről van kiolvasva, hanem mindenhol külön, kézzel van beírva. Ez könnyen szétcsúszik, ahogy itt is történt.

**Azt javaslom,** hogy vezess be egy `_helpers.tpl` fájlt, ami egyetlen közös helyről adja át a nevet minden resource-nak, és a portokat is egyetlen `values.yaml` mezőből olvassa mindegyik template, így fizikailag nem tudnak többé szétcsúszni. Figyelj arra, hogy mielőtt commitolsz egy Helm változtatást, mindig futtasd le `helm template .` parancsot, nézd át a renderelt YAML-t, és ellenőrizd kézzel, hogy a selectorok és portok tényleg egyeznek-e. Ez egy 10 másodperces check, ami elkapja ezt a fajta hibát, mielőtt clusterre kerülne.

## 2. A Terraform kód nem fog lefutni

A `main.tf`-ben a `helm_release` resource két `set` blokkja hibás:

```hcl
set {
    name  = "image.tag"
    value =
}
```

Itt az érték egyszerűen hiányzik, ezért ez érvénytelen HCL szintaxis, a `terraform validate` azonnal hibára fut miatta.

```hcl
set {
    name  = "environment"
    value = prod
}
```

Itt a `prod` változó idézőjel nélkül, és `var.` előtag nélkül szerepel, ezért a Terraform megpróbálja ezt egy létező resource vagy változó nevére feloldani, de mivel nincs ilyen nevű dolog a kódban, ez is hibára fog futni.

**Azt javaslom,** hogy cseréld ki mindkettőt a megfelelő változóhivatkozásra (`var.image_tag`, `var.environment`), és mielőtt legközelebb commitolsz, futtasd le helyben a `terraform validate` parancsot. Ez a leggyorsabb, leghatékonyabb módja annak, hogy elkapd az ilyen szintaxishibákat, mielőtt bárki más (vagy egy CI pipeline) találkozna velük.

## 3. A namespace változó deklarálva van, de sosem használod

A `variables.tf` tartalmaz egy `namespace` nevű változót, de a `main.tf`-ben a namespace neve kézzel `"production"`-ra van beállítva:

```hcl
resource "kubernetes_namespace" "homework" {
    metadata {
        name = "production"
    }
}
```

Ez azért veszélyes, mert könnyű elhinni, hogy a változó tényleg számít, de bárhogy is állítanád be a `namespace` változót mondjuk a `terraform apply -var="namespace=dev"` paranccsal, a kód mindig `production`-be telepítene. Egy tesztfuttatás így véletlenül éles namespace-t is érinthetne.

**Azt javaslom,** hogy cseréld le a `"production"` értéket `var.namespace`-re, és általános szabályként érdemes megjegyezni, hogyha deklarálsz egy változót, mindig keress rá a kódban, hogy ténylegesen hivatkozol-e rá valahol. Egy deklarált, de nem használt változó megtévesztő, mert azt sugallja, hogy valami konfigurálható, miközben nem az.

## 4. A CI pipeline jelenleg nem csinál semmit

A `.gitlab-ci.yml` két jobot tartalmaz, mindkettő egyetlen `echo` parancsból áll:

```yaml
build:
  stage: build
  script:
    - echo "Building the application..."
```

Ez lefut, zöld pipeline-t mutat, de a valóságban semmit nem épít és nem telepít semmit. Se teszt futtatást, se image build-et, sem deploy-t nem csinál. Ha valaki csak a pipeline állapotára néz, azt hiheti, hogy minden működik, miközben a build, illetve a deploy logika teljesen hiányzik.

**Azt javaslom,** hogy ne hagyd ezeket sosem placeholder állapotban, mert egy zöld, de semmit nem csináló pipeline veszélyesebb, mintha egyáltalán nincs pipeline, ugyanis hamis biztonságérzetet ad. Kezdd egy minimális, de valóban működő lint/test/build lépéssel, még ha a deploy rész később is készül el.

## 5. Az `outputs.tf` üres

Ez nem hiba abban az értelemben, hogy nem okoz futásidejű problémát, mert a Terraform simán lefut nélküle is, de egy üres `outputs.tf` azt jelenti, hogy a modul semmit nem ad vissza a végén. Nem tudod meg belőle, hogy milyen namespace-be telepített, milyen néven jött létre a Helm release, vagy hogy sikeres volt-e.

Ha ezt a modult egy CI pipeline-ból futtatnád, a pipeline logjából semmilyen automatikusan kinyerhető információt nem kapnál arról, mi történt. Ahhoz, hogy bármilyen infót kideríts, külön `kubectl`/`helm status` parancsot kellene utána futtatnod, hogy ellenőrizd minden rendben zajlott-e.

**Azt javaslom,** hogy adj hozzá pár `output` blokkot, például a namespace neve, a release neve, vagy a release státusza. Egy jól megírt modul nem csak *működik*, hanem *használható* is mások, vagy akár egy automatizált folyamat számára. Mindig gondold végig, aki vagy ami a te Terraform modulodat használja majd, annak milyen infóra lehet szüksége a végén. Mindig úgy kódolj, hogy annak is érthető legyen a kód, vagy akár az output, aki először látja vagy használja.

---

Összességében jók az alapok: a repo szerkezete logikus, az app, a helm, a terraform és a CI fájlok külön mappákban vannak, és egyik hiba sem koncepcionális tervezési probléma, inkább csak apró, könnyen elkövethető pontatlanságok, amiket egy `helm template`, egy `terraform validate`, és egy kicsit alaposabb önellenőrzés simán el tud csípni commit előtt. Ha ezt az 5 pontot végigjavítod, utána nézzük át együtt még egyszer, ha szeretnéd.
