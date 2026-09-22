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
from datetime import UTC

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
    return dict(
        os.environ, PATH=f"{extra_bin}{os.pathsep}{py_bin}{os.pathsep}/usr/bin:/bin"
    )


def render_script(profile: str, source_relpath: str) -> str:
    """Render a source-state script template (run_*, not deployed to HOME)."""
    if CHEZMOI is None:
        raise unittest.SkipTest("chezmoi not available")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-it-"))
    config = _config_for(profile, tmp)
    proc = subprocess.run(
        [
            CHEZMOI,
            "--config",
            str(config),
            "--source",
            str(REPO),
            "execute-template",
            "--file",
            source_relpath,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO),
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"execute-template {source_relpath} ({profile}): {proc.stderr}"
        )
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
        [
            CHEZMOI,
            "--config",
            str(config),
            "--source",
            str(REPO),
            "--destination",
            str(home),
            "cat",
            str(home / home_target.lstrip("/")),
        ],
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
        personal = render_script(
            "personal", "run_onchange_after_10-install-packages.sh.tmpl"
        )
        self.assertIn('OVERLAY="$SRC_DIR/work.toml"', work)
        self.assertIn('OVERLAY="$SRC_DIR/personal.toml"', personal)

    def test_ide_keys_intellij_gated(self) -> None:
        work = render_script("work", "run_onchange_after_30-ide-keys.sh.tmpl")
        personal = render_script("personal", "run_onchange_after_30-ide-keys.sh.tmpl")
        self.assertIn("DarculaCopy.xml", work)
        self.assertIn("skipping IntelliJ keymap", personal)

    def test_skills_script_targets_ide_for_host_os(self) -> None:
        expected = (
            (".gemini/config/skills", ".gemini/antigravity/skills")
            if IS_LINUX
            else (".cursor/skills", ".claude/skills")
        )
        for profile in ("work", "personal"):
            out = render_script(profile, "run_onchange_after_35-skills.sh.tmpl")
            for target in expected:
                self.assertIn(target, out, f"{profile}: missing {target}")
            unexpected = (
                '"$HOME/.cursor/skills"'
                if IS_LINUX
                else '"$HOME/.gemini/config/skills"'
            )
            self.assertNotIn(unexpected, out)
            self.assertIn("vcode-sdlc-", out)
            self.assertIn("k8s-mysql", out)

    def test_rules_gated_per_profile(self) -> None:
        work = render_script("work", "run_onchange_after_36-rules.sh.tmpl")
        personal = render_script("personal", "run_onchange_after_36-rules.sh.tmpl")
        self.assertIn('ACTIVE_RULE="commit-pr-jira"', work)
        self.assertIn('ACTIVE_RULE="personal-commits"', personal)
        for out in (work, personal):
            if IS_LINUX:
                self.assertIn(".gemini/GEMINI.md", out)
                self.assertNotIn(".cursor/rules", out)
            else:
                self.assertIn(".cursor/rules", out)
                self.assertIn(".claude/commands", out)
                self.assertNotIn(".gemini/", out)
            self.assertIn("dotfiles-rules:start", out)

    def test_launchd_plist_renders_home(self) -> None:
        # Library/ is chezmoiignored on non-darwin; exercise managed cat on
        # macOS and template expansion everywhere else.
        if IS_DARWIN:
            out = render("work", "Library/LaunchAgents/com.dotfiles.update.plist")
        else:
            out = render_script(
                "work", "Library/LaunchAgents/com.dotfiles.update.plist.tmpl"
            )
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
        write_stub(
            bin_dir,
            "dnf",
            # Never claim docker-ce-stable is enabled so personal profile
            # exercises addrepo (DNF5-safe enabled-repolist check).
            f'echo "dnf $*" >> "{log}"\n'
            'if [[ "$*" == *repolist* ]]; then echo "fedora"; exit 0; fi\n'
            "exit 0",
        )
        write_stub(bin_dir, "flatpak", f'echo "flatpak $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "systemctl", f'echo "systemctl $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "rpm", f'echo "rpm $*" >> "{log}"\nexit 0')
        write_stub(bin_dir, "sudo", 'exec "$@"')
        rendered = render_script(
            profile, "run_onchange_after_10-install-packages.sh.tmpl"
        )
        script = tmp / "dispatcher.sh"
        script.write_text(rendered)
        env = _base_env(bin_dir)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        proc = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True, timeout=120, env=env
        )
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

    def test_existing_unmanaged_cask_app_skips_download(self) -> None:
        if not IS_DARWIN:
            self.skipTest("cask dispatch branch needs macOS")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-disp-cask-"))
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        log = tmp / "calls.log"
        home = tmp / "home"
        (home / "Applications/Cursor.app").mkdir(parents=True)
        write_stub(
            bin_dir,
            "brew",
            f'echo "brew $*" >> "{log}"\n'
            'if [ "$1 $2" = "list --cask" ]; then exit 1; fi\nexit 0',
        )
        rendered = render_script(
            "personal", "run_onchange_after_10-install-packages.sh.tmpl"
        )
        script = tmp / "dispatcher.sh"
        script.write_text(rendered)
        env = _base_env(bin_dir)
        env.update(CHEZMOI_SOURCE_DIR=str(REPO), HOME=str(home))
        proc = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True, timeout=120, env=env
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("install --cask cursor", log.read_text())

    def test_fedora_dispatches_dnf_packages(self) -> None:
        if not IS_LINUX:
            self.skipTest("dnf/flatpak dispatch branch needs Linux")
        calls = self._run_dispatcher("personal")
        self.assertIn("neovim", calls)
        self.assertIn("dnf config-manager addrepo --from-repofile", calls)
        self.assertIn("docker-ce", calls)
        self.assertIn("rpm --import", calls)
        self.assertIn("systemctl enable --now docker.service", calls)


class SkillsExecutionTest(unittest.TestCase):
    """Execute the RENDERED skills script against a fake HOME."""

    def _run_skills(
        self, fake_home: pathlib.Path, *, extra_env: dict | None = None
    ) -> subprocess.CompletedProcess:
        rendered = render_script("work", "run_onchange_after_35-skills.sh.tmpl")
        script = fake_home / "skills.sh"
        script.write_text(rendered)
        # Empty stub dir first on PATH: the script must resolve python-free
        # POSIX tools only, and /usr/bin/python3 on macOS is an xcrun shim
        # that must never shadow the test python.
        bin_dir = fake_home / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        env = _base_env(bin_dir)
        env["HOME"] = str(fake_home)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

    def test_links_personal_skills_into_ide_for_host_os(self) -> None:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-skills-"))
        home = tmp / "home"
        store = home / ".config/skills/split"
        (store / "scripts").mkdir(parents=True)
        (store / "SKILL.md").write_text("---\nname: split\n---\n# split\n")
        proc = self._run_skills(home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        destinations = (
            (".gemini/config/skills/split", ".gemini/antigravity/skills/split")
            if IS_LINUX
            else (".cursor/skills/split", ".claude/skills/split")
        )
        for dest in destinations:
            link = home / dest
            self.assertTrue(link.is_symlink(), f"not a symlink: {dest}")
            self.assertEqual(
                link.resolve(),
                store.resolve(),
                f"wrong target: {dest}",
            )

    def test_work_skills_and_stale_links(self) -> None:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-skills-"))
        home = tmp / "home"
        store = home / ".config/skills/split"
        store.mkdir(parents=True)
        (store / "SKILL.md").write_text("---\nname: split\n---\n")
        # Work-owned entries the script must never touch.
        intuit_target = tmp / "intuit-sql-skill"
        intuit_target.mkdir()
        cursor_skills = home / ".cursor/skills"
        cursor_skills.mkdir(parents=True)
        (cursor_skills / "k8s-mysql").symlink_to(intuit_target)
        (cursor_skills / "vcode-sdlc-build").mkdir()
        # Stale dotfiles-managed symlink pruned; user file kept as backup.
        (cursor_skills / "old-skill").symlink_to(home / ".config/skills/old-skill")
        (cursor_skills / "split").mkdir()
        (cursor_skills / "split" / "notes.txt").write_text("mine\n")
        proc = self._run_skills(
            home, extra_env={"SKILL_TARGETS": str(home / ".cursor/skills")}
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            (cursor_skills / "k8s-mysql").resolve(), intuit_target.resolve()
        )
        self.assertTrue((cursor_skills / "vcode-sdlc-build").is_dir())
        self.assertFalse((cursor_skills / "vcode-sdlc-build").is_symlink())
        self.assertFalse((cursor_skills / "old-skill").exists())
        backups = list(cursor_skills.glob("split.backup.*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((cursor_skills / "split").is_symlink())

    def test_future_ide_via_extra_targets(self) -> None:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-skills-"))
        home = tmp / "home"
        store = home / ".config/skills/split"
        store.mkdir(parents=True)
        (store / "SKILL.md").write_text("---\nname: split\n---\n")
        proc = self._run_skills(
            home, extra_env={"SKILL_TARGETS_EXTRA": str(home / ".future/skills")}
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((home / ".future/skills/split").is_symlink())


class RulesExecutionTest(unittest.TestCase):
    """Execute the RENDERED rules scripts against a fake HOME."""

    def _run_rules(
        self, profile: str, fake_home: pathlib.Path
    ) -> subprocess.CompletedProcess:
        rendered = render_script(profile, "run_onchange_after_36-rules.sh.tmpl")
        script = fake_home / f"rules-{profile}.sh"
        script.write_text(rendered)
        # Empty stub dir first on PATH so the script's `python3` resolves
        # to the test interpreter, never macOS's xcrun /usr/bin/python3 shim.
        bin_dir = fake_home / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        env = _base_env(bin_dir)
        env["HOME"] = str(fake_home)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        return subprocess.run(
            ["bash", str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

    def test_work_profile_deploys_jira_rule_everywhere(self) -> None:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-rules-"))
        home = tmp / "home"
        (home / ".claude/CLAUDE.md").parent.mkdir(parents=True)
        (home / ".claude/CLAUDE.md").write_text(
            "# Global preferences\n\n## Git\n- Never add trailers.\n"
        )
        proc = self._run_rules("work", home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        if IS_LINUX:
            gemini_global = home / ".gemini/GEMINI.md"
            self.assertIn("dotfiles-rules:start", gemini_global.read_text())
            self.assertIn("DXS", gemini_global.read_text())
            return
        mdc = home / ".cursor/rules/commit-pr-jira.mdc"
        self.assertTrue(mdc.is_file())
        self.assertIn("DXS", mdc.read_text())
        cmd = home / ".claude/commands/commit-pr-jira.md"
        self.assertTrue(cmd.is_file())
        self.assertNotEqual(cmd.read_text().splitlines()[0], "---")
        self.assertIn("Conventional Commits", cmd.read_text())
        claude_global = home / ".claude/CLAUDE.md"
        self.assertIn("Never add trailers.", claude_global.read_text())
        self.assertIn("dotfiles-rules:start", claude_global.read_text())
        self.assertIn("DXS", claude_global.read_text())
        self.assertFalse((home / ".gemini").exists())
        self.assertFalse((home / ".cursor/rules/personal-commits.mdc").exists())

    def test_personal_profile_swaps_rule_and_cleans_work(self) -> None:
        if CHEZMOI is None:
            self.skipTest("chezmoi not available")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-rules-"))
        home = tmp / "home"
        home.mkdir(parents=True)
        proc = self._run_rules("work", home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        proc = self._run_rules("personal", home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        if IS_LINUX:
            gemini_global = (home / ".gemini/GEMINI.md").read_text()
            self.assertIn("No Jira key", gemini_global)
            self.assertNotIn("DXS", gemini_global)
            return
        self.assertTrue((home / ".cursor/rules/personal-commits.mdc").is_file())
        self.assertFalse((home / ".cursor/rules/commit-pr-jira.mdc").exists())
        self.assertFalse((home / ".claude/commands/commit-pr-jira.md").exists())
        claude_global = (home / ".claude/CLAUDE.md").read_text()
        self.assertIn("No Jira key", claude_global)
        self.assertNotIn("DXS", claude_global)
        # Idempotent: second run changes nothing, no backups pile up.
        proc = self._run_rules("personal", home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(list(home.rglob("*.backup.*")), [])


class SyncCheckTest(unittest.TestCase):
    """Run the real dotfiles-sync --check with stubbed host commands."""

    def _run_sync(
        self, *, extra_brew: str = "", extra_flatpak: str = ""
    ) -> subprocess.CompletedProcess:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-sync-"))
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        write_stub(
            bin_dir, "chezmoi", 'if [ "$1" = "status" ]; then exit 0; fi\nexit 0'
        )
        brews = (
            "git\nduti\ntealdeer\ndocker\ndocker-completion\nprotobuf\nawscli\nmysql"
            + extra_brew
        )
        write_stub(
            bin_dir,
            "brew",
            f'if [ "$1 $2" = "list --formula" ]; then printf "{brews}\\n"; exit 0; fi\n'
            'if [ "$1 $2" = "list --cask" ]; then printf "ghostty\\nvisual-studio-code\\ncursor\\nwindsurf\\n'
            "font-jetbrains-mono-nerd-font\\nfont-meslo-lg-nerd-font\\n"
            'intellij-idea\\njetbrains-toolbox\\npostman\\n"; exit 0; fi\nexit 0',
        )
        write_stub(
            bin_dir,
            "flatpak",
            'if [ "$1" = "list" ]; then printf "Application\\n'
            f'{extra_flatpak}"; exit 0; fi\nexit 0',
        )
        write_stub(bin_dir, "mise", 'if [ "$1" = "outdated" ]; then exit 0; fi\nexit 0')
        env = _base_env(bin_dir)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        return subprocess.run(
            ["bash", str(REPO / "dot_local/bin/executable_dotfiles-sync"), "--check"],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

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

    def _run_auto_update(
        self, args: list[str], status_body: str | None
    ) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
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
            [
                "bash",
                str(REPO / "dot_local/bin/executable_dotfiles-auto-update"),
                *args,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        return proc, fake_home

    def test_fresh_status_skips_without_force(self) -> None:
        from datetime import datetime

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        proc, home = self._run_auto_update(
            [], f"last_run={now}\nresult=ok\ndrift=clean\n"
        )
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


class DoctorTest(unittest.TestCase):
    """Run the real dotfiles-doctor with stubs + a fake HOME."""

    def _run_doctor(
        self,
        *,
        with_brew: bool = True,
        dirty: bool = False,
        scheduler_loaded: bool = True,
        gh_authed: bool = True,
        status_body: str | None = None,
        log_body: str | None = None,
        stdin: str | None = None,
    ) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="dot-doc-"))
        fake_home = tmp / "home"
        (fake_home / ".config/ghostty").mkdir(parents=True)
        (fake_home / ".config/mise").mkdir(parents=True)
        (fake_home / ".config/chezmoi").mkdir(parents=True)
        (fake_home / "Library/Application Support/Code/User").mkdir(parents=True)
        (fake_home / "Library/LaunchAgents").mkdir(parents=True)
        (fake_home / ".local/share").mkdir(parents=True)
        (fake_home / ".zshrc").write_text("# fake zshrc\n")
        (fake_home / ".config/ghostty/config").write_text("# fake ghostty\n")
        (fake_home / ".config/mise/config.toml").write_text("[tools]\n")
        (fake_home / ".config/chezmoi/chezmoi.toml").write_text(
            '[data]\nname = "IT"\nemail = "it@example.com"\n'
            "is_work = true\ninstall_intellij = true\n"
        )
        (
            fake_home / "Library/Application Support/Code/User/keybindings.json"
        ).write_text("[]\n")
        if status_body is not None:
            (fake_home / ".local/share/dotfiles-update.status").write_text(status_body)
        if log_body is not None:
            (fake_home / ".local/share/dotfiles-update.log").write_text(log_body)
        (fake_home / "Library/LaunchAgents/com.dotfiles.update.plist").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict><key>Label</key>'
            "<string>com.dotfiles.update</string></dict></plist>\n"
        )
        state = tmp / "state"
        state.mkdir()
        if dirty:
            (state / "drift").write_text("M .zshrc\n")
        if scheduler_loaded:
            (state / "scheduler").write_text("loaded\n")
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        write_stub(
            bin_dir,
            "chezmoi",
            'if [ "$1" = "status" ]; then cat "$DOCTOR_STATE/drift" 2>/dev/null; exit 0; fi\n'
            'if [ "$1" = "apply" ]; then rm -f "$DOCTOR_STATE/drift"; exit 0; fi\n'
            'if [ "$1" = "--version" ]; then echo "chezmoi version test"; exit 0; fi\nexit 0',
        )
        if with_brew:
            write_stub(bin_dir, "brew", "exit 0")
        for name in ("mise", "starship", "git"):
            write_stub(bin_dir, name, "exit 0")
        write_stub(bin_dir, "gh", "exit 0" if gh_authed else "exit 1")
        write_stub(
            bin_dir,
            "launchctl",
            'if [ "$1" = "list" ]; then cat "$DOCTOR_STATE/scheduler" 2>/dev/null && echo com.dotfiles.update; exit 0; fi\n'
            'if [ "$1" = "bootstrap" ]; then echo loaded > "$DOCTOR_STATE/scheduler"; exit 0; fi\n'
            "exit 0",
        )
        env = _base_env(bin_dir)
        env["HOME"] = str(fake_home)
        env["CHEZMOI_SOURCE_DIR"] = str(REPO)
        env["DOCTOR_STATE"] = str(state)
        proc = subprocess.run(
            ["bash", str(REPO / "dot_local/bin/executable_dotfiles-doctor")],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            input=stdin,
        )
        return proc, state

    def test_healthy_machine_exits_zero(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, _ = self._run_doctor()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("[ok]", proc.stdout)
        self.assertIn("is_work/install_intellij = true/true", proc.stdout)

    def test_missing_package_manager_fails(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, _ = self._run_doctor(with_brew=False)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("[fail]", proc.stdout)

    def test_default_mode_only_reports(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, state = self._run_doctor(dirty=True, scheduler_loaded=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("[warn]", proc.stdout)
        self.assertNotIn("[fixed]", proc.stdout)
        self.assertTrue((state / "drift").exists())

    def test_scheduler_enables_itself(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, state = self._run_doctor(scheduler_loaded=False)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("[fixed]", proc.stdout)
        self.assertTrue((state / "scheduler").exists())

    def test_gh_auth_is_required(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, _ = self._run_doctor(gh_authed=False)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("[fail]", proc.stdout)

    def test_stale_status_and_dirty_log_surface(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        proc, _ = self._run_doctor(
            status_body="last_run=2020-01-01T00:00:00Z\nresult=ok\ndrift=drift-detected\n",
            log_body="=== dotfiles-auto-update ===\nauto-update: drift detected, see log above\n",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("stale", proc.stdout)
        self.assertIn("drift-detected", proc.stdout)
        self.assertIn("log shows problems", proc.stdout)

    def test_fresh_status_and_clean_log_pass(self) -> None:
        if not IS_DARWIN:
            self.skipTest("brew/launchctl doctor branch needs macOS")
        from datetime import datetime

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        proc, _ = self._run_doctor(
            status_body=f"last_run={now}\nresult=ok\ndrift=clean\n",
            log_body="=== dotfiles-auto-update ===\nauto-update: drift check clean\n",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("weekly run fresh", proc.stdout)
        self.assertIn("update log clean", proc.stdout)


if __name__ == "__main__":
    unittest.main()
