"""Validate the machine-checkable rules used by public JTS projects."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from readme_badges import EXCLUDE_START, render_badges


PROFILES = {
    "jefferies-tube-solutions/dashboard-beam": {
        "brand_version": "v1.1.0",
        "version_file": "custom_components/dashboard_beam/manifest.json",
        "badge_workflow": "validate.yml",
        "license": "MIT",
        "images": (
            "docs/brand/jts-white-transparent.png#gh-dark-mode-only",
            "docs/brand/jts-deep-space-transparent.png#gh-light-mode-only",
            "docs/brand/dashboard-beam-full-dark-mode.png#gh-dark-mode-only",
            "docs/brand/dashboard-beam-full-light-mode.png#gh-light-mode-only",
        ),
        "artwork": {
            "docs/brand/jts-white-transparent.png": "b66b645f30265d93a68d5846aefb438290f16399f1c918741a1dbfc9aa4f52ca",
            "docs/brand/jts-deep-space-transparent.png": "3ea4532f50530d5ebf19c53cb12c2ef999e578345cbe04239805ff1a03420e86",
            "docs/brand/dashboard-beam-full-dark-mode.png": "4f98d1843d4fcced38c7c285848e9225c782692f9444bc2eeab2cd47f1241071",
            "docs/brand/dashboard-beam-full-light-mode.png": "7eb87ad0f67fc8f3dd79f36f211080f68585a34e34c2105c3ad7b16ff1b4a6d3",
            "custom_components/dashboard_beam/brand/dark_logo.png": "0a0c6ff6380f7a3bc5c28d4551846db73525e182a8463b6ca7cbe820d72b98fd",
            "custom_components/dashboard_beam/brand/icon.png": "e4b14a8daaa4e9dd914b4e0412b6ff53e209bbdaadd5c10e16f85ff629a2176d",
            "custom_components/dashboard_beam/brand/icon@2x.png": "e5e0a9f6c4233a2a2acf7fc04ec801b7786831aacc1d8435e6cf03058b1364ac",
        },
    },
}
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")
README_IMAGE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"')
NAVIGATION_VALIDATOR_SHA256 = "bbb84acc468d510a098fe39937e7dedece2ab445ef17377ea0d6ae33693275e2"
HONEYCOMB_LOGO_BLOB = "b86d9f007db8b2c7460085fbb7fa4b3e2213eaf7"


def project_file(root, path):
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise SystemExit(f"Expected a file inside the project: {path}")
    return target


def validate_manuals(root, readme, version, status):
    manuals = {
        kind: {file.stem for file in (root / "docs" / directory).glob("*.md")}
        for kind, directory in (("human", "guides"), ("ai", "ai"))
    }
    if not manuals["human"] or manuals["human"] != manuals["ai"]:
        raise SystemExit(f"DOC-001: unpaired manuals: {manuals}")
    for slug in sorted(manuals["human"]):
        for kind, directory, companion in (("human", "guides", "ai"), ("ai", "ai", "guides")):
            path = f"docs/{directory}/{slug}.md"
            source = project_file(root, path).read_text(encoding="utf-8")
            metadata = f"<!-- JTS-DOC: {kind}; slug: {slug}; status: {status}; version: {version} -->"
            if source.partition("\n")[0] != metadata or f"](../{companion}/{slug}.md)" not in source:
                raise SystemExit(f"DOC-001: invalid metadata or missing companion link in {path}")
            if f"]({path})" not in readme:
                raise SystemExit(f"DOC-001: README must link to {path}")
            for link in MARKDOWN_LINK.findall(source):
                if not link.startswith(("https://", "http://", "#")):
                    project_file(root, Path(path).parent / link.partition("#")[0])
    print(f"DOC-001: {len(manuals['human'])} paired manual(s), v{version} {status}")


def validate_artwork(root, readme, repository, profile, version, status):
    expected_readme = render_badges(root, readme, repository, profile["badge_workflow"],
                                    profile.get("branch", "main"), profile["license"])
    if readme != expected_readme:
        raise SystemExit("VIS-002: README badge row differs from the generated JTS header")
    readme = readme.removeprefix(EXCLUDE_START + "\n")
    badge, _, content = readme.partition("</p>")
    expected_badge = (
        f'alt="draft | v{version}"' if status == "draft" else
        f'src="https://img.shields.io/github/v/release/{repository}?label=stable&amp;color=2ea44f"'
    )
    if not badge.startswith('<p align="right">') or expected_badge not in badge:
        raise SystemExit("VIS-002: README badge must reflect the release status")
    expected_images = profile["images"]
    if tuple(README_IMAGE.findall(content)[:len(expected_images)]) != expected_images:
        raise SystemExit("VIS-001: README must show the approved publisher and product artwork")
    provenance = json.loads(project_file(root, "docs/brand/provenance.json").read_text(encoding="utf-8"))
    registered = {item["path"]: item["sha256"] for item in provenance["files"]}
    for path, expected in profile["artwork"].items():
        if registered.get(path) != expected:
            raise SystemExit(f"VIS-001: artwork provenance differs from the shared profile: {path}")
    for path, expected in registered.items():
        if hashlib.sha256(project_file(root, path).read_bytes()).hexdigest() != expected:
            raise SystemExit(f"VIS-001: artwork differs from the recorded export: {path}")
    print("VIS-001 and VIS-002: README and registered artwork verified")


def validate_navigation(root):
    instructions = project_file(root, "AGENTS.md").read_text(encoding="utf-8")
    if "## JTS Brand System" not in instructions or "jts-brand-system" not in instructions:
        raise SystemExit("AGENTS.md must reference JTS Brand System")

    package = json.loads(project_file(root, "package.json").read_text(encoding="utf-8"))
    if package["name"] == "jefferies-navigation":
        validator = project_file(root, "scripts/check-brand.js")
        source = validator.read_text(encoding="utf-8").encode()
        if hashlib.sha256(source).hexdigest() != NAVIGATION_VALIDATOR_SHA256:
            raise SystemExit("Navigation brand validator changed without a reviewed JTS pin update")
        subprocess.run(["node", str(validator)], cwd=root, check=True)
        return

    if package["name"] != "honeycomb-menu-ng":
        raise SystemExit("Unrecognized Navigation or legacy Honeycomb package identity")
    logo = project_file(root, "assets/honeycomb-menu-ng-logo.png").read_bytes()
    blob = f"blob {len(logo)}\0".encode() + logo
    if hashlib.sha1(blob).hexdigest() != HONEYCOMB_LOGO_BLOB:
        raise SystemExit("Legacy Honeycomb logo changed without a reviewed JTS migration")
    readme = project_file(root, "README.md").read_text(encoding="utf-8")
    if not readme.startswith('<p align="right">') or not re.search(
        r"github/v/release/[^?]+\?label=stable&amp;color=2ea44f", readme
    ):
        raise SystemExit("Legacy Honeycomb README must retain its stable release badge")
    for marker in (
        'src="assets/honeycomb-menu-ng-logo.png"',
        "# Honeycomb Menu NG for Home Assistant",
        "Sian Croser",
        "[GPLv3](LICENSE)",
    ):
        if marker not in readme:
            raise SystemExit(f"Legacy Honeycomb README must preserve {marker}")
    print("Legacy Honeycomb release identity, artwork and attribution verified")


def main():
    root = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    repository = os.environ["GITHUB_REPOSITORY"]
    if repository.lower() == "jefferies-tube-solutions/jts-tariff-engine":
        from tariff_engine import validate

        validate(root)
        return
    if repository.lower() == "jefferies-tube-solutions/jefferies-navigation":
        validate_navigation(root)
        return
    profile = PROFILES.get(repository.lower())
    if profile is None:
        raise SystemExit(f"No approved JTS profile for {repository}")
    print(f"JTS Brand System {profile['brand_version']} profile for {repository}")
    version = json.loads(project_file(root, profile["version_file"]).read_text(encoding="utf-8"))["version"]
    status = "draft" if "-" in version else "stable"
    readme = project_file(root, "README.md").read_text(encoding="utf-8")
    validate_manuals(root, readme, version, status)
    validate_artwork(root, readme, repository, profile, version, status)


if __name__ == "__main__":
    main()
