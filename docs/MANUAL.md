# Manual-install lists (apps you install YOURSELF, outside dotfiles)

Everything installable from code lives in `dot_config/packages/*.toml`
(system apps) and `dot_config/mise/config.toml.tmpl` (runtimes + CLIs).
This file lists what cannot be automated and must be installed by hand.

## Work Mac (MDM-assisted)

1. Enroll the Mac and install **Intelligent Hub / Company Portal** first.
2. From Company Portal, install everything in [MDM.md](MDM.md):
   Slack, Zoom, Rancher Desktop, Beyond Identity, PingID, Zscaler,
   Falcon, CyberArk EPM, DisplayLink, EON, UNIXi Security.
3. Sign into Slack (work workspace) and Zoom (work SSO).
4. Start Rancher Desktop once so the `docker` CLI from brew has a daemon.
5. Run `chezmoi init --apply <repo-url>` (answer `is_work = yes`).
6. Verify: `dotfiles-sync --check` should report clean; anything it flags
   as EXTRA-BREW either belongs in `work.toml` or in [MDM.md](MDM.md).

## Personal Fedora (fully manual)

1. Install Fedora Workstation from USB, enable third-party/RPM Fusion
   repositories, and run GNOME Software updates once.
2. Install Ghostty prerequisites if the COPR build fails (the dispatcher
   normally handles Ghostty via COPR; see [FEDORA.md](FEDORA.md)).
3. Firmware/drivers that dnf cannot own (e.g. Lenovo/ThinkPad firmware
   via GNOME Firmware, Bluetooth/Wi-Fi quirks) stay manual.
4. Run `chezmoi init --apply <repo-url>` (answer `is_work = no`).
5. Sign into Firefox Sync, Slack (personal, if ever needed), and Zoom
   (only if you add them back to `personal.toml`; they are work tools
   and intentionally absent today).
6. Docker Engine, Compose, and Buildx are installed from Docker's official
   DNF repository by the dispatcher. It also enables `docker.service`; run
   Docker with `sudo` unless you deliberately add your user to the `docker`
   group (which grants root-equivalent access).

## How update results reach you

- Desktop toast after every weekly run (Notification Center on macOS,
  `notify-send` on Fedora). The toast says when drift was found.
- Full log: `~/.local/share/dotfiles-update.log` (`tail -f` it).
- Last-run summary: `~/.local/share/dotfiles-update.status` (now includes
  a `drift=` line: `clean`, `drift-detected`, or `drift-pr-opened`).
- Upstream bumps arrive as GitHub PRs from the weekly audit workflow
  (normal GitHub notifications apply).

## Sync runs on its own every week

Yes: each weekly `dotfiles-auto-update` run ends with `dotfiles-sync --check`.
When drift is found it is logged, flagged in the status file, and named in
the toast. It opens a PR by itself only when every guard passes: the repo
checkout has committable changes, `gh` is authed, no sync PR is already open,
and `DOTFILES_SYNC_AUTO_PR` is not `0`. Machine-side-only drift (e.g. a
hand-brewed package with no repo change) never auto-PRs — it just notifies,
and you run `dotfiles-sync` by hand after editing the manifests.

## zsh files and pollution

- `~/.zshrc`, `~/.zsh_aliases`, `~/.zprofile` are chezmoi-managed. Any local
  edit — yours or a tool installer appending an init snippet — shows up in
  `chezmoi status`, is reported by `dotfiles-sync --check` (including the
  automatic weekly one), and is reverted by the next `chezmoi apply`.
- Machine-specific shell bits belong in `~/.zsh_local` (unmanaged, sourced
  at the end of `~/.zshrc`). Same pattern as `~/.gitconfig_local`.
- If an installer pollutes `~/.zshrc`, move its snippet to `~/.zsh_local`
  (or into the repo if every machine needs it) instead of keeping a dirty
  managed file.

## When the machine was off at update time

- Fedora: the systemd timer has `Persistent=true`, so a missed run fires
  shortly after the next boot. Nothing to do.
- macOS: launchd skips calendar events while the Mac sleeps or is off.
  The plist also sets `RunAtLoad`, so the next boot/login re-invokes the
  updater, and its staleness guard (6 days) runs it only if the last run
  is stale — fresh logins are a silent no-op.
- Either way you can always run `dotfiles-auto-update` (or with `--force`
  to bypass the staleness guard) and check the status file.

## Adding new software later (Mac vs Fedora)

Repo-first (seamless): decide the profile, edit, push, then `chezmoi update`
on each machine. The dispatcher/mise scripts re-run automatically because
the manifest hashes are embedded in them.

- New Mac app, both profiles: `shared.toml` with `brew`/`cask` entry.
- New Mac app, work only: `work.toml`.
- New Fedora app: `personal.toml` (`[dnf]` for system packages,
  `[flatpak]` for desktop apps). If it exists on both OSes, declare both
  backends in `shared.toml` — chezmoi picks per OS.
- New CLI in mise registry: `dot_config/mise/config.toml.tmpl`, optionally
  work-gated like kubectl (see below).

Hand-installed first (also seamless): install it however you like, then run
`dotfiles-sync`. It reports EXTRA-BREW (Mac) / EXTRA-FLATPAK (Fedora) /
`chezmoi status` drift and opens a PR recording the change. Merge it and
every machine converges; ignore it and the next apply keeps flagging it.

Worked example — kubectl on personal Fedora: kubectl is mise-owned and
work-gated, so `chezmoi apply` on Fedora will never install it. Two paths:
(a) you need it there permanently → PR removing the `is_work` gate around
kubectl in `config.toml.tmpl` (one-line change; the mise hash re-triggers
install on all machines, work Macs see no change); (b) one-off experiment
→ `mise use -g kubectl@latest` locally, which edits the chezmoi-managed
config, shows up as drift in `dotfiles-sync`, and you either commit it or
`chezmoi apply` reverts it. Never `dnf install kubectl`: the mise-first
rule keeps one copy per tool.
