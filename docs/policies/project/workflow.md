# Session Workflow

This contract owns Session Episode identity, deterministic Focus projection, user assertions and the Workflow route. It preserves the distinction between observations, candidates and user-confirmed corrections; Workstream organization remains separately owned.

## Workflow Episode And Direction

- A workflow Episode is a rebuildable descriptor of one eligible primary work
  Session, not a new persisted resource or a replacement for the Session. Its
  stable derived key hashes the length-delimited numeric source ID and source-native
  Session ID; the current local Session ID remains navigation only. Subsessions
  remain evidence owned by their primary Session rather than peer Episodes.
- Episode observation bounds use the earliest and latest valid source-backed
  timestamps. Activity (`active`, `quiet`, `unknown`), lifecycle (`open`,
  `closed`, `unknown`), closure reason, and authority are separate axes. A
  Session ending is an observation and never proves that its work closed.
- Direction is intentionally limited to `continues`, `branches-from`, and
  `merged-into`. A retained relation must move strictly forward in observation
  time, avoid self-edges and directed cycles, and cite at least one strong
  reason: a direct source relation, a shared reference, explicit Thread or
  Workstream membership, or a user assertion. Workspace, Git, lexical, temporal,
  and similar proximity can support a relation but cannot establish one alone.
- Candidate, explicit-organization, and user-confirmed authority remain visibly
  distinct. Invalid or insufficient relations are omitted with bounded
  diagnostics; LocalBrain does not silently upgrade a candidate into user
  organization or invent intent, outcome, next action, or closure.
- The versioned Episode and direction contract is a pure in-memory projection.
  It reads no database or source, performs no remote or model work, persists
  nothing, and changes no existing Session, Workstream, or navigation behavior.
- The database-backed source and candidate Focus projection is derived on
  demand and read-only. It always returns an eligible selected Episode, then admits at most
  200 relation candidates through exact shared user Thread membership, or a
  documented combination of shared direct reference, user Workstream,
  workspace, and observed Git facts. One broad Workstream, workspace, Git root,
  branch, title, wording, or nearby time never creates a line alone.
- `continues` joins adjacent time-ordered Episodes inside one qualifying exact
  set. `branches-from` requires the same non-empty observed Git root, different
  non-empty observed branches, and a shared direct reference or user
  organization owner; it remains a deterministic candidate, not a claim about
  Git ancestry. A later return to `main`, `master`, or another branch name does
  not infer `merged-into`.
- A Focus result contains at most 24 Episodes, four outward side-branch roots,
  four Episodes reached within one side branch, and five expanded evidence
  items per source family. Candidate, Episode, branch, and evidence totals keep
  truncation visible. Jira, Wiki, Local Context, local/external Resources,
  Workstream/Thread memberships, and direct Subsessions attach as evidence;
  they do not become peer workflow nodes.
- Opening or recomputing Focus consumes only current normalized SQLite state.
  Stale or unavailable evidence stays labeled, and the read starts no Session
  synchronization, source scan, body parse, external discovery, Atlassian Sync
  or Refresh, model, embedding, or database write.
- An eligible primary Session detail exposes one additive `작업 흐름` link to
  `/sessions/{id}/workflow`. The separate Focus surface keeps Episodes on a
  stable time-directed spine, places bounded side branches on deterministic
  lanes, and keeps Jira, Wiki, Local Context, Resource, organization, and
  Subsession records inside the selected Episode's evidence constellation and
  Trace rather than turning them into peer nodes. Selecting an Episode updates
  its canonical Workflow URL and reveals its supported ancestry, descendants,
  adjacent directions, complete reason list, and safe source destinations.
- Focus rendering is progressive enhancement over a server-rendered lineage.
  Wide layouts use a left-to-right time axis, compact layouts use the same
  relations top-to-bottom, and narrow, no-script, or render-failure states keep
  the text lineage and Trace usable. An unconnected Session remains a valid
  one-Episode result and never implies completion. Missing, ineligible,
  partial, stale, unavailable, and unexpected-error states preserve an honest
  local return path.
- Focus browsing remains read-only. A contextual correction form can append a
  user-confirmed relation or lifecycle assertion only after showing the exact
  consequence; it does not create or rename Workstreams, rewrite a candidate or
  its reasons, refresh a source, generate a summary, or use Qwen, embeddings, or
  another model. Existing Session conversation, pin, metadata, Subsession, and
  Related Materials behavior stays authoritative and unchanged.

## Workflow Assertion And Correction

- Consequential workflow correction belongs to one dedicated local assertion
  ledger, not to Sessions, candidate relations, Workstream/Thread membership,
  or Suggestions. It targets stable Episode keys and retains nullable current
  Session IDs only as lookup aids.
- The exact initial actions are `same-flow`, `split-here`, `merge-into`,
  `close`, and `reopen`. Close always requires one explicit reason:
  `completed`, `abandoned`, `superseded`, `merged`, or `other`; inactivity,
  Session end, and age never imply closure.
- User-confirmed assertions overlay the derived Focus projection after source
  and deterministic candidate assembly. They control the effective selected
  boundary while the complete base relation, evidence reasons, and base
  lifecycle stay available for Trace.
- Action, correction, reopen, and undo are append-only superseding records.
  Undo applies only to the current record in one boundary chain and restores
  the prior effective meaning without deleting history. Missing source Episodes
  retain unresolved assertions for later deterministic re-resolution.
- Mutation is explicit, local, revision-checked, and atomic. It never writes a
  source file or external system, starts Refresh or synchronization, changes
  Workstream organization, or calls Qwen, an embedding service, or another
  model.
- The selected Episode or relation Trace offers only currently valid actions.
  Each ordinary form exposes the exact before/after meaning, affected Episodes,
  user-confirmed authority, and supersession consequence before submission;
  choosing or cancelling a disclosure performs no write.
- Success reprojects the same bounded Focus and highlights the corrected
  boundary while restoring the selected Episode, branch disclosures, evidence
  disclosures, scale, pan, Trace and page scroll, and meaningful keyboard
  focus. A stale revision or validation failure keeps the prior map in place,
  restores the owning controls, and offers an explicit reload path. Narrow and
  no-script presentations retain the same sequential form and fixed result
  language.

## Workflow Projection And Correction

The pure descriptor contract precedes the database read projection. User
assertions overlay that projection through a separate mutation boundary;
the route renders the resulting payload.

### Workflow Projection Contract

- `workflow/projection.py` owns the versioned, pure descriptor boundary for
  workflow Episodes, directional relations, reasons, and omission diagnostics.
  Importing or calling this contract performs no SQLite, filesystem, source,
  connector, network, model, embedding, or maintenance work.
- One Episode corresponds only to an eligible primary work Session. Its opaque
  key is derived from a length-delimited numeric source ID and source-native
  Session ID; local row ID is carried only as the current `/sessions/{id}`
  navigation destination. No Episode table exists. The source-PK upgrade converts
  retained assertion boundaries for existing Sessions; assertion IDs and history
  remain unchanged.
- Observation time, activity, lifecycle, closure reason, and authority remain
  separate descriptor fields. `sessions.ended_at` may extend the observation
  bound but cannot infer lifecycle closure.
- Relation normalization accepts only `continues`, `branches-from`, and
  `merged-into`, requires a strictly later target plus at least one strong
  source, organization, or user-assertion reason, and deterministically omits
  self-edges, invalid values, unsupported authority/reason combinations, and
  edges that would form a directed cycle. Workspace, Git, lexical, and temporal
  signals are supporting evidence only.
- Descriptor serialization is bounded and excludes source messages, document
  bodies, opaque payloads, raw local paths, and source-native Session IDs.
  Database-backed producers must assemble this shape from already-normalized
  facts without weakening the contract or persisting an inferred graph.

### Workflow Focus Read Model

- `workflow/focus.py` is the sole initial database-backed producer of the
  versioned Session Focus payload. It accepts one local Session ID, validates
  primary-work meaningful eligibility, and returns `ready`, `missing`, or
  `ineligible` without adding a route or persistence owner.
- The producer reads Session/source/workspace metadata, privacy-minimized direct
  reference keys, user-authored organization links, current Related Materials,
  direct-child metadata, and persisted Atlassian structure-reference identity.
  It never selects Activity Event text, Context Document body, source path for
  output, remote body, opaque payload, or search text.
- Candidate admission is exact and conjunctive. Shared user Thread is
  sufficient; otherwise shared reference or user Workstream must combine with
  the documented workspace/Git fact. Classification sees at most 200 candidates
  and uses stable strength, temporal-distance, observation, and Episode-key
  ordering. Generated or accepted-suggestion membership may remain evidence but
  is not directional authority in this baseline.
- The relation producer creates adjacent `continues` candidates and nearest-
  earlier `branches-from` candidates, selects at most one derived incoming edge
  per Episode, emits no heuristic `merged-into`, and delegates forward-time,
  reason, and acyclic validation to `workflow/projection.py`.
- Stable outward traversal owns the 24-Episode, four-branch-root, and four-
  Episodes-per-branch limits. Evidence assembly reuses the stricter Related
  Materials destination boundary, groups source families with a five-item
  presentation limit, and reports observed versus retained totals and
  stale/partial state.
- The entire call is a SQLite read projection. It performs no DML, schema work,
  cache write, source parse, filesystem check, connector/capability operation,
  Refresh, network request, model call, or background scheduling. Repeating it
  against unchanged SQLite state returns the same semantic ordering.

### Workflow Assertion Ledger And Overlay

- `workflow/assertions.py` owns the only workflow-correction mutation and
  overlay boundary. The `workflow_assertions` table is append-only application
  state keyed by a digest of stable Episode identity; nullable Session foreign
  keys are current lookup aids with `ON DELETE SET NULL`, and one unique
  self-supersession link prevents a history fork.
- The domain exposes exact create, undo, history, and overlay operations. Each
  write recomputes the current overlay, compares an optimistic projection
  revision, validates endpoints, forward time, incoming-boundary consistency,
  cycles, tip closure, and active supersession, then appends inside one bounded
  savepoint without committing its caller's outer transaction.
- Focus first constructs the unchanged source and deterministic
  candidate projection. Active user assertions then replace only the effective
  selected relation pair or Episode lifecycle. The read model retains
  `base_relations`, base lifecycle, resolution summaries, diagnostics, and a
  deterministic revision so presentation and Trace can distinguish observed,
  candidate, and user-confirmed authority.
- Assertion rows survive Session deletion and projection rebuild. An absent or
  newly incompatible endpoint makes the active assertion unresolved rather
  than deleting it or weakening graph invariants; restoration of the same
  source-scoped native identity can resolve it again.
- These operations read or write only normalized SQLite state. They perform no
  source-file, Git, connector, remote, Refresh, synchronization, model,
  embedding, training, or Workstream-organization mutation.

### Session Workflow Focus Route

- `workflow/map.py` is the pure presentation adapter for one validated
  `WorkflowFocusProjection`; `workflow/correction_view.py` adds registry-backed
  active-assertion summaries, stable boundary identities, exact consequence
  previews, and only currently valid actions without querying a second
  authority. `GET /sessions/{id}/workflow` opens one SQLite connection, invokes
  `workflow_focus_projection` once, closes that read scope, and then renders
  only the returned payload. It has no detail-query fallback, source/body
  access, connector, background task, model call, or write.
- `workflow_session_is_eligible` shares the primary-work/full-index/
  meaningful-activity predicate with Session detail. Its failure is isolated so
  the existing Session route omits only the additive Workflow link and still
  renders conversation, pin, Subsessions, and Related Materials.
- `session-workflow.html` is the complete server fallback and Trace owner.
  Every retained Episode, relation, reason, evidence group, availability, and
  safe destination exists before enhancement. Its correction partial uses
  ordinary forms and exposes exact before/after, endpoints, authority,
  supersession, close reason, bounded note, cancel, and recovery controls before
  JavaScript runs. Missing, ineligible, and unexpected projection states render
  bounded local destinations with `404`, `422`, and `500` respectively; a
  connected or unconnected ready projection is `200`.
- `workflow/correction.py` owns the strict `application/x-www-form-urlencoded`
  boundary for `POST /sessions/{id}/workflow/corrections`: at most 16 KiB and
  eight fields, exact action-specific shapes, one optimistic projection
  revision, bounded note, strict percent decoding, and same-origin Fetch
  Metadata. The route reconstructs Focus and performs exactly one assertion
  apply or undo inside one transaction. Success commits once; parse,
  validation, conflict, and unexpected failure roll back completely and expose
  only fixed local messages. Enhanced requests receive bounded JSON with
  `200`, `409`, `422`, `400`, or `500`; ordinary forms receive a same-route
  `303` on success or a server-rendered current map on failure.
- `workflow-map.js` is a route-scoped fixed renderer. Observation order and
  stable Episode keys determine positions; `continues` retains a lane and
  `branches-from` allocates the next stable lane. It draws no force simulation
  and persists no durable layout. Selection and bounded branch disclosure
  change only DOM state; Episode selection pushes the target Session's canonical
  Workflow route, and back/forward restores an in-payload focus without
  recomputation. Immediately before an enhanced correction it records a
  bounded, versioned, path-scoped one-shot restoration envelope in
  `sessionStorage`; the following successful same-route render consumes and
  removes it after restoring only selected Episode, branch/evidence disclosure,
  scale, pan, Trace/page scroll, corrected-boundary focus, and a fixed result
  code. Failure does not reload or replace the graph and re-enables only the
  owning form.
- The graph owns only modified wheel/pinch zoom and its bounded scroll region.
  Ordinary wheel input remains with page or viewport scrolling. At the existing
  `920px` breakpoint direction becomes vertical; at `700px` and below the
  graphical viewport yields to the server lineage. Renderer failure does the
  same while leaving controls disabled and Trace navigable.
