# EVAL-0110 Contract: CLI Startup

## Metadata

- ID: `eval-0110-contract-cli-startup`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-135](../run/run-20261001-135-personal-insight-cli-startup.md)
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md)
- Execution Profile: `backend-product`
- Surface Lane: `backend`
- Created: `2026-10-01`

## Result

The launcher now resolves its executable path before spawning and grants read access to that exact file for sandboxed bootstrap. The permission value is assembled as TOML with an encoded path key, preserving quoted and non-ASCII filenames. New settings record runner policy `personal-insight-cli-v3-bootstrap` and the runtime-file allowance. The guide, schema, profile, model, working directory, ephemeral flag, blocked command network, and read-only artifact policy are unchanged.

Twenty-five focused tests pass: guidance 16, Run guidance 2, usage 7. The new contract test covers both a symlink launcher and a direct executable, exact permission entries, path escaping, retained network/web restrictions and ephemeral execution. Existing checks cover package/schema freezing, old guide compatibility, report rendering, usage on failure and cancellation, and accounting idempotency.

No profile-home, installation-directory or general-home read permission is added. The minimal runtime policy still owns its existing platform exceptions; it must not be described as excluding every path outside the artifact folder. No blanket sandbox bypass or automatic paid retry is introduced. Historical failed Runs remain intact. Actual platform verification and its narrower evidence limits are recorded in the [functional evaluation](eval-0110-functional-cli-startup.md).
