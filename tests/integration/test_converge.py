"""Integration tests: converge work/personal profiles through real chezmoi.

These tests execute the actual repo artifacts (chezmoi rendering, the
dispatcher, dotfiles-sync, dotfiles-auto-update) with stubbed package
managers, so they verify end-to-end behaviour without touching the host.

Matrix intent (see docs/TEST_PLAN.md): CI runs this file on
  macos-15 x {work, personal} and fedora container x {work, personal}.
Locally it exercises the branch matching the current OS; OS-specific
branches are skipped with a clear reason.
"""

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT
CHEZMOI = shutil.which("chezmoi")
IS_DARWIN = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

PROFILE_CONFIG = {
    "work": '[data]\nname = "IT Work"\nemail = "work@example.com"\n'
            "is_work = true\ninstall_intellij = true\n",
    "personal": '[data]\nname = "IT Personal"\nemail = "personal@example.com"\n'
                "is_work = false\ninstall_intellij = false\n",
}


def _config_for(profile: str, tmp: pathlib.Path) -> pathlib.Path:
    config = tmp / f"chezmoi-{profile}.toml"
    config.write_text(PROFILE_CONFIG[profile])
    return config


def _base_env(extra_bin: pathlib.Path) -> dict:
    # Put the CURRENT python first: sync/dispatcher embed `python3`, and a
    # bare /usr/bin/python3 shim may be broken inside CI images.
    py_bin = os.path.dirname(sys.executable)
    return dict(os.environ, PATH=f"{extra_bin}{os.pathsep}{py_bin}{os.pathsep}/usr/bin:/bin")


def render_script(profile: str, source_relpath: str) -> str:
    """Render a source-state script template (run_*, not deployed to HOME)."""
    if CHEZMOI is None:
        raise unittest.SkipTest("chezmoi not available")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-it-"))
    config = _config_for(profile, tmp)
    proc = subprocess.run(
        [CHEZMOI, "--config", str(config), "--source", str(REPO),
         "execute-template", "--file", source_relpath],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO),
    )
    if proc.returncode != 0:
        raise AssertionError(f"execute-template {source_relpath} ({profile}): {proc.stderr}")
    return proc.stdout


def render(profile: str, home_target: str) -> str:
    """Render a destination path through real chezmoi for a profile."""
    if CHEZMOI is None:
        raise unittest.SkipTest("chezmoi not available")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-it-"))
    home = tmp / "home"
    home.mkdir()
    config = _config_for(profile, tmp)
    proc = subprocess.run(
        [CHEZMOI, "--config", str(config), "--source", str(REPO),
         "--destination", str(home), "cat", str(home / home_target.lstrip("/"))],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise AssertionError(f"chezmoi cat {home_target} ({profile}): {proc.stderr}")
    return proc.stdout


def write_stub(bin_dir: pathlib.Path, name: str, body: str) -> None:
    path = bin_dir / name
    path.write_text("#!/usr/bin/env bash\n" + body + "\n")
    path.chmod(0o755)


class ChezmoiWorkProfileTest(unittest.TestCase):
    """Work assumptions rendered through real chezmoi (both profiles)."""

    def test_mise_kubectl_work_only(self) -> None:
        self.assertIn("kubectl", render("work", ".config/mise/config.toml"))
        self.assertNotIn("kubectl", render("personal", ".config/mise/config.toml"))

    def test_git_credential_helper_personal_only(self) -> None:
        self.assertNotIn("gh auth git-credential", render("work", ".gitconfig"))
        self.assertIn("gh auth git-credential", render("personal", ".gitconfig"))

    def test_zshrc_rancher_block_work_only(self) -> None:
        self.assertIn("RANCHER DESKTOP", render("work", ".zshrc"))
        self.assertNotIn("RANCHER DESKTOP", render("personal", ".zshrc"))

    def test_dispatcher_overlay_per_profile(self) -> None:
        work = render_script("work", "run_onchange_after_10-install-packages.sh.tmpl")
        personal = render_script("personal", "run_onchange_after_10-install-packages.sh.tmpl")
        self.assertIn('OVERLAY="$SRC_DIR/work.toml"', work)
        self.assertIn('OVERLAY="$SRC_DIR/personal.toml"', personal)

    def test_ide_keys_intellij_gated(self) -> None:
        work = render_script("work", "run_onchange_after_30-ide-keys.sh.tmpl")
        personal = render_script("personal", "run_onchange_after_30-ide-keys.sh.tmpl")
        self.assertIn("DarculaCopy.xml", work)
        self.assertIn("skipping IntelliJ keymap", personal)

    def test_launchd_plist_renders_home(self) -> None:
        out = render("work", "Library/LaunchAgents/com.dotfiles.update.plist")
        self.assertIn("dotfiles-auto-update", out)
        self.assertNotIn("{{", out)


class DispatcherExecutionTest(unittest.TestCase):
    """Execute the RENDERED dispatcher with logging stub package managers."""

    def _run_dispatcher(self, profile: str) -> str:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-disp-"))
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        log = tmp / "calls.log"
        write_stub(bin_dir, "brew", f'echo "brew $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "dnf", f'echo "dnf $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "flatpak", f'echo "flatpak $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "sudo", 'exec "$@"')
        rendered = render_script(profile, "run_onchange_after_10-install-packages.sh.tmpl")
        script = tmp / "dispatcher.sh"
        script.write_text(rendered)
        env = _base_env(bin_dir)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        proc = subprocess.run(["bash", str(script)], capture_output=True,
                              text=True, timeout=120, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return log.read_text() if log.exists() else ""

    def test_work_dispatches_work_packages(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/cask dispatch branch needs macOS")
        calls = self._run_dispatcher("work")
        self.assertIn("awscli", calls)
        self.assertIn("intellij-idea", calls)

    def test_personal_dispatch_does_not_install_work_packages(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/cask dispatch branch needs macOS")
        calls = self._run_dispatcher("personal")
        self.assertNotIn("awscli", calls)
        self.assertNotIn("intellij-idea", calls)

    def test_fedora_dispatches_dnf_packages(self) -> None:
        if not IS_LINUX:
            self.skipTest("dnf/flatpak dispatch branch needs Linux")
        calls = self._run_dispatcher("personal")
        self.assertIn("neovim", calls)


class SyncCheckTest(unittest.TestCase):
    """Run the real dotfiles-sync --check with stubbed host commands."""

    def _run_sync(self, *, extra_brew: str = "", extra_flatpak: str = "") -> subprocess.CompletedProcess:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-sync-"))
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        write_stub(bin_dir, "chezmoi", 'if [ "$1" = "status" ]; then exit 0; fi\nexit 0')
        brews = "git\nduti\ntealdeer\ndocker\ndocker-completion\nprotobuf\nawscli\nmysql" + extra_brew
        write_stub(bin_dir, "brew",
                   f'if [ "$1 $2" = "list --formula" ]; then printf "{brews}\\n"; exit 0; fi\n'
                   'if [ "$1 $2" = "list --cask" ]; then printf "ghostty\\nvisual-studio-code\\ncursor\\nwindsurf\\n'
                   'font-jetbrains-mono-nerd-font\\nfont-meslo-lg-nerd-font\\nfirefox\\ngoogle-chrome\\n'
                   'intellij-idea\\njetbrains-toolbox\\npostman\\n"; exit 0; fi\nexit 0')
        write_stub(bin_dir, "flatpak",
                   'if [ "$1" = "list" ]; then printf "Application\\norg.mozilla.firefox\\n'
                   f'{extra_flatpak}"; exit 0; fi\nexit 0')
        write_stub(bin_dir, "mise", 'if [ "$1" = "outdated" ]; then exit 0; fi\nexit 0')
        env = _base_env(bin_dir)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        return subprocess.run(
            ["bash", str(REPO / "dot_local/bin/dotfiles-sync"), "--check"],
            capture_output=True, text=True, timeout=60, env=env)

    def test_clean_machine_reports_no_drift(self) -> None:
        proc = self._run_sync()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("no drift detected", proc.stdout)

    def test_extra_package_reports_drift(self) -> None:
        if IS_DARWIN:
            proc = self._run_sync(extra_brew="\nhand-brewed-pkg")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("EXTRA-BREW", proc.stdout)
            self.assertIn("hand-brewed-pkg", proc.stdout)
        elif IS_LINUX:
            proc = self._run_sync(extra_flatpak="\ncom.example.HandInstalled")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("EXTRA-FLATPAK", proc.stdout)
        else:
            self.skipTest("unsupported OS for drift test")


class AutoUpdateTest(unittest.TestCase):
    """Run the real auto-update with stubs: staleness guard + status file."""

    def _run_auto_update(self, args: list[str], status_body: str | None) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-auto-"))
        fake_home = tmp / "home"
        (fake_home / ".local/share").mkdir(parents=True)
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        for name in ("brew", "mise", "flatpak", "dnf", "osascript", "notify-send"):
            write_stub(bin_dir, name, "exit 0")
        write_stub(bin_dir, "dotfiles-sync", "echo sync-check-ok\nexit 0")
        if status_body is not None:
            (fake_home / ".local/share/dotfiles-update.status").write_text(status_body)
        env = _base_env(bin_dir)
        env["HOME"] = str(fake_home)
        proc = subprocess.run(
            ["bash", str(REPO / "dot_local/bin/dotfiles-auto-update"), *args],
            capture_output=True, text=True, timeout=120, env=env)
        return proc, fake_home

    def test_fresh_status_skips_without_force(self) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        proc, home = self._run_auto_update([], f"last_run={now}\nresult=ok\ndrift=clean\n")
        self.assertEqual(proc.returncode, 0)
        # NOTE: auto-update redirects all output to the log file
        # (exec >>"$LOG"), so assert on the log, not stdout.
        log = (home / ".local/share/dotfiles-update.log").read_text()
        self.assertIn("fresh", log)

    def test_force_runs_and_writes_clean_status(self) -> None:
        proc, home = self._run_auto_update(["--force"], None)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        status = (home / ".local/share/dotfiles-update.status").read_text()
        self.assertIn("result=ok", status)
        self.assertIn("drift=clean", status)
        self.assertTrue((home / ".local/share/dotfiles-update.log").exists())


if __name__ == "__main__":
    unittest.main()
