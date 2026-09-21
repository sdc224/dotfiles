"""Unit tests: schedulers (launchd plist, systemd units) + workflows."""

import unittest
import xml.etree.ElementTree as ET

from tests.lib import repo

REPO = repo.REPO_ROOT


def read(path: str) -> str:
    return (REPO / path).read_text()


class LaunchdTest(unittest.TestCase):
    TEXT = read("Library/LaunchAgents/com.dotfiles.update.plist.tmpl")

    def test_valid_plist_xml(self) -> None:
        rendered = self.TEXT.replace("{{ .chezmoi.homeDir }}", "/Users/test")
        root = ET.fromstring(rendered)
        self.assertEqual(root.tag, "plist")

    def test_wednesday_10am(self) -> None:
        self.assertIn("<key>Weekday</key>", self.TEXT)
        self.assertIn("<integer>3</integer>", self.TEXT)
        self.assertIn("<integer>10</integer>", self.TEXT)

    def test_run_at_load_catchup(self) -> None:
        self.assertIn("<key>RunAtLoad</key>", self.TEXT)
        self.assertIn("<true/>", self.TEXT)

    def test_invokes_auto_update(self) -> None:
        self.assertIn("dotfiles-auto-update", self.TEXT)

    def test_logs_to_update_log(self) -> None:
        self.assertIn("dotfiles-update.log", self.TEXT)


class SystemdTest(unittest.TestCase):
    def test_service_is_oneshot(self) -> None:
        text = read("dot_config/systemd/user/dotfiles-update.service")
        self.assertIn("Type=oneshot", text)
        self.assertIn("dotfiles-auto-update", text)

    def test_timer_wednesday_persistent(self) -> None:
        text = read("dot_config/systemd/user/dotfiles-update.timer")
        self.assertIn("OnCalendar=Wed 10:00", text)
        self.assertIn("Persistent=true", text)
        self.assertIn("timers.target", text)

    def test_timer_and_service_names_match(self) -> None:
        timer = read("dot_config/systemd/user/dotfiles-update.timer")
        self.assertIn("dotfiles auto-update", timer.lower())


class ManifestLintWorkflowTest(unittest.TestCase):
    TEXT = read(".github/workflows/manifest-lint.yml")

    def test_triggers_on_manifest_paths(self) -> None:
        self.assertIn("dot_config/packages/*.toml", self.TEXT)
        self.assertIn("config.toml.tmpl", self.TEXT)

    def test_banned_set_matches_lib(self) -> None:
        for tool in repo.BANNED_SYSTEM_BACKENDS:
            self.assertIn(tool, self.TEXT, f"lint missing banned {tool}")

    def test_checks_brew_dnf_winget(self) -> None:
        for backend in ("brew", "dnf", "winget"):
            self.assertIn(backend, self.TEXT)


class AuditWorkflowTest(unittest.TestCase):
    TEXT = read(".github/workflows/brew-mise-audit.yml")

    def test_weekly_wednesday_schedule(self) -> None:
        self.assertIn("cron:", self.TEXT)
        self.assertIn("* * 3", self.TEXT)

    def test_arm64_mac_runner(self) -> None:
        self.assertIn("macos-15", self.TEXT)

    def test_fedora_container_check(self) -> None:
        self.assertIn("fedora", self.TEXT.lower())

    def test_opens_update_pr(self) -> None:
        self.assertIn("create-pull-request", self.TEXT)

    def test_greedy_cask_note(self) -> None:
        self.assertIn("--greedy", self.TEXT)


class RenovateTest(unittest.TestCase):
    def test_renovate_config_valid(self) -> None:
        import json

        data = json.loads(read("renovate.json"))
        self.assertIn("extends", data)
        self.assertIn("schedule", data)

    def test_groups_github_actions(self) -> None:
        self.assertIn("github-actions", read("renovate.json"))


class TestsWorkflowTest(unittest.TestCase):
    TEXT = read(".github/workflows/tests.yml")

    def test_unit_job_runs_pytest_and_coverage(self) -> None:
        self.assertIn("tests/unit", self.TEXT)
        self.assertIn("coverage", self.TEXT)

    def test_matrix_covers_mac_and_linux(self) -> None:
        self.assertIn("macos-15", self.TEXT)
        self.assertIn("ubuntu-latest", self.TEXT)

    def test_fedora_container_job_exists(self) -> None:
        self.assertIn("fedora", self.TEXT)

    def test_integration_runs_both_profiles(self) -> None:
        self.assertIn("tests/integration", self.TEXT)

    def test_shellcheck_guards_shipped_scripts(self) -> None:
        self.assertIn("shellcheck", self.TEXT)
        self.assertIn("dotfiles-sync", self.TEXT)
        self.assertIn("dotfiles-doctor", self.TEXT)


class SmokeWorkflowTest(unittest.TestCase):
    TEXT = read(".github/workflows/smoke.yml")

    def test_scheduled_and_manual(self) -> None:
        self.assertIn("schedule:", self.TEXT)
        self.assertIn("workflow_dispatch:", self.TEXT)

    def test_fedora_matrix_both_profiles(self) -> None:
        self.assertIn("fedora:latest", self.TEXT)
        self.assertIn("personal", self.TEXT)
        self.assertIn("work", self.TEXT)
        self.assertIn("tests/smoke/run.sh", self.TEXT)

    def test_not_on_pull_request(self) -> None:
        self.assertNotIn("pull_request", self.TEXT)


if __name__ == "__main__":
    unittest.main()
