# Fedora (personal) notes

This machine is owned by you. Scaffolding is in place; package names are yours
to finalize in `dot_config/packages/personal.toml` ([dnf] / [flatpak]).

- Converge: `chezmoi update -v` (dispatcher installs dnf + flatpak + mise).
- Ghostty: installed from the `ghostty/ghostty` COPR by the dispatcher when
  missing. Same `dot_config/ghostty/config` as macOS, including Ctrl-C
  copy-or-interrupt and Shift+Insert paste parity.
- Auto-update: `systemd --user enable --now dotfiles-update.timer`
  (also enabled once by `run_once_after_40-enable-schedulers`). GNOME Software
  still owns unattended OS/flatpak upgrades; the timer keeps mise + flatpak
  CLIs in sync and only notifies for dnf.
- Local drift PRs: run `dotfiles-sync` after hand-installing anything; it
  diffs manifests and opens a PR via `gh`.
- Docker on Fedora (Engine + Desktop) was in the old `install.sh` and is
  intentionally not ported: add it to `personal.toml` when you want it back.
