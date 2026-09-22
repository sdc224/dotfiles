"""Unit tests: chezmoi templates (gates, prompts, ignore rules)."""

import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT


def read(path: str) -> str:
    return (REPO / path).read_text()


class ChezmoiConfigTest(unittest.TestCase):
    def test_prompts_for_name_email(self) -> None:
        text = read(".chezmoi.toml.tmpl")
        self.assertIn("promptString", text)
        self.assertIn("name", text)
        self.assertIn("email", text)

    def test_is_work_defaults_to_darwin(self) -> None:
        text = read(".chezmoi.toml.tmpl")
        self.assertIn("is_work", text)
        self.assertIn('eq .chezmoi.os "darwin"', text)

    def test_install_intellij_flag_exists(self) -> None:
        text = read(".chezmoi.toml.tmpl")
        self.assertIn("install_intellij", text)


class ChezmoiIgnoreTest(unittest.TestCase):
    def test_docs_and_github_never_deployed(self) -> None:
        text = read(".chezmoiignore")
        self.assertIn("docs/", text)
        self.assertIn(".github/", text)

    def test_test_tooling_never_deployed(self) -> None:
        text = read(".chezmoiignore")
        for entry in ("tests/", "pyproject.toml", ".coveragerc"):
            self.assertIn(entry, text)

    def test_launchagents_macos_only(self) -> None:
        text = read(".chezmoiignore")
        self.assertIn("Library/", text)
        self.assertIn('ne .chezmoi.os "darwin"', text)

    def test_systemd_linux_only(self) -> None:
        text = read(".chezmoiignore")
        self.assertIn("dot_config/systemd/", text)
        self.assertIn('ne .chezmoi.os "linux"', text)

    def test_ide_state_dirs_ignored(self) -> None:
        text = read(".chezmoiignore")
        for entry in (".idea/", ".vscode/", ".cursor/", ".windsurf/"):
            self.assertIn(entry, text)


class GitconfigTemplateTest(unittest.TestCase):
    def test_name_email_templated(self) -> None:
        text = read("dot_gitconfig.tmpl")
        self.assertIn(".name", text)
        self.assertIn(".email", text)

    def test_gh_credential_helper_personal_only(self) -> None:
        text = read("dot_gitconfig.tmpl")
        self.assertIn("gh auth git-credential", text)
        self.assertIn("if not .is_work", text)

    def test_local_override_include(self) -> None:
        text = read("dot_gitconfig.tmpl")
        self.assertIn("~/.gitconfig_local", text)

    def test_delta_pager_kept(self) -> None:
        text = read("dot_gitconfig.tmpl")
        self.assertIn("pager = delta", text)


class ZshrcTemplateTest(unittest.TestCase):
    def test_rancher_block_work_only(self) -> None:
        text = read("dot_zshrc.tmpl")
        self.assertTrue(repo.template_has_is_work_gate(text))
        self.assertIn("RANCHER DESKTOP", text)
        self.assertIn("ZIA-CERT-STORE", text)

    def test_zsh_local_sourced(self) -> None:
        text = read("dot_zshrc.tmpl")
        self.assertIn("~/.zsh_local", text)

    def test_mise_starship_zoxide_wired(self) -> None:
        text = read("dot_zshrc.tmpl")
        self.assertIn("mise activate zsh", text)
        self.assertIn("starship init zsh", text)
        self.assertIn("zoxide init zsh", text)

    def test_dump_zsh_state_stub(self) -> None:
        text = read("dot_zshrc.tmpl")
        self.assertIn("dump_zsh_state", text)


class IdeKeysTemplateTest(unittest.TestCase):
    def test_intellij_gated_on_work_or_flag(self) -> None:
        text = read("run_onchange_after_30-ide-keys.sh.tmpl")
        self.assertIn(".is_work", text)
        self.assertIn(".install_intellij", text)

    def test_deploys_to_code_cursor_windsurf(self) -> None:
        text = read("run_onchange_after_30-ide-keys.sh.tmpl")
        for app in ("Code", "Cursor", "Windsurf"):
            self.assertIn(app, text)

    def test_backs_up_before_overwrite(self) -> None:
        text = read("run_onchange_after_30-ide-keys.sh.tmpl")
        self.assertIn(".backup.", text)

    def test_src_dir_appends_ide_subdir(self) -> None:
        # Same CHEZMOI_SOURCE_DIR root regression as the package dispatcher:
        # when set, it is the source root — must append /dot_config/ide.
        text = read("run_onchange_after_30-ide-keys.sh.tmpl")
        self.assertIn(
            "${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}/dot_config/ide",
            text,
        )
        self.assertNotIn(
            "${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi/dot_config/ide}",
            text,
        )


if __name__ == "__main__":
    unittest.main()
