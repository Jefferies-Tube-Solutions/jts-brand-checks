# JTS Brand Checks

Shared GitHub checks for public Jefferies Tube Solutions projects. The check implements machine-verifiable parts of DOC-001, VIS-001 and VIS-002 for the JTS Brand System version recorded in the project profile.

## Commissioning

Generate a product's standard badge row from its checkout using
`python readme_badges.py --root /path/to/project --repository OWNER/REPO --workflow validate.yml --branch main --license MIT`.
Use the project's actual workflow, branch and license. The generator preserves
the leading status badge, reads any declared Home Assistant minimum from
`hacs.json`, and excludes the row from Home Assistant Marketplace. Run the
same command with `--check` in CI to detect drift without writing to the checkout.

In a GitHub Actions job, check out the project and call this composite action using a full commit SHA. Run it on every pull request and require that job in the ruleset for the target branch.

The profiles cover Dashboard Beam, Tariff Engine and Jefferies Navigation. To onboard a project, add a reviewed profile with its version file and approved public artwork hashes. Changes to approved artwork require coordinated updates to the profile and the project's provenance.

Tariff Engine retains its existing README layout, asset gallery and Home Assistant identity checks. Its validator was adapted from [Tariff Engine's original MIT-licensed validator](https://github.com/Jefferies-Tube-Solutions/jts-tariff-engine/blob/4d856cc703423fc591280811cca10b0aa5fa0c12/tools/validate_brand.py).

The Navigation profile checks legacy Honeycomb branding directly and runs Navigation v2's existing brand validator after verifying its SHA-256 checksum. A deliberate change to that validator requires a reviewed checksum update here before the project can adopt it.

## Verification

The check verifies paired manuals, reciprocal links, consistent version and status, the README badge and artwork, and the published artwork hashes. PR review covers whether the documentation matches the implementation and whether visual changes meet the design standard.

The JTS Brand System repository holds the canonical standards and assets. This repository distributes only the public validation code and profiles.
