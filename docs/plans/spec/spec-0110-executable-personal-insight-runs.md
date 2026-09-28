# SPEC-0110: Executable Personal Insight Runs

## Owner And Profile

- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Execution profile: `fullstack-product`
- Lanes: `data`, `backend`, `frontend`
- Source owners: `personal_insight_evidence.py` for admission, `personal_insight_runs.py` for lifecycle, `personal_insight_guide.md` for analysis instruction, `session_insights.html` for product surface.

## Data And Execution

- Fresh and compatible startup creates `personal_insight_runs` through idempotent `schema.sql`. The row has no FK to Sessions, Workstreams, or maintenance Runs. The artifact root is `settings.data_dir/personal-insight-runs/<id>/` with owner-only directories/files. Paths in DB identify the frozen manifest, exact prompt, structured response, stream, stderr, and report.
- On POST, enforce local/same-origin submission, bounded URL-encoded form, available Codex CLI and local profile, one active analysis at a time under an immediate write transaction, nonempty question for `ask`, and at least one selected excerpt. The existing manifest bounds are 100 Sessions, 300 excerpts, 600 characters each, and 120,000 characters total.
- Resolve the local profile from `LOCALBRAIN_INSIGHT_CODEX_HOME`, then `CODEX_HOME`, then an existing `~/.codex-company`, then `~/.codex`; freeze its path, display label, selected model, and high reasoning effort in the Run. Use the first versioned guide to separate observation, alternative, uncertainty, action, effort, and follow-up. Send the manifest by stdin. Codex uses the frozen `CODEX_HOME`, `--ephemeral`, ignored user rules/config, restricted read-only artifact scope, disabled network tools, and output schema.
- The model result must match the fixed shape and cite admitted `source_key:event_id` references. A recurring claim needs references from at least two distinct Sessions. No-finding requires a reason. Generate Markdown locally from validated values; do not trust model-authored Markdown links or raw HTML.
- Cancel active subprocess and persist `cancelled`; on app shutdown/startup persist `interrupted`. Failed result, process exit, or invalid evidence leaves a failed Run and private diagnostics. No automatic retry.

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

## Post-Run Guide Integration

After FEAT-0108 passed, [RUN-122](../run/run-20260928-122-guided-personal-insight-result-integration.md) replaced the new-Run v1 instruction/result shape with the versioned selected core/playbook bundle and three-way result contract. The selected guide versions and digests are frozen in Run settings; exact text remains in its private prompt. The local validator now requires a disconfirming check and separates findings, no actionable finding, and a bounded additional-evidence request. Historical RUN-120 evidence describes the earlier first increment; it does not claim that a real provider result was reviewed. A locally generated report's cited `/sessions/{id}` links are activated only through an exact allowlist from that Run's frozen manifest.
