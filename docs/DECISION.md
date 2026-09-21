# Where does a new app go? Decision flowchart for all future installs.
# Rule zero: if mise can install it, it MUST be mise. No exceptions, no brew/dnf copies.

# 1. Run: mise search <name>  (or: mise registry | grep -i <name>)
#    Found? -> add to dot_config/mise/config.toml.tmpl under [tools], backend stays mise.
#    This covers: node, python, java, rust, dart, go, kubectl, gum, gh, and every
#    Rust CLI (ripgrep, bat, fd, eza, delta, dust, duf, fzf, zoxide, lazygit,
#    lazydocker, gping, bottom, atuin, yazi, starship, uv, procs, tokei).
#
# 2. Not in mise? Is it a GUI app or Mac-native service?
#    Yes -> generic manifests:
#      macOS: dot_config/packages/shared.toml or work.toml [cask] / [brew]
#      Fedora: [dnf] / [flatpak]  |  Windows: [winget]
#    Examples: ghostty, vscode, cursor, windsurf, fonts, postman,
#    intellij-idea (work only), docker CLI, duti.
#    (slack, zoom, rancher-desktop are MDM-provided, never in manifests.)
#
# 3. Not in mise and not GUI? Is it a brew-only formula with no mise backend?
#    Examples today: awscli, protobuf, tealdeer (arm64 gap), mysql (work).
#    -> generic manifests [brew] with a comment explaining WHY it cannot be mise.
#    When the mise backend lands, move it and delete the brew entry.
#
# 4. Never do these:
#    - Never list transitive brew deps (openssl, sqlite, icu4c, xz, zstd, ...).
#      Brew resolves them. Listing them freezes upgrades and breaks `brew bundle`.
#    - Never add node / python / java / kubectl / gum / gh via brew, dnf, or
#      winget. The guard script (run_onchange_after_15-enforce-mise) uninstalls
#      them and CI (manifest-lint) fails the PR.
#    - Never `brew install` / `dnf install` / `flatpak install` by hand without
#      running dotfiles-sync afterwards. It reports EXTRA-BREW / EXTRA-FLATPAK
#      drift and opens the reconciling PR.
#
# 5. Profile-gated tools (kubectl, IntelliJ today): gated with
#    {{ if .is_work }} in the mise config / deploy scripts. To promote one to
#    shared, delete the gate (one-line PR); the embedded hashes re-trigger
#    install everywhere. See docs/MANUAL.md for the kubectl-on-Fedora example.
#
# Banned backends (enforced by guard + CI):
#   node, python, python@3.13, java, kubectl, kubernetes-cli, gum, gh
#   must resolve to backend=mise. Brew python as a hidden dependency of
#   awscli/mysql is fine because it is never declared in a manifest.
#
# arm64 (M4) note: every mise tool in config.toml ships an arm64 prebuild
# except cargo:procs and cargo:tokei, which compile from source on first
# install (arm64-safe). tealdeer is the single documented brew exception
# until its mise arm64 binary exists.
