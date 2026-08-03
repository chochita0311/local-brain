<!-- Generated from src/localbrain/value-registry.json by scripts/build-data-model-value-dictionaries.py. Do not edit. -->
# Data Model Value Dictionaries

This index projects the executable bounded-value authority into nine subject-owned dictionaries. The existing subject catalogs continue to own tables, columns, relationships, lifecycle, deletion, and recovery.

## Presentation Modes

- `direct`: every value in the complete family renders as its physical token.
- `logical-label`: every allowed value and permitted fallback uses the complete mapping.
- `internal-only`: the complete family stays off ordinary product screens.

A family never mixes modes. Runtime code loads `src/localbrain/value-registry.json`; it does not parse these Markdown files.

## Subject Dictionaries

| Subject | Families | Explicit exclusions | Dictionary |
| --- | ---: | ---: | --- |
| Source registry and scans | 9 | 2 | [Open](value-dictionaries/source-registry-and-scans.md) |
| Workspace and Session activity | 8 | 3 | [Open](value-dictionaries/workspace-and-session-activity.md) |
| Usage and cost records | 5 | 1 | [Open](value-dictionaries/usage-and-cost-records.md) |
| Local Context corpus | 4 | 1 | [Open](value-dictionaries/local-context-corpus.md) |
| Work organization and resources | 6 | 1 | [Open](value-dictionaries/work-organization-and-resources.md) |
| Atlassian source memory | 14 | 0 | [Open](value-dictionaries/atlassian-source-memory.md) |
| Review and resume continuity | 4 | 1 | [Open](value-dictionaries/review-and-resume-continuity.md) |
| Maintenance execution | 8 | 1 | [Open](value-dictionaries/maintenance-execution.md) |
| Derived retrieval index | 1 | 1 | [Open](value-dictionaries/derived-retrieval-index.md) |

## Verification

```bash
uv run python scripts/build-data-model-value-dictionaries.py check
uv run python scripts/check-data-model-docs.py
```
