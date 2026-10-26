# SPEC-0139: 독립 테스트 앱 전달

## Metadata

- Status: `approved`
- Parent Feature: [FEAT-0139](../feature/feat-0139-standalone-test-app-delivery.md)
- Parent PRD: [PRD-0021](../prd/prd-0021-macos-standalone-test-app-and-local-settings.md)
- Run: [initial delivery](../run/run-20261018-177-standalone-test-app-delivery.md), [portable metadata correction](../run/run-20261020-182-portable-python-build-metadata.md)
- Execution Profile: `infra-devtool`
- Updated: `2026-10-20`

## Implementation Boundary

The [common settings and desktop contract](../../policies/project/desktop-app-and-settings.md)
owns field precedence, source identity, search admission, locking, local recovery and
edition boundaries. This specification applies those rules to this Feature.
The [test-app guide](../../policies/project/standalone-test-app-guide.md) owns delivery and usage.

## Acceptance Mapping

- AC1: 개인 자료 없는 Apple Silicon .app ZIP, ad-hoc 서명·수동 교체 안내.
- AC2: 로컬 패키지 실행 근거와 다운로드한 팀원 Mac 실행 근거 구분.
- AC3: 확인한 환경·지원 한계·모델/인덱스 별도 공간 기록.

## Failure And Regression

Preserve originals, source/session IDs, frozen Usage attribution, unknown settings and
unrelated development features. Errors keep entered values and provide retry/recovery.
No implicit model download, external upload, paid signing or data relocation.

## Execution And Evidence

Primary-agent implementation with synthetic unit/integration/browser checks and an
independently launched bundled runtime. Record code, browser, packaged-app and teammate
Mac evidence separately. A build alone does not establish successful execution.
The active Run records observations and unresolved checks; do not infer a pass from this specification.

## Portable Python Metadata Correction — 2026-10-20

[Run 182](../run/run-20261020-182-portable-python-build-metadata.md) repairs a
privacy defect found in the delivered runtime. The compressed sysconfig module
retained the builder's interpreter installation prefix in 20 dictionary fields.
This is installation metadata, not the application's user-data location.

- Generate a build-only replacement for the target interpreter's sysconfig data.
  Preserve ABI/compiler/platform values; derive interpreter installation paths
  from the running bundled Python prefix. Never substitute another assumed home
  directory or require Python installation on the recipient Mac.
- Select this module before PyInstaller analysis caches code. Keep the builder's
  Python installation and user settings untouched. Generated files belong in
  the owned temporary build directory.
- Fail before packaging a ZIP when raw assets, Python archive code/filenames,
  nested stdlib ZIP or gzip content still contain known builder home/checkout
  and temporary-build paths. Report artifact/module names without echoing private values.
- Replace the delivered app and ZIP/checksum only after focused tests, archive
  inspection, isolated frozen startup and signature checks. Verify runtime
  relocation and preservation of actual settings/source-registry hashes.
- Record other-Mac execution and broader standalone acceptance gaps separately.
  No new model download, upload, signing account, UI or data-migration behavior.
