"""Unit tests: mise config template (runtimes, CLIs, work-gating)."""

import unittest

from tests.lib import repo

TEXT = (repo.REPO_ROOT / "dot_config/mise/config.toml.tmpl").read_text()

EXPECTED_TOOLS = [
    "java", "rust", "node", "python", "starship", "usage", "uv", "dart",
    "chezmoi", "ripgrep", "bat", "fd", "eza", "delta", "dust", "duf",
    "fzf", "zoxide", "lazygit", "lazydocker", "gping", "bottom", "atuin",
    "gh", "gum", "yazi", "cargo:procs", "cargo:tokei",
]


class MiseTemplateTest(unittest.TestCase):
    def test_template_gates_on_is_work(self) -> None:
        self.assertTrue(repo.template_has_is_work_gate(TEXT))

    def test_kubectl_work_only(self) -> None:
        work_tools = repo.mise_tool_names(repo.render_mise_template(TEXT, is_work=True))
        personal_tools = repo.mise_tool_names(
            repo.render_mise_template(TEXT, is_work=False)
        )
        self.assertIn("kubectl", work_tools)
        self.assertNotIn("kubectl", personal_tools)

    def test_all_expected_tools_present_in_work_render(self) -> None:
        tools = repo.mise_tool_names(repo.render_mise_template(TEXT, is_work=True))
        for tool in EXPECTED_TOOLS:
            self.assertIn(tool, tools, f"mise missing {tool}")

    def test_shared_tools_present_in_personal_render(self) -> None:
        tools = repo.mise_tool_names(repo.render_mise_template(TEXT, is_work=False))
        for tool in EXPECTED_TOOLS:
            if tool == "kubectl":
                continue
            self.assertIn(tool, tools, f"personal mise missing {tool}")

    def test_no_brew_duplicates_of_mise_tools(self) -> None:
        # Every mise-owned CLI must not appear in system manifests either.
        shared = repo.load_toml(repo.REPO_ROOT / "dot_config/packages/shared.toml")
        entries = repo.manifest_entries(shared)
        for tool in ("node", "python", "gh", "gum"):
            self.assertNotIn(tool, entries["brew"])

    def test_render_is_valid_toml(self) -> None:
        import tomllib

        for is_work in (True, False):
            rendered = repo.render_mise_template(TEXT, is_work=is_work)
            data = tomllib.loads(rendered)
            self.assertIn("tools", data)
            self.assertIn("settings", data)

    def test_cargo_backends_kept(self) -> None:
        tools = repo.mise_tool_names(repo.render_mise_template(TEXT, is_work=True))
        self.assertIn("cargo:procs", tools)
        self.assertIn("cargo:tokei", tools)


if __name__ == "__main__":
    unittest.main()
