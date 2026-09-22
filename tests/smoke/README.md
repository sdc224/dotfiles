# Smoke tests — real Fedora install (not stubbed)

This repo is **first contact** for a brand-new machine. Smoke mirrors that:

1. CI harness shims only (systemctl/sudo in containers)
2. `curl` + chezmoi binary (human path in README)
3. Non-interactive profile config → `chezmoi apply`
4. Assert binaries / packages / profile gates

**Do not** pre-install gcc, python3, flatpak, fonts, etc. in smoke.
Those belong in `run_once_before_00-bootstrap.sh.tmpl`.

| File | Role |
|---|---|
| `run.sh` | Harness + chezmoi apply + verify |
| `verify.sh` | Profile assertions (`node -v`, packages, rules, …) |
| `lib.sh` | Shared helpers (shims, asserts) |
| `docker-run.sh` | Local Docker wrapper mirroring CI |

CI: `.github/workflows/smoke.yml` (weekly Thursday + manual).

```bash
PROFILE=personal bash tests/smoke/run.sh   # on Fedora
./tests/smoke/docker-run.sh work           # via Docker
```
