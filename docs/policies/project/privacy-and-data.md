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

It contains `localbrain.db`, guarded schema-migration backups such as `localbrain.db-pre-usage-attribution-check-v1.bak`, `localbrain.db-pre-maintenance-workstream-fk-v1.bak`, `localbrain.db-pre-maintenance-session-contract-v1.bak`, and `localbrain.db-pre-external-resource-url-scope-v1.bak`, and Run artifacts. `LOCALBRAIN_DATA_DIR` may override this location, but it should not point to a tracked repository path. A versioned migration backup is local-only, is validated before use, and is never overwritten by a later startup.

An in-app Task Runner stream remains a private Run artifact used for the Run Console and result parsing. It must not be re-imported as a Session, Usage Record, Local Context document, Activity Event, or search row. The selected Claude or Codex runner's persisted native JSONL is the sole Session and Usage source for that execution; maintenance policy keeps its content and resolved child content out of ordinary activity and search consumers while their direct real-model Usage Records remain eligible for cost totals.

Removing a source from LocalBrain must be distinguished from deleting the original local file or note. The application must not delete an original source as a side effect of unregistering or purging its index.

General backup, user-facing restore, retention, purge, encryption, and broader schema-recovery controls remain open work tracked in the [Project Backlog](../../plans/project/backlog.md); a migration-specific recovery copy does not close that wider requirement.

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
- Local Source Instance records may store a stable local key, provider/service identity, display name, and a shape-validated Gateway alias or canonical Atlassian Cloud ID, but never arbitrary opaque values, site URLs, credentials, access tokens, sampled content, or raw connector payloads.
- Capability observations retain only versioned logical-operation names, a schema fingerprint, availability, timestamps, invalidation, and bounded error evidence. They are refreshed explicitly rather than on startup, page load, search, or ordinary preview.
- A version-controlled allowlist must map logical reads to exact provider targets and validate bounded arguments before dispatch. Runtime rows, model output, prompts, or caller-supplied tool names cannot grant external writes.
- External synchronization requires a host-side executor that receives only a pre-authorized dispatch. Provider arguments and returned content stay in private Run artifacts; query projections and call-accounting rows contain no arguments or provider content. Claude or Codex receives only the validated local evidence and cannot access broad external tools in that Run.
- Applied Atlassian facts are private runtime data: Site domains, exact URLs, remote identifiers, bounded metadata, source bodies, normalized text, hashes, freshness evidence, local notes, Topic/Tag vocabulary and assignments, and FTS rows remain outside Git. Remote metadata cannot contain Jira description or Confluence body; approved body content is stored in its separate source-preserving table and reaches the content-role FTS row only under explicit indexed coverage.
- Derived Atlassian sightings are private runtime data. They may retain an eligible primary work Session or enabled Local Context Document identity, event/line/occurrence locator, exact and normalized URL, and optional bounded title/remote-ID observations from an approved read result. They must not retain a Session or Document excerpt, opaque tool arguments/results, comments, attachments, command output, or maintenance/subsession content.
- Direct Atlassian URL preview, first-connection setup, registration, and connection display editing are local-only operations. A selected or unambiguous configured Site is reused; for a first domain, one explicit provider choice may create a stable Source Instance, Site, and reference atomically. Provider denotes the local official-Atlassian or Gateway access path and is not inferred from URL content. An optional configuration reference remains restricted to a shape-validated Cloud ID or Gateway alias; credentials and tokens are never accepted. Key-only text, invalid URLs, ambiguous Site matches, and failed setup create no partial rows and trigger no remote lookup.
- Space-candidate retrieval is an explicit, Source Instance-scoped maintenance action. Its bounded result is private runtime evidence, is labeled partial because current providers expose no complete catalog operation, and never causes automatic bulk registration.
- Atlassian refresh preview is computed entirely from local state. Only an explicit submitted selection may dispatch reads, and preparation rejects more than 20 calculated reads. Item, Space, Thread, Workstream, and all-known scopes include only existing local Items; they never enumerate the company estate implicitly.
- A mixed-Source refresh stores only per-target Source Instance authorization in the private manifest and a nullable aggregate Source Instance in the query projection. Validated results may update remote state/content, but cannot overwrite local attention, notes, Topics, Tags, or Workstream/Thread relations. Confluence catalog results create only bounded stale indexed-intent stubs and do not fetch Page bodies.
- Browse, detail, search, and local note/Topic/Tag updates use only stored local state. Search keeps identity, eligible metadata/content, and user-owned local text in separate derived roles and groups them at read time; it never sends a query or result to Atlassian or an AI service.
- Atlassian Add orientation, Add-method switching, and MCP-connection management read only persisted local rows. The registered-scope projection excludes unregistered evidence and candidate results. A target Site and MCP connection must match locally before an explicitly submitted candidate-discovery Run may be prepared.
- Reference coverage rejects remote metadata and body persistence; metadata coverage rejects bodies. Explicitly downgrading indexed coverage removes the stored body and rebuilds the remaining eligible identity/local FTS roles, while ordinary failure or unavailability never performs that destructive downgrade.
- A due timestamp is local advisory state and performs no external or model call. Failed, unavailable, and not-found checks retain last-known content and local organization until an explicit destructive local action.
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
