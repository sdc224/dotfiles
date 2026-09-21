# Smoke tests — real Fedora install (not stubbed)

Scripts here drive a blank Fedora image through non-interactive
`chezmoi apply` (pre-written config + linked source), scan the apply log,
then assert binaries and paths.

| File | Role |
|---|---|
| `run.sh` | Host setup + chezmoi apply + invoke verify |
| `verify.sh` | Profile assertions (`node -v`, packages, rules, …) |
| `lib.sh` | Shared helpers (shims, asserts) |
| `docker-run.sh` | Local Docker wrapper mirroring CI |

CI: `.github/workflows/smoke.yml` (weekly Thursday + manual).

```bash
PROFILE=personal bash tests/smoke/run.sh   # on Fedora
./tests/smoke/docker-run.sh work           # via Docker
```
