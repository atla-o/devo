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

One Cloud Run service (`devo-web`, `us-west1`) switches on the `Host` header:

| Host | Page |
| --- | --- |
| `devoutshaman.com`, `www.devoutshaman.com` | Holding |
| `phenomatch.devoutshaman.com` | Phenomatch landing |
| `antiporn.devoutshaman.com` | Antiporn landing |
| `lessfret.devoutshaman.com` | Lessfret (also `/lessfret`) |
| `lightround.devoutshaman.com` | Lightround (also `/lightround`; `/fund` aliases here) |
| `fund.devoutshaman.com` | Redirects to Lightround |
| unknown host, including `*.run.app` | Holding |

`phenomatch` and `antiporn` are already mapped. Prefer Lightround over a generic
`fund` host. After deploy, map `lessfret.devoutshaman.com` and
`lightround.devoutshaman.com` on Cloud Run `devo-web`, then add Cloudflare
CNAME records (DNS-only, not proxied) to `ghs.googlehosted.com`.

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

Browser on localhost: `/` (holding), `/phenomatch`, `/antiporn`, `/lessfret`,
`/lightround`.

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
