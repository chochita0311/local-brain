# Run254: Persistent Terminal Workspaces

- Status: `passed`
- Feature: [FEAT0173](../feature/feat-0173-persistent-terminal-workspaces.md)
- Spec: [SPEC0173](../spec/spec-0173-persistent-terminal-workspaces.md)
- Parent: [PRD0030](../prd/prd-0030-macos-terminal-work-area.md)
- Profile: `fullstack-product`; host persistence/launch, frontend, integration/docs.

The user replaces the previous fixed-folder group contract with named groups
that can contain different-root tabs and panes and remain empty. The same episode
also removes duplicate collapse controls, reduces Terminal density and explicitly
approves automatic zsh command-state integration. Earlier Feature172/Run253
results remain historical; preserve its direct End, retry/input/focus/order,
background and existing user process contracts. No installed-app replacement,
active manager stop/upgrade, generic settings/DB migration or Git write requested.

Primary owns architecture, persistence, implementation and final acceptance.
screen-alignment extend/current constitution governs the existing frame;
clean-code applies to separating durable workspace identity from cwd/process
state and startup integration. Named research_worker gets bounded official zsh/
VS Code startup evidence only, no final implementation or acceptance authority.
The daemon interrupted initial reads; source state was checked before proceeding.
No product edits had completed at that restart.

The private baseline includes106 previously dirty/new files. Existing runtime
payload66b53da… remains the compatibility target; implement through host metadata
and the existing generic executable contract. Contract lane precedes UI acceptance;
startup integration must pass real synthetic zsh/PTY evidence. Earlier native IME
automation failures remain unaccepted and outside this behavior correction.

## Implementation And Impact

This is a deliberate UI/data/interaction change, with host API, recovery,
packaging and bilingual guide consumers. Workspaces now own logical identity,
name and optional default cwd rather than deriving identity from a tab's cwd.
The new private JSON store uses the existing global writer lock and atomic writer;
fresh generation/member checks preserve current jobs, confirmed retry ownership
and hidden ordering slots. Backup/restore includes and validates metadata; it
does not archive generated launch shims or restore processes. Existing settings,
DB schema and source/Session/Workstream/Usage semantics remain unchanged.

The host prepares versioned zsh launch/startup files through the manager's existing
generic executable contract. A real zsh still loads user startup files; no live
input injection, `.zshrc` edit or manager upgrade is required. The GUI captures
configured defaults, explicit other-folder tabs/splits and workspace membership
without making group changes into process relaunches. Exactly one Terminal panel
toggle and scoped compact controls preserve shared shell and narrow touch roles.

Primary semantic review followed actual create→membership, retry, move→existing
input, empty→restart and startup→precmd/preexec paths. Removing the obsolete
frontend folder fallback avoids two competing group models. The independent
frozen challenge found a post-create `TerminalError` escape: a fresh membership
read could fail after creation and hide the known process behind HTTP500.
The repaired path returns identity plus warning; a focused test verifies one
creation. Primary also resolved defaulted HTTP shell integration and backup
disposition gaps. One informed frozen repair recheck supports these repairs;
worker output is evidence rather than acceptance.

## Verification And Recovery

[Eval0170](../evaluation/eval-0170-persistent-terminal-workspaces.md) owns the
test/design/interaction findings and limits. Final shared browser95, Node75,
Python1700 (49 opt-in skips), separate zsh5-case integrity/real-PTY packet and
319-file final app integrity checks pass. First Python1699 failed one stale
generated schema reference row; the standard writer, six focused audit checks
and the final1700 run pass without a schema/decision change.

The first native driver run advanced to another split before its control was
re-enabled. Waiting on actual enabled state passed that stage. A second run
reached the workspace modal but its content disappeared from the external AX
child walk; normal synthetic ASCII focus/Tab/Enter is the selected form witness,
not an accessibility/IME acceptance substitute. Its screenshot also exposed a
wrapping folder picker and unstyled name input; two scoped CSS rules repair their
containment. Final CSS repeats the95 browser checks and ships in a new app build.
Failed observations remain in private evidence rather than being relabeled pass.

The development HTTP host was restarted with original argv/environment for new
routes/assets, then final CSS/log detachment. Both original terminal IDs/PIDs and
generation survived both reflections; the manager was never stopped or upgraded.
No user process, startup file or installed app was replaced. Dist contains the
local signed candidate; final native evidence and closure are recorded below.

## Final Result And Handoff

Actual packaged native12 checks pass with the final source/build-input SHA256
`01628f1b0bd1b48b7e93ff415dbbef0225b238415b7cbde0c4cda6416d3ac449`.
The native form is exercised through synthetic English keyboard focus/Tab/Enter.
Cold New, last-close/recreate, empty named workspace creation without a process,
four panes, different-folder integrated zsh prompt/running/nonzero result, order,
minimize/red close/Dock, Quit/source removal and relaunch preserve the observed
identities. The new zsh stays alive throughout lifetime checks. Final exact-scope
stop ends only test work and retains empty workspace names/defaults/IDs.
Suspension/resume is not a physical Mac sleep witness.

The final app contains319 verified runtime entries and uses unchanged payload
`66b53da245e4cb9be9deba12d1079217efce0a62977c053514cc71f81352e9e8`.
App regular-file bytes:988228537; ad-hoc signed, no notarization or installed-app
replacement. ZIP SHA256:
`9d86933a6322e0bc3b68abc90b4be00ac541bd0b5570aa673fca300f6d2372e1`.
Outputs remain `dist/LocalBrain-apple-silicon/LocalBrain.app` and
`dist/LocalBrain-apple-silicon.zip`.

Contract/functional/design/interaction evaluation passes this increment with
partial platform coverage. External AX modal traversal remains unresolved and
the existing native Korean IME probe is not passed. Physical input/VoiceOver,
real sleep/wake, minimum OS hardware, recipient/resource and human visual
acceptance remain separate. No additional Python family was migrated; the
parent Rust and app PRDs remain approved boundaries, not complete.

Private stage evidence retains frozen sources, research/review provenance, failed
attempts, final checks and owned synthetic screenshots. Task scratch, generated
test runtimes and this task's build cache are retired after archive verification;
the live development host has no dependency on task scratch. No Git write or
public/source export was requested or performed.
