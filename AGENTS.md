# Devo workspace

Parent holding. Products ship under Devo. Phenomatch and Antiporn use the **same** process: half cloud, half local.

## Half cloud / half local

- **Cloud (Cursor cloud agent):** web app, backend, GCP, GitHub, docs.
- **Local Mac (Cursor on the machine, or Cursor My Machines):** overlay, audio, camera, native client, installer, simulator.

A Linux cloud VM cannot drive local audio or UI.

## Repos

- [phenomatch](https://github.com/atla-o/phenomatch)
- [antiporn](https://github.com/atla-o/antiporn) (public) / [anti-porn](https://github.com/atla-o/anti-porn) (private Swift)
- Cursor web UI workspace: `devon-schauman/antiporn`

GitHub publisher is `atla-o` (`github.com/devo` is taken). GCP: project `devo-holding`, org `atla-o.com`, folder `Devo`. Not Firebase.
