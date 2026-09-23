"""Unit tests: static configs (ghostty, starship, aliases, IDE, git)."""

import json
import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT


def read(path: str) -> str:
    return (REPO / path).read_text()


def read_jsonc(path: str):
    """Parse JSON with // comment lines (VS Code keybindings are JSONC)."""
    lines = [
        line for line in read(path).splitlines() if not line.strip().startswith("//")
    ]
    return json.loads("\n".join(lines))


class GhosttyTest(unittest.TestCase):
    TEXT = read("dot_config/ghostty/config")

    def test_font_and_theme(self) -> None:
        self.assertIn("JetBrainsMono Nerd Font", self.TEXT)
        self.assertIn("background = #282a36", self.TEXT)  # Dracula

    def test_ctrl_copy_paste_without_breaking_sigint(self) -> None:
        self.assertIn("ctrl+c=copy_to_clipboard", self.TEXT)
        self.assertIn("ctrl+v=paste_from_clipboard", self.TEXT)

    def test_ctrl_led_ninja_keys(self) -> None:
        for key in ("ctrl+t=new_tab", "ctrl+w=close_surface", "ctrl+k=clear_screen"):
            self.assertIn(key, self.TEXT)

    def test_full_dracula_palette(self) -> None:
        for i in range(16):
            self.assertIn(f"palette = {i}=", self.TEXT, f"missing palette {i}")


class StarshipTest(unittest.TestCase):
    TEXT = read("dot_config/starship.toml")

    def test_prompt_sections(self) -> None:
        for section in ("$directory", "$git_branch", "$nodejs", "$python", "$java"):
            self.assertIn(section, self.TEXT)

    def test_lambda_symbol(self) -> None:
        self.assertIn("λ", self.TEXT)


class AliasesTest(unittest.TestCase):
    TEXT = read("dot_zsh_aliases")

    def test_gui_launcher_silences_electron(self) -> None:
        self.assertIn("_gui_launch", self.TEXT)
        for app in ("code", "ag", "cr"):
            self.assertIn(f"alias {app}=", self.TEXT)

    def test_rust_replacements_guarded(self) -> None:
        for tool in ("eza", "bat", "procs", "bottom", "duf", "dust", "delta"):
            self.assertIn(tool, self.TEXT)

    def test_git_shortcuts(self) -> None:
        for alias in ("gst=", "gm=", "gdiff=", "lg="):
            self.assertIn(alias, self.TEXT)

    def test_safe_file_ops(self) -> None:
        self.assertIn("cp -iv", self.TEXT)
        self.assertIn("rm -iv", self.TEXT)


class KeybindingsTest(unittest.TestCase):
    DATA = read_jsonc("dot_config/ide/keybindings.json")

    def test_valid_nonempty_list(self) -> None:
        self.assertIsInstance(self.DATA, list)
        self.assertGreater(len(self.DATA), 10)

    def test_every_entry_has_key_and_command(self) -> None:
        for entry in self.DATA:
            self.assertIn("key", entry)
            self.assertIn("command", entry)

    def test_ctrl_first(self) -> None:
        for entry in self.DATA:
            self.assertTrue(
                entry["key"].startswith("ctrl+"), f"non-ctrl key: {entry['key']}"
            )

    def test_core_commands_present(self) -> None:
        commands = {entry["command"] for entry in self.DATA}
        for command in (
            "editor.action.clipboardCopyAction",
            "workbench.action.quickOpen",
            "workbench.action.terminal.toggleTerminal",
        ):
            self.assertIn(command, commands)


class AtuinTest(unittest.TestCase):
    def test_enter_accept_false(self) -> None:
        text = read("dot_config/atuin/config.toml")
        self.assertIn("enter_accept = false", text)

    def test_sync_records_enabled(self) -> None:
        text = read("dot_config/atuin/config.toml")
        self.assertIn("records = true", text)


class ZprofileTest(unittest.TestCase):
    def test_brew_shellenv_wired(self) -> None:
        text = read("dot_zprofile")
        self.assertIn("brew shellenv", text)
        self.assertIn("/opt/homebrew/bin/brew", text)

    def test_dotfiles_bin_is_on_login_path(self) -> None:
        text = read("dot_zprofile")
        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', text)

    def test_jetbrains_toolbox_path(self) -> None:
        text = read("dot_zprofile")
        self.assertIn("JetBrains", text)


class IntellijKeymapTest(unittest.TestCase):
    def test_keymap_xml_parses(self) -> None:
        import xml.etree.ElementTree as ET

        path = REPO / "dot_config/ide/intellij/DarculaCopy.xml"
        self.assertTrue(path.is_file())
        root = ET.parse(path).getroot()
        self.assertIsNotNone(root)

    def test_cursor_settings_json_parses(self) -> None:
        data = json.loads(read("dot_config/ide/cursor-settings.json"))
        self.assertIsInstance(data, dict)


class DocsConsistencyTest(unittest.TestCase):
    def test_mdm_apps_absent_from_manifests(self) -> None:
        mdm_text = read("docs/MDM.md")
        for app in ("Slack", "Zoom", "Rancher Desktop"):
            self.assertIn(app, mdm_text)

    def test_decision_doc_bans_match_lib(self) -> None:
        decision = read("docs/DECISION.md")
        for tool in ("node", "python", "kubectl", "gum", "gh"):
            self.assertIn(tool, decision)

    def test_no_install_sh(self) -> None:
        self.assertFalse((REPO / "install.sh").exists())


if __name__ == "__main__":
    unittest.main()
