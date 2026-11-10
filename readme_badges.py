"""Generate the standard JTS badge row for a product README."""

import argparse
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, urlencode


EXCLUDE_START = "<!-- ha-marketplace:exclude-start -->"
EXCLUDE_END = "<!-- ha-marketplace:exclude-end -->"
HEADER = re.compile(
    rf'\A(?:{re.escape(EXCLUDE_START)}\n)?<p align="right">(.*?)</p>'
    rf'(?:\n{re.escape(EXCLUDE_END)})?',
    re.DOTALL,
)
STATUS_BADGE = re.compile(r'\s*(<a\b[^>]*>.*?</a>|<img\b[^>]*>)', re.DOTALL)


def badge(label, url, target):
    return (
        f'<a href="{escape(target)}">'
        f'<img alt="{escape(label)}" src="{escape(url)}"></a>'
    )


def render_badges(root, readme, repository, workflow, branch, license_id):
    header = HEADER.match(readme)
    status = STATUS_BADGE.match(header[1]) if header else None
    if not status:
        raise ValueError("README must begin with the JTS status badge")
    workflow_file = root / ".github" / "workflows" / workflow
    if workflow_file.parent != root / ".github" / "workflows" or not workflow_file.is_file():
        raise ValueError(f"Missing CI workflow: {workflow}")

    github = f"https://github.com/{repository}"
    shields = "https://img.shields.io"
    workflow_url = f"{github}/actions/workflows/{quote(workflow)}"
    query = urlencode({"branch": branch, "label": "CI"})
    badges = [
        status[1],
        badge("CI", f"{shields}/github/actions/workflow/status/{repository}/{quote(workflow)}?{query}", workflow_url),
    ]

    marketplace = root / "hacs.json"
    if marketplace.is_file():
        version = json.loads(marketplace.read_text(encoding="utf-8")).get("homeassistant")
        if version:
            version = version.removesuffix(".0")
            minimum = quote(version + "+")
            badges.append(badge(f"Home Assistant {version} or newer",
                                f"{shields}/badge/Home%20Assistant-{minimum}-blue",
                                f"{github}/blob/{quote(branch, safe='')}/hacs.json"))

    if license_id:
        if not (root / "LICENSE").is_file():
            raise ValueError("A license badge requires a LICENSE file")
        value = quote(license_id.replace("-", "--"))
        badges.append(badge(f"License {license_id}", f"{shields}/badge/license-{value}-blue",
                            f"{github}/blob/{quote(branch, safe='')}/LICENSE"))

    row = '<p align="right">\n' + "\n".join(f"  {item}" for item in badges) + "\n</p>"
    if marketplace.is_file():
        row = f"{EXCLUDE_START}\n{row}\n{EXCLUDE_END}"
    return row + readme[header.end():]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--license", dest="license_id")
    parser.add_argument("--check", action="store_true", help="Check the badge row without writing it")
    args = parser.parse_args()
    path = args.root / "README.md"
    existing = path.read_text(encoding="utf-8")
    rendered = render_badges(args.root, existing, args.repository,
                             args.workflow, args.branch, args.license_id)
    if args.check:
        if rendered != existing:
            raise SystemExit("VIS-002: README badge row differs from the generated JTS header")
        return
    path.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
