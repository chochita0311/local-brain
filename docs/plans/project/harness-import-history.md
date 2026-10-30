# Shared Harness Import History

This file preserves LocalBrain-specific shared-harness import events. The
[Agent Workflow](../../agents/README.md#shared-harness-refresh) owns current refresh
and ownership rules. The [Harness Import Manifest](../../agents/harness-import-manifest.json)
records accepted source/rendered baselines and the declared selection.

## Recorded Import Events

Dates for the initial merge and link restoration are not stated in this account;
the sequence below retains its recorded relative timing.

During the initial controlled merge, the accepted shared rendering was recorded separately from the retained LocalBrain specializations; its hash does not claim that a local file equals the shared rendering.

These baselines predate Harness Improvement selection; restoring the evaluation template's two capability links did not rebase its local entry.

### 2026-10-30 — Latest Committed Local Source Refresh

Accepted `ai-assets` revision `a16698813773ea74c310bb6bb5f1493e1b6addeb`,
advancing from `dc15bf9ad9aae2eaa6c819117a28e807cfbdb755` under mapping v8.
All 43 selected source files are unchanged between those commits, so no installed
harness content changed. The 34 managed entries advance their baseline source
revision while retaining the same source and rendered hashes. The nine local
entries retain their ownership, installed content, and complete detachment
baselines.

Repository surfaces, optional capabilities, and the empty public-record
selection are unchanged. Existing private experience records, discovery binding,
and Git exclusions are preserved. The source commit's standalone tooling remains
outside the selected harness; personal runtime installation follows its separate
procedure.

The complete eight-file Harness Improvement core was already installed and
remains selected. Its [policy](../../policies/harness/harness-improvement.md) and
[operation](../../agents/operations/harness-improvement.md) own the agent-performed
experience and improvement lifecycle, including its existing task, evidence,
and publication boundaries. Configured local stage hooks are retained; binding
readiness and observed local history remain in the private experience records.
Installation and this refresh do not establish an improvement's effectiveness
or prove future hook execution.

Verification passed for manifest schema, paths, ordering, uniqueness, source
provenance and hashes; managed installed-content hashes; local-entry/content
preservation; selected documents' local links and anchors; private Git
exclusions; repository privacy; and whitespace checks. Application unit tests
and browser evaluation were not run because this refresh changed only import
state and documentation. Source freshness was checked against the committed
local checkout; remote `ai-assets` freshness and runtime behavior were not
evaluated.
