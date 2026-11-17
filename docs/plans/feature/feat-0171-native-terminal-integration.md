# FEAT-0171: Native Terminal Integration

- ID: `feat-0171`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0030](../prd/prd-0030-macos-terminal-work-area.md)
- Created: `2026-11-13`
- Updated: `2026-11-13`
- Authority: explicit human request to implement app integration and validate payloads with subagents.

## Goal And Acceptance

Apple Silicon/macOS14 app provides the shared Terminal workspace through the Rust
runtime from FEAT0170, including a verified offline Node/PTY/helper payload. Users
do not install Node/npm. First explicit use prepares the private stable payload;
viewing pages/list/settings does not start a shell or install a login agent.

HTTP and WS both require current desktop authentication, exact loopback Host/Origin
and existing input leases. Terminal-only admission/assets are enabled while other
optional/suspended features keep their existing exclusions. Window hide and normal
Quit detach without stopping jobs. Stable cached helper/management entry survives
backend/app path loss; explicit stop/update uses exact scope and existing identity
checks. Shutdown/reboot does not replay commands or restore processes.

Builder uses public official Node24.15 arm64 with verified release hash and locked
engine, final signed file hashes/licenses/manifest, relocatable resources and
owner-private immutable cache publication. Actual build/ABI/codesign/relocation/
offline first-use/close/Quit/reconnect and malformed-payload cases are required.
Physical IME/VoiceOver/minimum-OS hardware/performance observations stay distinct.
No broad shell permissions, remote machines, agent automation or source-data reset.

## Trace

Contract/backend/integration: FEAT0170 and runtime payload lifecycle.
Frontend/native: same workspace, authenticated admission, existing host lifecycle.
Infra/docs: payload builder, PyInstaller/Tauri resources, package inspection and guides.

- Spec: [SPEC-0171](../spec/spec-0171-native-terminal-integration.md)
- Run: [Run252](../run/run-20261113-252-native-terminal-integration.md)
- Evaluation: [Eval0168](../evaluation/eval-0168-native-terminal-integration.md) owns initial package/host evidence. [Run253/Eval0169](../evaluation/eval-0169-terminal-everyday-interactions.md) closes the formerly locked required window/close/relaunch gap with the final actual native-window10 checks. This is technical integration acceptance; native IME automation did not pass, and physical input/human visual/VoiceOver/sleep/minimum-OS/recipient/performance readiness is not accepted.
