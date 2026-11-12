# RUN-244: Terminal Korean And Embedded Terminal Audit

- Status: `returned-to-spec`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Active Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Evaluation: [EVAL-0160](../evaluation/eval-0160-terminal-korean-and-embedded-audit.md)
- Profile: `fullstack-product`; attempt1,2026-11-11.
- Authorization: human reports broken Korean, requests comparison with local
  iTerm2 fonts and VS Code/IntelliJ embedded terminals, then explicitly requests
  overall sub-agent verification. Primary owns diagnosis, architecture, fixes,
  persistence, integration and final judgment.

## Boundary And Method

Investigate font coverage/metrics, UTF-8 and terminal transport, Unicode width,
composition/input and shell environment as distinct possible causes. Compare
ordinary embedded-terminal requirements with official IDE sources and actual
implementation, separating essential behavior, developer conveniences and
deliberate scope exclusions. Correct reproduced contract violations; newly
proposed capabilities remain recommendations pending scope decisions.

Research-SADR with raw local observations, alternative mechanisms and bounded
discriminating checks. Screen-alignment extend preserves the existing Settings,
Terminal and shell families. Lanes: renderer/input/backend contract; web integration;
docs and evaluation. Preserve private runtime data, existing defaults/service/jobs,
CLI lifecycle and native exclusion. No commit/push, native build or external upload
of local preferences/fonts/content. Read local IDE preferences only for selected
font/locale fields. Actual process checks use synthetic HOME/data/cache/PTYs.

Baseline HEAD4ff4a2daf6a714063b19ba077bb169711441bdaa plus full prior delivery1844
files; manifest SHA256 b424d6c7fafcf66a3347827ad48bd33860f3a13aa47f2fb56ae3e9fadaf3aaac.
Keep all prior uncommitted changes. Run242 whole-feature gaps and Run243 bounded
PASS are historical evidence, not a claim that the reported Korean issue is solved.

## Delegation And Verification Allocation

Explicit user authorization allows named capable workers: a fresh research worker
for official reference criteria, fresh non-editing/non-executing code challenger
for the frozen whole existing Terminal, and bounded verifier for fixed synthetic
checks. No inherited author discussion for independent discovery. Primary handles
local font/content, cause selection, changes and adjudication; no worker approves
scope, persistence or completion. Record actual model/permissions/evidence limits.

No hard caller time/token limit. Plan one fresh reference investigation and code
challenge, one fixed validation packet, and evidence-driven repair confirmations.
Reassess only for new material evidence, retaining time for browser/package/docs
and exact scratch cleanup. Compare source/candidate separately after repairs.

The first informed confirmation found three new delivery consequences of the
width repair: corporate tarball resolution, cached vendor exports and legacy
browser→new-manager width disagreement. New discriminating evidence and these
changed inputs justify a second bounded confirmation, not a fresh broad pass.
No hard limit is extended. Complete VT checkpoint compatibility remains a
supported technical blocker; snapshot text/alternate-buffer successes do not
establish full restoration. No private xterm state mutation is introduced as an
unreviewed workaround. Current audit/fixes and the remaining checkpoint work stay
distinct; the earlier complete-defaults increment is not invalidated wholesale.

## Result And Return Boundary

The user-requested overall audit and font investigation are delivered.
[Eval0160](../evaluation/eval-0160-terminal-korean-and-embedded-audit.md) records
FAIL for full terminal compatibility and partial evidence. The reproduced glyph
case is fixed: installed D2Coding renders the same Powerline characters that the
former fallback displayed as boxes. Matching width rules, bounded input/paste,
partial-module recovery and public/cached/mixed-version upgrade paths are repaired.
Six current real-PTY methods, actual browser witnesses and final1637 suite/24
conditional skips pass. These are scoped corrections, not whole-feature acceptance.

Return to Spec is technical: the selected serializer lacks complete parser/VT
checkpoint state, demonstrated for partial CSI/OSC, scroll region, saved cursor
and custom tab stops. A bounded checkpoint protocol/adapter decision and its
performance/privacy evidence are needed before that implementation proceeds.
The requirement remains binding; this is not accepted as intentional behavior.
No new product choice, engine migration or additional IDE convenience is approved.
Physical IME and the earlier representative acceptance gaps also remain open.

The review allowance used one fresh research pass, one fresh whole-code challenge
and two informed repair confirmations. The fixed validator packet's context/
permission errors were discriminated with escalated and writable-copy probes;
new checks used separate execution state and bytecode suppression. No hard caller
budget was specified/extended and no review exhaustion became a readiness claim.
Primary owns all dispositions and the next technical Spec boundary.

## Closeout Evidence

Final web wheel17 files match source; native collection125 data files/234 modules
excludes Terminal/Unicode assets, without a native build. Reproducible assets,
renderer import hash, JS syntax, privacy1847 and catalog/diff checks pass.
The user's saved font/app observations and complete frozen review evidence are
retained only at the configured private stage owner. Public records use synthetic
reproductions. Actual user terminal output was never printed or persisted.

QA manager/PTYs/backend and task-created browser pages7–9 are stopped/closed;
the pre-existing blank page remains. Private frozen sources/review returns/logs/
synthetic screenshots are retained before exact scratch cleanup. HEAD remains
4ff4a2daf6a714063b19ba077bb169711441bdaa; no commit/push/native build or default-user
service restart/component installation/settings mutation was performed. Font
display requires loading the current web assets; engine updates remain explicit
stop/install/start operations after the user finishes their existing work.
Required evidence: raw Korean round-trip and width, browser rendering/input and
keyboard/paste/resize/reconnect, actual configured font comparison, core/lease/
resource/privacy boundaries, focused/full tests, JS/assets/package and native
admission. Physical OS IME and long-soak cannot be inferred from synthetic events.
