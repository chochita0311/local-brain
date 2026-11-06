# SPEC-0158: Platform Storage Accounting

## Metadata

- ID: `spec-0158`
- Status: `approved`
- Run: [Run234](../run/run-20261105-234-platform-storage-accounting.md)
- Attempt: `1`
- Parent Feature: [FEAT-0158](../feature/feat-0158-platform-storage-accounting.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Contract

Report actual configured app data, app cache and shared Hub cache. Measure regular
logical bytes without following nested symlinks and deduplicate hard links per
location. Missing locations are explicitly empty; unreadable/partial totals are
never silently zero. Resolve free space from each location's actual volume or
nearest existing ancestor for a not-yet-created directory. Group equal volumes;
never sum repeated free space. Use GiB for 1024-based numbers. Shared Hub size
includes other models/tools. Keep all source, cache-clear and backup/restore
ownership/eligibility unchanged. Windows paths are expected documentation only.

Storage read has pending, ready, partial, failed and retry states. Switching tabs
must not erase failure evidence or create requests to unavailable products.
