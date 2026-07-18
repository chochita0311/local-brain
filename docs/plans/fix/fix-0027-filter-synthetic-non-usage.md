# FIX-0027: Filter Synthetic Non-Usage

## Metadata

- ID: `fix-0027-filter-synthetic-non-usage`
- Status: `complete`
- Run ID: `run-20260718-29`
- Attempt: `3`
- Feature: [feat-0022-usage-summary-and-history](../feature/feat-0022-usage-summary-and-history.md)
- Spec: [spec-0022-usage-summary-and-history](../spec/spec-0022-usage-summary-and-history.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Sessions Dashboard read model
- Created: `2026-07-18`
- Updated: `2026-07-18`

## Input Report

- Human review identified Claude `<synthetic>` rows as assistant or API-error evidence rather than model usage and confirmed that real Haiku subsession usage must remain monetary usage.

## Fix Scope

- Exclude exact Claude raw model `<synthetic>` records in both the earliest-date query and shared dashboard Fact query.
- Preserve every stored Fact, source record, Session, and Activity Event.
- Preserve actual maintenance and subsession usage, including Haiku.

## Validation

- 84 automated tests passed.
- A private read-only runtime query omitted `<synthetic>` and retained the fully priced Haiku Model row.
- No schema, migration, sync, price, source, route, template, or client change was required.

## Remaining Issues

- None in scope.

## Return Decision

- `pass`
