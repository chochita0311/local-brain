# SPEC-0110: Executable Personal Insight Runs

## Owner And Profile

- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Execution profile: `fullstack-product`
- Lanes: `data`, `backend`, `frontend`
- Source owners: `personal_insight_evidence.py` for admission, `personal_insight_runs.py` for lifecycle, and the [SPEC-0108 guide package](spec-0108-personal-improvement-guide-and-finding-contract.md) for analysis instructions and result validation; `session_insights.html` owns the product surface. The standalone `personal_insight_guide.md` is historical v1 input.

## Data And Execution

- Fresh and compatible startup creates `personal_insight_runs` through idempotent `schema.sql`. The row has no FK to Sessions, Workstreams, or maintenance Runs. The artifact root is `settings.data_dir/personal-insight-runs/<id>/` with owner-only directories/files. Paths in DB identify the frozen manifest, exact prompt, structured response, stream, stderr, and report.
- On POST, enforce local/same-origin submission, bounded URL-encoded form, available Codex CLI and local profile, one active analysis at a time under an immediate write transaction, nonempty question for `ask`, and at least one selected excerpt. The existing manifest bounds are 100 Sessions, 300 excerpts, 600 characters each, and 120,000 characters total.
- Resolve the local profile from `LOCALBRAIN_INSIGHT_CODEX_HOME`, then `CODEX_HOME`, then an existing `~/.codex-company`, then `~/.codex`; freeze its path, display label, selected model, and high reasoning effort in the Run. Freeze the active selected guide bundle to separate observation, alternative, uncertainty, action, effort, and follow-up. Send the manifest by stdin. Codex uses the frozen `CODEX_HOME`, `--ephemeral`, ignored user rules/config, restricted read-only artifact scope, disabled network tools, and output schema.
- The model result must match the fixed shape and cite admitted `source_key:event_id` references. A recurring claim needs references from at least two distinct Sessions. No-finding requires a reason. Generate Markdown locally from validated values; do not trust model-authored Markdown links or raw HTML.
- Cancel active subprocess and persist `cancelled`; on app shutdown/startup persist `interrupted`. Failed result, process exit, or invalid evidence leaves a failed Run and private diagnostics. No automatic retry.
- Runner policy v3 resolves the selected Codex launcher to its actual executable before spawning, and permits reading that exact executable for sandboxed startup helpers. Keep the existing minimal-platform and read-only artifact scope, with no grant to its parent installation directory, profile home or general home directory. [RUN-135](../run/run-20261001-135-personal-insight-cli-startup.md) owns the observed macOS launcher correction; older failed Run records remain unchanged.

## Routes And UI

- `GET /sessions-dashboard/insights`: skill ranking, resolved Codex CLI profile and model, 20 newest Runs; no model call or report render on unselected first visit.
- `POST /sessions-dashboard/insights/runs`: creates one Run, redirects to selected detail; form errors remain inline.
- `GET /sessions-dashboard/insights?run=<id>`: selected status or safe Markdown report, settings, usage, download, rerun action; cited references are rechecked against current Session text and marked stale/unavailable when needed.
- `POST /sessions-dashboard/insights/runs/<id>/cancel`: deliberate cancellation.
- `GET /api/insight-runs/<id>`: bounded status polling only.
- `GET /sessions-dashboard/insights/runs/<id>/download`: known report artifact only, private/no-store headers.
- The Run history supports cursor paging. Reanalysis preserves prior IDs and artifacts. No report action edits a work file or creates a work Session.

## Review Scope

- Design and interaction: preserve current shell/tokens; verify wide and 320px layout, focus, empty/active/completed/failed/no-finding states, clear transfer notice, and truthful actions.
- Contract and functional: inspect table and private-root ownership, route transitions, source eligibility, malformed response failure, distinct-Session recurrence rule, no Session ingestion from analysis, cancellation/restart state, and report download path.
- A live provider call remains a separate action by the owner on the Insights page; implementation review does not start a paid model Run.

## Approved Closeout Corrections

The owner's 2026-10-02 request authorizes [RUN-137](../run/run-20261002-137-insight-closeout-corrections.md). Profile: `fullstack-product`; lanes: `data`, `backend`, `frontend`, `docs`.

- Selected Run detail reads its one normalized Usage record and immutable price snapshot. Display its estimated USD amount and calculation state, including a genuine zero; absent usage, unknown pricing, incomplete components and failed calculation stay distinguishable. Keep any CLI-reported amount separately labeled. Reading detail never reprices usage or calls a provider.
- Put the frozen price label and the estimate-versus-billing explanation in the existing settings disclosure. Reuse shared tokens, labels and wrapping behavior; no new action or model selector is introduced.
- Shared root sizing must fit the available document width at a 320px viewport even with a classic vertical scrollbar. Preserve local navigation/table scrollers and verify Usage & Cost and Auto Work as peer consumers.
- Register exact `gpt-6.1-sol` with verified dated Standard/Fast prices and its 5% cached-input rate. Reprice only eligible `unpriced` records from the unavailable snapshot, using retained date, tier and normalized tokens. Preserve previously priced records and all original usage/provenance/attribution fields. Repeat startup is idempotent.
- Reconcile the six usage test failures with dated prices and explicit tier fixtures, preserving independent arithmetic checks. Update schema counts from executable/semantic owners; permit only reviewed public documentation citation URLs in semantic text, never runtime/private URLs or paths.

## Approved Scope And Selection Display

The owner's 2026-09-29 continuation approves [RUN-129](../run/run-20260929-129-personal-insight-scope-and-requests.md), consuming the corrected SPEC-0108 contract after its foundation contract checks.

- Freeze the current FEAT-0108 guide (core v8/report v3) and its response schema when preparing a Run. Support report v3 for historical core v4/v5/v6/v7 and the mapped v2 shape for historical core v2/v3 Runs; reject an unknown or mismatched version or changed frozen schema. Preserve all saved reports.
- Extend manifest v1 additively with each Session's eligible `message_count`, each excerpt's zero-based `message_index` within that scoped eligible list, and the number of truncated excerpts. Selection order, eligibility, and caps are unchanged. Expose positions/completeness in the model prompt to support exact missing-message validation.
- Show eligible versus selected Session/message counts, selected source distribution, selected known time range and undated count, and truncation when recorded. Counts come from the Run's frozen manifest/coverage, never model claims. Before execution explain source/month spread, recency within each group, excerpt sampling, and absence of project balancing or guaranteed novelty. No preview model call or extra source scan on GET.
- Render the candidate selection explanation and admitted links for every new report; render each finding's type rationale. For abstentions show the supplied-context interpretation and missing fact. Conversation request actions are generated only from validated targets, with a Session link, one-based scoped position, and a nearby supplied anchor. Do not display the model's unconstrained conversation-request prose as another request. Other bounded question kinds remain visible.
- Recheck selection and request anchors alongside finding/counterevidence references when opening a report. Never imply a requested omitted message was itself reviewed or that an old position locates unchanged current text.
- Extend the existing Insights screen with shared tokens and native disclosure, preserving the shell and 320px floor. A historical report without explanations remains readable; identify that they were not recorded rather than inventing them.
- Verify synthetic selected/no-finding/failed/active/legacy states, browser layout and keyboard disclosure, safe links/download, no provider call on reads, and usage after validation failure. Model options, a new sampling policy, automatic follow-up retrieval, and an actual paid CLI call remain outside this correction.

## Post-Run Guide Integration

After FEAT-0108 passed, [RUN-122](../run/run-20260928-122-guided-personal-insight-result-integration.md) replaced the new-Run v1 instruction/result shape with the versioned selected core/playbook bundle and three-way result contract. The selected guide versions and digests are frozen in Run settings; exact text remains in its private prompt. The local validator now requires a disconfirming check and separates findings, no actionable finding, and a bounded additional-evidence request. Historical RUN-120 evidence describes the earlier first increment; it does not claim that a real provider result was reviewed. A locally generated report's cited `/sessions/{id}` links are activated only through an exact allowlist from that Run's frozen manifest.

## Approved Usage Accounting Correction

- [RUN-125](../run/run-20260928-125-personal-insight-usage-accounting.md), approved by the owner's 2026-09-28 correction request, restores usage and estimated cost to the existing dashboard. Profile: `backend-product`; lanes: `data`, `backend`; evaluators: `contract`, `functional`.
- Keep ephemeral execution with both process cwd and Codex `-C` at the private Run artifact directory. Match and freeze the registered Codex source by its source root and the selected `CODEX_HOME/sessions`; reject an unmatched or ambiguous profile before launching a model. New Runs explicitly select Standard service tier. Historical unmarked Runs retain a labeled default-tier assumption because they ignored user config.
- Use a deterministic, metadata-only Maintenance Session as the accounting parent required by `usage_records`. Its external identity is `localbrain-insight:<Run ID>`, its path is the Run stream, and it has no work workspace, events, search entries, or maintenance Run FK. This is an application relation to the independent insight Run, not a persisted native conversation. Project attribution is `unassigned`; the runtime folder and analyzed repositories do not become the execution's Project.
- One ephemeral analysis attempt has one latest CLI usage summary and one stable Usage identity. Persist observed usage before validating the report, preserving it after failure, cancellation, or interruption. Reanalysis uses a new Run ID. Replaying a summary never adds a second charge.
- Normalize inclusive input minus cached input, price cached input separately, and do not add reasoning tokens to output again. Reuse the existing immutable dated model prices and Decimal calculator. Missing/malformed usage and unknown models keep explicit capability/calculation states. An aggregate input above a request-pricing threshold is partial because the CLI summary cannot establish individual request context tiers.
- CLI usage-field reference: [OpenAI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode). Installed CLI help confirms the working-directory, ephemeral, ignored-user-config, and JSON-stream options; no provider call was used to inspect them.
- Native source Usage repair must preserve the separately produced analysis records. Startup recovers unaccounted retained summaries or terminal CLI stream evidence without calling a provider. Missing evidence stays unavailable. Preserve historical snapshots and attribution when replaying an existing identity.
- Verify source-specific and All totals, history and Project breakdown, work-Session exclusion, replay idempotency, native source repair, failure/cancellation, and retained-run recovery using synthetic local evidence. A paid provider execution is outside this correction's verification.
