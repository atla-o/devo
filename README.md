# Devo

Parent holding for a lateral health company. Products ship under Devo, not as
separate companies.

## Products

- [Phenomatch](https://github.com/atla-o/phenomatch) — match people by phenotype. Revenue toward a fertility program.
- [Antiporn](https://github.com/atla-o/antiporn) — computer restriction. Blocks porn and anything the user flags as a net negative.

App data lives on Google Cloud project `devo-holding`.

## Public site

One Cloud Run service (`devo-web`, `us-west1`) switches on the `Host` header:

| Host | Page |
| --- | --- |
| `devoutshaman.com`, `www.devoutshaman.com` | Holding |
| `antiporn.devoutshaman.com` | Antiporn landing |
| `phenomatch.devoutshaman.com` | Phenomatch landing |
| `fund.devoutshaman.com` | The fund (also `/fund`) |
| `lessfret.devoutshaman.com` | Lessfret (also `/lessfret`) |
| unknown host, including `*.run.app` | Holding |

`antiporn` and `phenomatch` subdomains are already mapped. Apex mapping comes later.

### Local preview

```bash
PORT=8080 python3 server.py
```

Host routing (the production path):

```bash
curl -s -H 'Host: devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: antiporn.devoutshaman.com' localhost:8080 | head
curl -s -H 'Host: phenomatch.devoutshaman.com' localhost:8080 | head
```

Browser on localhost: `/` (holding), `/phenomatch`, `/antiporn`, `/fund`, `/lessfret`.

```bash
python3 test_host.py
```

### Deploy

Do not deploy from Cloudflare. Build the image and replace Cloud Run service
`devo-web` in project `devo-holding`, region `us-west1`. The container listens
on `$PORT` (Cloud Run default 8080).

```bash
gcloud run deploy deo-web \
  --source . \
  --region=us-west1 \
  --project=devo-holding \
  --allow-unauthenticated
```

That rebuilds from this `Dockerfile` and updates the existing service. Map
`devoutshaman.com` / `www` to `devo-web` when ready.
