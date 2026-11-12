# FEAT-0166: Web Terminal Work Area

## Metadata

- ID: `feat-0166`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, design, functional, ux-heuristic
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Created: `2026-11-10`
- Updated: `2026-11-12`
- Authorization: reviewed PRD decisions, internal-only and close/background confirmations, lb/concise-UI direction, then the human proceed instruction on 2026-11-10. That implementation authorization excluded publication, native delivery and broader terminal products. Later source closeout is separately authorized below.

## Goal

Provide the agreed macOS web Terminal area: real shells in tabs and up to four
panes, retained independently of the browser/backend and controllable from the
web and lb CLI. The existing proposed contract/runtime/view outcomes form the
coupled lanes of this one usable surface; they do not introduce separate products.

## Acceptance Contract

PRD A-01–16 apply. The menu is above Sessions; × terminates its explicit scope;
background is a separate action; list/inspection never starts a service. Service
stop/restart ends all its terminals before stopping, with no command replay.
Input/resize ownership, reconnection, output bounds and private storage are explicit.
`lb` and existing `localbrain` share dispatch. Installed dependencies are optional
to the other web workflows and excluded from desktop. Use compact controls and
contextual failure feedback. No raw-output indexing or transcript archive.

## Scope Boundary

- In: private local manager/PTY ownership, controlled optional engine setup,
  snapshots/stream/lease, web bridge, tabs/splits/background/stop, direct CLI,
  locally built assets, owning docs and meaningful synthetic/process/browser checks.
- Out: desktop terminal delivery, Windows first release, external iTerm2,
  remote machines, agent automation, CLI run/attach, cold process recovery,
  unlimited history, new global service registry, provider resume, publication.

## Surface Lanes

| Lane | Path roots | Responsibility / dependency | Evidence / evaluator |
| --- | --- | --- | --- |
| contract/backend/infra | src/localbrain/terminal | optional engine, local IPC, manager/process/input ownership, lifecycle and bounded state | process/IPC/CLI tests; contract and functional |
| frontend | templates/terminal.html, static/terminal*, static/vendor/xterm | concise Terminal surface, focus, stream and reconnect; consumes stable manager contract | wide/narrow browser; design and interaction |
| integration | app assembly, cli.py, pyproject, desktop build exclusions | web-only admission and aliases; no unrelated lifecycle effects | boundary/legacy CLI/package tests; contract |
| docs | policies, app guide and README | final behavior, install/stop/limits and design ownership | links/privacy; contract |

## Entry, Exit And State

Explicit new terminal/service start starts the manager; read-only entry shows
empty/stopped or current metadata. Browser/page/hidden tab detaches without
termination. Runtime IDs, tab IDs and provider Session IDs are distinct. Default,
installing, connecting, live, background, exited, failed and disconnected states
remain actionable. Status failure never becomes zero or successful stop.

## Dependencies And Regression Surfaces

Existing FastAPI/Jinja assembly, local shell and optional Node engine. Preserve
Sessions/Usage/search/collection, existing CLI commands, shared navigation and
all desktop boundaries. No DB migration. Engine choices, hard bounds and test
witnesses are in the active Spec; unknown product semantics must not be guessed.

## Harness Trace

- Active spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Active run: [RUN-246](../run/run-20261112-246-terminal-final-audit.md)
- Initial delivery: [EVAL-0158](../evaluation/eval-0158-web-terminal-work-area.md)
- Defaults follow-up: [EVAL-0159](../evaluation/eval-0159-terminal-defaults-and-quick-launch.md)
- Korean/whole-terminal audit: [EVAL-0160](../evaluation/eval-0160-terminal-korean-and-embedded-audit.md)
- Checkpoint/font follow-up: [EVAL-0161](../evaluation/eval-0161-terminal-checkpoint-and-font.md)

- Evaluation: [EVAL-0162](../evaluation/eval-0162-terminal-final-audit.md)

## Delivery And Acceptance

2026-11-12 final audit: [Run246](../run/run-20261112-246-terminal-final-audit.md)
passes after three fresh sub-agent inquiries and informed repair confirmations.
[Eval0162](../evaluation/eval-0162-terminal-final-audit.md) owns the latest bounded
result:1648 Python tests including31 real-PTY cases,67 Node tests, actual Chrome/
WebKit/native-input/launchd, package and representative-workload checks. Additional
cursor, focus, composition, color-query, bounded-input, setup and identity causes
found after Eval0161 are repaired. Font/OFL and13px remain; the current checkpoint
is v3. No supported finding remains open in this scope; listed environment and
long-soak limits remain. Earlier passing results are not rewritten as universal
stability evidence.

2026-11-12 follow-up: [Run245](../run/run-20261111-245-terminal-checkpoint-and-font.md)
passes the installation-independent font, complete supported checkpoint and
WebKit Korean-input repairs. [Eval0161](../evaluation/eval-0161-terminal-checkpoint-and-font.md)
records the independent challenge,1,640 Python/57 terminal tests, real PTY,
browser/native-input, hidden-page, representative-corpus/flood and package
evidence. The original checkpoint and missing required environment/workload
witnesses are resolved for the evaluated macOS web scope; technical acceptance
passes with explicit remaining coverage limits. No A-01–16 criterion or approved
product boundary was relaxed.

Run244/Eval0160 remain the historical failed audit of the earlier serializer.
They found fresh-view VT state loss after repairing the font/width/input/setup
issues; their return to Spec led to Run245's bounded technical checkpoint.
Run242/Eval0158 retain their original blocked/partial evidence, rather than being
retroactively relabeled as passing or as broad TUI compatibility proof.

`2026-11-11` follow-up: the human directs saved Terminal defaults in Settings,
immediate instance creation, and discoverable background/end controls. Run243
passed this approved interaction revision under the amended Spec0166;
Run242 and its blocked whole-feature evidence remain preserved, not resumed or
implicitly accepted. Eval0159 owns the bounded follow-up evidence: saved defaults,
immediate New/Split, stable uncertain retries and explicit background/open/end.

The agreed implementation is available in the working tree. Contract, design,
functional and interaction evaluation pass in the observed scope. Actual OS
Korean input, truly hidden streams and representative existing-screen/flood
measurements now replace the earlier synthetic-only/empty-corpus gaps. They do
not establish hardware-keyboard/Safari-app repetition, VoiceOver, complex emoji,
every-machine or long-soak behavior. The evaluation owns those exact limits.

These implementation Runs left source local and uncommitted; they did not install
or control the default-user service, build the LocalBrain desktop product,
release or publish. The later 2026-11-12 preset1 request separately authorizes
reviewed source commit and push after required checks. It does not activate the
user's runtime or release a packaged product. The owner can review use after explicitly updating the web
server/service; current jobs were left running. This is not another scope-selection
round or a claim that user-environment updates happened automatically.
