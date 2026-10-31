# Auto Work

This contract owns explicit full-history simulation, passive affinity inspection and the separate retained sample mode. Similarity and source observations do not establish production work identity, causal lineage or organization approval.

## Auto Work Inspection

`자동 작업`, immediately above Workstreams in the sidebar, is a read-only
inspection destination. Its default full-history affinity map observes prepared
coarse groups, finer subgroups and Session evidence without creating Workstream
identity or an approval queue. Actual message time runs left-to-right; curved
strands and their activity knots expose recurring similar material. Empty periods
are dashed, not continuous work duration. Unknown dates stay unplaced. The map
does not expose raw embedding points: each knot combines a group's chunk
occurrences within one period. Its capped size reflects occurrence volume,
not distinct Session count or grouping quality. Coarse and within-parent finer
similarity groups are already applied; their meaning is not a verified enduring
work area or common task. Selection
preserves geometry; matching strands and connections share one continuous map,
independent of the text list's 24-item pages. Horizontal scrolling traverses time,
vertical scrolling reaches other strands, and list paging preserves the camera.
A period knot filters exact evidence to that observed interval,
and explicit neighborhood zoom or hierarchy expansion brings context closer.
Time-anchored undirected edges express similarity only, not a causal branch/merge. Representative
Session titles, observed dates, exact quotes, overlap, fragmentation, exclusions
and complete paginated access keep uncertainty visible. All admitted indexed
history is covered, not a first-60 sample. Viewing is passive; source changes,
invalid/expired results and obsolete selections are explicit recoverable states.
The map consumes the existing 30-day simulation owner, never a new private corpus.

The separately labeled previous-sample view presents unassessed rule-based
output. It presents all inferred
groups and unassigned statements through bounded pages, literal source/span
evidence, and the actual chronological sample boundary. It is not a quality
verdict, replacement Workstream inventory, or approval/promotion queue.

Ordinary browse revalidates the frozen local evidence; it never starts analysis.
Its `결과 갱신` explicitly prepares the currently stored eligible history through
now under the existing experiment caps, excluding manual organization from the
grouping arm. It uses no model, remote call, source rescan, or organization write.
One private result is retained for seven days and atomically replaced on a
successful refresh; failure keeps the previous valid result. Expired or changed
evidence is not displayed as current. Unassessed inspection may precede quality
assessment; production replacement still cannot.

## Full-History Simulation Producer

`auto_work/simulation.py`, its verified local encoder and ordered grouping engine
produce the private input for observation-only affinity inspection. Preparation
is explicit; browsing cannot invoke it. It accounts for all stored Sessions and
processes all nonempty user/assistant messages of admitted primary/full work
Sessions. Maintenance, Subsessions, metadata-only and missing-source Sessions,
non-message Events, empty messages and unknown dates retain separate counts;
an unknown date does not remove otherwise eligible text. This is experimental
similarity grouping, not admitted work identity or causal lineage.

Character windows are exhaustive and non-overlapping: default 1,800 code points,
accepted integer range 128–16,000. Source text is reread only for verified spans;
stored inventory holds identity, hashes, role, offsets and observed time, not a
full-body copy. Stable source/native Session identity and Event/span coordinates
address occurrences; repeated embedding inputs may share a vector while every
source occurrence survives. Complete source inventory is revalidated before
publication, so concurrent change refuses a new current report.

| Producer parameter | Current default / accepted values |
| --- | --- |
| Embedding batch size | 16; 1–256 |
| `neighbors` | 8; integer 1–64 |
| `similarity` | 0.65; `0 < value <= 1` |
| `area_resolution` / `work_resolution` | 0.6 / 1.2; each `0 < value <= 10` |
| `seed` | Integer 0 by default |

An encoding execution verifies model files before private input is read;
inventory-only/status/purge do not invoke an encoder. Local-files-only,
offline/telemetry controls and the existing outbound Python socket guard precede
inference; they are not an OS network sandbox. No model download, training,
external inference or source modification follows from simulation. New vectors
are finite, correctly dimensioned and normalized. Cache reads check dimension
times four bytes, finite values and a nonzero norm. Missing/corrupt vectors are
recomputed in committed bounded batches; unchanged compatible vectors are reused.
Changing grouping parameters can reuse vectors; source/model/chunk/runtime
identity controls compatibility. A fixed seed alone is insufficient: the current
`cosine-knn-louvain-v2-ordered` engine canonicalizes node/neighbor order in both
coarse and within-parent passes, preserves disconnected components/singletons,
and emits undirected similarity rather than causal edges.

### Simulation Store And Report

The existing `localbrain.session-simulation.v1` owner binds its private directory
to the database's resolved path, device and inode. The database must be an
existing absolute regular non-symlink file. Output must be an absolute resolved
private runtime directory outside the repository/package and distinct from the
database directory, with an existing parent. Private ownership/permissions,
recognized files and no symlink/hardlink substitution are checked before use;
unknown/unowned output refuses adoption or cleanup. A nonblocking exclusive
`writer.lock` serializes producer/purge work. Atomic owner-only JSON publication
never treats an unfinished write as a valid result.

| Owned file or report field | Contract |
| --- | --- |
| `owner.json`, `writer.lock` | Marker fields `owner`, `database`, `expires_at` bind the source and 30-day inactivity expiry; the separate lock serializes work; both survive purge |
| `state.sqlite3` and its rollback journal | Rebuildable current inventory, unique content-addressed vectors and compatibility metadata; no second authoritative application DB |
| `progress.json` | Fixed prepared/inventory/embedding/grouping/complete or failed/interrupted state and aggregate progress; normal CLI stdout stays fixed codes unless counts are explicitly requested |
| Report identity | `owner`, UTC `created_at`, source `manifest`, `model` contract, `namespace`, `parameters`, `configuration` digest |
| Report authority | `processing_complete=true`, `quality='unassessed'`, `lineage_status='not_inferred'`; completion is not semantic quality |
| Source `manifest` | `extraction='all-message-character-windows-with-session-context.v1'`, `chunk_chars`, complete `coverage`, `digest`, `sampled=false` |
| `sessions` / `chunks` | Session `key`, local `id`, at-most-300-character `title`, `status`; each original-address chunk's `key`, `session_key`, `event_id`, `start`, `end`, `content_hash`, `input_hash`, `role`, `at` |
| `grouping` | `engine`, `authority='inferred-affinity-only'`, `areas` (ID/members and complete within-parent `work_groups`), `node_count`, `edge_count`, `singleton_areas`, finite undirected `edges` (`left`, `right`, `similarity`) |
| `inspection` | `areas`, `single_session_areas`, `cross_session_areas`, `sessions_in_multiple_areas`; each area's `area_id`, `session_keys`, `representative_title`, `label_basis='source-session-title-not-area-name'`, `representative_chunk`, known `observed_dates`, `lifecycle='unknown'` |
| `cache` / `comparison` | `reused`, `encoded`, `total`; `previous_available`, `same_input`, `same_configuration`, `same_grouping` |
| Published files | Atomic `report.json` and at most one `previous-report.json`; no full raw message-body backup |

Namespace hashes model contract, extraction version and chunk size; configuration
also hashes grouping parameters and engine identity. Content changes replace
current inventory atomically and remove unused vectors. Only after successful
report publication are old model namespaces pruned. Interrupted work retains
checkpoints, and a failed run does not publish an incomplete current report.
After 30 inactive days, the next explicit execution/startup/owned storage cleanup
enforces expiry; status rejects expired state. Explicit purge removes only known
derived files under lock, preserving sources, shared public weights and marker/
lock. Recognized abandoned atomic-write scratch is removed only inside this
validated owner. There is no new scheduler, private corpus or automatic model run.

Manifest coverage names `total_sessions`, `eligible_sessions`,
`excluded-maintenance_sessions`, `excluded-subsession_sessions`,
`excluded-metadata-only_sessions`, `excluded-missing-source_sessions`,
`excluded_nonmessage_events`, `message_events`, `empty_events`,
`unknown_date_events`, `admitted_characters`, `chunks`, `sessions_with_text` and
`sessions_without_text`. Session status uses the same eligible/excluded vocabulary.
The grouping parameter mapping contains exactly `neighbors`, `similarity`,
`area_resolution`, `work_resolution` and `seed`. The engine records `method` and
`numpy`, `sklearn`, `networkx` versions for replay compatibility. After publication,
the private checkpoint DB is vacuumed; no full-text copy is retained there.

The [Developer Guide](development/session-simulation.md#operations)
owns invocation and replay operation. Frozen experiment/evaluation records retain
their original processing/replay evidence; neither an exhaustive run nor a valid
report admits production work semantics, organization changes or a new extractor.

## Observation-Only Work Inspection

### Auto Work Inspection Read Model

`GET /auto-work` defaults to the current `auto_work/affinity.py` consumer. The
server renders complete native text navigation and exact evidence; optional
`affinity-map.js` draws a viewport-bounded temporal SVG and owns zoom/pan plus cancellable
same-route navigation. History retains only viewport/Trace coordinates and edge
visibility preferences and text-list disclosure, not evidence. Reader `v2`
separates 24-row `nodes` from full matching-scope `map_nodes` and edges. Map
scope includes snapshot/hierarchy/search, never a text/evidence page or selection.
Native scroll extents move a sticky SVG viewport; horizontal movement traverses
time and vertical movement reaches every strand. List paging keeps geometry and
camera. Initial inspection is 200%; whole-time fit is 100%. Adjacency indexing
avoids per-knot whole-edge scans and repeated all-node sorting.
Selection never changes the layout input. The read model derives a common absolute-time
domain before search/paging, comparing timezone-aware observations as instants.
Serialized occurrence times retain admitted offsets; the renderer uses epoch
milliseconds and a UTC-labeled axis. Period boundaries start at midnight in
the earliest observation's retained offset.
The read model supplies at most 64 day-multiple activity periods per strand,
exact occurrence counts and existing-edge witness dates. Optional `period`
selection filters original evidence without changing snapshot identity or storage.
At the selected hierarchy level, each knot aggregates one group's occurrences
within one time period, not a single embedding point or a distinct Session.
Knot radius grows logarithmically with occurrence count and is capped; it is not
a cohesion, confidence or importance score. A group observed in only one period
can therefore remain a lone point even after both grouping stages. Neither the
generative work-context trials nor the source-claim/state projector feeds this
reader. The rule-based sample is a separate consumer, not a third merge.
Unknown times stay outside the dated plane. The renderer locks x to time and
uses deterministic affinity ordering/vertical attraction, curved strands and
explicit empty-period gaps; dates and labels remain readable under zoom. A
selected-neighborhood lens and short reduced-motion-aware camera transitions
provide observation rather than editing or perpetual physics.
Browsing cannot invoke the producer. The reader validation, payload bounds
and states are defined below.

#### Affinity Reader Contract And States

The current reader emits `localbrain.session-affinity.v2` from the existing
simulation store. A nonblocking shared writer lock protects passive reads. The
directory must be resolved, user-owned and private; the lock, owner marker and
report must be safe owned regular files. `owner.json` is bounded to 64 KiB and
`report.json` to 128 MiB. Validate the simulation owner, exact database path/
device/inode binding and unexpired marker before consuming the report.

The report must be processing-complete, unassessed and lineage-not-inferred, with
the current extraction and ordered grouping engine, an unsampled manifest,
valid parameters, matching namespace/configuration digests over the recorded
model contract, complete source coverage,
valid occurrence identities and exact coarse/within-parent membership partitions.
Finite unique undirected edges and coverage/count identities are checked; a
well-formed JSON object alone is insufficient.

- Session keys are unique 64-hex digests; local IDs are positive actual integers,
  titles are strings of at most 300 characters, and statuses use the producer's
  eligible/excluded vocabulary.
- Each chunk belongs to an eligible Session, has integer
  `0 <= start < end` with `end - start <= chunk_chars`, a string Event ID of at
  most 1,000 characters, user/assistant role, valid content/input hashes, a
  matching occurrence key and an at-most-80-character timezone-aware time or
  unknown. Chunk keys are unique.
- Every distinct embedding input belongs to exactly one coarse group and one
  subgroup within that parent. Groups have nonempty unique members and matching
  kind/member-derived IDs. Unique undirected edge endpoints are ordered, weights
  are finite with `0 <= similarity <= 1`, and stored totals/counts agree.

One derived index may live only in process memory, keyed by report signature and
source DB/WAL signatures. A changed key triggers exhaustive current source
inventory, not a sample; signatures must remain stable through validation.
Current manifest mismatch withholds old map/evidence and reports old/current
coverage plus added/changed/removed occurrences. Exact displayed passages are
independently resolved from current SQLite and checked for source/role/time,
span length and content/embedding-input hashes. No persistent reader cache or
new owner is created. An evidence row starts `available=False`; only a passing
current source check adds literal `wording`, Session `href` and `focus_href`.
Missing/changed evidence stays unavailable without a replacement quote or anchor.

The public payload groups these fields:

| Family | Fields |
| --- | --- |
| Identity and coverage | `version`, `state`, `snapshot`, `created_at`, `coverage`, `counts`, `model`, `parameters`, `configuration` |
| Scope and selection | `level`, `map_scope`, `scope_title`, `crumbs`, `q`, `base`, `selection`, `timeline`, `period` |
| Matching map and text | Whole matching `map_nodes`, `edges`; paged `nodes`, `total`, `matched`, `page`, `pages`, `previous`, `next` |
| Exact source evidence | `evidence`, `evidence_total`, `evidence_page`, `evidence_pages`, `evidence_previous`, `evidence_next` |
| Local recovery/navigation | `clear_url`, `overview_url`, `inventory_url` |

URL inputs are `snapshot`, `group`, `subgroup`, `pick`, `inventory=all`, `q`,
`page`, `evidence_page` and `period`. `q` is trimmed to at most 120 characters and
matched case-insensitively against group/constituent Session titles across the
complete selected level. Page input must be digit text of at most six characters;
otherwise it defaults to one. Valid numbers clamp to available pages. Snapshot
identity hashes the source-manifest digest and grouping
configuration; group and membership identities stay snapshot-scoped. Text lists
have 24 rows; evidence has eight occurrence rows. Title search covers the whole
selected level. Inventory includes stored excluded/no-text Sessions. Selection
is separate from expansion; observed role, offsets and time accompany literal
text. Undirected edge maxima are similarity, not confidence or causation.

Refusal states carry `version`, `state`, `title` and `explanation`.
`selection-stale` also supplies a valid `overview_url`; `stale` carries the old
`coverage`, `current_coverage`, `created_at` and `delta` counts for `added`,
`changed` and `removed` occurrences.

| Reader state | Predicate and consequence |
| --- | --- |
| `missing` | No owned result directory or no published report; no preparation starts |
| `busy` | Shared lock unavailable or source DB/WAL changes during validation; wait/retry without trusting a mixed snapshot |
| `current` | Complete validated source-bound report matches current inventory; a zero-match title query is still a current search result |
| `stale` | Current complete source manifest differs; hide old map/evidence and expose coverage/deltas without rerunning |
| `expired` | Owner expiry is at or before the read time; do not renew it on GET |
| `invalid` | Ownership/shape/size/version/configuration/coverage/partition or value validation fails; never overwrite or repair it on browse |
| `unavailable` | Database is absent/unsafe or local filesystem/SQLite access fails; source evidence is unavailable |
| `empty` | A valid current report contains no coarse groups; not a synonym for no title-search matches |
| `selection-stale` | Snapshot, hierarchy, selected membership or period is obsolete/invalid; return to valid overview rather than remapping selection |

Missing/stale/expired/invalid results never fall back silently to the prior sample.
GET neither creates/renews/deletes store artifacts nor computes vectors/groups,
collects sources, calls a model/external service or changes organization. Current
v2 keeps every matching strand and connection on one map regardless of text or
evidence page. Paging text or evidence never partitions that map.

### Sample Inspection

The separate `auto_work/preview.py` preview adapter consumes the experimentally verified
preparation/extraction shape, not the Focus projection. `GET /auto-work?mode=sample` reads
one owner-checked, 10-MiB-bounded, seven-day runtime file, revalidates current
source eligibility and frozen hashes through the read-only input adapter, and
binds displayed wording to admitted spans. Server-side pages expose every group
and unassigned statement with constructed local source destinations. Unknown
assessment remains unknown. It owns no DB table, production flow ID or correction.

`POST /auto-work/refresh` requires same-origin loopback access and an empty body.
It redirects back to the labeled sample mode, never refreshes the full-history map.
The server invokes the explicit preview command in a separate subprocess with
fixed configured input paths, quiet output and a 300-second outer timeout;
preparation and extraction retain their own 120-second/512-MiB limits. An
advisory lock makes refresh single-flight. Atomic, owner-only replacement retains
the prior valid result on failure; staging is removed on every write outcome.
Expired valid owned output is removed on a subsequent visit under that lock.
There is no startup/GET analysis, background job, source sync, model, migration,
or organization write. The sidebar link is capability-gated during mixed-version
template/server updates; a server restart activates the new route.

<a id="current-implementation-baseline"></a>

## Implementation Ownership

- `auto_work/simulation.py` and `auto_work/graph.py`, using shared
  `models/embedding.py`: explicitly invoked full-Session experiment;
  source-read-only inventory, separately owned replayable cache, verified local
  embeddings and experimental two-resolution affinity communities. The
  [simulation producer contract](#full-history-simulation-producer)
  owns current report/lifecycle definitions; the [Developer Guide](development/session-simulation.md#operations) owns command operation. No automatic preparation, source migration,
  production identity or causal-lineage inference is introduced.
  Source messages are exhaustively chunked (1,800 characters by default), encoded,
  and linked by thresholded cosine nearest-neighbor similarity. Weighted Louvain
  first forms coarse communities, then runs within each parent to form finer
  communities. These are nested similarity groups, not two successive
  work-identity merges. Disconnected components and singletons remain explicit;
  one Session can contribute chunks to several groups. Group counts are derived,
  not a fixed number of Workstreams.
  Inventory uses bounded character read-ahead with unchanged exhaustive chunk
  boundaries. The ordered v2 grouping engine canonicalizes node and neighbor
  insertion for each Louvain pass, including nested communities; fixed RNG seed
  alone does not guarantee cross-process replay. Every cosine-distance batch is
  validated for finite, valid values. Grouping version changes do not invalidate
  otherwise compatible cached embedding vectors.


- `auto_work/affinity.py`: passive whole-history simulation consumer. It validates
  the existing source-bound owner under a shared nonblocking lock and rechecks
  the full admitted source manifest. One process-memory index is invalidated by
  report or source DB/WAL file changes; it creates no second runtime owner,
  persistent corpus, model call or organization table. Snapshot-scoped coarse
  groups, subgroups and occurrence-preserving Session evidence have complete
  paged text access; a separate whole-scope map projection aggregates actual
  undirected affinity across text-page boundaries. Exact quotes
  are independently resolved from current original records. Stale/expired/
  invalid output never presents old evidence as current and triggers no work.
  [affinity reader contract](#affinity-reader-contract-and-states)
  owns bounds and states. Group labels are representative Session titles, not
  generated category names or confirmed work identities.
