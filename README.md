# Modern Dotfiles (Fedora & macOS)

A superfast, modern development environment managed with [chezmoi](https://www.chezmoi.io/) and [mise](https://mise.jdx.dev/). Built for speed with **Rust-based** tools.

## 🚀 Key Features

- **Prompt**: [Starship](https://starship.rs/) — A unified, blazing-fast prompt for all terminals.
- **Tool Manager**: [mise](https://mise.jdx.dev/) — Automatically manages all CLI tools and runtimes.
- **Plugins**: [zinit](https://github.com/zdharma-continuum/zinit) — Optimized with "Turbo Mode" for near-instant shell startup.
- **Smart Launcher**: Custom GUI wrapper that silences Electron/V8 noise and detaches apps from the terminal.
- **Primary Editor**: VS Code / Cursor (configured as default for all CLI operations).

## 📂 Included Files

| File | Deploys to | What |
|---|---|---|
| `dot_zshrc` | `~/.zshrc` | Unified Zsh config with Starship |
| `dot_zsh_aliases` | `~/.zsh_aliases` | Modern Rust-tool aliases (`ag`, `cat`, `ls`, etc.) |
| `dot_config/starship.toml` | `~/.config/starship.toml` | Global prompt configuration |
| `dot_config/mise/config.toml` | `~/.config/mise/config.toml` | All modern CLI tools |
| `dot_config/ghostty/config` | `~/.config/ghostty/config` | Native GPU terminal config (Dracula theme) |
| `dot_config/ide/keybindings.json` | `~/.config/ide/` | Shared keybindings (Cursor/VSCode/Windsurf) |
| `dot_config/skills/*` | `~/.config/skills/` + symlinks | Personal skills → Cursor, Claude, Antigravity |
| `dot_config/rules/*.mdc` | IDE rules dirs + globals | Commit/PR rules, work-gated (DXS) vs personal |

# 🛠️ Installation (chezmoi-native, no install script)

```bash
# Fresh machine: bootstrap + converge in one command.
# Prompts: Git name, email, is_work (defaults true on macOS, false on Linux),
# and install_intellij (defaults true on macOS).
chezmoi init --apply <your-repo-url>

# Day-to-day: pull latest and converge (packages + mise + configs).
chezmoi update -v
```

**How it converges (no `install.sh`):**
1. `run_once_before_00-bootstrap` installs only Homebrew (Mac) or dnf basics (Fedora), mise, zinit, and Nerd Fonts.
2. `run_onchange_after_10-install-packages` reads `dot_config/packages/shared.toml` plus `work.toml` (work) or `personal.toml` (personal) and installs via brew/cask (Mac), dnf/flatpak (Fedora), or winget (future Windows).
3. `run_onchange_after_15-enforce-mise` removes brew duplicates of mise-owned tools (node, python, kubectl, gum, gh).
4. `run_onchange_after_20-mise-install` runs `mise install` for all runtimes and Rust CLIs.
5. IDE keybindings/keymaps deploy via `run_onchange_after_30-ide-keys` with timestamped backups.
6. Agent skills + rules converge via `run_onchange_after_35-skills` (symlinks into Cursor, Claude, Antigravity) and `run_onchange_after_36-rules` (work-gated commit rules, personal otherwise).

Profiles: shared base always applies. Work Mac gets `work.toml` (IntelliJ, AWS, MySQL). Personal Fedora gets `personal.toml`. See `docs/DECISION.md` before adding any new app.

## 📄 Guides

- `docs/MANUAL.md` — apps you install by hand (Intelligent Hub flow for work, Fedora checklist for personal) and how update results reach you
- `docs/MDM.md` — company-provided apps that must never enter the manifests
- `docs/FEDORA.md` — personal Fedora notes (COPR Ghostty, systemd timer, Docker)
- `docs/DECISION.md` — where a new app goes (mise-first rule + banned list)
- `docs/TESTING.md` — how to run the unit + integration suites
- `docs/TEST_PLAN.md` — OS × profile integration matrix for every feature

## 🧠 What is Atuin?

[Atuin](https://atuin.sh/) replaces your standard shell history with a SQLite database. 
- **Magical Search**: Press `Up` or `Ctrl+r` to open a full-screen, searchable history UI.
- **Smart Filters**: Search by command status, directory, or time.
- **Rust-powered**: It's incredibly fast even with millions of history entries.

## ⌨️ Common Shortcuts

### Shell Aliases
- `ag` -> Antigravity / `cr` -> Cursor
- `cat` -> `bat` (syntax highlighting)
- `ls` -> `eza` (modern icons/git status)
- `top` -> `btm` (Rust system monitor)
- `ya` -> `yazi` (Modern terminal file manager)
- `reload` -> Instantly restart your shell

## 🔄 Day-to-Day Usage

```bash
# Edit a dotfile (edits repo source, applies to home)
chezmoi edit ~/.zshrc

# Apply all dotfiles from repo to home
chezmoi apply

# Update all CLI tools via mise
mise upgrade
```

### Health check
```bash
dotfiles-doctor   # verify setup, invoke owning modules on failure, read logs
```

### Why Chezmoi instead of Stow?
`chezmoi` is more powerful than `stow` (which uses symlinks). It allows us to use **one** file for both Mac and Fedora by using templates. You don't need to manually symlink anything; `chezmoi apply` handles it all for you.
