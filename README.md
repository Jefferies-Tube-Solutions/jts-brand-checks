# JTS Brand Checks

Shared GitHub checks for public Jefferies Tube Solutions projects. The check implements machine-verifiable parts of DOC-001, VIS-001 and VIS-002 for the JTS Brand System version recorded in the project profile.

## Commissioning

In a GitHub Actions job, check out the project and call this composite action using a full commit SHA. Run it on every pull request and require that job in the ruleset for the target branch.

The initial profile covers Dashboard Beam. To onboard a project, add a reviewed profile with its version file and approved public artwork hashes. Changes to approved artwork require coordinated updates to the profile and the project's provenance.

## Verification

The check verifies paired manuals, reciprocal links, consistent version and status, the README badge and artwork, and the published artwork hashes. PR review covers whether the documentation matches the implementation and whether visual changes meet the design standard.

The JTS Brand System repository holds the canonical standards and assets. This repository distributes only the public validation code and profiles.
