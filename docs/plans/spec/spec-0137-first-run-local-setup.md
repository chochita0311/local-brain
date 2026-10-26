# SPEC-0137: 첫 실행 안내

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0137](../feature/feat-0137-first-run-local-setup.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [run-20261018-175-first-run-local-setup](../run/run-20261018-175-first-run-local-setup.md)
- Execution Profile: `fullstack-product`
- Updated: `2026-10-23`
- Active follow-up: [Run 185](../run/run-20261023-185-onboarding-visual-refinement.md)

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 후보 경로는 선택 제안이며 등록 동의 없이 수집하지 않음.
- AC2: 빈 세션/Context·모델 건너뛰기 지원, 첫 가져오기와 주기 실행 중복 방지.
- AC3: 기존 설정·소스·핀·기록 보존, 온보딩 강제 반복 없음.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## First-Use Overlay Wizard — 2026-10-23

The owner's correction replaces the standalone onboarding page with a sequential
dialog over the actual configured startup screen. Welcome, Session sources,
Local Context and Search appear one at a time. Previous, Next and Skip have a
stable footer; an explicit Later action can finish without required sources or
models. The modal owns focus, blocks the background and fits down to 320px.

Use the existing Session/Context/model forms and persistence services. Next saves
pending Session or Context input before advancing; invalid or rejected input
keeps the step and values. Back retains drafts; Skip intentionally advances
without registering them. The model step retains keyword availability, installed
model status and explicit download/cancel/prepare controls. No step transition,
page load or completion starts a model download.

`onboarding_completed` remains false until completion or an explicit Later action
is successfully saved. Read the current revision before completion; failure
keeps the modal open and retryable. Already saved registrations survive exit or
restart. A fresh/incomplete desktop entry opens the wizard, while an ordinary
web page remains unchanged unless onboarding is explicitly opened. Completed
users retain normal startup behavior. The final handoff refreshes the selected
startup surface without exposing an intermediate card page.

Regular settings retain their category navigation, existing forms, errors,
general autosave and compact dialog rules. Use the same inputs/actions rather
than duplicate registration or installation pathways. This supersedes the former
three-card landing composition without changing source consent or optionality.

## Onboarding Visual Refinement — 2026-10-23

The owner requests a more polished native setup feel, with bottom progress dots
and transition direction inspired by the Tesla homepage under LocalBrain's
constitution. Keep the four real steps and all existing persistence/consent
semantics. Replace the numbered top strip with four small bottom indicators;
the current dot differs by shape and tone and retains an accessible step name.
Dots are observational, while Previous/Next/Skip remain the navigation actions.

Use a quiet header, lighter internal boundaries, restrained title weight and
the existing compact dialog dimensions. Keep a stable action/footer region
while outgoing and incoming content overlap for one shared overlay-duration
crossfade with a small directional offset. Preserve outgoing scroll position
visually, start the destination at its top, suppress duplicate transitions and
keep outgoing/incoming controls inert until focus moves to the destination title.
Reduced motion bypasses animation. No autoplay, swipe-to-submit, new external
assets or model actions are added. Normal settings preserve their existing
categories, geometry, source controls and general autosave.
