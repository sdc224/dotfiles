# Fedora (personal) notes

This machine is owned by you. Scaffolding is in place; package names are yours
to finalize in `dot_config/packages/personal.toml` ([dnf] / [flatpak]).

- Converge: `chezmoi update -v` (dispatcher installs dnf + flatpak + mise).
- Ghostty: installed from the `ghostty/ghostty` COPR by the dispatcher when
  missing. Same `dot_config/ghostty/config` as macOS, including Ctrl-C
  copy-or-interrupt and Shift+Insert paste parity.
- Auto-update: `systemd --user enable --now dotfiles-update.timer`
  (also enabled once by `run_once_after_40-enable-schedulers`). GNOME Software
  owns unattended DNF upgrades, including Docker Engine from Docker's official
  repository. The timer keeps mise and Flatpak CLIs in sync and reports any
  DNF updates it sees.
- Local drift PRs: run `dotfiles-sync` after hand-installing anything; it
  diffs manifests and opens a PR via `gh`.
- Docker Engine is declared in `personal.toml`. The dispatcher enables Docker's
  signed DNF repository through DNF itself (no curl installer), imports the
  Docker GPG key, installs Engine/Buildx/Compose, then enables `docker.service`.
  Repo detection uses `dnf repolist --enabled` (DNF5-safe). Sign out and back in
  after adding yourself to the `docker` group if you want non-`sudo` access.
