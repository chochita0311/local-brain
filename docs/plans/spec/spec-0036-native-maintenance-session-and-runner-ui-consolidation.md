# SPEC-0036: Native Maintenance Session And Runner UI Consolidation

## Metadata

- ID: `spec-0036`
- Status: `approved`
- Run ID: `run-20260719-41`
- Attempt: `1`
- Parent Feature: [feat-0036-native-maintenance-session-and-runner-ui-consolidation](../feature/feat-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Parent PRD: [prd-0003-data-model-visibility-and-schema-cleanup](../prd/prd-0003-data-model-visibility-and-schema-cleanup.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: Runner and ingestion → Dashboard and Workstream UI → docs and generated contracts
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Implementation Goal

- Replace the invalid stream-backed synthetic producer with one native Claude Session source, and remove the now-redundant marker workflow while exposing the exact Runner command at the point of execution.

## Runner And Ingestion Contract

1. One shared command builder supplies both `asyncio.create_subprocess_exec` and the Workstream command preview.
2. Arguments retain `--print`, `--output-format stream-json`, `--verbose`, `--permission-mode plan`, and the structured `--json-schema`; `--no-session-persistence` is absent.
3. The composed prompt still begins with the internal Run/mode marker and is written to stdin. The selected basic request and optional extra request follow it.
4. `prepare_run` creates only the `maintenance_runs` ledger row and private artifact paths; it does not create a Session.
5. After a terminal or recovered Run, a Claude-only source scan ingests the native JSONL. Existing periodic startup sync remains a recovery path.
6. The native parser links a registered marker Session through `maintenance_run_id`; unregistered marker input remains classified maintenance without an FK.
7. Parent reconciliation propagates `maintenance` and `metadata_only` from a linked maintenance primary to Claude child Sessions, clears their activity/search material, preserves their direct Usage Records, and leaves their `maintenance_run_id` null.
8. Runner stream parsing, synthetic `localbrain-run:<id>` Sessions, stream Usage normalization, startup historical stream backfill, and scanner preservation exceptions are removed.

## UI And API Contract

1. Remove both Dashboard and Workstream Maintenance Run marker panels, their create/copy JavaScript, and `POST /api/maintenance-runs`.
2. Keep `POST /api/workstreams/{workstream_id}/runs` and the existing Task Runner interaction unchanged.
3. In the Workstream Runner form, show:
   - the selected task's basic request
   - the exact shell-rendered command from the shared command builder
   - a statement that the basic and extra requests are delivered through stdin
4. Use the existing compact panel hierarchy, typography, border, and code treatment. Long command content must scroll within its container at desktop and 320px widths.

## Data And Compatibility Contract

- Preserve FEAT-0035's fresh and compatible `session_class`, `index_policy`, `maintenance_run_id` FK/UNIQUE, and linked-row CHECK constraints.
- Native source cleanup and Usage repair again follow ordinary source ownership; no special preservation branch exists for linked Maintenance Sessions.
- Historical synthetic test Sessions may be removed only after a guarded local preflight proves they have no events, Usage Records, search rows, parent/child edges, or curated relations. Historical Run ledger rows remain.
- `maintenance_runs.workstream_id` compatible FK restoration remains explicitly out of scope.

## Documentation Contract

- Task Runner, architecture, Session/activity, Usage/cost, maintenance execution, privacy, Data Model, backlog, and PRD continuity all name native Claude JSONL as source of truth and `stream.jsonl` as an operational artifact only.
- FEAT-0035 and RUN-40 record the rejected producer assumption and point to FEAT-0036/RUN-41 rather than appearing current.

## Evaluation Focus

- Exact command producer parity and absence of the no-persistence flag.
- Primary and child maintenance classification, usage inclusion, and work-consumer exclusion.
- No synthetic producer or marker surface residue.
- Desktop and narrow Workstream containment plus Dashboard/Workstream route behavior.
- Full regression, schema presentation parity, privacy, and guarded actual-data cleanup.

## Open Blockers

- None. The human owner directly approved the correction boundary and explicitly allowed the negligible historical test streams to be ignored.
