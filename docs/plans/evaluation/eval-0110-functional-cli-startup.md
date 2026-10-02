# EVAL-0110 Functional: CLI Startup

## Metadata

- ID: `eval-0110-functional-cli-startup`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `partial`
- Run: [RUN-135](../run/run-20261001-135-personal-insight-cli-startup.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `backend-product`
- Surface Lane: `backend`
- Created: `2026-10-01`

## Observed Failure And Correction

The owner-started Run selected the intended profile and current guide but failed before a model response or usage stream existed. Private stderr identifies a filesystem-helper bootstrap failure while re-executing the Codex launcher under macOS Seatbelt. Preserve the failed Run and diagnostics; do not invent a zero-cost provider receipt from missing usage.

Local CLI 0.159.3 reproduces the failure. The initial candidate, adding readable launcher and target paths while still invoking the launcher, also fails. Invoking the resolved executable succeeds. The initial outside-file canary was under temporary storage admitted by the minimal policy, so it was replaced with a repository-file check; the failed and unsuitable checks remain in private evidence.

Using the product's corrected generated permission options, seven offline checks pass:

| Check | Observed result |
| --- | --- |
| Resolved Codex self-execution | Version command succeeds |
| Artifact input read | Synthetic input is readable |
| Repository file outside allowed roots | Read denied |
| Artifact write | Denied; no file created |
| Command network to a listening local socket | Denied; unsandboxed control connection succeeded |
| Original launcher and old policy, local prompt bootstrap | Reproduces the same helper/AGENTS startup error |
| Resolved executable and corrected policy, local prompt bootstrap | Produces valid model-input JSON |

The prompt-bootstrap checks use `codex debug prompt-input`, an isolated temporary profile, synthetic input and a local-only provider definition. They submit no model turn. The parent test process used the approved tool escalation because nested macOS sandbox creation is denied in the tool sandbox; the tested child permission restrictions remained enabled throughout.

## Limits And Follow-up

This establishes correction of the observed installed-CLI startup failure and checks the listed restrictions. It is not an exhaustive filesystem/network audit or evidence for other operating systems or CLI versions. The [official permission documentation](https://learn.chatgpt.com/docs/permissions) documents exact read-path rules and the distinction between sandboxed command access and client model traffic; the launcher-specific result comes from local execution evidence.

The existing local server was restarted with its captured launch command and environment after checking that no jobs were active. Health, Insights and the failed-Run status route return HTTP 200. Before/after hashes confirm the original failed database row and all artifacts are unchanged. The replacement runs in the background with a private runtime operational log; no provider analysis was started.

At the initial evaluation, the selected company's live authentication, a paid model response, output validation against real provider content and a completed production report remained unverified. The 25 [contract tests](eval-0110-contract-cli-startup.md) did not replace that real provider step. Private `eval-20261001-135` retains the original diagnostic, intermediate attempts, final CLI output, test logs and server verification under the established [archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis).

## Owner-Executed Follow-up · 2026-10-02

A subsequent owner-started question Run completed under the corrected policy and selected company profile. Its response validated as `no_actionable_finding`, which the Run ledger represents as `no_finding`; the report exists despite there being no new finding. Status and detail routes return HTTP 200, the detail contains the download action, and the download returns HTTP 200 with Markdown attachment and private/no-store headers. Its bytes match the retained report exactly. These checks submitted no model request.

This is one observed successful production path, not a repeatability or recommendation-quality evaluation. The CLI-reported model identity is absent, so the configured model is not independently confirmed by the stream. The result cites an earlier proposal as the reason for adding no new action while explicitly leaving adoption and benefit unconfirmed. The retained production Run owns its input, response, validated result, report and usage; private contents are not copied into tracked evidence.
