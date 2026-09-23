# Smoke tests — real install (Fedora + macOS)

This repo is **first contact** for a brand-new machine. Smoke mirrors that:

1. CI harness shims only (systemctl/sudo in Linux containers)
2. `curl` + chezmoi binary (human path in README)
3. Non-interactive profile config → `chezmoi apply`
4. Assert binaries / packages / profile gates

**Do not** pre-install gcc, python3, flatpak, brew formulae, fonts, etc. in smoke.
Those belong in `run_once_before_00-bootstrap.sh.tmpl` / the package dispatcher.

| File | Role |
|---|---|
| `run.sh` | Harness + chezmoi apply + verify (OS-aware) |
| `verify.sh` | Profile assertions (`node -v`, packages, rules, …) |
| `lib.sh` | Shared helpers (shims, asserts) |
| `docker-run.sh` | Local Docker wrapper mirroring Fedora CI |

CI:

- `.github/workflows/smoke.yml` — Fedora, weekly Thursday + manual
- `.github/workflows/smoke-macos.yml` — macOS 26 arm64, weekly Thursday + manual

```bash
PROFILE=personal bash tests/smoke/run.sh   # on Fedora or macOS
PROFILE=work bash tests/smoke/run.sh
./tests/smoke/docker-run.sh work           # Fedora via Docker
```
