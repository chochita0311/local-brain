# EVAL-0128: 공통 로컬 설정 계약 contract

## Metadata

- ID: `eval-0128`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-166](../run/run-20261018-166-local-settings-contract.md)
- Feature: [FEAT-0128](../feature/feat-0128-local-settings-contract.md)
- Spec: [SPEC-0128](../spec/spec-0128-local-settings-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: shared configuration and persistence contracts
- Evidence Coverage: `complete` for this foundation contract
- Created: `2026-10-18`

## Initial Checks And Evidence — 2026-10-18 (Superseded)

The original precedence and Project-display rules below are historical. The owner
corrections recorded under Current Contract replace them.

The primary agent reviewed the owning [desktop/settings policy](../../policies/project/desktop-app-and-settings.md), implementation and consumers against the approved PRD. No delegation or external publication occurred.

The settings tests exercise default/saved/environment precedence, revision conflicts, private permissions, invalid/future schemas, unknown TOML date preservation, and most-specific Project display without source-path mutation.

- TOML schema 1; 로컬 파일의 원자적 저장·revision 충돌·0600 권한.
- 지원 값은 환경변수→저장값→기본값. 저장값과 적용값·출처를 표시.
- 시작 화면은 다음 시작, 시간대·표시·동기화 설정은 즉시 다음 동작에 적용. 기존 도메인 정본과 데이터 위치 보존.

## Boundaries

This accepts field ownership, identity, admission and failure semantics. It does
not certify native GUI behavior, another Mac, every corpus, or distribution.
The [integration evaluation](eval-0139-functional-standalone-test-app.md) owns
those implementation checks and outstanding evidence.

## Route

`pass` for the foundation contract; product checks remain independently scoped.

## Current Contract — 2026-10-19

General preferences use local `settings.toml` values, with defaults only for absent
fields. The four former general-preference environment variables are ignored even
when malformed. System zoneinfo supplies the initial time zone; process `TZ` does
not override it. Runtime storage and desktop authentication configuration retain
their separate owners. The compatible API still has `saved` and `effective`, but
both contain the same values; `source` is only `saved` or `default`.

Project display now always abbreviates the current home to `~`; its retired fields
remain inactive and are preserved when saving. Schema 1, unknown-field retention,
atomic private writes, revision conflicts, error preservation and application
timing are retained. Settings no longer expose override or split-value messages.

All 28 settings tests and the combined 131-test relevant run passed. Conflicting
and malformed old variables, missing-file defaults, sync scheduling from the file,
restart persistence and unchanged real user settings were checked. Scoped contract
PASS; [C07's Run](../run/run-20261018-172-general-and-project-settings.md#file-owned-general-settings--2026-10-19)
and the latest integration receipt own runtime evidence and its limits.

## First-Startup Persistence — 2026-10-19

Scoped PASS: the existing shared app/web startup creates a schema-1 settings file
with all defaults when absent. It does so before requests, without requiring Save
or completed onboarding. Later startups preserve existing files; only absent fields
fall back in memory. Malformed or newer files remain intact and report an error.
The read helper itself has no write side effect.

Two new lifecycle tests passed across twelve independent web/desktop startups;
all 28 existing settings tests passed. Fresh private creation, restart/unknown-field
and byte/mtime preservation, ignoring retired variables and error cases passed.
The current frozen app backend also passed three isolated starts with authenticated
API save/restart/error checks. [The Run](../run/run-20261018-166-local-settings-contract.md#first-startup-confirmation--2026-10-19)
owns the bounded evidence. Application code and distributed artifacts are unchanged.
