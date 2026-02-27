# GitHub Secrets & Variables – Besiktningsapp

Denna fil dokumenterar alla GitHub Secrets och Variables som behöver konfigureras
i repo-inställningarna. Filen är **inte** gitignorerad – den innehåller inga verkliga värden.

Verkliga värden finns lokalt i `.env` (gitignorerad).

---

## Var konfigurerar man dem?

Settings → Secrets and variables → Actions

- **Secrets**: krypterade, syns aldrig i loggar
- **Variables**: okrypterade, publika i workflow-loggar – använd bara för icke-känsliga värden

---

## Repository Secrets (gäller alla environments)

| Secret | Värde | Används av |
|--------|-------|-----------|
| _(inga repo-level secrets just nu)_ | | |

> **OBS:** `GITHUB_TOKEN` behövs **inte** läggas till – det genereras automatiskt av GitHub Actions och ger behörighet att pusha till ghcr.io.

---

## Environment: `local`

Settings → Environments → local → Secrets

| Secret | Exempelvärde | Beskrivning |
|--------|-------------|-------------|
| `KUBECONFIG_LOCAL` | *(se nedan)* | Base64-kodad kubeconfig för din minikube |

### KUBECONFIG_LOCAL – behöver du den nu?

**Nej, inte ännu.** CD-jobbet `deploy-local` körs bara om:
```
vars.ENABLE_K8S_DEPLOY == 'true'
```
Har du satt `ENABLE_K8S_DEPLOY=false` (eller inte satt den alls) hoppar GitHub Actions
över det steget automatiskt. Builden och pushen till ghcr.io sker ändå.

#### När du vill aktivera lokal deploy (valfritt)
Lokal minikube nås inte från GitHubs servrar. Du har två alternativ:

**Alt A – Self-hosted runner (rekommenderat):**
1. Installera GitHub Actions runner på din lokala dator
   ```bash
   # Settings → Actions → Runners → New self-hosted runner
   ```
2. Ändra `runs-on: ubuntu-latest` till `runs-on: self-hosted` i `deploy-local`-jobbet
3. Kör `minikube start` på din dator
4. Exportera kubeconfig:
   ```bash
   kubectl config view --minify --flatten | base64 -w0
   # Klistra in output som värde för KUBECONFIG_LOCAL secret
   ```
5. Sätt `ENABLE_K8S_DEPLOY=true` under Variables → local

**Alt B – Hoppa över lokal deploy:**
Låt `ENABLE_K8S_DEPLOY` vara `false`. Builden sköts av GitHub, du deployer manuellt:
```bash
make k8s-local-up
```

---

## Environment: `local` – Variables

Settings → Environments → local → Variables

| Variable | Värde | Beskrivning |
|----------|-------|-------------|
| `ENABLE_K8S_DEPLOY` | `false` | Styr om deploy-local-jobbet körs |

---

## Environment: `production`

Settings → Environments → production → Secrets

| Secret | Varifrån | Beskrivning |
|--------|----------|-------------|
| `KUBECONFIG_PROD` | Din produktions-K8s | Base64-kodad kubeconfig för prod-clustret |

> Produktionsmiljön kräver manuellt godkännande i GitHub (Environment protection rules).
> CD-jobbet triggas bara av `workflow_dispatch` med `environment=production` eller en `v*`-tag.

---

## Secrets som används av CI-testerna (integration-tests)

CI-jobbet `integration-tests` startar en riktig PostgreSQL-container och behöver dessa:

Settings → Secrets and variables → Actions → Repository secrets

| Secret | Värde (från .env) | Beskrivning |
|--------|------------------|-------------|
| `POSTGRES_PASSWORD` | `besiktning_dev_pass` | PostgreSQL-lösenord i CI |
| `SECRET_KEY` | `dev-secret-key-byt-ut-i-produktion-min32tecken` | Flask SECRET_KEY |
| `JWT_SECRET_KEY` | `dev-jwt-secret-byt-ut-i-produktion-min32tecken` | JWT-signering |

> **OBS för produktion:** Generera riktiga slumpmässiga värden:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Snabbguide – vad behöver sättas upp nu?

För att CI (lint + tester) och CD (build + push) ska fungera direkt:

```
Repository secrets:
  ✅ GITHUB_TOKEN     → automatiskt, inget att göra
  ☐  POSTGRES_PASSWORD → besiktning_dev_pass
  ☐  SECRET_KEY        → dev-secret-key-byt-ut-i-produktion-min32tecken
  ☐  JWT_SECRET_KEY    → dev-jwt-secret-byt-ut-i-produktion-min32tecken

Environment: local → Variables:
  ✅ ENABLE_K8S_DEPLOY → false  (du sa att du lagt till variabeln)

Environment: local → Secrets:
  ⏭️  KUBECONFIG_LOCAL → lämna tom för nu (deploy-jobbet hoppas över)

Environment: production:
  ⏭️  Konfigurera när du har ett produktions-cluster
```

---

## Paketera kubeconfig för GitHub Secret (framtida referens)

```bash
# macOS/Linux
kubectl config view --minify --flatten | base64 -w0

# Windows (PowerShell)
kubectl config view --minify --flatten | [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((kubectl config view --minify --flatten)))
```

Klistra in output-strängen direkt som värde för `KUBECONFIG_LOCAL` eller `KUBECONFIG_PROD`.
