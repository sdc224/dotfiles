"""Unit tests: package manifests (shared/work/personal) + mise-first policy.

Covers docs/DECISION.md rules, the dispatcher merge order, work-profile
assumptions (IntelliJ/AWS/MySQL work-only), and MDM exclusions.
"""

import pathlib
import unittest

from tests.lib import repo

REPO = repo.REPO_ROOT
SHARED = repo.load_toml(REPO / "dot_config/packages/shared.toml")
WORK = repo.load_toml(REPO / "dot_config/packages/work.toml")
PERSONAL = repo.load_toml(REPO / "dot_config/packages/personal.toml")


class ManifestShapeTest(unittest.TestCase):
    def test_all_manifests_parse(self) -> None:
        for manifest in (SHARED, WORK, PERSONAL):
            self.assertIsInstance(manifest, dict)

    def test_expected_sections_only(self) -> None:
        allowed = {"brew", "cask", "dnf", "flatpak", "winget"}
        for manifest in (SHARED, WORK, PERSONAL):
            self.assertTrue(set(manifest) <= allowed, set(manifest) - allowed)

    def test_entries_are_nonempty_strings(self) -> None:
        for manifest in (SHARED, WORK, PERSONAL):
            for backend, names in repo.manifest_entries(manifest).items():
                for name in names:
                    self.assertIsInstance(name, str)
                    self.assertTrue(name.strip(), f"{backend} has blank entry")

    def test_no_duplicates_within_manifest(self) -> None:
        for manifest in (SHARED, WORK, PERSONAL):
            for backend, names in repo.manifest_entries(manifest).items():
                self.assertEqual(len(names), len(set(names)), f"dup in {backend}")

    def test_manifest_files_exist(self) -> None:
        for name in ("shared.toml", "work.toml", "personal.toml"):
            self.assertTrue((REPO / "dot_config/packages" / name).is_file())


class MiseFirstPolicyTest(unittest.TestCase):
    def test_no_banned_tools_in_any_manifest(self) -> None:
        bad = repo.find_bannedDeclarations(SHARED, WORK, PERSONAL)
        self.assertEqual(bad, [], f"banned backends declared: {bad}")

    def test_each_banned_tool_individually(self) -> None:
        for tool in sorted(repo.BANNED_SYSTEM_BACKENDS):
            for manifest in (SHARED, WORK, PERSONAL):
                entries = repo.manifest_entries(manifest)
                for backend in ("brew", "dnf", "winget"):
                    self.assertNotIn(tool, entries[backend])

    def test_no_transitive_brew_deps_declared(self) -> None:
        for manifest, label in (
            (SHARED, "shared"),
            (WORK, "work"),
            (PERSONAL, "personal"),
        ):
            self.assertEqual(
                repo.find_transitive_declarations(manifest),
                [],
                f"{label} lists transitive deps",
            )

    def test_protobuf_is_explicit_exception(self) -> None:
        # protoc has no mise backend, so the shared brew entry is intentional.
        self.assertIn("protobuf", repo.manifest_entries(SHARED)["brew"])
        self.assertNotIn("protobuf", repo.TRANSITIVE_BREW_DEPS - {"protobuf"} or set())


class WorkProfileTest(unittest.TestCase):
    def test_work_has_aws_mysql(self) -> None:
        brew = repo.manifest_entries(WORK)["brew"]
        self.assertIn("awscli", brew)
        self.assertIn("mysql", brew)

    def test_work_has_intellij_toolbox_postman(self) -> None:
        casks = repo.manifest_entries(WORK)["cask"]
        self.assertIn("intellij-idea", casks)
        self.assertIn("jetbrains-toolbox", casks)
        self.assertIn("postman", casks)

    def test_personal_has_no_intellij(self) -> None:
        entries = repo.manifest_entries(PERSONAL)
        for backend, names in entries.items():
            self.assertNotIn("intellij-idea", names, backend)

    def test_personal_has_no_mysql(self) -> None:
        entries = repo.manifest_entries(PERSONAL)
        for backend, names in entries.items():
            self.assertNotIn("mysql", names, backend)

    def test_personal_has_fedora_tools(self) -> None:
        dnf = repo.manifest_entries(PERSONAL)["dnf"]
        self.assertIn("neovim", dnf)
        self.assertIn("distrobox", dnf)
        for package in (
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ):
            self.assertIn(package, dnf)
        # Flathub app-id is com.getpostman.Postman (not com.postman.Postman).
        flatpak = repo.manifest_entries(PERSONAL)["flatpak"]
        self.assertIn("com.getpostman.Postman", flatpak)
        self.assertNotIn("com.postman.Postman", flatpak)

    def test_work_and_personal_do_not_overlap(self) -> None:
        for backend in ("brew", "cask", "dnf", "flatpak", "winget"):
            overlap = set(repo.manifest_entries(WORK)[backend]) & set(
                repo.manifest_entries(PERSONAL)[backend]
            )
            self.assertEqual(overlap, set(), f"overlap in {backend}")

    def test_mdm_apps_never_declared(self) -> None:
        mdm = {"slack", "zoom", "rancher-desktop", "slack-app", "zoom-app"}
        for manifest in (SHARED, WORK, PERSONAL):
            for backend, names in repo.manifest_entries(manifest).items():
                self.assertTrue(mdm.isdisjoint(names), f"MDM app in {backend}")


class DispatcherMergeTest(unittest.TestCase):
    def test_work_plan_contains_shared_plus_work(self) -> None:
        plan = repo.merged_plan(SHARED, WORK)
        self.assertIn("brew:git", plan)
        self.assertIn("brew:awscli", plan)
        self.assertIn("cask:intellij-idea", plan)

    def test_personal_plan_contains_shared_plus_personal(self) -> None:
        plan = repo.merged_plan(SHARED, PERSONAL)
        self.assertIn("brew:git", plan)
        self.assertIn("dnf:neovim", plan)
        self.assertNotIn("cask:intellij-idea", plan)

    def test_plan_dedupes_shared_first(self) -> None:
        plan = repo.merged_plan(SHARED, WORK)
        self.assertEqual(len(plan), len(set(plan)))
        self.assertLess(plan.index("brew:git"), plan.index("brew:awscli"))

    def test_plan_for_backend_filters(self) -> None:
        plan = repo.merged_plan(SHARED, WORK)
        brew = repo.plan_for_backend(plan, "brew")
        self.assertIn("git", brew)
        self.assertIn("awscli", brew)
        self.assertNotIn("intellij-idea", brew)

    def test_missing_overlay_loads_empty(self) -> None:
        missing = repo.load_toml(pathlib.Path("/nonexistent/overlay.toml"))
        plan = repo.merged_plan(SHARED, missing)
        self.assertIn("brew:git", plan)

    def test_extras_drift_helper(self) -> None:
        declared = {"git", "awscli"}
        self.assertEqual(
            repo.extras_vs_declared({"git", "hand-brewed"}, declared, set()),
            ["hand-brewed"],
        )
        self.assertEqual(repo.extras_vs_declared({"git"}, declared, set()), [])

    def test_merge_dedupes_across_overlays(self) -> None:
        shared = {"brew": {"formulae": ["git", "duti"]}}
        overlay = {"brew": {"formulae": ["git", "awscli"]}}
        self.assertEqual(
            repo.merged_plan(shared, overlay),
            ["brew:git", "brew:duti", "brew:awscli"],
        )

    def test_banned_tool_flagged_in_synthetic_manifest(self) -> None:
        bad_manifest = {"brew": {"formulae": ["git", "node"]}}
        bad = repo.find_bannedDeclarations(bad_manifest)
        self.assertEqual(bad, ["brew:node"])

    def test_transitive_dep_flagged_except_protobuf(self) -> None:
        self.assertEqual(
            repo.find_transitive_declarations({"brew": {"formulae": ["openssl@3"]}}),
            ["openssl@3"],
        )
        self.assertEqual(
            repo.find_transitive_declarations({"brew": {"formulae": ["protobuf"]}}),
            [],
        )


if __name__ == "__main__":
    unittest.main()
