"""Unit tests: shell scripts (syntax + policy assertions via static analysis).

Runs `bash -n` on every script and asserts the key policy strings that
integration tests then execute with stubbed package managers:
  - dispatcher profile selection, iterm2 removal, COPR ghostty, winget
  - enforce-mise guard list matches BANNED set minus casks
  - dotfiles-sync drift/PR behaviour and --check flag
  - auto-update staleness guard, greedy brew, drift states, notifications
"""

import shutil
import subprocess
import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT

SCRIPTS = [
    "run_once_before_00-bootstrap.sh.tmpl",
    "run_onchange_after_10-install-packages.sh.tmpl",
    "run_onchange_after_15-enforce-mise.sh.tmpl",
    "run_onchange_after_20-mise-install.sh.tmpl",
    "run_onchange_after_30-ide-keys.sh.tmpl",
    "run_once_after_40-enable-schedulers.sh.tmpl",
    "dot_local/bin/dotfiles-sync",
    "dot_local/bin/dotfiles-auto-update",
    "dot_local/bin/dotfiles-doctor",
]


def read(path: str) -> str:
    return (REPO / path).read_text()


class ShellSyntaxTest(unittest.TestCase):
    def test_bash_n_passes_for_all_scripts(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        for script in SCRIPTS:
            text = read(script)
            # Strip the chezmoi first line for .tmpl files (not valid bash).
            body = "\n".join(
                line for line in text.splitlines()
                if not line.lstrip().startswith("# {{")
            )
            proc = subprocess.run(
                [bash, "-n"],
                input=body,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(
                proc.returncode, 0, f"{script} failed bash -n: {proc.stderr}"
            )

    def test_all_scripts_set_strict_mode(self) -> None:
        for script in SCRIPTS:
            text = read(script)
            # dotfiles-auto-update intentionally omits -e: it runs
            # unattended under launchd/systemd and every step has
            # `|| true`, so one failing updater must not abort the rest.
            self.assertIn("pipefail", text, script)
            if script.endswith("dotfiles-auto-update"):
                self.assertIn("set -uo pipefail", text, script)
            else:
                self.assertIn("set -euo pipefail", text, script)

    def test_scripts_have_shebang(self) -> None:
        for script in SCRIPTS:
            self.assertTrue(
                read(script).startswith("#!/usr/bin/env bash"), script
            )


class DispatcherScriptTest(unittest.TestCase):
    TEXT = read("run_onchange_after_10-install-packages.sh.tmpl")

    def test_reruns_on_manifest_hash(self) -> None:
        self.assertIn("shared.toml", self.TEXT)
        self.assertIn("work.toml", self.TEXT)
        self.assertIn("personal.toml", self.TEXT)
        self.assertIn("sha256sum", self.TEXT)

    def test_selects_overlay_by_is_work(self) -> None:
        self.assertIn(".is_work", self.TEXT)
        self.assertIn("OVERLAY", self.TEXT)

    def test_src_dir_points_at_packages_subdir(self) -> None:
        # Regression: CHEZMOI_SOURCE_DIR is the source root, so the
        # packages subdir must be appended (the fallback already does).
        self.assertIn("CHEZMOI_SOURCE_DIR", self.TEXT)
        self.assertIn("/dot_config/packages", self.TEXT)

    def test_empty_backend_lists_cannot_fail(self) -> None:
        # grep finds nothing -> exit 1 -> pipefail would kill the script.
        self.assertIn("done || true", self.TEXT)

    def test_removes_iterm2(self) -> None:
        self.assertIn("iterm2", self.TEXT)

    def test_fedora_copr_ghostty(self) -> None:
        self.assertIn("ghostty/ghostty", self.TEXT)

    def test_flatpak_flathub_ensured(self) -> None:
        self.assertIn("flathub", self.TEXT)

    def test_winget_branch_exists(self) -> None:
        self.assertIn("winget", self.TEXT)


class EnforceMiseScriptTest(unittest.TestCase):
    TEXT = read("run_onchange_after_15-enforce-mise.sh.tmpl")

    def test_banned_list_matches_repo_policy(self) -> None:
        for formula in repo.GUARD_BANNED_FORMULAE:
            self.assertIn(formula, self.TEXT, f"guard missing {formula}")

    def test_reruns_on_mise_hash(self) -> None:
        self.assertIn("config.toml.tmpl", self.TEXT)
        self.assertIn("sha256sum", self.TEXT)

    def test_darwin_only(self) -> None:
        self.assertIn("Darwin", self.TEXT)

    def test_warns_about_hidden_python(self) -> None:
        self.assertIn("python@3.13", self.TEXT)


class SyncScriptTest(unittest.TestCase):
    TEXT = read("dot_local/bin/dotfiles-sync")

    def test_check_flag_supported(self) -> None:
        self.assertIn("--check", self.TEXT)

    def test_reports_chezmoi_drift(self) -> None:
        self.assertIn("chezmoi status", self.TEXT)

    def test_reports_extra_brew_and_flatpak(self) -> None:
        self.assertIn("EXTRA-BREW", self.TEXT)
        self.assertIn("EXTRA-FLATPAK", self.TEXT)

    def test_reports_mise_outdated(self) -> None:
        self.assertIn("mise outdated", self.TEXT)

    def test_opens_pr_with_gh(self) -> None:
        self.assertIn("gh pr create", self.TEXT)

    def test_transitive_allowlist_mirrors_lib(self) -> None:
        for dep in ("openssl@3", "sqlite", "xz", "zstd", "readline"):
            self.assertIn(dep, self.TEXT, f"sync missing transitive {dep}")


class AutoUpdateScriptTest(unittest.TestCase):
    TEXT = read("dot_local/bin/dotfiles-auto-update")

    def test_staleness_guard(self) -> None:
        self.assertIn("STALE_DAYS=6", self.TEXT)
        self.assertIn("--force", self.TEXT)

    def test_greedy_brew_upgrade(self) -> None:
        self.assertIn("brew upgrade --greedy", self.TEXT)

    def test_mise_upgrade_and_prune(self) -> None:
        self.assertIn("mise upgrade", self.TEXT)
        self.assertIn("mise prune", self.TEXT)

    def test_dnf_notify_only(self) -> None:
        self.assertIn("dnf check-update", self.TEXT)
        self.assertNotIn("dnf upgrade", self.TEXT)

    def test_drift_states_written(self) -> None:
        for state in ("clean", "drift-detected", "drift-pr-opened"):
            self.assertIn(state, self.TEXT, f"missing drift state {state}")

    def test_desktop_notifications(self) -> None:
        self.assertIn("osascript", self.TEXT)
        self.assertIn("notify-send", self.TEXT)

    def test_sync_auto_pr_guards(self) -> None:
        self.assertIn("DOTFILES_SYNC_AUTO_PR", self.TEXT)
        self.assertIn("gh auth token", self.TEXT)

    def test_status_file_fields(self) -> None:
        self.assertIn("last_run=", self.TEXT)
        self.assertIn("drift=", self.TEXT)


class BootstrapSchedulerScriptTest(unittest.TestCase):
    def test_bootstrap_installs_brew_mise_zinit(self) -> None:
        text = read("run_once_before_00-bootstrap.sh.tmpl")
        self.assertIn("Homebrew", text)
        self.assertIn("mise.run", text)
        self.assertIn("zinit", text)

    def test_bootstrap_installs_nerd_fonts_linux(self) -> None:
        text = read("run_once_before_00-bootstrap.sh.tmpl")
        self.assertIn("NerdFonts", text)
        self.assertIn("JetBrainsMono", text)

    def test_scheduler_enables_launchd_and_systemd(self) -> None:
        text = read("run_once_after_40-enable-schedulers.sh.tmpl")
        self.assertIn("launchctl", text)
        self.assertIn("dotfiles-update.timer", text)

    def test_scheduler_verifies_loudly(self) -> None:
        # Install steps own correctness: enable must be followed by a
        # verification that fails the run instead of swallowing errors.
        text = read("run_once_after_40-enable-schedulers.sh.tmpl")
        self.assertIn("launchctl list | grep -q com.dotfiles.update", text)
        self.assertIn("systemctl --user is-enabled dotfiles-update.timer", text)
        self.assertNotIn('launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null', text)
        self.assertNotIn("systemctl --user enable --now dotfiles-update.timer 2>/dev/null", text)


class DoctorScriptTest(unittest.TestCase):
    TEXT = read("dot_local/bin/dotfiles-doctor")

    @classmethod
    def code_text(cls) -> str:
        """Doctor source minus comments and quoted strings (advice text
        may NAME mutating commands without running them)."""
        import re

        code = "\n".join(
            line for line in cls.TEXT.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        code = re.sub(r'"[^"\n]*"', '""', code)
        return re.sub(r"'[^'\n]*'", "''", code)

    def test_interactive_prompts(self) -> None:
        self.assertIn("[ -t 0 ]", self.TEXT)
        self.assertIn("read -r -p", self.TEXT)
        self.assertIn("gh auth login", self.TEXT)
        self.assertIn("chezmoi re-add", self.TEXT)
        self.assertNotIn('"$FIX"', self.TEXT)

    def test_destructive_choices_are_prompt_gated(self) -> None:
        import re

        code = self.code_text()
        raw = "\n".join(
            line for line in self.TEXT.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        lines = code.splitlines()
        raw_lines = raw.splitlines()
        # Lines inside fix_drift_*() bodies are covered by gating their
        # invocations instead (checked below).
        in_def = False
        sites = []
        for i, line in enumerate(lines):
            s = raw_lines[i].strip()
            if re.match(r"fix_drift_(apply|record)\(\)", s):
                in_def = True
                continue
            if in_def and s == "}":
                in_def = False
                continue
            if in_def:
                continue
            if (re.search(r"(?<![\w()])chezmoi (apply|re-add)\b", line)
                    or re.search(r"(?<![\w()])gh auth login\b", line)
                    or re.search(r"(?<![\w()])fix_drift_(apply|record)\b", line)):
                sites.append((i, s))
        self.assertTrue(sites, "expected prompt-gated call sites")
        for i, call in sites:
            window = "\n".join(raw_lines[max(0, i - 10):i])
            self.assertTrue(
                ("prompt_drift" in window or "ask_yes_no" in window
                 or "[ -t 0 ]" in window),
                f"ungated mutation: {call}")

    def test_scheduler_enables_itself(self) -> None:
        # No prompt, no flag: a missing scheduler is converged on the spot.
        self.assertIn("fix_scheduler", self.TEXT)
        self.assertIn("launchd job could not be enabled", self.TEXT)

    def test_evaluates_update_logs(self) -> None:
        for marker in ("dotfiles-update.log", "last_run=", "drift detected",
                       "NOT opening a PR", "stale"):
            self.assertIn(marker, self.TEXT, f"doctor ignores log evidence: {marker}")

    def test_failures_name_owner_module(self) -> None:
        self.assertIn("run_once_before_00-bootstrap", self.TEXT)
        self.assertIn("run_once_after_40-enable-schedulers", self.TEXT)

    def test_exit_code_contract(self) -> None:
        self.assertIn('[ "$fails" -eq 0 ]', self.TEXT)

    def test_severity_levels(self) -> None:
        self.assertIn("[ok]", self.TEXT)
        self.assertIn("[warn]", self.TEXT)
        self.assertIn("[fail]", self.TEXT)

    def test_covers_all_setup_areas(self) -> None:
        for area in ("profile", "chezmoi", "manifests", "mise", ".zshrc",
                     "ghostty", "keybindings", "launchd", "update.status",
                     "git identity", "gh"):
            self.assertIn(area, self.TEXT, f"doctor missing area: {area}")

    def test_profile_survives_old_configs(self) -> None:
        # Older configs predate install_intellij; detection must degrade
        # to unknown instead of erroring (no execute-template missingkey).
        self.assertIn("unknown", self.TEXT)
        self.assertNotIn("execute-template", self.code_text())


if __name__ == "__main__":
    unittest.main()
