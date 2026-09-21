# Integration test plan (OS × profile matrix)

Every feature below is exercised for **work** (`is_work=true`) and
**personal** (`is_work=false`) on **macOS 15 (arm64)** and **Fedora**.
Status `auto` = implemented in `tests/integration/test_converge.py` (stubbed
package managers, real chezmoi + real scripts). Status `ci-only` = runs in
the `tests.yml` matrix, skipped locally on the wrong OS. Status `manual` =
requires hardware/MDM that CI cannot provide; verify by hand after reprovision.

## 1. Bootstrap (`run_once_before_00`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| Homebrew installed when missing | ✅ | n/a | manual |
| dnf basics + Nerd Fonts | n/a | ✅ | manual |
| mise installed when missing | ✅ | ✅ | manual |
| zinit cloned when missing | ✅ | ✅ | manual |

Why manual: mutates the host package manager. CI covers the *shape*
(strict mode, tool list) in unit tests.

## 2. Package dispatcher (`run_onchange_after_10`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| work profile installs awscli/mysql/intellij-idea | ✅ | n/a | auto |
| personal profile installs neovim/distrobox, no work pkgs | ✅/n/a | ✅ | auto + ci-only |
| shared casks land on mac (ghostty/vscode/cursor) | ✅ | n/a | auto |
| iterm2 removed (Ghostty-only policy) | ✅ | n/a | unit (string) + manual |
| COPR ghostty on Fedora | n/a | ✅ | unit (string) + ci-only |
| flathub remote ensured, flatpak installs | n/a | ✅ | unit + ci-only |
| empty backend list never fails (`grep`/`pipefail`) | ✅ | ✅ | auto (regression) |
| manifest hash re-triggers on edit | ✅ | ✅ | unit (hash lines) |

## 3. mise-first guard (`run_onchange_after_15`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| brew node/python/kubectl/gum copies removed | ✅ | n/a | unit + manual |
| hidden brew python only warns (awscli/mysql dep) | ✅ | n/a | unit |
| no-op on Linux | n/a | ✅ | unit (Darwin gate) + ci-only |

## 4. mise install (`run_onchange_after_20`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| `mise install` runs with gh token when authed | ✅ | ✅ | unit (string) |
| kubectl present iff work | ✅ | ✅ | auto (render) |
| full tool list resolves upstream | ✅ | ✅ | ci-only (`mise outdated` in audit workflow) |

## 5. IDE keys (`run_onchange_after_30`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| keybindings → Code/Cursor/Windsurf with backup | ✅ | ✅ | auto (render) + manual (real apps) |
| IntelliJ keymap iff work or `install_intellij` | ✅ | ✅ | auto (render) |
| personal without flag skips IntelliJ | ✅ | ✅ | auto (render) |

## 6. Schedulers (`run_once_after_40` + units)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| launchd plist valid, Wed 10:00 + RunAtLoad | ✅ | n/a | auto (render + XML) |
| systemd timer valid, Wed 10:00 + Persistent | n/a | ✅ | unit + ci-only |
| staleness guard: fresh run skips, `--force` runs | ✅ | ✅ | auto |
| status file + toast written | ✅ | ✅ | auto (file), manual (toast seen) |

## 7. Drift + auto-update (`dotfiles-sync`, `dotfiles-auto-update`)

| Case | macOS | Fedora | Status |
|---|---|---|---|
| clean machine exits 0 | ✅ | ✅ | auto (stubs) |
| EXTRA-BREW / EXTRA-FLATPAK detected, exit 1 | ✅ | ✅ | auto (stubs) + ci-only |
| `--check` never opens a PR | ✅ | ✅ | auto |
| auto-PR guards (gh auth, no open sync PR, opt-out) | ✅ | ✅ | unit (strings) |
| greedy cask upgrade, mise upgrade+prune | ✅ | ✅ | auto (stubs) |
| dnf notify-only (never upgrades OS) | n/a | ✅ | unit + auto |

## 8. Work-profile assumptions (cross-cutting)

| Assumption | Covered by |
|---|---|
| IntelliJ/AWS/MySQL never install on personal | auto (`DispatcherExecutionTest`, render) |
| kubectl never on personal (mise gate) | auto (render both profiles) |
| MDM apps (Slack/Zoom/Rancher/…) never in manifests | unit (`test_manifests`) + manual Company Portal check |
| `is_work` defaults true on macOS, false on Linux | unit (`test_templates`) + manual `chezmoi init` |
| Personal uses gh credential helper; work does not | auto (render both profiles) |
| Rancher/ZIA shell sourcing work-only | auto (render both profiles) |

## Adding a new app? Update this plan

1. Decide the backend per `docs/DECISION.md`.
2. Add the manifest entry + a unit assertion in `test_manifests.py`
   (profile membership / MDM exclusion).
3. If it changes install behaviour, extend `test_converge.py`
   (render or stub-call assertion for work + personal).
4. CI matrix picks it up automatically — no workflow edit needed.
