# RUN-243: Terminal Defaults And Quick Launch

- Status: `passed`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Active Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Profile: `fullstack-product`; attempt1,2026-11-11.
- Authorization: direct human instruction to move cwd/shell defaults into a
  Terminal settings tab and immediately launch instances. Retain existing
  background versus terminate semantics while making both actions discoverable.
- Predecessor: [Run242](run-20261110-242-web-terminal-work-area.md) remains blocked
  on its original whole-feature evidence. This is an approved interaction
  revision, not a claim that physical IME/performance gaps are resolved.
- Evaluation: [Eval0159](../evaluation/eval-0159-terminal-defaults-and-quick-launch.md).

## Scope, Ownership And Preservation

Primary owns requirements/persistence/architecture, implementation and acceptance.
Backend/contract: feature-owned `[terminal]` preferences use the existing private
settings file, revision and atomic-write lock; each new web action captures
validated defaults once and retains its explicit request across uncertain retries.
Frontend: existing Settings family and Terminal quick create, split and management.
Integration: web/macOS admission, shared preference revision and preserved generic
settings consumers. Docs/evaluation: current owner contracts and rendered checks.
No change to node-pty/core/signalling, engine lock/install, CLI/service lifetime,
terminal output persistence, Sessions/Usage or native Terminal availability.

Initial worktree is the complete prior uncommitted delivery,1840 files at HEAD
4ff4a2daf6a714063b19ba077bb169711441bdaa. Immutable baseline manifest SHA256
bf26acb46c450f8b5449421e58adb0bf2e473af29aa251e86d6baf57a3561254.
Preserve all prior changes and the user's now-installed/running default service.
Tests use synthetic HOME/data/cache and copied public engine dependencies only.

## UI Alignment And Checks

Screen-alignment `extend`: constitution and current Settings/Terminal are the
authority, with no external target. Keep the shared nav, dialog, labels, paths,
32/40px controls and focus semantics; add no cards, token system or prose rail.
Before/after actual browser evidence will compare General/Terminal, quick new
without dialog, split inheritance, background/open/end and narrow320px actions.

Required checks: private-file/unknown-field and concurrent-revision preservation,
invalid defaults/no side effects, exact paths, fresh new-action snapshots and
stable retries after settings changes,
web/desktop route admission, real synthetic PTYs, relevant settings regressions,
full Python/privacy/catalog/JS and actual browser. Independent bounded read-only
challenge at freeze is warranted by shared private settings/revision and a local
execution consumer; core process/signalling is unchanged. No hard caller budget;
allocate one fresh pass and evidence-driven repair confirmation, reserve browser,
package/docs and scratch cleanup. No commit/push/native build authorized.

## Result And Repairs

Settings → Terminal now saves default cwd/shell with the shared private settings
transaction. New opens an instance directly; Split uses its source pane. Running
provides separate view/open, background and end actions with concise state text.
No engine/core/signalling, CLI/service lifetime, dependency or native delivery
change was required. Runtime create remains a pass-through; the web action obtains
validated explicit launch values once and retains them with its retry identity.

[Eval0159](../evaluation/eval-0159-terminal-defaults-and-quick-launch.md) records
PASS for contract/design/functional/interaction and complete coverage for this
bounded increment. Full Python1633/22 skipped, focused real-PTY3, settings12,
UI contracts45, JS/assets, wheel-byte18, native collection/privacy/catalog and
actual wide/320px browser evidence pass. Prior Run242/Eval0158 and the whole
Feature remain blocked on their existing physical/representative evidence gaps.

The primary accepted and repaired the fresh challenger's exact-path, common-read
race and changed-default retry candidates. An informed confirmation found a
related mutable-cwd split retry; stable pane ID/direction and a renewed actual
lost-reply/OSC7 witness repaired it. One fresh pass and two bounded confirmations
were used against full frozen baseline/candidates; no hard caller budget was
specified or extended. Primary retains the final acceptance decision. No code
objections remain within this increment; no broader stability or parity claim.

Closeout preserves all prior delivery bytes except these authorized owners and
affected consumers. HEAD remains4ff4a2daf6a714063b19ba077bb169711441bdaa, with
local uncommitted source only. Private evidence owns frozen snapshots/logs, and
task-owned QA processes, PTYs and temporary artifacts are removed after capture.
No default-user service or settings mutation, commit, push or native build.
