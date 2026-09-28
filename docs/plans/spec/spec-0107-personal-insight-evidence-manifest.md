# SPEC-0107: Personal Insight Evidence Manifest

## Metadata

- ID: `spec-0107`
- Status: `approved`
- Parent Feature: [FEAT-0107](../feature/feat-0107-personal-insight-evidence-manifest.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Created: `2026-09-27`
- Updated: `2026-09-27`

## Implementation Goal

Provide a read-only, versioned value producer for a bounded sample of currently stored Claude and Codex work Session messages. A later Run may freeze this private value as its input. This Spec creates no Run, model call, UI route, or new persistent table.

## Input And Eligibility

- The module exposes `build_insight_evidence_manifest(connection, *, mode, requested_at, question=None, source_keys=None, date_from=None, date_to=None, timezone="Asia/Seoul")` and `resolve_insight_evidence_reference(connection, reference)`.
- `requested_at` is a required timezone-aware `datetime`; the manifest stores it as UTC. `mode` is `ask` or `discover`. An `ask` question is nonempty after trimming and at most 2,000 characters; `discover` accepts no question. `source_keys` is either `None` for all currently registered Claude/Codex sources or a nonempty set of existing eligible source keys. Dates are optional strict `YYYY-MM-DD`, inclusive in an IANA timezone; an inverted interval is invalid.
- Eligible Sessions are `work`, `primary`, `full`, from registered `claude` or `codex` providers, with at least one nonblank `message` Activity Event from `user` or `assistant`. Scope applies to the event occurrence time, not merely the Session's last activity. Known event times after `requested_at` are excluded. An undated event is eligible only when no date bound is supplied; bounded dates cannot imply when it occurred.
- Read from `sources`, `sessions`, `activity_events`, and the existing Session `search_index`. Never read native files, tool calls, tool payloads, Workstream links, the skill-observation ledger, or Usage Records. No write or synchronization occurs.

## Selection

- Count all eligible Sessions and messages for the selected scope before sampling. Expose these totals, selected totals, per-source coverage, earliest and latest selected known event times, unknown-time count, and omission reasons. A sample is never represented as exhaustive when eligible material was omitted.
- `discover` distributes Session picks across source key and local calendar month; within a bucket it prefers more recent Sessions. Ties use the stable Session ID. It takes at most 100 Sessions.
- `ask` builds an escaped OR query from at most 16 distinct question terms against the existing `search_index.body` column. It selects up to 70 eligible Sessions in FTS rank order, then fills remaining slots with the same source/month spread. If there is no indexed match or no usable term, spread selection may still produce evidence but the manifest explicitly says it found no lexical match. An indexed Session hit is only a search candidate; a message excerpt is marked lexical only when its own text contains a selected term.
- At most three eligible message excerpts are taken from each selected Session. For a lexical candidate, prefer matching messages by distinct term overlap, then user role, then sequence. Otherwise choose first, middle, and last message in source order. Deduplicate any repeated positions.
- Hard caps: 100 Sessions, 300 excerpts, 600 Unicode characters per excerpt, and 120,000 Unicode excerpt characters overall. The excerpt records its full-text SHA-256 revision, full text length, and character start/end offsets. A lexical excerpt centers its first matched term with context; a spread excerpt starts at character zero. The selected output is ordered by Session selection rank and event sequence.

## Manifest And Reference Review

- The value includes `version`, normalized input scope with resolved UTC date bounds, selection method and lexical-match state, generation time, coverage, omission reasons, and `sessions` with ordered `events`. The event reference carries source key, provider kind, current Session ID, Activity Event ID, role, occurrence time, sequence, complete-text digest, excerpt, offsets, and a `/sessions/{id}` destination. It contains no native source path or external Session ID.
- `resolve_insight_evidence_reference` rereads the current Session and Event with the same IDs. It returns `current` only when source key, provider kind, eligibility, event role, and full-text digest still agree. Missing Session or Event is `unavailable`; a present but changed or newly ineligible row is `stale`. Resolution returns status and a Session destination when the Session exists, not a replacement excerpt. It never rewrites a frozen manifest.
- A future Run artifact owner may retain the manifest privately outside Git. This module creates no retention owner and does not persist it.

## Failure And Boundary Behavior

- Invalid mode, timezone, date, source, or question raises `ValueError` before evidence is read. A valid empty scope returns an empty manifest with an explicit `no_eligible_messages` reason. No indexed match in `ask` is a coverage note, not evidence of no useful personal improvement.
- Unknown dates, lexical search misses, sampling, and source disappearance remain explicit. No inference about task success, productivity, or causation is produced here.
- A single SQLite read savepoint holds source, eligibility, selection, and excerpts at one database state. The same database state and inputs produce the same manifest bytes apart from no ambient clock or random choice; the caller supplies `requested_at`.

## Synthetic Review Cases

| Case | Supplied situation | Required result |
| --- | --- | --- |
| Positive | One Claude primary work Session and one Codex primary work Session contain dated user/assistant messages in scope. | Both sources can appear with exact current Event references and source coverage. |
| Negative | Maintenance, metadata-only, provider-internal, child, tool-call, and whitespace-only rows share the same dates and search terms. | None enter the manifest or eligible-message totals. |
| Boundary | More than 100 eligible Sessions, 300 potential excerpts, or 120,000 excerpt characters exist. | Every hard cap holds and omissions show that the sample is incomplete. |
| Time | A message has no timestamp, one falls just inside the local date, and another just outside it. | The bounded date includes only the inside message and reports excluded undated coverage. |
| Staleness | An Event's normalized text changes after a manifest is frozen, then its Session disappears. | The first review is `stale`; the later review is `unavailable`; the frozen excerpt is unchanged. |
| Privacy | A source message contains a private path or credential-like string. | No native file or external call occurs; the private excerpt stays only in the returned in-memory value and never enters tracked output or logs. |

## Ownership And Evaluation Focus

- Implement the read-only producer in `src/localbrain/personal_insight_evidence.py`. Update the project architecture, Session data-model, and privacy owners for the new contract. No schema migration is needed because the existing Session and Activity Event keys and indexes suffice for an explicitly started bounded Run.
- Contract evaluation covers input validation, source and event eligibility, value shape, digest resolution, hard limits, no persistence or external call, and no ambiguity for the downstream Run Feature.
- Functional evaluation covers both modes, empty and over-limit scopes, source/time spread, undated events, lexical search fallback, stale and unavailable references, and noninterference with the Usage & Cost opening route.

## Open Blockers

- None for this evidence-only producer. The model execution/privacy choice remains with a later analysis-Run Feature.
