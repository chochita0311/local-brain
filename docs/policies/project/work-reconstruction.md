# Work Reconstruction Experiment

This contract owns the bounded, model-free comparison, source admission, input/output shapes, independent assessment and resource limits. It does not admit production reconstruction or replace current Workstream organization.

## Experimental Scope And Authority

The explicit local experiment compares the unchanged reference-pair contract
with a minimal deterministic Korean/English goal extractor. It groups exact
normalized subject/change and compatible completion criteria, keeps activity
phases subordinate, attributes source wording, and leaves unsupported meaning
unassigned. It requires no routine create/name/assign/accept/promote action.
This is an experimental prototype, not a general semantic understanding capability.

Comparison scores use separate source-bound expectations, not generated labels
as truth. Processing coverage, synthetic correctness, local quality, and product
viability remain distinct; missing private evidence cannot authorize replacement
UI. After explicit current-data scope selection, the command can freeze a bounded
chronological sample across existing history. Its unassessed execution check
creates no answer key and cannot claim accuracy or useful automatic grouping.
Population/sample counts and incomplete text stay distinct from quality.

The comparison command changes no Workstream/Thread, Suggestion, assertion,
or source. The [user-managed organization rules](product.md#workstream-centered-organization)
remain runtime truth until an approved transition replaces them. [Experimental contract](#isolated-work-reconstruction-experiment)
owns current input, processing and output bounds; the [Developer Guide](development/work-reconstruction.md#operations)
owns invocation, and [Privacy](privacy-and-data.md#local-persistence) owns private
input and review limits. This experiment performs neither product transition nor
legacy cleanup.

## Isolated Work Reconstruction Experiment

- The `experiments/reconstruction/` modules own only the versioned experimental
  `localbrain.work-reconstruction.v1` shape. Their only app consumer is the
  [sample-mode Auto Work inspection adapter](auto-work.md#sample-inspection). They have no schema,
  migration, schedule, production identity, or assertion-ledger ownership.
- Extraction consumes supplied bounded text. Evidence keys and offsets retain
  source attribution; normalized goal identity is separate from wording, labels,
  revisions, and experimental exact-scope corrections. Unknown goals and
  lifecycle remain unknown. Shared references cannot force a semantic merge.
- The comparator receives metadata and admitted record spans, never body text.
  It enumerates all qualifying bounded pairs through the unchanged candidate
  normalizer. Local canonical keys use Context source/relative-path and
  Atlassian Site/remote identity, not raw row-based target keys.
- Private input requires an explicit existing database and frozen source/time/
  record manifest. A read-only URI, query-only transaction, and SQLite authorizer
  prohibit mutation, attachment, and extension loading. Eligibility is checked
  before bounded body selections and hash verification. No application database
  helper, source parser, connector, model, or external operation is used.
- Once the owner selects current LocalBrain data, the operator may resolve its
  configured database without asking for a manual path. Explicit preparation
  samples the approved existing-history scope before prediction, keeps
  per-snapshot omissions in the manifest, and revalidates hashes/permissions
  through the same adapter. `--unassessed` leaves every quality answer unknown;
  it is execution evidence only, never generated truth or a viability gate pass.
- Each analysis/admission worker is a spawn-free supervised process on macOS or
  Linux. Its own peak RSS covers that single-process worker tree; an in-worker
  watcher and parent completion check enforce the memory bound, and the parent
  enforces wall time and reaps cancelled/failed workers. Unavailable monitoring
  fails closed; the command does not inspect unrelated processes.
- Results and independent expectations stay local. New owner-only output outside
  the repository is bounded, never overwrites an existing result, and records
  its owner and expiry. The tool adds no retention scheduler or whole-DB copy.
  Quality and stability measurements do not automatically approve viability.
### Reconstruction Input And Bounds

The pure snapshot has `version: 1`, a nonempty name, `sessions`, `records`,
`artifacts`, `references`, `coverage` and `organization_links`; unknown
fields refuse. Identifiers are nonempty strings of at most 500 characters unless
an explicit integer identity is required below. Supplied timestamps are aware
ISO timestamps of at most 80 characters. A Session record uses positive actual
integer `id`/`source_id`, nonempty `external_id`, nonnegative actual integer
`event_count`, eligibility fields `session_class`, `session_role`, `index_policy`,
and optional `title`, `workspace_id`, `ended_at`, `has_activity_events`,
`has_usage_records`; titles are null or at most 500 characters. Session IDs are
unique. Artifact/reference field allowlists and semantic validation reuse
[Candidate Inputs And Producer Duties](workstream-candidates.md#candidate-inputs-and-producer-duties).

| Boundary | Current hard limit |
| --- | --- |
| Snapshot history | 1–12 distinct named snapshots |
| Sources / Sessions per snapshot | At most eight Sources and 60 Sessions; work/primary/full eligibility remains mandatory for private admission |
| Records / total text | At most 12,060 records and 2,500,000 text characters |
| Session evidence | At most 200 records and 32,000 characters per Session; each selected message span at most 4,000 characters |
| Other evidence | At most 20 Documents, 20 Items and 20 organization records; each Document/Item span at most 8,000 characters, organization span at most 2,000 |
| Metadata | At most 2,000 artifacts, 12,000 references and 200 organization links |
| Metadata comparator pairs | At most 4,096 qualifying pairs; overflow fails rather than clipping |
| Corrections | At most 100 unique correction IDs; each names at most 12,060 unique statement keys, with no key reused across corrections; optional label is null or 1–500 characters |
| File / worker | Input and encoded output at most 10 MiB; each admission/analysis/scoring worker at most 120 seconds and 512 MiB peak RSS |

Every text record has a unique `key`, a `kind` (`session`, `document`, `item`,
`organization`), `session_id`, `role`, nonnegative actual integer `offset`,
nullable aware `at`, and text. Session records require a selected Session ID and
user/assistant role; other records require a null Session ID and document/owner
role. Coverage has actual boolean `complete` and nonnegative actual integer
`unexamined`; complete coverage requires zero unexamined items. Bounds do not
convert omitted or unsupported source into a complete reconstruction.

A private selection manifest has exactly `version: 1`, `source_ids`, `start`,
`end`, `snapshots`, `owner`, `expires_at`. Source IDs are 1–8 unique positive
actual integers. Its aware start is no later than end. Each snapshot has unique
`name`, ordered `as_of` within that interval, `session_ids`, `events`,
`documents`, `items`, `organization`, `organization_links`, and optional explicit
coverage. Session/link IDs are unique positive actual integers. A text selection
has `id`, `start`, `end`, `sha256`, plus `table` only for organization:
`id` is an actual integer or nonempty string whose spelling is at most 500
characters; offsets are actual integers with `0 <= start < end`, obey their
kind's span limit, and use a lowercase 64-hex UTF-8 SHA-256. Only one selection
per record identity is allowed. Organization tables are exactly `workstreams`,
`threads`, `checkpoints`. No arbitrary table/column is admitted.

The explicit database must be an existing absolute nonsymlink file. A URI
`mode=ro` connection, `query_only`, memory-only temporary storage, one read
transaction, SQLite authorizer and deadline prohibit writes/attachment/extension
loading. Session admission requires a registered Source in the selected set and
work/primary/full classification. Selected Events must be user/assistant
messages in that Session. Documents require an enabled, readable, ready root;
Items require indexed content and no disabled bound Source. Organization uses
current summary/goal text and user-created links to selected Sessions only.
Each selected record's relevant occurrence/import/application/update/link time
must lie within start and snapshot cutoff. Bounds and permission checks precede
selected text reads; exact selected substrings must still match their hashes.

Reference projection reads persisted evidence only, capped at 12,000 rows across
selected Sessions. Missing/non-ok scans, missing times or unresolved canonical
references make coverage partial; known out-of-scope references are excluded.
Only selected Documents/Items participate. Document identity uses Context scope
and relative path; Jira uses Site/issue key, Wiki Site/page identity; generic
references require safe persisted credential-free HTTP(S) URLs. The comparator
receives canonical metadata and admitted source spans, never text. It enumerates
artifact pairs independently supported by two Sessions through the unchanged
candidate normalizer; references cannot force goal identity.

Explicit preparation uses `localbrain.chronological-spread.v1`: metadata selects
up to 60 Sessions evenly across their earliest eligible message times, including
both chronological endpoints, before predictions or body reads. It selects up
to 32 evenly spread message records per selected Session, at most the first
1,000 characters each; up to 20 referenced Documents and 20 referenced Items,
8,000 characters each; up to 20 linked organization records, 2,000 each, and
200 user links. It creates up to three distinct chronological cutoffs, records
outside-sample/omitted/truncated/unknown-time counts and revalidates the frozen
manifest through the same permission/hash adapter. No eligible population or
more than eight Sources refuses. This bounded preparation is distinct from the
[full-history simulation](auto-work.md#full-history-simulation-producer). Unassessed expectations have no groups or
negative answer key and at least one unresolved item, so they cannot pass quality.

### Reconstruction Output And Assessment

Sentence/newline extraction retains original record offsets and wording.
NFKC/casefold/whitespace normalization affects identity, never source coordinates.
The bounded Korean/English action vocabulary supports reduce/increase/improve/
fix/add/remove/replace/enable/disable. Unsupported negation, goals or subjects
remain explicit unassigned spans; subjects over 300 characters, URLs and braces
are unsupported. Investigation/implementation/verification are subordinate
phases. A reported `completed`/`done`/`완료` statement remains a source outcome,
not verified completion. Flow identity hashes normalized subject/change and a
compatible explicit completion criterion; a missing criterion stays unassigned
when several explicit criteria conflict. Lifecycle remains unknown.

Output `localbrain.work-reconstruction.v1` has `flows`, `unassigned`, `coverage`,
`corrections` and `routine_confirmations: 0`. Each flow retains `flow_id`,
subject/change/completion, derived label, nullable user label, inferred authority,
unknown lifecycle, ordered members and content revision. Members retain statement
key, exact record/start/end, Session/kind/role/time, normalized fields, original
wording and field evidence. Statement identity includes exact wording, so an
equal-length source edit is new evidence; unrelated appended text does not
invalidate an unchanged statement. Exact-scope corrections move only named
currently present statements into a correction-ID flow, mark those members
`user-corrected` and report their active count; the flow remains inferred, and
absent keys cannot target new claims.
The metadata arm retains spans and candidate identity/revision, not goal labels.

Independent expectations bind each snapshot digest before either arm executes.
A version-1 expectation supplies at most 100 distinct keyed groups with subject,
change, nullable completion, member spans and nullable acceptable labels (at most
20 nonempty labels, each at most 500 characters), `negative` spans and a
nonnegative unresolved count. Each group/negative list has at most 12,060 unique
exact record/start/end spans; spans must be inside admitted text, and negative
spans cannot overlap positives. Expected labels and unresolved assignments remain
unassessed when missing; predictions never supply the key. A predicted member
must be contained in an expected record/span and match its normalized
subject/completion and exact change value; Session overlap or a generated label
is not enough.
Every emitted assignment is correct, wrong or unassessed. Recovery, wrong
assignments, excess/unsupported groups, assessed correction freedom and stability
retain exact integer numerators/denominators; no rounding or zero denominator
can manufacture a pass. Correction-free requires one correctly supported flow,
an independently acceptable label, no assignment error and all expected member
contributions; an unknown label or missing contribution is not success.

The report compares text/metadata arms both with and without organization,
replays text deterministically, and reports per-arm resources/scores, source and
expectation digests, sample sufficiency and consecutive-snapshot identity,
assignment and label stability. Score gates require at least 80% goal recovery,
at most 10% incorrect membership, at most one excess/unsupported group per ten
recovered goals, no incompatible-outcome merges, at least 90% correction-free
recovered goals, and zero routine confirmations. Incomplete coverage, unresolved
expectations, unknown assignments, unassessed labels, no expected groups or no
members make quality insufficient rather than pass. Private sufficiency also
requires 40–60 eligible Sessions, at least ten expected efforts, an expected
effort spanning more than 24 Sessions and at least three snapshots. The report
lists independent local expectations, mandatory synthetic safety witnesses and
weak-reference/unrelated-append assessment as required evaluator checks. The
evaluator must verify at least 95% identity/assignment preservation after
unrelated append, without harmful reassignment. Source rename/loss and exact-scope
correction behavior also require separate synthetic witnesses. These evaluator
duties are not automatically computed CLI gates. Both arms use identical input; the metadata arm's poor quality does
not excuse a failed absolute text gate. Do not resample or tune against the
private answer key. These are separate checks, not an automatic viability
decision: reports retain `viability: unverified`.
The [Feature review disposition](../../plans/feature/feat-0095-bounded-work-reconstruction-experiment.md#review-allowance-disposition)
owns the finite human-review allowance and remaining availability; the
[privacy policy](privacy-and-data.md#local-persistence) owns the unknown/spent-budget
refusal. No technical pass,
unassessed execution, reproduction or replay authorizes a new review batch,
production transition or product identity.

## Implementation Ownership

- `src/localbrain/experiments/reconstruction/contract.py`: isolated experimental text extraction,
  semantic grouping, exact synthetic corrections, and metadata-only comparator

- `src/localbrain/experiments/reconstruction/scoring.py`: independent expectation
  validation, integer quality measures, and identity/assignment replay measures

- `src/localbrain/experiments/reconstruction/input.py`: explicit manifest validation and
  bounded read-only access to already-indexed selected records

- `src/localbrain/experiments/reconstruction/preparation.py`: explicitly invoked,
  prediction-independent chronological sampling, frozen manifests, omission
  accounting, and unknown-assessment placeholders; no independent answer key

- `src/localbrain/experiments/reconstruction/experiment.py` and
  `scripts/experiment-work-reconstruction.py`: opt-in local comparison command,
  supervised resource bounds, and private owner/expiry-bound result publication
