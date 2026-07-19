# EVAL-0036: Native Maintenance Session And Runner UI Consolidation — Contract

## Metadata

- ID: `eval-0036-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run ID: `run-20260719-41`
- Attempt: `1`
- Feature: [feat-0036-native-maintenance-session-and-runner-ui-consolidation](../feature/feat-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Spec: [spec-0036-native-maintenance-session-and-runner-ui-consolidation](../spec/spec-0036-native-maintenance-session-and-runner-ui-consolidation.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Runner/ingestion → Session and Usage ownership → UI/API boundary → current-truth artifacts
- Evidence Coverage: `complete`
- Created: `2026-07-19`

## Scope

- Evaluated the corrected native Claude Session source contract, removal of the synthetic stream producer, child maintenance inheritance, marker surface removal, shared command preview, and preservation of FEAT-0035's valid Session schema constraints.

## Checks And Evidence

- `runner_command_args()` is the single argument producer for process execution and user confirmation. It retains print/stream-json/verbose/plan/schema arguments and does not emit `--no-session-persistence`.
- `prepare_run` creates the Run ledger and artifacts but no Session. Terminal and interrupted paths invoke Claude-only native source synchronization.
- The ordinary Claude parser owns Session and Usage normalization. A registered internal header links the persisted primary to the unique Run FK; resolved Claude children inherit maintenance/metadata-only policy, keep a null Run FK, and lose event/search projections.
- `maintenance_usage.py`, Runner-stream Usage parsing, startup historical stream backfill, scanner preservation exceptions, and Usage repair exceptions are absent.
- Dashboard and Workstream marker controls, JavaScript, request model, and `POST /api/maintenance-runs` are absent. `POST /api/workstreams/{workstream_id}/runs` remains the sole in-app creation boundary.
- Data Model and generated Schema presentation remain at 20 ordinary tables, one FTS5 object, 244 columns, 20 physical FKs, 20 explicit indexes, 23 application relations, and eight owners. The enforced Run FK is no longer duplicated as an application relation.

## Actual Runtime Evidence

- The two FEAT-0035 synthetic `localbrain-run:*` Sessions each had zero Activity Events, Usage Records, search rows, children, Workstream/Thread links, and Checkpoint refs.
- A guarded transaction removed exactly those two Sessions, retained both `maintenance_runs` rows, left zero synthetic Session identities, returned `integrity_check=ok`, and reported no FK violations.

## Findings

- None. The separate compatible `maintenance_runs.workstream_id` FK repair remains outside this Run and is unchanged.

## Route

- Next action: `pass`.
