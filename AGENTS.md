# Devo workspace

Parent holding. Products ship under Devo, not as separate companies.

## Repos

- This repo: holding notes and links
- [phenomatch](https://github.com/atla-o/phenomatch) — phenotype matching → fertility
- [antiporn](https://github.com/atla-o/antiporn) — public OSS listing
- [anti-porn](https://github.com/atla-o/anti-porn) — private Swift macOS app
- Cursor workspace for the Antiporn web UI: `devon-schauman/antiporn`

`github.com/devo` is taken. Publisher on GitHub is `atla-o`.

## Where to code

- **Antiporn native (overlay, audio, filter extension):** local Mac in Cursor, or a Cursor My Machines worker. Linux cloud agents cannot drive that UI.
- **Antiporn web (Filter / Time vault / Install):** Cursor cloud agent or this GitHub remote.
- **Phenomatch / GCP:** cloud is fine. Project `devo-holding` under org `atla-o.com`, folder `Devo`.

## Cloud

App data is a GCP project, not Firebase. Billing is on `devo-holding`. Cloud Run is enabled.
