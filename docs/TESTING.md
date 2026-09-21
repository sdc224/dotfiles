# Testing guide

How to run the suite, what "100% coverage" means here, and how the OS ×
profile matrix is covered. The full feature-by-feature plan lives in
[TEST_PLAN.md](TEST_PLAN.md).

## Run it (no installs needed)

Python 3.11+ only (we use stdlib `tomllib`). Everything else is stdlib,
so the suite runs with zero dependencies:

```bash
python3 -m unittest discover -s tests/unit        # fast: ~0.2s, 130 tests
python3 -m unittest discover -s tests/integration # slower: runs real chezmoi + scripts with stubbed package managers
```

With pytest + coverage (as CI does):

```bash
python -m pip install -r tests/requirements.txt
coverage run -m pytest tests/unit -q && coverage report --show-missing
python -m pytest tests/integration -q
```

## Layout

- `tests/lib/repo.py` — the repo's policy (mise-first bans, profile merge,
  drift math) stated once in testable Python. Mirrors `docs/DECISION.md`,
  the dispatcher, the mise guard, and `dotfiles-sync`. Coverage is measured
  on this file and gated at **100%** (`pyproject.toml`).
- `tests/unit/` — policy + static-config tests: manifests, mise template,
  chezmoi templates/gates, shell syntax + policy strings, Ghostty/Starship/
  aliases/keybindings, schedulers, workflows, `.chezmoiignore`.
- `tests/integration/test_converge.py` — executes real artifacts with stub
  `brew`/`dnf`/`flatpak`/`mise`/`gh`: chezmoi renders for `work` vs
  `personal`, the rendered dispatcher, `dotfiles-sync --check` clean + drift,
  `dotfiles-auto-update` staleness guard + status file, and
  `dotfiles-doctor` healthy/broken/scheduler/gh-required/log-evaluation
  against a fake HOME.

## What "100% coverage" means

- **Unit**: 100% line + branch coverage on `tests/lib/repo.py` (enforced by
  `coverage report --fail-under=100` in CI), plus one test per policy string
  in every script/config (if a test doesn't name it, it isn't guaranteed).
- **Integration**: every feature in [TEST_PLAN.md](TEST_PLAN.md) has at least
  one automated case on each OS branch that can run it; OS-specific branches
  skip with a reason locally and run in CI (`tests.yml` matrix:
  `macos-15`, `ubuntu-latest`, `fedora:latest` container).

## Work-profile assumptions under test

| Assumption | Unit | Integration |
|---|---|---|
| `is_work` defaults true on macOS | `test_templates` | — |
| kubectl in mise iff work | `test_mise_config` | `ChezmoiWorkProfileTest` |
| awscli/mysql/intellij work-only | `test_manifests` | `DispatcherExecutionTest` |
| gh credential helper personal-only | `test_templates` | `ChezmoiWorkProfileTest` |
| Rancher/ZIA shell block work-only | `test_templates` | `ChezmoiWorkProfileTest` |
| IntelliJ keymap iff work or flag | `test_templates` | `ChezmoiWorkProfileTest` |
| MDM apps never in manifests | `test_manifests` | — (manual verify) |

## Bugs the suite has already caught

- Dispatcher `SRC_DIR` pointed at the source root instead of
  `.../dot_config/packages` when `CHEZMOI_SOURCE_DIR` was set (empty plan +
  `grep`/`pipefail` failure). Fixed; regression test in `test_scripts.py`.
- `keybindings.json` is JSONC (leading `//` comment) — the suite parses it
  as such instead of failing on strict JSON.
- `dotfiles-auto-update` intentionally uses `set -uo` (no `-e`): it runs
  unattended and every step has `|| true`. Pinned by test.
