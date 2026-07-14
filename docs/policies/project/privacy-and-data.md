# Privacy And Data Handling

## Purpose

LocalBrain can display highly sensitive local information. This policy defines the boundary between shareable source code and private runtime data and governs persistence, external access, and disclosure.

## Repository Boundary

The Git repository may contain:

- application source code
- schemas and migrations that contain no user data
- generated or synthetic tests and fixtures
- shareable documentation without private paths, source names, ticket identifiers, copied conversations, or credentials

The Git repository must not contain:

- SQLite databases or database journals
- Claude or Codex session JSONL
- indexed note or document contents
- Task Runner prompts, evidence, streams, or result artifacts
- exports, logs, credentials, tokens, or environment-specific secrets
- screenshots or fixtures containing real local or company information
- machine-specific workflow inventories and handoff context

`.gitignore` is a fallback guard. The primary protection is keeping runtime data physically outside the repository.

## Local Persistence

The default runtime directory is:

```text
~/Library/Application Support/LocalBrain
```

It contains `localbrain.db` and Run artifacts. `LOCALBRAIN_DATA_DIR` may override this location, but it should not point to a tracked repository path.

Removing a source from LocalBrain must be distinguished from deleting the original local file or note. The application must not delete an original source as a side effect of unregistering or purging its index.

Backup, restore, retention, purge, encryption, and schema-recovery controls remain open work tracked in the [Project Backlog](../../plans/project/backlog.md).

## Source Persistence Modes

External connectors should support explicit persistence behavior per source:

| Mode | Local persistence |
| --- | --- |
| `reference` | Identifier, link, and minimal metadata only |
| `cache` | Fetched content stored temporarily with an expiry policy |
| `index` | Approved content retained in the local search index |

No connector may silently promote content from `reference` or `cache` into durable `index` storage.

## External Access

- Company systems must be accessed only through approved connector or MCP Gateway capabilities.
- External integration begins read-only.
- Any future external write requires a visible preview, attribution, and explicit user confirmation.
- Local content must not be sent to an unapproved AI, embedding service, website, repository, or person.
- Generated summaries must preserve provenance and must not present inference as confirmed fact.
- Connector failures, stale content, and inaccessible sources must remain visible rather than being represented as current data.

## Credentials

Credentials should remain managed by the operating system, Claude CLI, or an approved gateway. LocalBrain must not copy credentials into its SQLite database, Run evidence, logs, tracked configuration, or documentation.

## Source Consent And Permissions

- Sources should be explicit and inspectable, including indexed paths, files, note accounts, and external scopes.
- Apple Notes access is optional and uses local macOS Automation. The operating system may request permission on first connection.
- Source-specific exclusions and retention controls must be implemented before broad automatic indexing.
- Error pages and logs should avoid full prompts, note bodies, session excerpts, credentials, and connector payloads by default.

## Tracked Examples

Tracked examples, tests, screenshots, and documentation must use synthetic names and content. Real Workstream titles, local absolute paths, ticket identifiers, Slack links, note text, and session excerpts belong only in local runtime data or ignored working context.

## Repository Enforcement

- `scripts/check-repo-privacy.sh` scans every tracked and non-ignored untracked candidate before commit.
- `.githooks/pre-commit` runs the same check through the repository-local `core.hooksPath` configuration.
- `.privacy-patterns.local` provides a local-only literal denylist for private names and phrases that generic detection cannot identify.
- `.privacy-allowlist` contains only exact paths of reviewed binary or media files approved for tracking.
- The scanner reports matching file paths without printing sensitive matching content.
- Passing the scanner reduces accidental disclosure risk but does not replace human review of newly approved media, external connector output, or export behavior.
