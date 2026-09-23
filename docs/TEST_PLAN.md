# Integration test plan (OS × profile matrix)

Every feature below is exercised for **work** (`is_work=true`) and
**personal** (`is_work=false`) on **macOS 26 (arm64)** and **Fedora**.
Status `auto` = implemented in `tests/integration/test_converge.py` (stubbed
package managers, real chezmoi + real scripts). Status `ci-only` = runs in
the `tests.yml` matrix, skipped locally on the wrong OS. Status `manual` =
requires hardware/MDM that CI cannot provide; verify by hand after reprovision.

## 1. Bootstrap (`run_once_before_00`)

First-contact script for a blank machine. Owns every OS primitive needed to
converge (package manager basics, python3 for the dispatcher, gcc/libatomic
for mise cargo/Node, font tooling, mise, zinit). Smoke/CI must not duplicate
these installs.

| Case | macOS | Fedora | Status |
|---|---|---|---|
| Homebrew installed when missing | ✅ | n/a | manual |
| dnf converge primitives (git/zsh/python3/gcc/libatomic/…) | n/a | ✅ | auto (bootstrap) + smoke |
| mise installed when missing | ✅ | ✅ | auto (bootstrap) + smoke |
| zinit cloned when missing | ✅ | ✅ | auto (bootstrap) + smoke |
| Nerd Fonts (best-effort; non-fatal) | n/a | ✅ | auto (bootstrap) |

## 2. Package dispatcher (`run_onchange_after_10`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| work profile installs awscli/mysql/jetbrains-toolbox (not intellij-idea cask) | ✅ | n/a | auto |
| personal profile installs neovim/distrobox, no work pkgs | ✅/n/a | ✅ | auto + ci-only |
| shared casks land on mac (ghostty/vscode/cursor) | ✅ | n/a | auto |
| existing unmanaged app/font skips the cask download | ✅ | n/a | unit + manual |
| COPR ghostty on Fedora | n/a | ✅ | unit (string) + ci-only |
| flathub remote ensured, flatpak installs | n/a | ✅ | unit + ci-only |
| empty backend list never fails (`grep`/`pipefail`) | ✅ | ✅ | auto (regression) |
| manifest hash re-triggers on edit | ✅ | ✅ | unit (hash lines) |

## 3. mise install (`run_onchange_after_20`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| `mise install` runs with gh token when authed | ✅ | ✅ | unit (string) |
| kubectl present iff work | ✅ | ✅ | auto (render) |
| full tool list resolves upstream | ✅ | ✅ | ci-only (`mise outdated` in audit workflow) |

## 4. IDE keys (`run_onchange_after_30`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| keybindings → Code/Cursor/Windsurf with backup | ✅ | ✅ | auto (render) + manual (real apps) |
| IntelliJ keymap iff work or `install_intellij` | ✅ | ✅ | auto (render) |
| personal without flag skips IntelliJ | ✅ | ✅ | auto (render) |

## 5. Schedulers (`run_once_after_40` + units)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| launchd plist valid, Wed 10:00 + RunAtLoad | ✅ | n/a | auto (render + XML) |
| systemd timer valid, Wed 10:00 + Persistent | n/a | ✅ | unit + ci-only |
| staleness guard: fresh run skips, `--force` runs | ✅ | ✅ | auto |
| status file + toast written | ✅ | ✅ | auto (file), manual (toast seen) |

## 6. Drift + auto-update (`dotfiles-sync`, `dotfiles-auto-update`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| clean machine exits 0 | ✅ | ✅ | auto (stubs) |
| EXTRA-BREW / EXTRA-FLATPAK detected, exit 1 | ✅ | ✅ | auto (stubs) + ci-only |
| `--check` never opens a PR | ✅ | ✅ | auto |
| auto-PR guards (gh auth, no open sync PR, opt-out) | ✅ | ✅ | unit (strings) |
| greedy cask upgrade, mise upgrade+prune | ✅ | ✅ | auto (stubs) |
| DNF updates owned by Fedora OS scheduler (user timer reports only) | n/a | ✅ | unit + auto |
| Docker DNF repository + Engine service enabled on personal Fedora | n/a | ✅ | auto (stubs) + ci-only |

## 7. Doctor (`dotfiles-doctor`: verify, invoke modules, read logs)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| healthy machine exits 0 with `[ok]` lines | ✅ | ✅ | auto (stubs + fake HOME) |
| missing package manager exits 1 with `[fail]` + owner module | ✅ | ✅ | auto + ci-only |
| drift asks apply / re-add / skip, never auto-reverts | ✅ | ✅ | unit (prompt gating) |
| scheduler auto-enabled on the spot, fail if it cannot | ✅ | ✅ | auto + ci-only |
| gh auth required: prompts, fails until authed | ✅ | ✅ | auto + ci-only |
| work profile notes second-account switch option | ✅ | ✅ | unit |
| stale status / dirty log surface as warnings | ✅ | ✅ | auto (fake status + log) |
| destructive choices only behind TTY prompts | ✅ | ✅ | unit (code scan) |
| shellcheck + shfmt clean | ✅ | ✅ | ci-only (lint job) |

## 8. Work-profile assumptions (cross-cutting)
| Assumption | Covered by |
|---|---|
| IntelliJ/AWS/MySQL never install on personal | auto (`DispatcherExecutionTest`, render) |
| kubectl never on personal (mise gate) | auto (render both profiles) |
| MDM apps (Slack/Zoom/Rancher/…) never in manifests | unit (`test_manifests`) + manual Company Portal check |
| `is_work` defaults true on macOS, false on Linux | unit (`test_templates`) + manual `chezmoi init` |
| Personal uses gh credential helper; work does not | auto (render both profiles) |
| Rancher/ZIA shell sourcing work-only | auto (render both profiles) |

## 9. Smoke (real install — weekly)

Status `smoke` = `tests/smoke/run.sh` on real hosts via schedule + manual:

- Fedora: [`.github/workflows/smoke.yml`](../.github/workflows/smoke.yml)
  (`fedora:latest` container)
- macOS: [`.github/workflows/smoke-macos.yml`](../.github/workflows/smoke-macos.yml)
  (`macos-26` arm64)

Package managers are **not** stubbed. Intelligent Hub / MDM apps are out of
scope. Both workflows run Thursday 06:00 UTC (day after Wed brew/mise audit).

| Case | personal | work | Status |
|---|---|---|---|
| Non-interactive `chezmoi apply` (pre-written config + linked source) | ✅ | ✅ | smoke |
| Apply log has no hard failure markers | ✅ | ✅ | smoke |
| Core mise tools respond (`node -v`, `rg`, `gh`, …) | ✅ | ✅ | smoke |
| Managed paths exist (`.zshrc`, mise, ghostty, doctor) | ✅ | ✅ | smoke |
| Personal dnf apps (`neovim`, `distrobox`, `docker-ce`) | ✅ Fedora | absent | smoke |
| Flatpak Postman | ✅ Fedora | n/a | smoke |
| Ghostty (COPR) on PATH | ✅ Fedora | shared-only | smoke |
| Shared brew formulae + casks (Ghostty, Cursor, fonts, …) | ✅ macOS | ✅ macOS | smoke |
| Work brew/cask (`awscli`, `mysql`, Toolbox, Postman; not intellij-idea/windsurf) | absent macOS | ✅ macOS | smoke |
| `kubectl` via mise | absent | ✅ | smoke |
| Work DXS rule / personal rule (GEMINI on Linux; Cursor/Claude on macOS) | ✅ | ✅ | smoke |
| IntelliJ keymap deploy (pre-seeded JetBrains dir) | absent | ✅ | smoke |
| systemd `enable --now` for docker/timer | shimmed in CI | shimmed | smoke (host = manual) |

## Adding a new app? Update this plan

1. Decide the backend per `docs/DECISION.md`.
2. Add the manifest entry + a unit assertion in `test_manifests.py`
   (profile membership / MDM exclusion).
3. If it changes install behaviour, extend `test_converge.py`
   (render or stub-call assertion for work + personal).
4. If it should appear on a real Fedora or macOS host, extend
   `tests/smoke/verify.sh` (OS-specific helpers).
5. Stubbed CI matrix picks it up automatically — no workflow edit needed.
