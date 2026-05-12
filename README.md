# Modern Dotfiles (Fedora & macOS)

A superfast, modern development environment managed with [chezmoi](https://www.chezmoi.io/) and [mise](https://mise.jdx.dev/). Built for speed with **Rust-based** tools.

## 🚀 Key Features

- **Prompt**: [Starship](https://starship.rs/) — A unified, blazing-fast prompt for all terminals.
- **Multiplexer**: [Zellij](https://zellij.dev/) — A modern, user-friendly Rust-based workspace manager (replaces Tmux).
- **Tool Manager**: [mise](https://mise.jdx.dev/) — Automatically manages all CLI tools and runtimes.
- **Plugins**: [zinit](https://github.com/zdharma-continuum/zinit) — Optimized with "Turbo Mode" for near-instant shell startup.
- **Primary Editor**: VS Code / Cursor (configured as default for all CLI operations).

## 📂 Included Files

| File | Deploys to | What |
|---|---|---|
| `dot_zshrc` | `~/.zshrc` | Unified Zsh config with Starship & Zellij |
| `dot_zsh_aliases` | `~/.zsh_aliases` | Modern Rust-tool aliases (`ag`, `cat`, `ls`, etc.) |
| `dot_config/starship.toml` | `~/.config/starship.toml` | Global prompt configuration |
| `dot_config/mise/config.toml` | `~/.config/mise/config.toml` | All modern CLI tools |
| `dot_config/ide/keybindings.json` | `~/.config/ide/` | Shared keybindings (Cursor/VSCode/Windsurf) |

## 🛠️ Installation

```bash
# Clone the repo
git clone <your-repo-url> ~/Programming/dotfiles
cd ~/Programming/dotfiles

# Run the installer
./install.sh
```

**The installer will:**
1. Detect your OS (Fedora, Mac, etc.).
2. Install base dependencies (`zsh`, `git`, `curl`).
3. **Fedora**: Automate VS Code installation via official RPM repo.
4. Install `mise`, `chezmoi`, and `zinit`.
5. Apply all dotfiles and download modern CLI tools.

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

### Zellij (Workspace Manager)
Zellij is active in all main terminals. It shows its shortcuts at the bottom of the screen!
- `Ctrl + t` -> Tab management
- `Ctrl + n` -> Pane management
- `Ctrl + s` -> Search / Scroll
- `Ctrl + q` -> Detach/Quit

## 🔄 Day-to-Day Usage

```bash
# Edit a dotfile (edits repo source, applies to home)
chezmoi edit ~/.zshrc

# Apply all dotfiles from repo to home
chezmoi apply

# Update all CLI tools via mise
mise upgrade
```

### Why Chezmoi instead of Stow?
`chezmoi` is more powerful than `stow` (which uses symlinks). It allows us to use **one** file for both Mac and Fedora by using templates. You don't need to manually symlink anything; `chezmoi apply` handles it all for you.
