# Modern Dotfiles

A chezmoi-managed development environment that is **profile-first** (work vs personal) and **backend-extensible** across OSes. Tooling is Rust-first: [mise](https://mise.jdx.dev/) owns runtimes and CLIs, [Ghostty](https://ghostty.org/) is the terminal, [Starship](https://starship.rs/) is the prompt, and [zinit](https://github.com/zdharma-continuum/zinit) keeps shell startup near-instant.

There is **no `install.sh`**. One command bootstraps a machine; weekly schedulers and GitHub Actions keep packages and mise tools current.

Supported today: **macOS** and **Linux** (Fedora is the reference Linux). Package manifests already declare a **`[winget]`** backend — Windows is the planned next OS, not a special case to redesign for later.

---

## Table of contents

1. [Quick start (new machine)](#1-quick-start-new-machine)
2. [How convergence works](#2-how-convergence-works)
3. [Profiles, backends & docs](#3-profiles-backends--docs)
4. [Day-to-day usage](#4-day-to-day-usage)
5. [Terminal stack](#5-terminal-stack)
6. [Aliases & shortcuts](#6-aliases--shortcuts)
7. [Skills & agent rules](#7-skills--agent-rules)
8. [Debugging & health checks](#8-debugging--health-checks)
9. [Local development & testing](#9-local-development--testing)
10. [GitHub Actions](#10-github-actions)
11. [Adding software](#11-adding-software)

---

## 1. Quick start (new machine)

The same flow on every OS. Profile (`is_work`) and OS backends are chosen at init / by the dispatcher — you do not pick a “Mac path” vs “Linux path” in the repo.

### Before bootstrap

- **Work machines with MDM:** install company-provided apps from the portal first. Never put those in package manifests — list them in [`docs/MDM.md`](docs/MDM.md). OS-specific checklists live in [`docs/MANUAL.md`](docs/MANUAL.md).
- **Personal / unmanaged hosts:** finish base OS setup (updates, package repos) once, then bootstrap.
- **Minimum prerequisite:** `curl` and internet access. You do not need
  Homebrew, Git, mise, python, a C compiler, or a preinstalled Chezmoi binary —
  `run_once_before_00-bootstrap` installs the converge primitives on first apply.

### Bootstrap

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply https://github.com/sdc224/dotfiles.git
```

The command installs Chezmoi and clones/applies this repository automatically;
you do not clone it separately. Its first hook installs the missing platform
tools: Homebrew on macOS, or OS packages via dnf/apt on Linux. The Homebrew
installer detects the current CPU itself: Apple Silicon uses `/opt/homebrew`;
Intel uses `/usr/local`.

Prompts:

| Prompt | Meaning |
|---|---|
| Git name / email | Written into templated git config |
| `is_work` | Work vs personal **profile** (packages, rules, gated tools). Default follows the host OS today; override freely. |
| `install_intellij` | Whether to deploy IntelliJ keymap / related bits independent of profile |

Then verify:

Open a new terminal first so the managed `.zprofile` adds `~/.local/bin` to
`PATH`, then run:

```bash
dotfiles-doctor
dotfiles-sync --check   # expect clean
```

### After first apply

| Command | Purpose |
|---|---|
| `chezmoi update -v` | Pull latest + re-converge packages/mise/configs |
| `dotfiles-doctor` | Interactive health check; fixes safe issues |
| `mise upgrade` | Bump all mise-owned tools |
| `reload` | Restart the shell (`exec zsh`) |

OS-specific notes (Ghostty COPR, launchd vs systemd, Docker stance, …) stay in [`docs/MANUAL.md`](docs/MANUAL.md) and [`docs/FEDORA.md`](docs/FEDORA.md) — they are host recipes, not the architecture.

---

## 2. How convergence works

`chezmoi apply` / `chezmoi update` runs ordered hooks. Hashes of manifests and configs are embedded in the scripts, so editing a TOML/JSON/`SKILL.md` re-triggers the right step on the next apply.

| Order | Script | What it does |
|---|---|---|
| once | `run_once_before_00-bootstrap` | Host bootstrap (package manager primitives, mise, zinit, Nerd Fonts) |
| on change | `run_onchange_after_10-install-packages` | Merges `shared.toml` + `work.toml` *or* `personal.toml`, then installs via the **OS backend** that matches the host |
| on change | `run_onchange_after_20-mise-install` | `mise install` for runtimes + Rust CLIs |
| on change | `run_onchange_after_30-ide-keys` | Deploys Ctrl-first keybindings to VS Code / Cursor / Windsurf (+ IntelliJ keymap when gated) |
| on change | `run_onchange_after_35-skills` | Symlinks personal skills into the host OS’s agent IDEs |
| on change | `run_onchange_after_36-rules` | Deploys work (`commit-pr-jira`) or personal (`personal-commits`) agent rules |
| once | `run_once_after_40-enable-schedulers` | Weekly auto-update (host scheduler: launchd, systemd, …) |

**Why chezmoi (not stow)?** Templates and data flags let one source tree serve every OS and profile. Sensitive or machine-local bits stay out of git (`~/.zsh_local`, `~/.gitconfig_local`).

---

## 3. Profiles, backends & docs

### Profiles (cross-OS)

Chezmoi data (from `.chezmoi.toml.tmpl`) gates **what** you get, not which OS you are on:

| Flag | Effect |
|---|---|
| `is_work` | Work packages, work-gated mise tools (e.g. kubectl), work shell blocks (e.g. Rancher/ZIA when present), DXS commit rules |
| `install_intellij` | IntelliJ keymap deploy; personal trials can flip this without a manifest rewrite |

### Package backends (per OS)

One manifest set; the dispatcher picks the section for the host:

| Backend | Typical host | Declared in |
|---|---|---|
| `[brew]` / `[cask]` | macOS | `dot_config/packages/*.toml` |
| `[dnf]` / `[flatpak]` | Linux (Fedora today) | same |
| `[winget]` | Windows (scaffolded; wire-up next) | same |

| File | When |
|---|---|
| `dot_config/packages/shared.toml` | Always (editors, terminal, browsers, shared CLIs, …) |
| `dot_config/packages/work.toml` | `is_work` — e.g. awscli, mysql, IntelliJ, Postman |
| `dot_config/packages/personal.toml` | `!is_work` — e.g. neovim, distrobox (Linux), personal extras |

Runtimes and cross-platform CLIs stay in **mise**, not in these backends. That is what keeps Windows (and any future OS) cheap to add: same mise config, new/expanded winget (or other) rows only for GUI/OS packages.

### Docs map

| Doc | Covers |
|---|---|
| [`docs/DECISION.md`](docs/DECISION.md) | **Where does a new app go?** mise-first rule, banned backends, skills/rules policy |
| [`docs/MANUAL.md`](docs/MANUAL.md) | Hand installs, weekly update UX, `~/.zsh_local`, adding software later |
| [`docs/MDM.md`](docs/MDM.md) | Company apps that must **never** enter package manifests |
| [`docs/FEDORA.md`](docs/FEDORA.md) | Linux/Fedora host notes (COPR Ghostty, systemd timer, Docker) |
| [`docs/TESTING.md`](docs/TESTING.md) | How to run unit/integration/coverage/lint |
| [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) | OS × profile feature matrix |
| [`cli_tools_guide.md`](cli_tools_guide.md) | What each modern CLI replaces and why |

---

## 4. Day-to-day usage

```bash
# Edit a managed file (opens source in repo, then apply)
chezmoi edit ~/.zshrc

# Apply everything from the repo source → home
chezmoi apply

# Pull remote + apply
chezmoi update -v

# See drift between home and source
chezmoi status
dotfiles-sync --check

# Record a deliberate home change back into the repo
chezmoi re-add ~/.zshrc   # or use doctor’s [r]e-add prompt
```

### Weekly automation

- **Local:** `dotfiles-auto-update` (host scheduler) upgrades mise + packages, then runs `dotfiles-sync --check`. Toast + log when drift appears.
- **Logs:** `~/.local/share/dotfiles-update.log` and `~/.local/share/dotfiles-update.status`
- **Upstream:** scheduled GitHub Action audits declared packages + `mise outdated` and may open a deps PR.

Machine-only drift (hand-installed package, no repo change) never auto-PRs — edit the manifest and run `dotfiles-sync`, or let doctor guide you. Details: [`docs/MANUAL.md`](docs/MANUAL.md).

### Machine-local overrides

| File | Managed? | Use for |
|---|---|---|
| `~/.zshrc`, `~/.zsh_aliases` | Yes | Shared shell |
| `~/.zsh_local` | **No** | Machine-only shell snippets (installer init lines belong here) |
| `~/.gitconfig_local` | **No** | Machine-only git bits |

Hand-editing a managed file shows up in `chezmoi status` / `dotfiles-sync --check` and is reverted by the next `chezmoi apply`.

---

## 5. Terminal stack

### Ghostty (primary terminal)

Config: `dot_config/ghostty/config` → `~/.config/ghostty/config`. Same file on every Ghostty host.

- **Theme:** Dracula; JetBrainsMono Nerd Font
- **Copy/paste:** `Ctrl+C` copies when text is selected, otherwise SIGINT; also `Ctrl+V`, `Shift+Insert`, `Ctrl+Shift+C/V`
- **Ninja keys (Ctrl-led, same muscle memory as the IDEs):**

| Key | Action |
|---|---|
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close surface |
| `Ctrl+D` / `Ctrl+Shift+D` | Split right / down |
| `Ctrl+F` | Toggle split zoom |
| `Ctrl+K` | Clear screen |
| `Ctrl+Shift+F` | Search |
| `Ctrl+=` / `-` / `0` | Font size |

Host install path for Ghostty (cask, COPR, winget, …) is owned by the package dispatcher — see OS notes in the docs when something fails to land.

### Shell (zsh)

`dot_zshrc.tmpl` builds `~/.zshrc`:

1. PATH, history, `EDITOR=code --wait`
2. Aliases from `~/.zsh_aliases`
3. **mise** shims + `mise activate`
4. Interactive only: **Starship**, **zinit** turbo plugins, **zoxide** / **fzf** / **Atuin**
5. Work-gated blocks (e.g. container runtime PATH, corporate cert `profile.d`) when the profile needs them
6. `~/.zsh_local` last

**zinit turbo plugins:** zsh-autosuggestions, zsh-completions, fzf-tab, fast-syntax-highlighting, forgit, Oh-My-Zsh git snippets.

**Atuin** replaces `Ctrl+R` / Up-arrow history with a SQLite-backed TUI (filter by status, directory, time). Config: `dot_config/atuin/config.toml`.

### Tools (mise-owned)

Declared in `dot_config/mise/config.toml.tmpl`. If mise can install it, it **must** live there — see [`docs/DECISION.md`](docs/DECISION.md). Same list on every OS.

| Category | Tools |
|---|---|
| Runtimes | node, python, java, rust, dart, uv |
| Core UX | starship, chezmoi, atuin, fzf, zoxide, yazi, gum |
| Modern replacements | ripgrep, bat, fd, eza, delta, dust, duf, bottom, procs, tokei |
| TUIs | lazygit, lazydocker |
| Platform | gh; **kubectl** only when `is_work` |

Narrative “why this tool” table: [`cli_tools_guide.md`](cli_tools_guide.md).

### Prompt

`dot_config/starship.toml` — one Starship config for every terminal that starts zsh.

---

## 6. Aliases & shortcuts

### Shell aliases (`dot_zsh_aliases`)

**Smart GUI launcher** — silences Electron noise and detaches from the terminal unless you pass CLI flags (`--help`, `-v`, …):

| Alias | App |
|---|---|
| `cr` | Cursor |
| `ag` | Antigravity |
| `code` | VS Code |
| `slack` / `discord` / `obsidian` | same pattern |

**Modern replacements** (only if the binary exists):

| Alias | Runs |
|---|---|
| `ls` / `ll` / `lt` | eza (+ git icons / tree) |
| `cat` / `dog` | bat |
| `ps` | procs |
| `top` / `htop` | btm (bottom) |
| `df` / `du` | duf / dust |
| `lg` / `ld` | lazygit / lazydocker |
| `ya` | yazi (cwd follows on quit) |
| `gst` / `gm` / `gdiff` | git shortcuts |
| `reload` | `exec zsh` |
| `:q` | exit |

**Navigation:** zoxide is wired as `cd` (and `z` / `zi` / `zf`). Fancy `Ctrl+Z` toggles a suspended job via fzf.

### IDE keybindings (Ctrl-first)

Source of truth: `dot_config/ide/keybindings.json`.

`run_onchange_after_30-ide-keys` copies it into each IDE’s User directory on the host (paths differ by OS; the script resolves them). Same Ctrl muscle memory as Ghostty: copy/paste, save, quick open, split, tabs, format, comment, … Timestamped backups are kept when an existing file differs.

**IntelliJ:** `dot_config/ide/intellij/DarculaCopy.xml` deploys when `is_work` **or** `install_intellij`.

---

## 7. Skills & agent rules

### Personal skills

Canonical store: `dot_config/skills/<name>/SKILL.md` → deployed to
`~/.config/skills/`, then symlinked into the host OS’s agent IDE:

- macOS: `~/.cursor/skills` and `~/.claude/skills`
- Fedora: `~/.gemini/config/skills` and legacy
  `~/.gemini/antigravity/skills` (Antigravity only)

| Skill | Purpose |
|---|---|
| `chrome-osascript-debug` | Drive the user’s real Chrome (SSO sessions) via AppleScript (macOS) |
| `review-github-pr` | Fetch PR diffs/comments and leave pending review comments |
| `split` | Split a large branch into stacked logical PRs |

**Work skills are never vendored** here (`vcode-sdlc-*`, `k8s-mysql`, plugin caches). The deploy script only manages symlinks that point back at `~/.config/skills`. Extra IDE targets: `SKILL_TARGETS_EXTRA=... chezmoi apply`.

Policy detail: [`docs/DECISION.md`](docs/DECISION.md) §6.

### Agent rules (profile-gated)

| Profile | Rule | Deployed to |
|---|---|---|
| Work | `dot_config/rules/commit-pr-jira.mdc` | macOS: Cursor `.mdc` + Claude command/block; Fedora: Antigravity `GEMINI.md` block |
| Personal | `dot_config/rules/personal-commits.mdc` | Same OS-specific targets; Conventional Commits style **without** Jira |

Inactive rule is removed on converge.

---

## 8. Debugging & health checks

### First stop: `dotfiles-doctor`

```bash
dotfiles-doctor
```

Checks profile, chezmoi install/source/drift, mise, package backends, scheduler (enables if missing), `gh` auth when needed, and reads the update log/status. Interactive TTY: choose **[a]pply** / **[r]e-add** / **[s]kip** for drift. Non-interactive: reports only (exit `1` if unfinished).

### Symptom → action

| Symptom | What to try |
|---|---|
| Shell looks wrong / old aliases | `chezmoi apply` then `reload`. Confirm Ghostty + zsh (or your intended shell). |
| Tool missing (`rg`, `bat`, `gh`, …) | `mise install` / `mise upgrade`. Confirm entry in `dot_config/mise/config.toml.tmpl`. |
| System package *and* mise both ship the same CLI | Expected to be cleaned by `run_onchange_after_15`. Re-apply; never add banned tools to package TOMLs. |
| `chezmoi status` dirty | Doctor → apply (repo wins) or re-add (home wins). Don’t leave managed files dirty. |
| Weekly update skipped / stale | Force: `dotfiles-auto-update --force`. Log: `~/.local/share/dotfiles-update.log`. Host scheduler notes in MANUAL / FEDORA. |
| Hand-installed app flagged as EXTRA | Add it to the right TOML (or MDM.md) then `dotfiles-sync`, or uninstall and re-apply. |
| IDE keys / skills / rules stale | Edit the source under `dot_config/` and `chezmoi apply` (hash lines re-trigger scripts 30/35/36). |
| Terminal / GUI missing | Check the OS backend section in the package TOMLs and re-run the dispatcher via `chezmoi apply`. |
| Work tools on personal (or reverse) | Check `~/.config/chezmoi/chezmoi.toml` → `is_work` / `install_intellij`. Doctor prints the profile. |
| Installer polluted `~/.zshrc` | Move the snippet to `~/.zsh_local`, then `chezmoi apply` to restore the managed file. |

### Useful inspection commands

```bash
chezmoi data                    # rendered template data (is_work, …)
chezmoi doctor                  # chezmoi’s own diagnostics
mise ls                         # installed tools + versions
mise doctor
dotfiles-sync --check           # manifest + chezmoi drift report
tail -f ~/.local/share/dotfiles-update.log
cat ~/.local/share/dotfiles-update.status
```

---

## 9. Local development & testing

Clone / edit in the chezmoi source directory (usually `~/.local/share/chezmoi`, or this repo if you `chezmoi init`’d from a working copy). Prefer editing via `chezmoi edit` or in the source tree, then `chezmoi apply`.

### Run tests (no installs for the hot path)

Python 3.11+ stdlib only for correctness:

```bash
python3 -m unittest discover -s tests/unit          # ~0.2s
python3 -m unittest discover -s tests/integration   # real chezmoi + stubbed package managers / mise / gh
./tests/smoke/docker-run.sh personal                # slow: real Fedora install smoke (also weekly in CI)
```

### Lint / format / coverage (opt-in locally; required in CI)

```bash
# Shell (shipped CLIs)
shellcheck -S warning dot_local/bin/dotfiles-{sync,auto-update,doctor}
shfmt -i 2 --diff   dot_local/bin/dotfiles-{sync,auto-update,doctor}

# Python tests
pip install -r tests/requirements.txt
ruff check tests/ && ruff format --check tests/

# 100% line+branch on tests/lib/repo.py (policy mirror)
coverage run -m unittest discover -s tests/unit
coverage report --fail-under=100 --show-missing
```

### Layout

| Path | Role |
|---|---|
| `tests/lib/repo.py` | Policy in testable Python (mise bans, profile merge, drift). **100% coverage gated.** |
| `tests/unit/` | Manifests, mise template, chezmoi gates, aliases, Ghostty, workflows, scripts |
| `tests/integration/test_converge.py` | Render + execute converge path for work vs personal (backends stubbed) |
| `tests/smoke/` | Real Fedora `chezmoi apply` + binary checks (personal + work) |

Full guide: [`docs/TESTING.md`](docs/TESTING.md). Feature matrix: [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md).

### Shipped helper CLIs

| Binary | Role |
|---|---|
| `dotfiles-doctor` | Interactive verify + safe fixes |
| `dotfiles-sync` | Diff machine vs manifests; optional PR for drift |
| `dotfiles-auto-update` | Unattended weekly upgrade + sync check |

---

## 10. GitHub Actions

| Workflow | Trigger | Job |
|---|---|---|
| [`.github/workflows/tests.yml`](.github/workflows/tests.yml) | PR / push `main` | **unit**, **coverage** (100% on `tests/lib`), **lint**, **integration** across current CI hosts |
| [`.github/workflows/manifest-lint.yml`](.github/workflows/manifest-lint.yml) | PR touching packages/mise | Fails if banned tools (`node`, `python`, `java`, `kubectl`, `gum`, `gh`, …) appear outside mise |
| [`.github/workflows/brew-mise-audit.yml`](.github/workflows/brew-mise-audit.yml) | Weekly + manual | Upstream package / mise drift; may open an audit PR |
| [`.github/workflows/smoke.yml`](.github/workflows/smoke.yml) | Weekly (Thu) + manual | Real Fedora install smoke × `{personal, work}` |

CI does **not** mutate your machines. Local hand-install → repo is `dotfiles-sync`’s job. Upstream bumps → weekly audit PR. As Windows lands, expect a winget-aware job beside the existing matrix — not a separate product.

---

## 11. Adding software

**Rule zero:** if `mise search <name>` finds it → `dot_config/mise/config.toml.tmpl`. No system-package copies. Guard script + CI enforce this.

Quick branches (full flowchart: [`docs/DECISION.md`](docs/DECISION.md)):

1. **mise tool** → mise config (optionally `{{ if .is_work }}` like kubectl).
2. **GUI / OS package** → `shared.toml` or profile TOML, under the backend(s) that should install it (`[brew]`/`[cask]`, `[dnf]`/`[flatpak]`, `[winget]`, …). Declare every OS you care about in one PR when the tool is shared.
3. **No mise backend yet** → system backend with a comment explaining why; move to mise when a backend lands.
4. **MDM / company** → [`docs/MDM.md`](docs/MDM.md) only — never manifests.
5. **Personal skill** → `dot_config/skills/<name>/SKILL.md`.
6. **Commit/agent rule** → `dot_config/rules/*.mdc` (work vs personal gating in `run_onchange_after_36-rules`).

Then push, and on each machine: `chezmoi update -v`. Manifest hashes re-trigger install automatically.

---

## Included source → home map

| Source | Deploys to | What |
|---|---|---|
| `dot_zshrc.tmpl` | `~/.zshrc` | Unified zsh (Starship, zinit, mise, Atuin, work gates) |
| `dot_zsh_aliases` | `~/.zsh_aliases` | GUI launcher + Rust-tool aliases |
| `dot_config/starship.toml` | `~/.config/starship.toml` | Prompt |
| `dot_config/mise/config.toml.tmpl` | `~/.config/mise/config.toml` | Runtimes + CLIs (cross-OS) |
| `dot_config/ghostty/config` | `~/.config/ghostty/config` | GPU terminal |
| `dot_config/atuin/config.toml` | `~/.config/atuin/config.toml` | History DB UI |
| `dot_config/ide/keybindings.json` | IDE User dirs | Ctrl-first keys |
| `dot_config/skills/*` | `~/.config/skills` + IDE symlinks | Personal agent skills |
| `dot_config/rules/*.mdc` | macOS Cursor/Claude; Fedora Antigravity | Profile-gated commit rules |
| `dot_config/packages/*.toml` | (via dispatcher) | System packages by profile + OS backend |
| `dot_local/bin/dotfiles-*` | `~/.local/bin/` | Doctor, sync, auto-update |
