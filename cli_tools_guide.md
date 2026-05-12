# Modern CLI Tools Guide

This document outlines the benefits of the modern CLI stack configured in your dotfiles.

## 🛠️ Management & Workflow
| Tool | Replacement for | Primary Benefit |
| :--- | :--- | :--- |
| **[mise](https://mise.jdx.dev/)** | `asdf`, `nvm`, `pyenv` | A single tool to manage all runtimes (Node, Python, Rust, etc.). It is significantly faster than `asdf` because it is written in Rust and handles tool versions automatically as you enter directories. |
| **[chezmoi](https://www.chezmoi.io/)** | Manual symlinks | Manages your dotfiles securely and across different machines. It allows you to use templates and keep sensitive data (like API keys) encrypted or ignored while syncing configs. |
| **[uv](https://github.com/astral-sh/uv)** | `pip`, `poetry`, `venv` | An extremely fast Python package manager and pip replacement. It's often 10-100x faster than standard tools and can manage Python versions too. |

## 🚀 Shell & Navigation
| Tool | Replacement for | Primary Benefit |
| :--- | :--- | :--- |
| **[zoxide](https://github.com/ajeetdsouza/zoxide)** | `cd` | A "smarter" cd command that learns which directories you visit most often. You can jump to a deep folder with just `z proj` instead of typing the full path. |
| **[atuin](https://atuin.sh/)** | `CTRL+R` history | Replaces your shell history with a SQLite database. It provides an interactive TUI to search history, syncs it across machines, and records exit codes and durations of commands. |
| **[fzf](https://github.com/junegunn/fzf)** | Manual searching | A general-purpose fuzzy finder. It powers interactive filtering for everything from files to git branches and shell history. |
| **[starship](https://starship.rs/)** | Standard `$PS1` | A fast, highly customizable shell prompt that shows you only the information you need (git status, package versions, battery, etc.) only when you need it. |

## 💎 Modern Core Utility Replacements
| Tool | Replacement for | Primary Benefit |
| :--- | :--- | :--- |
| **[eza](https://github.com/eza-community/eza)** | `ls` | Adds colors, file icons, git integration status, and a much better tree view (`lt` alias) to your directory listings. |
| **[bat](https://github.com/sharkdp/bat)** | `cat` | A `cat` clone with syntax highlighting, git integration (shows changes in the gutter), and automatic paging for long files. |
| **[ripgrep (rg)](https://github.com/BurntSushi/ripgrep)** | `grep` | Widely considered the fastest text search tool. It respects `.gitignore` by default and has a very intuitive syntax. |
| **[fd](https://github.com/sharkdp/fd)** | `find` | A simple, fast, and user-friendly alternative to `find`. It uses sane defaults (hidden/ignored files are skipped) and supports regex/globbing easily. |
| **[delta](https://github.com/dandavison/delta)** | `git diff` | Makes git diffs beautiful. It adds syntax highlighting within the diff, side-by-side views, and line numbers. |
| **[procs](https://github.com/dalance/procs)** | `ps` | A modern replacement for `ps` with colored output, multi-column search, and better readability of process trees. |
| **[bottom (btm)](https://github.com/ClementTsang/bottom)** | `top`, `htop` | A graphical system monitor that shows CPU, Memory, Disk, and Network usage with real-time charts in your terminal. |
| **[duf](https://github.com/muesli/duf)** | `df` | A disk usage utility that provides a user-friendly, colorful table showing your mounted drives and their remaining space. |
| **[dust](https://github.com/bootandy/dust)** | `du` | A more intuitive version of `du` that gives you a visual breakdown (a tree with bars) of what is taking up space in a directory. |

## 📺 Terminal User Interfaces (TUIs)
| Tool | Function | Primary Benefit |
| :--- | :--- | :--- |
| **[lazygit](https://github.com/jesseduffield/lazygit)** | Git UI | A simple terminal UI for git commands. It makes staging specific lines, resolving conflicts, and managing branches much faster than raw CLI commands. |
| **[lazydocker](https://github.com/jesseduffield/lazydocker)** | Docker UI | A TUI for managing docker containers, images, and volumes. You can view logs, restart containers, and prune data with single keystrokes. |
| **[zellij](https://zellij.dev/)** | Multiplexer | A modern alternative to `tmux`. It is much easier to configure, has built-in layouts/panels, and includes a "workspace" feel with tabs and plugins. |
| **[yazi](https://github.com/sxyazi/yazi)** | File Manager | An extremely fast terminal file manager with image previews and an asynchronous design that never blocks the UI. |

## 📈 Miscellaneous
*   **[gping](https://github.com/orf/gping):** Shows `ping` results as a live graph, making it easy to spot latency spikes visually.
*   **[tokei](https://github.com/XAMPPRocky/tokei):** Quickly counts lines of code across hundreds of languages, grouped by file type, while ignoring comments and blank lines.
