# Devo workspace

## Standing objective (Devo UI-first)

Cursor cloud work for this product: **one promptable environment / one cloud workspace**, kept current.

Priority order for every task unless Devo says otherwise:
1. **Complete functional UI** — usable end-to-end (persist data, real submit paths, loading/empty/error/success). No blocking coming-soon for core flows.
2. Black text on **white** backgrounds always — never follow system dark mode / white-on-black.
3. Ship via merge to `main` (Cloud Run Actions). Do not deploy from the agent unless Devo explicitly says push/ship/merge and deploy.

Parent: Devo (lateral health). Publisher: atla-o. GCP app data: project `devo-holding`. Public hosts on `*.devoutshaman.com` (Cloudflare DNS-only → Cloud Run).

Investor tops: Arcada, Lightround, Humanehealth, Mattercircle. Holding lander: atla-o/devo → devoutshaman.com.

## Investor surface

Holdings has two avenues. They are not lander tiles:

- biology o
- physics o

Planet is dissolved. Do not add it.

The holding lander shows exactly four tops, in this order:

1. **Arcada** — social club. Tile href `https://arcada.devoutshaman.com` (own app in [arcada](https://github.com/atla-o/arcada)). Soft-wired from this lander. Do not serve Arcada from `devo-web` and do not merge that repo here.
2. **Lightround** — counterdecadence fund. [lightround](https://github.com/atla-o/lightround).
3. **Humanehealth** — clinic network. [humanehealth](https://github.com/atla-o/humanehealth).
4. **Mattercircle** — factory essentials. [mattercircle](https://github.com/atla-o/mattercircle).

Nested under Humanehealth (copy and structure only — not peer tiles, not lander tops):

- Acashi (insurance)
- devoutshaman (sell-health)
- unnaturalfertility

unnaturalfertility stays in that nest. It is not its own lander top.

Soft-wire only. Do not merge product repos into this umbrella. No stage labels on the investor surface.

Each lander top tile carries a blurb of three words or fewer. The lander mark is a pinned bright **o** on warm paper with a soft glow: black ink, no neon, no footer chrome.

## This product

Holding lander + directory tiles; hostname routing in `server.py`.

Humanehealth and Mattercircle pages on this service are soft-wires until those houses have their own web apps. Arcada is already its own app.

## Half cloud / half local

Phenomatch and Antiporn use the **same** process: half cloud, half local. They are not investor tops and they are not in the Humanehealth nest.

- **Cloud (Cursor cloud agent):** web app, backend, GCP, GitHub, docs.
- **Local Mac (Cursor on the machine, or Cursor My Machines):** overlay, audio, camera, native client, installer, simulator.

A Linux cloud VM cannot drive local audio or UI.

## Repos

Tops:

- [arcada](https://github.com/atla-o/arcada)
- [lightround](https://github.com/atla-o/lightround)
- [humanehealth](https://github.com/atla-o/humanehealth)
- [mattercircle](https://github.com/atla-o/mattercircle)

Under Humanehealth (not lander tops):

- [acashi](https://github.com/atla-o/acashi) — insurance
- devoutshaman — sell-health
- unnaturalfertility

Not on the investor lander:

- [phenomatch](https://github.com/atla-o/phenomatch)
- [antiporn](https://github.com/atla-o/antiporn) (public) / [anti-porn](https://github.com/atla-o/anti-porn) (private Swift)
- [lessfret](https://github.com/atla-o/lessfret)

Antiporn web cloud workspace is only `atla-o/antiporn`; archive any `devon-schauman/antiporn` Cursor workspace.

GitHub publisher is `atla-o` (`github.com/devo` is taken). GCP: project `devo-holding`, org `atla-o.com`, folder `Devo`. Not Firebase.

## Public site

Holding pages for devoutshaman.com live in this repo. Merge to `main` deploys
Cloud Run `devo-web` (`us-west1`, `devo-holding`) and updates the holding pages
on devoutshaman.com (apex, www).

The lander tiles are Arcada, Lightround, Humanehealth, and Mattercircle.
Biology o and physics o are avenues under Holdings, not tiles. Planet is not on
this surface. Hosts still on this service include the Humanehealth and
Mattercircle soft-wires, Lightround, Acashi, and older stubs that are not
lander tops, plus fund until remapped. Arcada’s public host is its own service.

Product apps with their own Cloud Run services are **separate repos** and do
not deploy from here.

Cloudflare is DNS-only (grey cloud) to `ghs.googlehosted.com`. No Workers. No
beta host. Public access is invoker-iam-disabled (already true on the live
service). Never `--allow-unauthenticated` (org policy blocks `allUsers`). If a
revision loses public access, set
`--update-annotations=run.googleapis.com/invoker-iam-disabled=true`. Cloud
agents must not run `gcloud run deploy`; merging to main is the deploy path.
See the README.
