# MDM / company-provided apps (NOT managed by dotfiles)

These arrive via Workspace ONE / Company Portal / IT push. Never add them to
`dot_config/packages/*.toml`. This list exists so a fresh work Mac can be
verified against MDM after `chezmoi apply`.

- Beyond Identity
- Company Portal (Workspace ONE Intelligent Hub)
- CyberArk EPM
- DisplayLink Manager
- Falcon (CrowdStrike Endpoint Security)
- PingID
- Zscaler (ZIA cert store; note the ZIA profile.d sourcing in dotfiles is work-gated)
- EON, UNIXi Security
- Intuit Developer Desktop App, Intuit API Client Desktop
- Rancher Desktop (work-provided daemon backing the brew `docker` CLI)
- Slack (work workspace via Intelligent Hub, not brew)
- Zoom (work-licensed via Intelligent Hub, not brew)
- Microsoft Edge / Excel / Outlook (company-licensed; personal alternatives are
  Firefox / Chrome in shared.toml)
- eiamcli, gnupg tooling pushed to the brew Cellar by IT (left untouched by
  the mise guard script)

If IT renames or adds an agent, update this file in the same PR.
