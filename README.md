# Dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/) and [mise](https://mise.jdx.dev/).

## What's Included

| File | Deploys to | What |
|---|---|---|
| `dot_zshrc` | `~/.zshrc` | Zsh config — P10K in iTerm, Starship in IDEs, zinit plugins |
| `dot_zprofile` | `~/.zprofile` | Login shell PATH setup |
| `dot_zsh_aliases` | `~/.zsh_aliases` | Shell aliases (eza, tmux, git, zoxide) |
| `dot_tmux.conf` | `~/.tmux.conf` | Tmux with TPM, mouse, custom splits |
| `dot_gitconfig` | `~/.gitconfig` | Git configuration |
| `dot_p10k.zsh` | `~/.p10k.zsh` | Powerlevel10k theme |
| `dot_config/starship.toml` | `~/.config/starship.toml` | Starship prompt for IDE terminals |
| `dot_config/mise/config.toml` | `~/.config/mise/config.toml` | CLI tools + language runtimes |
| `dot_config/atuin/config.toml` | `~/.config/atuin/config.toml` | Shell history search |
| `dot_config/ide/keybindings.json` | `~/.config/ide/` | Shared keybindings (Cursor/VSCode/Windsurf) |
| `dot_config/ide/cursor-settings.json` | `~/.config/ide/` | Portable Cursor settings |

## Setup (New Machine)

```bash
git clone https://github.com/schatterjee10/dotfiles.git ~/Programming/Personal/dotfiles
cd ~/Programming/Personal/dotfiles
chmod +x install.sh
./install.sh
```

This will:
1. Install Homebrew (macOS) or system packages (Linux)
2. Install chezmoi, tmux, and Nerd Fonts
3. Install mise and all CLI tools (ripgrep, bat, eza, fzf, lazygit, etc.)
4. Install zinit (zsh plugin manager) and TPM (tmux plugin manager)
5. Apply all dotfiles via chezmoi
6. Deploy shared keybindings to all installed IDEs

### After Install

- **iTerm2**: Set font to `MesloLGS NF` (Preferences > Profiles > Text > Font)
- **Tmux**: Press `Ctrl-b I` (capital I) inside tmux to install plugins
- **Shell**: Run `exec zsh` or open a new terminal

## Shell Architecture

```
┌─────────────────────────────────────────────────────┐
│  GLOBAL (all terminals)                             │
│  brew, mise, PATH, history, aliases, starship (IDE) │
├─────────────────────────────────────────────────────┤
│  iTERM-ONLY                                         │
│  tmux auto-start, P10K, zinit plugins,              │
│  fzf/zoxide shell integration, atuin, fzf-tab       │
├─────────────────────────────────────────────────────┤
│  IDE TERMINALS (Cursor, VSCode, Windsurf)           │
│  Starship prompt, fzf/zoxide, no tmux               │
└─────────────────────────────────────────────────────┘
```

## CLI Tools (managed by mise)

All tools are version-tracked in `dot_config/mise/config.toml`:

| Tool | What |
|---|---|
| `rg` (ripgrep) | Fast grep |
| `bat` | Cat with syntax highlighting |
| `fd` | Fast find |
| `eza` | Modern ls with icons |
| `delta` | Git diff viewer |
| `fzf` | Fuzzy finder |
| `zoxide` | Smart cd |
| `lazygit` | Terminal git UI |
| `lazydocker` | Terminal Docker UI |
| `starship` | Cross-shell prompt |
| `atuin` | Shell history search |
| `dust` | Disk usage viewer |
| `duf` | Disk free viewer |
| `gping` | Graphical ping |
| `btm` (bottom) | System monitor |
| `yazi` | Terminal file manager |
| `gh` | GitHub CLI |

## Tmux Keybindings

Prefix: `Ctrl-b`

| Shortcut | What |
|---|---|
| `Ctrl-b c` | New window (home dir) |
| `Ctrl-b n` | New window (current dir) |
| `Ctrl-b h` | Split horizontal (home) |
| `Ctrl-b v` | Split vertical (home) |
| `Ctrl-b -` | Split horizontal (current dir) |
| `Ctrl-b \` | Split vertical (current dir) |
| `Ctrl-b r` | Reload config |

## Day-to-Day Usage

```bash
# Edit a dotfile (edits repo source, applies to home)
chezmoi edit ~/.zshrc

# After external tool modifies a dotfile, pull changes back
chezmoi re-add ~/.zshrc

# See what's different between repo and home
chezmoi diff

# Apply all dotfiles from repo to home
chezmoi apply
```
