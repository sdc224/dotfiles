"""Unit tests: personal skills + profile-gated rules.

Skills (dot_config/skills/*) are the personal, non-work set symlinked into
every agent IDE. Rules (dot_config/rules/*.mdc) are profile-gated: the DXS
work rule only on is_work machines, the personal rule otherwise.
"""

import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT

# Personal skills vendored in this repo. Work skills (vcode-sdlc-* from the
# Intuit developer desktop app, k8s-mysql pointing into ~/Programming/Intuit)
# must never appear here.
PERSONAL_SKILLS = (
    "chrome-osascript-debug",
    "review-github-pr",
    "split",
)

WORK_SKILL_PREFIXES = ("vcode-sdlc-", "k8s-mysql")


def read(path: str) -> str:
    return (REPO / path).read_text()


def skill_frontmatter(name: str) -> dict[str, str]:
    """Parse the YAML frontmatter of a vendored SKILL.md (flat keys only)."""
    text = read(f"dot_config/skills/{name}/SKILL.md")
    lines = text.splitlines()
    assert lines[0] == "---", f"{name}: missing frontmatter"
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


class SkillsVendoredTest(unittest.TestCase):
    def test_personal_skills_vendored(self) -> None:
        for skill in PERSONAL_SKILLS:
            path = REPO / "dot_config/skills" / skill / "SKILL.md"
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_every_skill_has_name_and_description(self) -> None:
        for skill in PERSONAL_SKILLS:
            fm = skill_frontmatter(skill)
            self.assertTrue(fm.get("name"), f"{skill}: frontmatter name empty")
            self.assertTrue(fm.get("description"), f"{skill}: no description")

    def test_split_helper_script_vendored(self) -> None:
        self.assertTrue(
            (REPO / "dot_config/skills/split/scripts/split_diff.py").is_file()
        )

    def test_no_work_skills_vendored(self) -> None:
        vendored = [p.name for p in (REPO / "dot_config/skills").iterdir()]
        for skill in vendored:
            for prefix in WORK_SKILL_PREFIXES:
                self.assertFalse(
                    skill.startswith(prefix), f"work skill vendored: {skill}"
                )


class SkillsScriptTest(unittest.TestCase):
    TEXT = read("run_onchange_after_35-skills.sh.tmpl")

    def test_targets_are_os_specific(self) -> None:
        for target in (
            ".cursor/skills",
            ".claude/skills",
            ".gemini/config/skills",
            ".gemini/antigravity/skills",
        ):
            self.assertIn(target, self.TEXT, f"missing skill target {target}")
        self.assertIn('eq .chezmoi.os "linux"', self.TEXT)

    def test_future_ides_without_editing(self) -> None:
        self.assertIn("SKILL_TARGETS", self.TEXT)
        self.assertIn("SKILL_TARGETS_EXTRA", self.TEXT)

    def test_reruns_on_skill_hash(self) -> None:
        for skill in PERSONAL_SKILLS:
            self.assertIn(skill, self.TEXT)
        self.assertIn("sha256sum", self.TEXT)

    def test_work_skills_skipped(self) -> None:
        for prefix in WORK_SKILL_PREFIXES:
            self.assertIn(prefix, self.TEXT)

    def test_prune_keeps_work_symlinks(self) -> None:
        # Only symlinks pointing back at the dotfiles store are pruned;
        # the k8s-mysql symlink into ~/Programming/Intuit must survive.
        self.assertIn('"$SRC"/*', self.TEXT)

    def test_plugin_caches_untouched(self) -> None:
        for managed in ("skills-cursor", "plugins/cache"):
            self.assertIn(managed, self.TEXT)

    def test_backs_up_real_dirs(self) -> None:
        self.assertIn(".backup.", self.TEXT)


class RulesSourceTest(unittest.TestCase):
    def test_work_rule_matches_deployed_home_copy(self) -> None:
        import pathlib

        home_copy = pathlib.Path.home() / ".cursor/rules/commit-pr-jira.mdc"
        if not home_copy.is_file():
            self.skipTest("home rule copy absent (fresh machine)")
        self.assertEqual(
            read("dot_config/rules/commit-pr-jira.mdc"),
            home_copy.read_text(),
            "repo work rule drifted from ~/.cursor/rules copy",
        )

    def test_work_rule_has_jira_markers(self) -> None:
        text = read("dot_config/rules/commit-pr-jira.mdc")
        for marker in ("DXS", "alwaysApply: true", "Conventional Commits"):
            self.assertIn(marker, text)

    def test_personal_rule_has_no_work_markers(self) -> None:
        text = read("dot_config/rules/personal-commits.mdc")
        for marker in ("DXS", "intuit", "Jira key"):
            if marker == "Jira key":
                # Allowed only as a negation ("No Jira key").
                self.assertIn("No Jira key", text)
                continue
            self.assertNotIn(marker, text)
        self.assertIn("alwaysApply: true", text)
        self.assertIn("Conventional Commits", text)


class RulesScriptTest(unittest.TestCase):
    TEXT = read("run_onchange_after_36-rules.sh.tmpl")

    def test_gated_on_is_work(self) -> None:
        self.assertIn(".is_work", self.TEXT)
        self.assertIn('ACTIVE_RULE="commit-pr-jira"', self.TEXT)
        self.assertIn('ACTIVE_RULE="personal-commits"', self.TEXT)

    def test_reruns_on_rule_hash(self) -> None:
        self.assertIn("commit-pr-jira.mdc", self.TEXT)
        self.assertIn("personal-commits.mdc", self.TEXT)
        self.assertIn("sha256sum", self.TEXT)

    def test_cursor_keeps_mdc(self) -> None:
        self.assertIn(".cursor/rules", self.TEXT)
        self.assertIn(".mdc", self.TEXT)

    def test_claude_gets_command_and_global_block(self) -> None:
        self.assertIn(".claude/commands", self.TEXT)
        self.assertIn("dotfiles-rules:start", self.TEXT)
        self.assertIn("CLAUDE.md", self.TEXT)

    def test_antigravity_rules_are_linux_only(self) -> None:
        self.assertIn(".gemini/GEMINI.md", self.TEXT)
        self.assertIn('eq .chezmoi.os "linux"', self.TEXT)

    def test_frontmatter_stripped_for_markdown_targets(self) -> None:
        self.assertIn("strip_frontmatter", self.TEXT)

    def test_inactive_profile_rule_removed(self) -> None:
        self.assertIn("INACTIVE_RULE", self.TEXT)

    def test_backs_up_changed_rules(self) -> None:
        self.assertIn(".backup.", self.TEXT)
        # cmp is optional: fedora containers may lack diffutils.
        self.assertIn("files_differ", self.TEXT)
        self.assertIn("cksum", self.TEXT)


if __name__ == "__main__":
    unittest.main()
