# Work-Grounded Learning

## Purpose And Current Boundary

This policy defines learning from personal work with reviewed source evidence.
It owns common lesson, evidence, immutable revision, attempt, interval and
visibility contracts. [Code And Command Learning](code-command-learning.md) owns
version-2 scenes, reviewed articles, daily selection, question depth and same-day
assistance rules.

The current producer is an explicitly reviewed local JSON packet. Import validates
its structure; it does not establish factual truth. No generator, external fetch,
model download or index refresh runs when a lesson or home is opened.

## Learning Concepts

| Concept | Meaning |
| --- | --- |
| Lesson | Reviewed teaching material connecting a work example with official evidence, identified by a stable lesson key. |
| Source evidence | A reviewed excerpt or faithful bounded summary with its locator, version, check date, conditions and exceptions; its stored snapshot is distinct from an unread full document. |
| Immutable revision | One normalized lesson with its reviewed source snapshots, questions and reference answers. The stable lesson key groups revisions; a content fingerprint identifies each revision. |
| Attempt | A saved response with later personal self-assessment, or an explicit reading record, tied to an immutable revision and question. A page visit creates neither. |
| Review interval | An explainable schedule from completed local-day records and reported assistance, rather than a correctness or mastery score. |
| Visibility | Reversible snooze/hide intent attached to the stable lesson key, shared by its revisions while preserving attempts and snapshots. |

## Packet And Source Ownership

### Lesson And Question Fields

Packet version is integer `1` or `2`, with `lessons` (1–30). Version 1 preserves
its normalized shape and revision identity. Version 2 adds the required scene,
selection, authorship and question fields in the [scene contract](code-command-learning.md#packet-version-2).
Both share these base fields. Each lesson has a stable
`key` (ASCII letters/digits/hyphens, 1–80), `title`, `topic`, `why`, `explanation`,
`version_status` (`matched` or `unverified`), `applicability`, `sources` (2–12),
and `questions` (1–12). Optional `reviewed_by` is `owner`, `assistant` or
`unspecified` (default). Assistant-reviewed material is visibly distinguished from
owner review; opening it never confirms its correctness. Questions have unique local `id`, `kind` (`recall` or
`apply`), `prompt`, `hint`, `answer`, and nonempty `source_ids`. Text is bounded;
packets are at most 2 MiB. Unsupported fields are rejected, not silently dropped.

### Source Evidence And Applicability

Each source has a unique `id`, `kind` (`work` or `official`), `title`, `locator`,
`checked_on` (nonfuture ISO calendar date), `version`, `snapshot`, and optional
`url`. At least one of each kind is required. Each question cites an official
source; source references must resolve inside its lesson. `snapshot` preserves a
reviewed excerpt or faithful bounded summary, including the material conditions
and exceptions for the claim. The importer adds `snapshot_sha256`, the fingerprint
of that stored snapshot, not of an unread full document. Version 2 preserves literal
snapshot whitespace and terminal newlines; version 1 keeps its original trimming.
Official sources require
an HTTPS URL with no embedded credentials. Work sources may link only to existing
local `/sessions/<integer>` or `/documents/<integer>` routes, or leave `url` empty
and show their locator as text. The importer does not read paths or follow URLs.

`version_status=matched` is the curator's statement that the official evidence's
version applies to the work example; all official versions must then be known
(not `unknown`). `unverified` is the safe default when historical/deployed versions
are unresolved. Both the version and applicability statement stay visible.
`checked_on` means the declared reviewer checked this snapshot at that date, not currentness or
automatic monitoring. UI calls snapshots over 90 days old “다시 확인할 자료”; that
is a pilot reminder threshold, not proof of invalidity or a guarantee for newer
sources. There is no current automatic recheck.

### Immutable Revisions And Atomic Intake

The reviewed packet is persisted in the private main SQLite DB. `lesson_key`
groups revisions; SHA-256 of canonical normalized lesson JSON identifies a
revision. The newest inserted revision is current. Reimporting any already stored
revision is a no-op and never rolls back the current revision. A genuinely new
revision starts its own learning schedule. Old source snapshots/questions/answers
remain readable with old attempts. Title alone does not establish identity.
An entire packet is validated before one transaction inserts any lessons.

Sources and questions currently belong to each immutable lesson packet; there is
no independent editable source registry, content editor, automated candidate
discovery or official-document monitoring. Version-2 packets contain manual
authorship and relevance metadata, which the deterministic daily selector uses;
version-1 `reviewed_by` records only a declared review role. These are curator
declarations, not a full generation audit. The curator selects and writes the
material and supplies the review date. HTTPS admission does not establish that a
domain is official or a claim is correct. Adding or revising a lesson requires a
reviewed packet import; opening local work or synchronizing its index does not
silently rewrite an existing lesson. The DB retains the normalized packet; the
importer does not retain the original authoring file or export an editable copy.

## Attempt Meaning And Transitions

An attempt points to an immutable lesson revision and a question inside it.
`answer` and `confidence` (`low`, `medium`, `high`) are recorded before feedback.
`hint_used` records help used in the submitted answer: a checked report or an
actually opened hint/additional-code disclosure in the enhanced reader. Optional
practice entered from the explanation-first home carries `from_note=1` and stores
`hint_used=1`, including without JavaScript and after a validation/save retry.
Other entry paths retain the native help-report checkbox. Same-origin URL-encoded POSTs
and an idempotency key bound to the lesson and question guard browser mutations
and duplicate submission. Idempotency collisions with different payloads fail.

Answer submissions begin `pending`. Exactly one self-assessment transitions them
to `again`, `partial` or `recalled`; repeated identical finalization is a no-op,
conflicting finalization fails. `read` is a separate explanation-first attempt,
with empty answer, no confidence and no claim of retrieval. The home openly shows
the reviewed article (or a legacy lesson's complete explanation); it does
not create a reading or exposure record. The reader's comparison, rubric and
saved evidence excerpts still follow a stored answer or explicit reading choice.
**읽은 내용 기록** explicitly saves `read` and returns home or the individual article.
Visiting a page, skipping,
snoozing or hiding makes no attempt and is never treated as an error or mastery.

Confidence and self-assessment are personal reports. The app does not label an
answer correct, measure mastery, infer ignorance from code, or train a model.
Every stored answer remains alongside its original question and feedback.

## Scheduling And Daily Selection

Calendar dates use the configured application timezone. For each current revision,
unfinished (`pending`) attempts do not advance scheduling. Completed records on
one local date count as a single review; that day's latest completed self-assessment
governs its result. `read`, `again`, `partial` or a hinted answer resets the streak
and schedules tomorrow. Consecutive distinct-day unhinted `recalled` assessments
schedule 3, 7, then 21 days later (capped). These are explainable pilot defaults.
For version 1, questions cycle through the stored list with distinct completed days, allowing
recall and application prompts. Repeating an attempt in one day cannot advance
the question sequence or multiply intervals.

Home selects at most one lesson total per local day. The
[selection and depth policy](code-command-learning.md#daily-eligibility-and-selection)
uses history before today to continue earlier pending work, then due reviews,
then new lessons ranked by curator-declared relevance and work date. It owns
version-2 concept depth and conservative same-day feedback assistance; neither
changes stored self-reports or establishes objective mastery. Today's selected
completed lesson stays visible without continuously refilling the feed. A pending submission stays resumable.
Explicit snooze/hide, a new revision/import or a timezone change may change the
eligible set. The whole library remains available for deliberate extra reading.

Visibility belongs to the stable lesson key, not a revision. Snooze means tomorrow;
hide is reversible in the library. Both preserve attempt history and snapshots.
There is no streak badge, debt counter or deadline penalty.

## Product And Operational Boundary

Home (`/`) offers one daily learning widget; `/learning` is the complete library and
`/learning/<revision-id>` is the reader. Existing Sessions Dashboard and work
organization keep their own routes. The CLI is `localbrain learning import PATH
--reviewed`; it requires explicit review acknowledgment and never fetches sources.
The packet format and a synthetic example are documented with that command.
The UI provides only actions with implemented backend support.

Home contains one work-based technical article with work context, labeled original
code, connected explanation sections and a reusable takeaway. A reference rail
contains genuine section navigation and numbered official sources; narrow screens
place references after the prose. Questions remain optional at the end. Article
content is reviewed separately from short question answers and is not automatically
summarized or truncated. Source versions/check dates, review responsibility and
applicability remain available beside it, with material limits in the prose.
An explicit read action finishes the article. Selection guidance and curator reasons
remain in the library; detailed evidence remains in the reader. With no selected
scene, home offers the library.
Version-2 readers keep preserved code/commands adjacent to the question
and feedback, with explicit practice links and optional tab-local draft recovery.
The library exposes review role,
version uncertainty, source titles/dates and preparation instructions without
showing the answer or saved source excerpts before the existing reading choice.
Its preparation disclosure explains manual intake and revision updates.

## Privacy And Source Navigation

Durable content belongs under [application storage](installation-and-storage.md),
outside Git. Private work sources, answers and screenshots are not tracked.
Public documentation and examples use synthetic work. Import diagnostics identify
fields rather than dumping private payloads. External source links use
`referrerpolicy=no-referrer`; visiting one is an explicit user navigation.

## Later Admission

Automated extraction, official-source retrieval and local generation need separate
bounded specs. Embeddings discover relevant material; they do not generate lessons
or establish knowledge. Before a generator can teach from private material, its
public/synthetic evaluation must address supported claims, conditions/exceptions,
version fit, ambiguous questions, grading mistakes, latency and memory. Current
model/relationship failures do not become passes under this learning contract. Product
benefit needs delayed independent explanation and transfer evidence from real use.

## Synthetic Packet Example

This is an illustrative HTTP lesson with invented work context. It is not imported
automatically and does not claim to describe the user's work. Save a packet
outside Git, review its facts and replace the work/source metadata for real use.
Legacy prose fields are displayed as plain text with preserved line breaks.
The optional version-2 article uses the shared safe Markdown renderer. Code previews use the shared safe local syntax highlighter without
changing stored snapshots. `unknown` is the unknown version token. `reviewed_by` declares who
reviewed the material; `--reviewed` acknowledges the importer's review responsibility.

```json
{
  "version": 1,
  "lessons": [{
    "key": "sample-http-safety",
    "title": "What does a safe HTTP method mean?",
    "topic": "HTTP",
    "why": "In this invented example, a developer adds a read-only report route.",
    "explanation": "Safety describes the requested semantics. Incidental logging can still happen.",
    "reviewed_by": "assistant",
    "version_status": "unverified",
    "applicability": "A synthetic exercise; no deployed implementation was inspected.",
    "sources": [{
      "id": "work",
      "kind": "work",
      "title": "Invented report-route change",
      "locator": "synthetic example, not a real file",
      "checked_on": "2026-10-17",
      "version": "synthetic-v1",
      "snapshot": "The example route returns a report and writes an access log."
    }, {
      "id": "official",
      "kind": "official",
      "title": "RFC 9110, section 9.2.1",
      "locator": "Safe Methods",
      "url": "https://www.rfc-editor.org/rfc/rfc9110.html#name-safe-methods",
      "checked_on": "2026-10-17",
      "version": "RFC 9110",
      "snapshot": "A safe method's requested semantics are read-only; incidental effects such as logging are not excluded."
    }],
    "questions": [{
      "id": "logging",
      "kind": "apply",
      "prompt": "Does an access-log entry alone make the report GET unsafe?",
      "hint": "Distinguish the requested effect from incidental processing.",
      "answer": "No. Incidental logging alone does not change the safe semantics of the requested read.",
      "source_ids": ["work", "official"]
    }]
  }]
}
```

This example preserves the distinction in
[RFC 9110 §9.2.1](https://www.rfc-editor.org/rfc/rfc9110.html#name-safe-methods).
The importer requires all question/source IDs to resolve and validates the whole
packet before insertion. Unsupported fields, oversized packets, invalid dates,
unadmitted URLs and unknown enum values produce bounded diagnostics. The CLI
prints only inserted/unchanged counts; it never echoes lesson content on success.

## Implementation Ownership

- `learning/service.py`, `learning/cli.py`, `learning/web.py`: reviewed local packet
  intake, immutable lessons/source snapshots, personal attempts, deterministic
  daily selection and native home/library/reader forms. Durable state is in the
  main DB; this flow does not invoke search, generation or external retrieval.
