# RUN-20261001-135: Personal Insight CLI Startup

## Metadata

- ID: `run-20261001-135`
- Status: `passed`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `backend-product`
- Surface: `backend`
- Required Evaluators: `contract`, `functional`
- Created: `2026-10-01`
- Current Phase: startup correction, server application and verification complete

## Trigger And Boundary

The owner reports failure immediately after starting a real question analysis from Insights. Private diagnostics identify Codex startup's filesystem helper failing to re-execute the launcher under the restricted macOS sandbox. The selected profile and guide are present; no model response or stream usage was produced. This is an implementation defect in the executable-analysis boundary, separate from RUN-134's guide-content evaluation.

Resolve the selected launcher to the actual executable and grant read access to that exact runtime file alongside the existing artifact and minimal-platform scope. Preserve ephemeral execution, profile/model selection, write/network restrictions, frozen evidence, paid-retry behavior and original failed records. Do not replace the configured model or modify user CLI configuration. The primary owns diagnosis, implementation and evaluation; no delegation is needed.

## Diagnosis And Verification Plan

An offline sandbox probe reproduces the startup denial. Merely adding both launcher and target to the read list fails when invoking the launcher; invoking the resolved target with read permission succeeds. Read access to a repository file outside the allowed roots remains denied. The first synthetic outside canary was under system temporary storage, already covered by the minimal runtime policy, so it is not valid evidence of external-read restriction; use the repository file for that check.

Use the installed CLI with synthetic local inputs and no model turn to verify actual bootstrap and retained boundaries. Add focused unit coverage for a symlink launcher, direct executable, quoted/non-ASCII paths, exact file grants and retained restrictions. Run related guide/Run/usage regression checks. Preserve private diagnostics outside Git and clean task-owned scratch after verification. A paid provider analysis remains an explicit owner action in Insights.

## Outcome And Evidence Limits

The [contract evaluation](../evaluation/eval-0110-contract-cli-startup.md) passes 25 focused tests. The initial [functional evaluation](../evaluation/eval-0110-functional-cli-startup.md) passes with partial coverage: seven checks using the installed CLI reproduce the original startup failure, establish corrected local prompt bootstrap, and verify the listed read/write/network boundaries. That verification submitted no model turn; live company authentication, model completion and a validated production report were unverified at that point.

The existing local server was restarted using its captured launch command and environment after confirming there were no queued/running jobs. The environment stayed in memory and was not logged. Health, Insights and the failed-Run status route return HTTP 200. Hash comparisons confirm that the failed database row and all original artifacts are unchanged. The replacement server runs in the background; its private operational log belongs to the runtime `server-logs` directory, separately from evaluation evidence. A page refresh and an explicit new analysis are the owner's next action.

## Preservation

Private `eval-20261001-135` under the established [evaluation archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis) retains source snapshots, diagnostic scripts as historical evidence, original/intermediate/final probe output, test logs, server-restart verification and repository checks. Historical paths identify where a probe ran; archived logs are readable independently of those paths. Temporary profiles, caches and synthetic execution directories are not durable evidence. Verify archived file hashes and owner-only permissions before removing the exact task-owned scratch directory.

Repository checks pass: 836 local link destinations, current artifact catalog, privacy across 1,140 candidate files, and whitespace. The private evidence archive passed two source/archive hash comparisons and owner-only permission checks; exact task scratch was removed after checking for active file use.

## Owner-Executed Follow-up · 2026-10-02

The owner explicitly retried from Insights. The new Run used the corrected runner policy and frozen company profile, returned a schema-valid `no_actionable_finding` response, and generated a retained Markdown report. Read-only checks of its status, detail page and download succeeded; the download action is present and its response bytes match the saved report. No further model Run was started for these checks. This closes the previously unverified live startup-to-report path for one owner execution. The CLI did not expose a resolved model identity; the selected model remains a request setting. Finding quality, applied changes and owner benefit are separate from successful execution.
