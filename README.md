# Dotfiles

Personal dotfiles managed with [GNU Stow](https://www.gnu.org/software/stow/).

## Structure

```
dotfiles/
├── bash/           # Bash configuration files
│   ├── .bashrc     # → ~/.bashrc
│   └── .zprofile   # → ~/.zprofile
├── starship/       # Starship prompt configuration
│   └── .config/
│       └── starship/
│           └── starship.toml  # → ~/.config/starship/starship.toml
└── zshrc/          # Zsh configuration files
    └── .zshrc      # → ~/.zshrc
```

## Setup

1. Install [GNU Stow](https://www.gnu.org/software/stow/):
   ```bash
   # macOS
   brew install stow
   
   # Ubuntu/Debian  
   sudo apt install stow
   ```

2. Clone this repository:
   ```bash
   git clone <repository-url> ~/.dotfiles
   cd ~/.dotfiles
   ```

3. Run the setup script:
   ```bash
   ./setup.sh
   ```

## Manual Stowing

You can also stow packages individually:

```bash
# Stow specific package
stow zshrc

# Stow all packages
stow bash starship zshrc
```

## Unstowing

To remove symlinks:

```bash
# Unstow specific package
stow -D zshrc

# Unstow all packages
stow -D bash starship zshrc
```
