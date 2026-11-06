# SPEC-0159: Identifiable macOS Trial Build

## Metadata

- ID: `spec-0159`
- Status: `approved`
- Run: [Run235](../run/run-20261105-235-identifiable-macos-trial-build.md)
- Attempt: `1`
- Parent Feature: [FEAT-0159](../feature/feat-0159-identifiable-macos-trial-build.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `infra-devtool`
- Required Evaluators: contract, functional
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Delivery Contract

Keep existing Git/agent installation entry and locked Apple Silicon build. Record
source commit, dirty state and a content fingerprint of explicit build inputs in
BUILD-INFO alongside version/time/OS/architecture/signing. Do not expose local
paths or runtime data. Check source identity before and after build and reject
changed inputs. Preserve the prior canonical app until candidate verification
passes. All version manifests remain consistent; source fingerprint identifies
this dirty v0.0.1 rebuild. Validate auth/hidden routes, twelve offline Docs, settings
and configured storage in actual frozen runtime, and native WebKit startup.

Full suite, privacy and independent omission challenge precede delivery. No real
source collection, model download, external publication or Windows support claim.
Recipient/physical interaction, signing/notarization and Windows remain separately
unverified even if local source, frozen backend and isolated WebKit checks pass.
