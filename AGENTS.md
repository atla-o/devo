# Devo workspace

Parent holding. Products ship under Devo: Phenomatch, Antiporn, Lessfret, and
Lightround. Phenomatch and Antiporn use the **same** process: half cloud, half
local.

## Half cloud / half local

- **Cloud (Cursor cloud agent):** web app, backend, GCP, GitHub, docs.
- **Local Mac (Cursor on the machine, or Cursor My Machines):** overlay, audio, camera, native client, installer, simulator.

A Linux cloud VM cannot drive local audio or UI.

## Repos

- [phenomatch](https://github.com/atla-o/phenomatch)
- [antiporn](https://github.com/atla-o/antiporn) (public) / [anti-porn](https://github.com/atla-o/anti-porn) (private Swift)
- [lessfret](https://github.com/atla-o/lessfret)
- [lightround](https://github.com/atla-o/lightround)
- Cursor web UI workspace: `devon-schauman/antiporn`

GitHub publisher is `atla-o` (`github.com/devo` is taken). GCP: project `devo-holding`, org `atla-o.com`, folder `Devo`. Not Firebase.

## Public site

Holding pages for devoutshaman.com live in this repo. Merge to `main` deploys
Cloud Run `devo-web` (`us-west1`, `devo-holding`) and updates the holding pages
on devoutshaman.com (apex, www). Hosts still on this service include antiporn
until Antiporn has its own web app, and possibly fund until remapped.

Product apps with their own Cloud Run services are **separate repos** and do
not deploy from here: `phenomatch-web` today; `lessfret-web` / `lightround-web`
soon.

Cloudflare is DNS-only (grey cloud) to `ghs.googlehosted.com`. No Workers. No
beta host. Public access is invoker-iam-disabled (already true on the live
service). Never `--allow-unauthenticated` (org policy blocks `allUsers`). If a
revision loses public access, set
`--update-annotations=run.googleapis.com/invoker-iam-disabled=true`. Cloud
agents must not run `gcloud run deploy`; merging to main is the deploy path.
See the README.
