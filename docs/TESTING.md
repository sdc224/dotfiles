# Testing guide

How to run the suite, what "100% coverage" means here, and how the OS ×
profile matrix is covered. The full feature-by-feature plan lives in
[TEST_PLAN.md](TEST_PLAN.md).

## Run it (no installs needed)

Python 3.11+ only (we use stdlib `tomllib`). Everything else is stdlib,
so the suite runs with zero dependencies:

```bash
python3 -m unittest discover -s tests/unit        # fast: ~0.2s, 139 tests
python3 -m unittest discover -s tests/integration # slower: runs real chezmoi + scripts with stubbed package managers
```

Correctness for day-to-day work comes from those two commands. Coverage and
lint are separate, opt-in quality gates (see below).

### Smoke (real installs — periodic)

Fedora container and macOS 26 × `{personal, work}`. Smoke is **first-contact**:
it does not pre-seed converge packages. `run_once_before_00-bootstrap` owns
gcc/python3/flatpak (Linux) or Homebrew (macOS). Smoke only installs chezmoi
(needs `curl`) and applies.

```bash
# Fedora via Docker (mirrors Fedora CI)
./tests/smoke/docker-run.sh personal
./tests/smoke/docker-run.sh work

# On a real Fedora or macOS host:
PROFILE=personal bash tests/smoke/run.sh
PROFILE=work bash tests/smoke/run.sh
```

CI writes a chezmoi config (answers prompts), links the checkout to
`~/.local/share/chezmoi`, then `chezmoi apply` — it does **not** `git clone`
the workspace (GHA Fedora images lack git at checkout time).

CI (weekly Thursday + `workflow_dispatch`, not on every PR):

- [`.github/workflows/smoke.yml`](../.github/workflows/smoke.yml) — Fedora
- [`.github/workflows/smoke-macos.yml`](../.github/workflows/smoke-macos.yml) — macOS 26

## Lint + format

| Area | Linter | Formatter | Run locally |
|---|---|---|---|
| Shell scripts + templates | `shellcheck -S warning` | `shfmt -i 2` | CI `lint` job (install via `apt install shellcheck shfmt` / `brew`) |
| Python tests (`tests/`) | `ruff check` (Rust, fastest) | `ruff format` | `pip install -r tests/requirements.txt` then `ruff check tests/ && ruff format --check tests/` |

`E501` (line length) is intentionally ignored in `pyproject.toml`: the
formatter owns layout, and policy-literal `assertIn` strings cannot be
split. Lint owns correctness (`E/F/I/UP`), format owns style.

## Coverage (completeness, not correctness)

```bash
python -m pip install -r tests/requirements.txt   # coverage + ruff only
coverage run -m unittest discover -s tests/unit
coverage report --fail-under=100 --show-missing
```

No `pytest` anywhere: `coverage run -m unittest` is sufficient and keeps
the hot path dependency-free. CI runs this as a separate blocking `coverage`
job so `unit` stays fast (~0.2s, no `pip install`).

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
- `tests/smoke/` — real Fedora + macOS install smoke (`run.sh` + `verify.sh`):
  non-interactive `chezmoi apply` (config written, source linked), log scan,
  then `node -v` / package / path assertions for personal and work (no MDM).

## What "100% coverage" means

- **Unit**: 100% line + branch coverage on `tests/lib/repo.py` (enforced by
  `coverage report --fail-under=100` in CI), plus one test per policy string
  in every script/config (if a test doesn't name it, it isn't guaranteed).
- **Integration**: every feature in [TEST_PLAN.md](TEST_PLAN.md) has at least
  one automated case on each OS branch that can run it; OS-specific branches
  skip with a reason locally and run in CI (`tests.yml` matrix:
  `macos-26`, `ubuntu-24.04`, `fedora:latest` container).

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
