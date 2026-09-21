"""Shared, stdlib-only helpers that mirror repo policy.

The bash dispatcher / guard scripts implement this logic in shell; this
module re-states it in testable Python so unit tests can assert 100% of
the policy surface (mise-first, profile merge, transitive-dep ban) and
CI can measure coverage on this file. Keep in sync with:
  - docs/DECISION.md
  - run_onchange_after_10-install-packages.sh.tmpl (PLAN builder)
  - run_onchange_after_15-enforce-mise.sh.tmpl (BANNED_FORMULAE)
  - dotfiles-sync (transitive allowlist)
"""

from __future__ import annotations

import pathlib
import re
import tomllib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

PACKAGES_DIR = REPO_ROOT / "dot_config" / "packages"
MISE_TMPL = REPO_ROOT / "dot_config" / "mise" / "config.toml.tmpl"

# Tools that MUST resolve to backend=mise (docs/DECISION.md + manifest-lint.yml).
BANNED_SYSTEM_BACKENDS = frozenset(
    {
        "node",
        "python",
        "python@3.13",
        "python@3.12",
        "python@3.11",
        "java",
        "kubectl",
        "kubernetes-cli",
        "gum",
        "gh",
    }
)

# Brew formulae the dispatcher/sync scripts treat as hidden transitive deps
# (resolved by brew itself, never declared). Kept identical to the
# `transitive` set in dotfiles-sync.
TRANSITIVE_BREW_DEPS = frozenset(
    {
        "abseil",
        "brotli",
        "c-ares",
        "ca-certificates",
        "cffi",
        "cryptography",
        "gettext",
        "icu4c@77",
        "icu4c@78",
        "libnghttp2",
        "libunistring",
        "libuv",
        "lz4",
        "mpdecimal",
        "openssl@3",
        "pcre2",
        "protobuf",
        "pycparser",
        "python@3.13",
        "readline",
        "sqlite",
        "xz",
        "zlib-ng-compat",
        "zstd",
    }
)

# Formulae the enforce-mise guard actively uninstalls (brew copies owned
# by mise). Mirrors BANNED_FORMULAE in run_onchange_after_15-enforce-mise.
GUARD_BANNED_FORMULAE = (
    "node",
    "python@3.13",
    "python@3.12",
    "python@3.11",
    "kubernetes-cli",
    "gum",
)

BACKEND_SECTIONS = (
    ("brew", "brew", ("formulae",)),
    ("cask", "cask", ("casks",)),
    ("dnf", "dnf", ("packages",)),
    ("flatpak", "flatpak", ("packages",)),
    ("winget", "winget", ("packages",)),
)


def load_toml(path: pathlib.Path) -> dict:
    """Load a TOML file, returning {} when missing."""
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}


def manifest_entries(data: dict) -> dict[str, list[str]]:
    """Map backend -> declared names for one manifest dict."""
    out: dict[str, list[str]] = {}
    for _section, backend, keys in BACKEND_SECTIONS:
        items = data.get(_section, {}) or {}
        names: list[str] = []
        for key in keys:
            names.extend(items.get(key) or [])
        out[backend] = list(names)
    return out


def merged_plan(shared: dict, overlay: dict) -> list[str]:
    """Merge shared + overlay manifests into ordered backend:name lines.

    Mirrors the python block inside run_onchange_after_10 (dedup, order
    preserving, shared first).
    """
    seen: set[tuple[str, str]] = set()
    plan: list[str] = []
    for data in (shared, overlay):
        for backend, names in manifest_entries(data).items():
            for name in names:
                if (backend, name) not in seen:
                    seen.add((backend, name))
                    plan.append(f"{backend}:{name}")
    return plan


def plan_for_backend(plan: list[str], backend: str) -> list[str]:
    """Filter a merged plan to one backend's package names."""
    prefix = backend + ":"
    return [line[len(prefix) :] for line in plan if line.startswith(prefix)]


def find_bannedDeclarations(*manifests: dict) -> list[str]:
    """Return banned tool declarations outside mise (path-less)."""
    bad: list[str] = []
    for data in manifests:
        entries = manifest_entries(data)
        for backend in ("brew", "dnf", "winget"):
            for name in entries.get(backend, []):
                if name in BANNED_SYSTEM_BACKENDS:
                    bad.append(f"{backend}:{name}")
    return bad


def find_transitive_declarations(data: dict) -> list[str]:
    """Return brew entries that are hidden transitive deps (not protoc)."""
    return [
        name
        for name in manifest_entries(data).get("brew", [])
        if name in TRANSITIVE_BREW_DEPS and name != "protobuf"
    ]


def render_mise_template(text: str, *, is_work: bool) -> str:
    """Render the single is_work conditional in config.toml.tmpl.

    Only the kubectl work-gate uses templating today; everything else is
    literal. Sufficient for unit tests without invoking chezmoi.
    """
    pattern = re.compile(
        r"\{\{\s*if\s+\.is_work\s*-\}\}(.*?)\{\{\s*end\s*-\}\}", re.DOTALL
    )

    def _replace(match: re.Match[str]) -> str:
        return match.group(1) if is_work else ""

    return pattern.sub(_replace, text)


def mise_tool_names(rendered: str) -> list[str]:
    """Extract tool names from the [tools] section of rendered mise TOML."""
    in_tools = False
    names: list[str] = []
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if line.startswith("["):
            in_tools = line == "[tools]"
            continue
        if in_tools and line and not line.startswith("#") and "=" in line:
            names.append(line.split("=", 1)[0].strip().strip('"').strip("'"))
    return names


def template_has_is_work_gate(text: str) -> bool:
    """Check a chezmoi template gates on .is_work."""
    return ".is_work" in text


def extras_vs_declared(
    installed: set[str], declared: set[str], ignore: set[str] | frozenset = frozenset()
) -> list[str]:
    """Compute EXTRA-* drift (mirrors dotfiles-sync reporting)."""
    return sorted(installed - declared - set(ignore))
