# SPEC-0061: Bounded-Value Consumer Normalization

## Metadata

- ID: `spec-0061`
- Status: `approved`
- Run ID: `run-20260724-66`
- Attempt: `1`
- Parent Feature: [feat-0061-bounded-value-consumer-normalization](../feature/feat-0061-bounded-value-consumer-normalization.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Surface Lanes: registry projection → server/client consumers → ordinary-screen vocabulary → drift checks
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Source Set

- Human approval on `2026-07-24`: execute both approved PRDs' Features automatically and sequentially.
- Passed FEAT-0057 registry, nine generated subject dictionaries, and its exact visible-consumer inventory.
- Current bounded-value producers, query projections, routes, templates, form redisplay, and client-side Run polling.
- Design Constitution, Design Evaluation, and Interaction Evaluation using the Fullstack Product profile.
- Screen Alignment mode: `extend`; the repository constitution is the target and no durable Figma file key is owned by the source set.

## Registry And Projection Contract

- `src/localbrain/value-registry.json` remains the executable authority. The current inventory contains `54` families: `40` complete `logical-label` families and `14` `internal-only` families.
- The `40` logical-label families own `72` registry-backed path declarations. Every ordinary template family reference must be declared in that inventory, and every declared ordinary template path must call the named family.
- A complete logical-label mapping may own zero current visible consumers. The registry must not force a defined family onto an ordinary screen merely to satisfy consumer inventory parity.
- `visible_value_label` remains the strict contract helper. A missing family, internal-only family, invalid type, unknown value without an approved label, or incomplete mapping raises a bounded registry error.
- `display_value_label` is the ordinary-screen projection. It delegates to the strict helper and converts any rejected value to `표시할 수 없음`; it never returns the raw input as fallback.
- `visible_value_help` exposes only approved registry help for visible families.
- Physical values remain the source for persistence, form values, CSS state classes, query behavior, polling decisions, and API identity. Presentation labels are separate outputs.

## Consumer Contract

- Server-rendered values in Sources, Sessions, Session/Subsession detail, Sessions Dashboard, Local Context, Dashboard, Workstreams, Workstream detail, Local Resource, Atlassian browse/Add/item/refresh, Search, and maintenance Run views resolve through `value_label`.
- Consequential bounded coverage help resolves through `value_help`; ordinary screen-local partial dictionaries are not introduced.
- Run polling reads raw status only from the explicit `data-run-status` behavior field and uses the server-projected `status_label` for visible replacement text.
- Query projections expose the physical family value needed by the shared presentation boundary; they do not synthesize duplicate labels.
- All allowed values in one family use the same mapping. Internal-only families remain absent from ordinary screens.

## Drift And Safety Contract

- Registry checks compare schema `CHECK` vocabularies, approved application constants, required boolean/derived families, generated dictionaries, and the path/family consumer inventory.
- Static tests reject a declared ordinary consumer that omits its family call, a template family call absent from the inventory, an incomplete mapping, a known raw-token direct output, or client polling that replaces visible state with the raw status.
- Unexpected runtime values render `표시할 수 없음` and do not change the underlying state machine.
- User-authored content, Session text, Document text, external titles/content, identifiers, URLs, and diagnostic schema payloads are outside translation.

## Presentation Contract

- Ordinary state badges, facts, counts, filters, select options, empty/error text, and dynamically replaced Run status use one coherent family vocabulary.
- Short labels describe current state. Registered help explains coverage or other consequential meaning without making the label itself verbose.
- A logical-label definition does not require every physical state to appear on every ordinary screen. Local Context source lists keep label, path, and document count only; the selected source toolbar owns the single useful root-status label.
- Existing component structure, semantic state roles, keyboard behavior, and layout remain unchanged except for bounded text growth.
- Supported widths remain `1440`, `920`, `700`, and `320`; no affected page may acquire horizontal document overflow.

## Verification

```bash
uv run python -m unittest \
  tests.test_value_registry tests.test_ui_contract tests.test_session_pin_ui \
  tests.test_session_details tests.test_usage_dashboard tests.test_atlassian_browse \
  tests.test_atlassian_refresh tests.test_atlassian_registration tests.test_external_access \
  tests.test_workstreams tests.test_context_roots tests.test_session_inventory \
  tests.test_runner tests.test_external_sync tests.test_retrieval -v
uv run python scripts/build-data-model-value-dictionaries.py check
uv run python scripts/check-data-model-docs.py
```

- Render a temporary synthetic database at `1440`, `920`, `700`, and emulated `320`.
- Inspect Sessions Dashboard, Workstream/Run, Atlassian browse/item, Search, Local Context, and Session detail.
- Confirm complete labels, bounded fallback/help, no relevant raw-token output, no horizontal overflow, no console errors, and no external requests.

## Open Blockers

- None.
