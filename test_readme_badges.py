import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from readme_badges import EXCLUDE_END, EXCLUDE_START, render_badges


class ReadmeBadgeTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        workflow = self.root / ".github/workflows/check.yml"
        workflow.parent.mkdir(parents=True)
        workflow.touch()
        (self.root / "LICENSE").touch()
        self.readme = '<p align="right"><img alt="stable" src="stable.svg"></p>\n\n# Product\n'

    def render(self, readme, license_id):
        return render_badges(self.root, readme, "Example/product", "check.yml", "master", license_id)

    def test_marketplace_badges_use_the_project_version_and_are_hidden(self):
        (self.root / "hacs.json").write_text(json.dumps({"homeassistant": "2026.11.0"}))
        readme = self.render(self.readme, "MIT")
        self.assertTrue(readme.startswith(EXCLUDE_START + "\n"))
        self.assertEqual(readme.partition(EXCLUDE_END)[2], "\n\n# Product\n")
        self.assertIn("Home%20Assistant-2026.11%2B-blue", readme)
        self.assertIn("branch=master&amp;label=CI", readme)
        self.assertIn("license-MIT-blue", readme)
        self.assertEqual(self.render(readme, "MIT"), readme)

    def test_other_projects_use_their_own_license_and_no_home_assistant_badge(self):
        readme = self.render(self.readme, "GPL-3.0")
        self.assertIn("license-GPL--3.0-blue", readme)
        self.assertNotIn("Home Assistant", readme)
        self.assertNotIn(EXCLUDE_START, readme)

    def test_marketplace_without_minimum_omits_the_compatibility_badge(self):
        (self.root / "hacs.json").write_text("{}")
        self.assertNotIn("Home Assistant", self.render(self.readme, "MIT"))
