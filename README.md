# Devo

Parent holding for a lateral health company. Products ship under Devo, not as
separate companies.

## Products

- [Phenomatch](https://github.com/atla-o/phenomatch) — match people by phenotype. Revenue toward a fertility program.
- [Antiporn](https://github.com/atla-o/antiporn) — computer restriction. Blocks porn and anything the user flags as a net negative.
- [Lessfret](https://github.com/atla-o/lessfret) — coaching and care coordination. Not therapy.
- [Lightround](https://github.com/atla-o/lightround) — counterdecadence fund.

App data lives on Google Cloud project `devo-holding`.

## Public site

This repo is the holding lander. Merge to `main` deploys Cloud Run `devo-web`
(`devo-holding`, `us-west1`) and updates the holding pages on
[devoutshaman.com](https://devoutshaman.com).

Product apps that have their own Cloud Run services live in **other repos** and
do not deploy from here:

| Service | Repo |
| --- | --- |
| `phenomatch-web` | [atla-o/phenomatch](https://github.com/atla-o/phenomatch) |
| `lessfret-web` (soon) | [atla-o/lessfret](https://github.com/atla-o/lessfret) |
| `lightround-web` (soon) | [atla-o/lightround](https://github.com/atla-o/lightround) |

### Hosts on `devo-web`

The container still switches on `Host` (and localhost path prefixes). In
production, only hosts that still map to this service hit it:

| Host | Page |
| --- | --- |
| `devoutshaman.com`, `www.devoutshaman.com` | Holding |
| `antiporn.devoutshaman.com` | Antiporn stub (until Antiporn has its own web app) |
| `fund.devoutshaman.com` | Redirects to Lightround (until remapped) |
| unknown host, including `*.run.app` | Holding |

Local preview can still serve Phenomatch / Lessfret / Lightround stubs on those
hosts or `/phenomatch`, `/lessfret`, `/lightround`. Production DNS for product
apps should point at their own services when those exist.

Cloudflare is **DNS-only** (grey cloud), CNAME to `ghs.googlehosted.com` (apex
already uses Google A records). No Workers. No orange-cloud proxy. No beta host.

### Local preview

```bash
PORT=8080 python3 server.py
```

Host routing (the production path):

```bash
curl -s -H 'Host: devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: phenomatch.devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: antiporn.devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: lessfret.devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: lightround.devoutshaman.com' localhost:8080 | head
```

Browser on localhost: `/` (holding), `/insurance` (ACA intake; `/aca` redirects here),
`/phenomatch`, `/antiporn`, `/lessfret`, `/lightround`.

```bash
python3 test_host.py
```

### ACA subsidized insurance

The holding directory includes an **Insurance** tile that opens `/insurance`
(also `/aca`). That page is Devo intake for Affordable Care Act subsidized
insurance interest: a short form and a status lookup. It is not insurance
advice, a quote, or a broker service. Enrollment stays on
[HealthCare.gov](https://www.healthcare.gov) or the state exchange.

Submit `POST /api/aca/applications` (JSON). Look up
`GET /api/aca/applications?receipt_id=aca_…` or `?email=…`. New applications
start as `received` (`in_review`, `needs_info`, `submitted_to_marketplace` are
stored for later review). The browser keeps the receipt id in `localStorage`.

Local/tests persist to a JSON file (`ACA_STORE=json`, default
`ACA_DATA_PATH=/tmp/devo-aca-applications.json`). On Cloud Run, the same
endpoints write Firestore collection `aca_applications` in project
`devo-holding` (native mode). The `devo-web` runtime service account needs
`roles/datastore.user`. If Firestore is not created yet:

```bash
gcloud firestore databases create --database="(default)" --location=us-west1 \
  --project=devo-holding
gcloud projects add-iam-policy-binding devo-holding \
  --member="serviceAccount:RUNTIME_SA" \
  --role=roles/datastore.user
```

Use the Cloud Run runtime account for `RUNTIME_SA` (not the GitHub deploy
account). Spell the project id `devo-holding`.

### Deploy

Push to `main` runs `.github/workflows/deploy.yml`: host-routing tests, then
`gcloud run deploy devo-web --source . --project=devo-holding --region=us-west1`.
That uses this `Dockerfile` (optional `cloudbuild.yaml` tags `$_IMAGE` for
Artifact Registry). The container listens on `$PORT` (Cloud Run default 8080).

**Invoker IAM:** never `--allow-unauthenticated`. Org policy (domain restricted
sharing) blocks binding `allUsers` as Cloud Run Invoker. Public traffic uses
**invoker-iam-disabled** (`run.googleapis.com/invoker-iam-disabled: true`),
already set on the live service.

CI does not pass `--no-invoker-iam-check` or `--invoker-iam-check=disabled`.
Current `gcloud run deploy` docs list `--[no-]invoker-iam-check`, but operator
gcloud rejected `--invoker-iam-check=disabled`. If a revision loses public
access, update the annotation (do not grant `allUsers`):

```bash
gcloud run services update devo-web \
  --project=devo-holding \
  --region=us-west1 \
  --update-annotations=run.googleapis.com/invoker-iam-disabled=true
```

Do not deploy from Cloudflare. Cloud agents must not run `gcloud run deploy`;
merging to `main` is the path.

#### One-time GitHub → GCP

Workload Identity Federation from `atla-o/devo` to a deploy service account
that can source-deploy Cloud Run (`roles/run.sourceDeveloper`,
`roles/iam.serviceAccountUser`, `roles/serviceusage.serviceUsageConsumer`; the
Cloud Build SA needs `roles/run.builder`). Then set repository **variables**
(Settings → Secrets and variables → Actions):

| Variable | Example |
| --- | --- |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_SERVICE_ACCOUNT` | `github-devo-web@devo-holding.iam.gserviceaccount.com` |

#### Manual

Same flags as CI. Do not pass `--allow-unauthenticated`.

```bash
gcloud run deploy devo-web \
  --source . \
  --project=devo-holding \
  --region=us-west1
```
