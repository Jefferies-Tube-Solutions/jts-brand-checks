"""Validate the machine-checkable rules used by public JTS projects."""

import hashlib
import json
import os
from pathlib import Path
import re


PROFILES = {
    "jefferies-tube-solutions/dashboard-beam": {
        "brand_version": "v1.1.0",
        "version_file": "custom_components/dashboard_beam/manifest.json",
        "images": (
            "docs/brand/jts-white-transparent.png#gh-dark-mode-only",
            "docs/brand/jts-deep-space-transparent.png#gh-light-mode-only",
            "custom_components/dashboard_beam/brand/icon.png",
        ),
        "artwork": {
            "docs/brand/jts-white-transparent.png": "b66b645f30265d93a68d5846aefb438290f16399f1c918741a1dbfc9aa4f52ca",
            "docs/brand/jts-deep-space-transparent.png": "3ea4532f50530d5ebf19c53cb12c2ef999e578345cbe04239805ff1a03420e86",
            "custom_components/dashboard_beam/brand/dark_logo.png": "0a0c6ff6380f7a3bc5c28d4551846db73525e182a8463b6ca7cbe820d72b98fd",
            "custom_components/dashboard_beam/brand/icon.png": "e4b14a8daaa4e9dd914b4e0412b6ff53e209bbdaadd5c10e16f85ff629a2176d",
            "custom_components/dashboard_beam/brand/icon@2x.png": "e5e0a9f6c4233a2a2acf7fc04ec801b7786831aacc1d8435e6cf03058b1364ac",
        },
    },
}
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")
README_IMAGE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"')


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
    badge, _, content = readme.partition("</p>")
    expected_badge = (
        f'alt="draft | v{version}"' if status == "draft" else
        f'src="https://img.shields.io/github/v/release/{repository}?label=stable&amp;color=2ea44f"'
    )
    if not badge.startswith('<p align="right">') or expected_badge not in badge:
        raise SystemExit("VIS-002: README badge must reflect the release status")
    if tuple(README_IMAGE.findall(content)[:3]) != profile["images"]:
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


def main():
    root = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    repository = os.environ["GITHUB_REPOSITORY"]
    if repository.lower() == "jefferies-tube-solutions/jts-tariff-engine":
        from tariff_engine import validate

        validate(root)
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
