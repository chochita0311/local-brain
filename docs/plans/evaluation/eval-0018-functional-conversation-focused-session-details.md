# EVAL-0018: Conversation-Focused Session Details Functional

## Metadata

- ID: `eval-0018-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260717-18`
- Attempt: `1`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: normalized and legacy detail routes
- Created: `2026-07-17`

## Browser Evidence

- A synthetic primary containing two messages and two tool calls rendered exactly two conversation rows and zero tool rows. Both visible messages retained their literal `Bash`, `exec`, and `Write` wording.
- The primary displayed its full raw count and two normalized direct children in the retained Subagents section.
- A direct child rendered two messages, no tool row, `상위 Agent` and source Subagent role labels, a parent notice, and parent and inventory back destinations. It did not expose its grandchild.
- A tool-only primary displayed zero conversation rows, a raw event count of one, and the intentional no-conversation state.
- Grandchild and unresolved child requests returned `404`.
- A matching legacy Claude URL redirected to the normalized child. A valid unimported lazy child remained readable with two messages and no `Bash` tool row.
- No browser console messages were reported.
- A mobile Lighthouse snapshot scored Accessibility and Best Practices at `100`.

## Automated Evidence

- JavaScript syntax, Jinja parsing, Python compilation with a local temp bytecode cache, all 38 tests, and the repository privacy check passed.

## Findings And Regression

- No blocking functional finding.

## Route

- Next action: `pass`
