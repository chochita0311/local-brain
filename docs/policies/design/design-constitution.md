# Design Constitution

## Use

This file and its explicitly linked surface companions are the durable design source of truth for LocalBrain. It governs implementation and evaluation across the local web application.

Creative rationale lives in [DESIGN.md](../../../DESIGN.md). Reusable review checks live in [Design Evaluation](design-evaluation.md). Ownership and update rules live in [Design Document Governance](design-document-governance.md).

Keep reusable law here. Do not add implementation sequencing, migration notes, page-local exceptions, or unresolved experiments.

## 1. Project Context

- **Product type:** local-first developer work-context hub and personal continuity workspace.
- **Primary user:** one developer, PM, or analyst organizing their own sessions, projects, documents, sources, Workstreams, and maintenance activity.
- **Primary jobs:** learn from personal work evidence, resume interrupted work, reconstruct a Session-backed work flow, organize evidence into Workstreams and Threads, inspect source activity, search local context, review Suggestions, and monitor maintenance Runs.
- **Interaction character:** workflow-heavy and read-heavy. The interface must support fast scanning and sustained detail reading without separating evidence from state.
- **Device priority:** desktop-first local browser UI. Narrow viewports preserve access and comprehension but do not redefine the product as mobile-first.
- **Technical constraints:** FastAPI, server-rendered Jinja2, small JSON interactions, SQLite and FTS5, locally served assets, no external CDN, and no interface that implies unsupported backend behavior.
- **Starting source-set type:** screen-plus-context.

## 2. Source Reconciliation And Provenance

The design baseline reconciles three source roles:

| Source role | Contribution | Boundary |
|---|---|---|
| Initial upstream design system (AI) | neutral scale, warm brand direction, typography scale, spacing rhythm, radius and component cues | visual input only; commerce concepts and unsupported states do not transfer |
| LocalBrain product policies and code | entities, navigation, status values, privacy, provenance, routes, validation, and runtime behavior | implementation and product compatibility truth |
| Existing LocalBrain templates and CSS | proven shell shape, density pressure, content patterns, and responsive evidence | starting artifact; near-equivalent ad hoc values are normalized into this constitution |

The initial upstream review occurred through authenticated Figma access on 2026-07-15. External file keys and private URLs are not durable dependencies. The imported source remains identifiable by its stable public alias, review date, scope and contribution, while the rules below are self-contained.

Classification of the resulting system:

- **Imported direction:** cool neutral workspace, warm red brand accent, SF Pro-oriented typography, compact spacing, restrained radii, and low elevation.
- **Adapted rules:** accessible foreground and feedback colors, separate danger semantics, dark navigation, semantic spacing and elevation roles, reduced motion, and responsive transformations.
- **LocalBrain-specific rules:** learning-first home and Workstream-centered organization, source provenance, long-path handling, reviewable Suggestions, Local Context health, Run execution states, split-pane exploration, and technical console treatment.

## 3. Compatibility Constraints

### Product And Data

- Core visible entities are Lesson, Learning Attempt, Workstream, Thread, Checkpoint, Session, Activity Event, Source, Local Context source, Document, Project, Resource, Suggestion, and maintenance Run.
- Learning keeps the work example, official evidence, source/version uncertainty and personal response distinct. Reading and self-assessment never imply verified correctness or mastery. Daily suggestions have an end; existing work organization remains accessible through its own navigation.
- Code/command learning keeps the literal source beside its question and feedback, with compact screens stacking source before reasoning. Actual material and synthetic examples, reported execution and observed results, manual relevance and scheduling reasons remain separately labeled. Question depth names the reasoning task, never a mastery score.
- Workstreams and Threads are user-defined organization. Imported or inferred data must not look user-confirmed until accepted.
- Source identity, timestamps, status, and evidence remain visible wherever they materially affect trust or recovery.
- Missing, unreadable, stale, conflicting, or unavailable information must be labeled rather than silently omitted or presented as current.
- Long titles, paths, URLs, excerpts, and generated summaries must preserve layout containment at every supported width.

### Roles And Permissions

- The application is single-user and local-first; there is no visual role hierarchy.
- External references are read-only unless an approved feature explicitly owns a write action.
- Destructive local actions require clear scope and consequence. Suggestions remain reversible and reviewable.

### Forms And Validation

- Required names and titles display their requirement before submission and keep the entered value after a validation failure.
- Inline errors appear next to the owning field or action region and do not replace the page with raw server detail.
- Buttons and controls must not imply unavailable integrations, writes, or automation.
- Path and URL fields support long values without widening their container; truncation must provide a way to inspect the full value.

### Privacy And Provenance

- Local paths, source names, and evidence may be shown because the product is local, but they remain visually subordinate to the user's work context.
- Screenshots, examples, and tracked documentation use synthetic content unless a path is explicitly approved.
- Imported, inferred, accepted, rejected, unavailable, and user-confirmed information use distinguishable labels or structure; color alone is insufficient.

### Responsive Compatibility

- The supported viewport floor is 320px.
- Essential navigation and actions remain reachable at all supported widths.
- Dense tables, rails, and split panes simplify structurally before typography is reduced.
- No user-visible body text is smaller than the body-small role. Micro text is limited to nonessential metadata.

## 4. Design DNA

- **Tone keywords:** professional clarity, structured depth, calm hierarchy, neutral workspace, evidence-rich, quiet authority, precise recovery.
- **Visual principles:**
  - Use whitespace and typography before decoration.
  - Make state, source, and consequence legible at the point of action.
  - Keep one dominant action per action group, not one accent on every control.
  - Let neutral surfaces carry density; reserve strong color for action, status, and focus.
  - Preserve shell continuity while content changes.
  - Normalize repeated spacing and geometry instead of preserving incidental screen values.
- **Anti-principles:**
  - No commerce, loyalty, marketing, or promotional patterns.
  - No generic widget wall without a learning, Workstream or source-inspection purpose.
  - No decorative gradients on structural surfaces.
  - No state communicated by color alone.
  - No mixed radius or shadow language inside one component family.
  - No page-specific raw design values.
  - No animation-dependent meaning or attention-seeking motion.

## 5. Primitive Tokens

Primitive tokens are raw constants. They do not describe components or screen roles.

```css
:root {
  /* Neutral */
  --color-neutral-0: #ffffff;
  --color-neutral-100: #fcfcfd;
  --color-neutral-200: #f9f9fb;
  --color-neutral-300: #f7f7fa;
  --color-neutral-400: #f1f1f3;
  --color-neutral-450: #e8e9ed;
  --color-neutral-500: #dcdde2;
  --color-neutral-550: #c1c4cc;
  --color-neutral-600: #989ca5;
  --color-neutral-700: #7e8189;
  --color-neutral-750: #73767e;
  --color-neutral-800: #6d6f76;
  --color-neutral-900: #4e5054;
  --color-neutral-950: #37383c;
  --color-neutral-1000: #191919;

  /* Brand and feedback */
  --color-brand-100: #fff4f5;
  --color-brand-500: #fd4752;
  --color-brand-700: #da1e28;
  --color-blue-50: #fdfeff;
  --color-blue-100: #e9f0fb;
  --color-blue-600: #315ea8;
  --color-green-100: #e5f4ee;
  --color-green-600: #13795b;
  --color-amber-100: #fff3d6;
  --color-amber-600: #9a6700;
  --color-amber-700: #875a00;
  --color-red-100: #feeceb;
  --color-red-700: #b42318;
  --color-code-blue-500: #9bbcf4;
  --color-code-cyan-500: #8fd3df;
  --color-code-green-500: #9ed6bd;
  --color-code-amber-500: #f0c36e;
  --color-code-violet-500: #c8b6e8;

  /* Source provenance */
  --color-claude-100: #f9ece7;
  --color-claude-700: #a7492b;
  --color-codex-100: #e5f4ee;
  --color-codex-700: #2f6b57;

  /* Alpha */
  --color-black-5: rgb(25 25 26 / 5%);
  --color-black-10: rgb(25 25 26 / 10%);
  --color-black-35: rgb(25 25 26 / 35%);
  --color-white-96: rgb(255 255 255 / 96%);

  /* Type families */
  --font-display: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-body: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;

  /* Type sizes */
  --size-10: 0.625rem;
  --size-11: 0.6875rem;
  --size-12: 0.75rem;
  --size-13: 0.8125rem;
  --size-14: 0.875rem;
  --size-16: 1rem;
  --size-18: 1.125rem;
  --size-20: 1.25rem;
  --size-24: 1.5rem;
  --size-28: 1.75rem;
  --size-32: 2rem;

  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
  --line-tight: 1.2;
  --line-compact: 1.4;
  --line-body: 1.55;
  --line-reading: 1.65;

  /* Spacing */
  --space-0: 0;
  --space-2: 2px;
  --space-4: 4px;
  --space-8: 8px;
  --space-12: 12px;
  --space-14: 14px;
  --space-16: 16px;
  --space-20: 20px;
  --space-24: 24px;
  --space-32: 32px;
  --space-40: 40px;
  --space-48: 48px;
  --space-64: 64px;

  /* Shape and stroke */
  --radius-0: 0;
  --radius-2: 2px;
  --radius-4: 4px;
  --radius-8: 8px;
  --radius-12: 12px;
  --radius-16: 16px;
  --radius-20: 20px;
  --radius-full: 9999px;
  --stroke-0: 0;
  --stroke-1: 1px;
  --stroke-2: 2px;
  --stroke-3: 3px;

  /* Elevation */
  --shadow-rest: 0 1px 2px var(--color-black-5);
  --shadow-raised: 0 4px 12px var(--color-black-10);
  --shadow-overlay: 0 8px 24px var(--color-black-10);

  /* Motion and state */
  --duration-instant: 0ms;
  --duration-fast: 120ms;
  --duration-standard: 180ms;
  --duration-deliberate: 240ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --opacity-disabled: 0.38;
  --opacity-muted: 0.68;
}
```

## 6. Semantic Tokens

Components consume semantic roles only. Color, type, spacing, radius, elevation, and motion aliases reference primitive tokens. Role-specific shell dimensions live here because their meaning is inherently semantic.

```css
:root {
  /* Canvas and surfaces */
  --page-bg: var(--color-neutral-100);
  --surface-default: var(--color-neutral-0);
  --surface-conversation-input: var(--color-blue-50);
  --surface-subtle: var(--color-neutral-200);
  --surface-muted: var(--color-neutral-300);
  --surface-disabled: var(--color-neutral-400);
  --surface-navigation: var(--color-neutral-950);
  --surface-navigation-active: var(--color-neutral-900);
  --surface-code: var(--color-neutral-1000);
  --surface-code-reading: var(--color-neutral-950);
  --surface-code-reading-header: var(--color-neutral-900);
  --surface-overlay: var(--color-neutral-0);
  --surface-scrim: var(--color-black-35);

  /* Feedback surfaces */
  --surface-info: var(--color-blue-100);
  --surface-success: var(--color-green-100);
  --surface-warning: var(--color-amber-100);
  --surface-danger: var(--color-red-100);
  --surface-brand-soft: var(--color-brand-100);
  --surface-profile-green: var(--color-codex-100);
  --text-profile-green: var(--color-codex-700);
  --surface-profile-blue: var(--color-blue-100);
  --text-profile-blue: var(--color-blue-600);
  --surface-profile-orange: var(--color-claude-100);
  --text-profile-orange: var(--color-claude-700);
  --surface-profile-yellow: var(--color-amber-100);
  --text-profile-yellow: var(--color-amber-700);
  --surface-profile-red: var(--color-red-100);
  --text-profile-red: var(--color-red-700);
  --surface-profile-gray: var(--color-neutral-400);
  --text-profile-gray: var(--color-neutral-900);
  --surface-source-claude: var(--color-claude-100);
  --surface-source-codex: var(--color-codex-100);

  /* Text */
  --text-primary: var(--color-neutral-1000);
  --text-secondary: var(--color-neutral-800);
  --text-tertiary: var(--color-neutral-750);
  --text-disabled: var(--color-neutral-600);
  --text-inverse: var(--color-neutral-0);
  --text-navigation-muted: var(--color-neutral-550);
  --text-brand: var(--color-brand-700);
  --text-link: var(--color-blue-600);
  --text-info: var(--color-blue-600);
  --text-success: var(--color-green-600);
  --text-warning: var(--color-amber-700);
  --text-danger: var(--color-red-700);
  --text-source-claude: var(--color-claude-700);
  --text-source-codex: var(--color-codex-700);
  --text-code-reading: var(--color-neutral-100);
  --text-code-muted: var(--color-neutral-550);
  --text-code-keyword: var(--color-code-blue-500);
  --text-code-name: var(--color-code-cyan-500);
  --text-code-string: var(--color-code-green-500);
  --text-code-number: var(--color-code-amber-500);
  --text-code-attribute: var(--color-code-violet-500);

  /* Borders, dividers, and focus */
  --border-subtle: var(--color-neutral-450);
  --border-default: var(--color-neutral-700);
  --border-strong: var(--color-neutral-800);
  --border-navigation: var(--color-neutral-900);
  --border-code-reading: var(--color-neutral-800);
  --border-brand: var(--color-brand-500);
  --border-info: var(--color-blue-600);
  --border-success: var(--color-green-600);
  --border-warning: var(--color-amber-600);
  --border-danger: var(--color-red-700);
  --border-source-claude: var(--color-claude-700);
  --border-source-codex: var(--color-codex-700);
  --focus-ring: var(--color-blue-600);
  --focus-ring-soft: var(--color-blue-100);
  --divider-row: var(--color-neutral-450);

  /* Actions */
  --action-primary-bg: var(--color-brand-700);
  --action-primary-fg: var(--color-neutral-0);
  --action-primary-accent: var(--color-brand-500);
  --action-secondary-bg: var(--color-neutral-0);
  --action-secondary-fg: var(--color-neutral-1000);
  --action-secondary-border: var(--color-neutral-700);
  --action-ghost-fg: var(--color-neutral-800);
  --action-danger-bg: var(--color-red-700);
  --action-danger-fg: var(--color-neutral-0);
  --action-disabled-bg: var(--color-neutral-400);
  --action-disabled-fg: var(--color-neutral-600);

  /* Type roles */
  --type-display-font: var(--font-display);
  --type-body-font: var(--font-body);
  --type-mono-font: var(--font-mono);
  --type-page-size: var(--size-28);
  --type-section-size: var(--size-18);
  --type-title-size: var(--size-16);
  --type-body-size: var(--size-14);
  --type-prose-size: var(--size-16);
  --type-body-small-size: var(--size-13);
  --type-label-size: var(--size-12);
  --type-caption-size: var(--size-11);
  --type-micro-size: var(--size-10);
  --type-regular: var(--weight-regular);
  --type-medium: var(--weight-medium);
  --type-semibold: var(--weight-semibold);
  --type-bold: var(--weight-bold);
  --type-line-title: var(--line-tight);
  --type-line-ui: var(--line-compact);
  --type-line-body: var(--line-body);
  --type-line-reading: var(--line-reading);

  /* Spacing roles */
  --space-none: var(--space-0);
  --space-micro: var(--space-2);
  --space-compact: var(--space-4);
  --space-control-gap: var(--space-8);
  --space-control-block: var(--space-8);
  --space-control-inline: var(--space-16);
  --space-row-block: var(--space-12);
  --space-row-inline: var(--space-16);
  --space-card: var(--space-16);
  --space-panel: var(--space-20);
  --space-grid: var(--space-16);
  --space-column: var(--space-24);
  --space-section: var(--space-24);
  --space-page-inline: var(--space-32);
  --space-page-inline-narrow: var(--space-14);
  --space-page-start: var(--space-32);
  --space-page-start-narrow: var(--space-24);
  --space-page-end: var(--space-64);
  --space-empty-block: var(--space-48);
  --space-visually-hidden-offset: calc(var(--space-micro) * -0.5);

  /* Shape and depth roles */
  --radius-control: var(--radius-4);
  --radius-card: var(--radius-8);
  --radius-panel: var(--radius-8);
  --radius-dialog: var(--radius-16);
  --radius-sheet: var(--radius-20);
  --radius-pill: var(--radius-full);
  --border-width-none: var(--stroke-0);
  --border-width-control: var(--stroke-1);
  --border-width-focus: var(--stroke-2);
  --border-width-accent: var(--stroke-3);
  --elevation-card: var(--shadow-rest);
  --elevation-raised: var(--shadow-raised);
  --elevation-overlay: var(--shadow-overlay);
  --elevation-focus: 0 0 0 var(--border-width-accent) var(--focus-ring-soft);
  --elevation-outline: 0 0 0 var(--border-width-control) var(--border-default);
  --elevation-navigation-active: inset var(--border-width-accent) 0 0 var(--border-brand);
  --elevation-filter-active: inset var(--border-width-focus) 0 0 var(--border-brand), var(--elevation-card);
  --elevation-current-record: inset var(--border-width-focus) 0 var(--text-link);
  --elevation-conversation-input: inset var(--border-width-accent) 0 0 var(--border-info);
  --elevation-conversation-result: inset 0 0 0 var(--border-width-control) var(--border-default);
  --state-disabled-opacity: var(--opacity-disabled);
  --state-muted-opacity: var(--opacity-muted);

  /* Motion roles */
  --motion-state-duration: var(--duration-fast);
  --motion-standard-duration: var(--duration-standard);
  --motion-overlay-duration: var(--duration-deliberate);
  --motion-reduced-duration: var(--duration-instant);
  --motion-ease: var(--ease-standard);

  /* Shell and component geometry */
  --shell-sidebar-width: 220px;
  --shell-sidebar-width-compact: 188px;
  --shell-header-height: 58px;
  --shell-header-min-height-narrow: 54px;
  --shell-sticky-offset: 80px;
  --shell-content-max: 1440px;
  --content-reading-max: 1040px;
  --content-search-max: 980px;
  --rail-filter-width: 260px;
  --rail-context-width: 340px;
  --drawer-max-width: 400px;
  --control-min-height: 32px;
  --control-min-height-touch: 40px;
  --row-min-height: 48px;
  --breakpoint-compact: 920px;
  --breakpoint-narrow: 700px;
  --viewport-min-width: 320px;
}
```

Semantic status families are fixed:

| Family | Surface | Text and icon | Border |
|---|---|---|---|
| neutral | `--surface-muted` | `--text-secondary` | `--border-subtle` |
| info | `--surface-info` | `--text-info` | `--border-info` |
| brand | `--surface-brand-soft` | `--text-brand` | `--border-brand` |
| success | `--surface-success` | `--text-success` | `--border-success` |
| warning | `--surface-warning` | `--text-warning` | `--border-warning` |
| danger | `--surface-danger` | `--text-danger` | `--border-danger` |

Provenance separates provider identity from profile color. Session profile
identity is the existing numeric source ID; several configured Sources may share
one provider adapter. Provider letters are `CL` for Claude and `CX` for Codex.
The saved palette choice controls record-cue color through
`--surface-profile-{color}` and `--text-profile-{color}`, independently of provider
or a personal/company name. These rules apply across Session inventory, Pinned
cards, detail headings, Subsession/child projections, Charts and Sessions Dashboard.

Provider-only provenance roles apply to consumers without `data-profile-color`:

| Source | Surface | Text and icon | Border | Fallback |
|---|---|---|---|---|
| Claude | `--surface-source-claude` | `--text-source-claude` | `--border-source-claude` | `CL` plus accessible configured label |
| Codex | `--surface-source-codex` | `--text-source-codex` | `--border-source-codex` | `CX` plus accessible configured label |
| Other or unknown | `--surface-muted` | `--text-secondary` | `--border-subtle` | readable source-kind label |

Profile-aware Session record cues carry `data-profile-color`. A saved palette
choice takes precedence; the default palette is Claude orange, Codex green, and
unknown or missing profile gray. Their background and text use the profile roles
above, and their border uses the same profile ink. These record-cue rules do not
replace the provider-only roles for consumers without that attribute.

Provenance color identifies origin only. It never communicates health, success,
failure, selection, confidence, or action priority. When source identity and a
product state appear together, each keeps its own label and structural role.

Configured source names remain in accessible text, so color or initials never
carry account identity alone. Ordinary cards, Pinned cards, detail headings and
detail Subsession rows omit that name visually; source controls and composition
continue to expose configured readable labels where comparison requires them.
Detail Subsession rows preserve the inventory-family scan order of question
count, event count, then activity date after the title and source-native identifier.
The [profile cue controls](#user-managed-session-profile-cues) define palette
geometry, interaction and source-filter presentation.

## 7. Layout Rules

### App Shell

- Above 920px, the shell is a two-column grid with a 220px left navigation and a fluid workspace.
- From 701px through 920px, the navigation narrows to 188px and supporting columns move into the main flow when they would compress primary content.
- At 700px and below, the shell becomes a single block. Navigation becomes a horizontally scrollable top region and the workspace header remains sticky below it.
- The sidebar is sticky and viewport-height on desktop. The document owns page scrolling; the main workspace does not create a competing page-level scroll container.
- The workspace header is sticky, 58px on desktop, and at least 54px on narrow viewports.

### Navigation Model

The persistent navigation has three groups and ten stable destinations:

- **Overview:** Dashboard, Sessions Dashboard, Context Search
- **Workspace:** 자동 작업, Workstreams, Sessions, Atlassian, Local Contexts
- **System:** Sources, Schema

Active navigation uses text, surface, and an accent indicator. Narrow navigation preserves every destination, supports horizontal scrolling, and keeps the active item visible.

The shared footer places Docs immediately above Settings. Compact layouts keep
both utilities reachable while hiding nonessential footer status text. Product
Docs retain the app shell and a compact current-topic contents list beside the
reading area; at 920px and below the contents enter normal flow. English guide
prose uses the shared Markdown and reading-width/type roles, with local table
overflow rather than page-wide overflow. Docs do not create a separate visual
system or require setup/model installation for reading.

Sessions owns two mutually exclusive local inventory views: `Sessions` is the default and `Projects` is its Session-derived path grouping. Their selected indicator may move with the shared motion roles, but the visible label and matching programmatic current state remain authoritative under normal and reduced motion.

The Sessions inventory additionally owns a subordinate `List/Chart` display
switch. List keeps its row/recall hierarchy. Chart fills the main content width
without the Pinned Sessions rail; it preserves source/workspace scope and offers
an observation-only explorer under the same shell.

### Content Width And Rhythm

- The application canvas is capped by `--shell-content-max` and centered inside the workspace.
- Standard page padding uses the page spacing roles; narrow padding uses `--space-page-inline-narrow`.
- Long-form Session and Document content uses `--content-reading-max`.
- Search results use `--content-search-max`.
- Filter rails use `--rail-filter-width`; contextual action rails use `--rail-context-width`.
- Browse surfaces may be fluid. Reading surfaces must not stretch into an uncomfortable full-width line measure.

### Density

- Default rows use `--row-min-height`, `--space-row-block`, and `--space-row-inline`.
- Compact metadata may use caption or micro type, but interactive labels use label type or larger.
- Dense views hide secondary columns or move them below primary content before reducing type size.
- Repeated cards and rows keep metadata zones aligned despite variable title or summary length.

## 8. Product State To UI Mapping

Every persisted or user-visible derived state has one semantic family and a text label. New domain states require a mapping here before appearing in templates.

### Domain States

| Entity | State | Family | Structural treatment |
|---|---|---|---|
| Workstream | `active` | success | default emphasis |
| Workstream | `paused` | warning | muted secondary content |
| Workstream | `done` | neutral | muted; remains discoverable |
| Workstream | `archived` | neutral | excluded from default listing |
| Thread | `active` | success | default |
| Thread | `blocked` | danger | labeled accent and visible blocker |
| Thread | `paused` | warning | muted |
| Thread | `done` | neutral | muted |
| Suggestion | `pending` | brand | review actions visible |
| Suggestion | `accepted` | success | resolved treatment |
| Suggestion | `rejected` | neutral | resolved and restorable |
| Suggestion | `superseded` | neutral | inactive historical treatment |
| Run | `prepared` | neutral | configuration ready |
| Run | `queued` | info | waiting indicator |
| Run | `running` | brand | activity indicator plus text |
| Run | `cancelling` | warning | stop-in-progress label |
| Run | `cancelled` | neutral | terminal treatment |
| Run | `completed` | success | terminal treatment |
| Run | `failed` | danger | error and recovery context |
| Run | `interrupted` | warning | terminal interruption context |
| Local Context | `pending` | info | awaiting first scan |
| Local Context | `ready` | success | readable |
| Local Context | `unreadable` | danger | reason visible |
| Local Context | `error` | danger | error and recovery action |
| Local Context | `missing` | warning | missing path visible |
| Source file | `ok` | success | no warning treatment |
| Source file | `error` | danger | contributes to source error count |
| Local resource | available | success | normal link treatment |
| Local resource | missing | warning | historical path remains visible |
| Natural search | `disabled` | neutral | preparation action with local scope |
| Natural search | `model-missing` | warning | installation guidance; never an empty result |
| Natural search | `preparing` | info | aggregate progress and cancellation; preserve query/focus |
| Natural search | `partial` | warning | current evidence remains usable; refresh guidance |
| Natural search | `failed` | danger | bounded explanation and retry |
| Natural search | `ready` | success | ordinary search availability |
| Natural search | `no-data` | neutral | eligible source setup/Sync guidance |
| Natural search | no-match | neutral | query-specific empty result with applied conditions |
| External Source Instance capability | `current` | success | remote maintenance action may be offered |
| External Source Instance capability | `unknown` or `stale` | warning | identity remains visible; remote action unavailable pending inspection |
| External Source Instance capability | `disabled` or `unavailable` | neutral | local inventory remains visible; remote action unavailable |
| External Source Instance capability | `unauthorized` or `error` | danger | bounded reason and recovery context remain visible |
| Atlassian link/document freshness | `current` | success | last successful check remains visible |
| Atlassian link/document freshness | `due` or `stale` | warning | advisory label; never implies an automatic refresh |
| Atlassian link/document freshness | `unknown` | neutral | no successful check evidence |
| Atlassian link/document freshness | `unavailable` | danger | last-known local record remains visible |
| Atlassian local Sync outcome | `new` | success | newly registered local link/document count; source units remain separate |
| Atlassian local Sync outcome | `reused` | info | existing local link/document or evidence reused without remote confirmation |
| Atlassian local Sync outcome | `skipped` | neutral | bounded excluded-source or target reason remains inspectable |
| Atlassian local Sync outcome | `unavailable` | warning | prior evidence remains; source synchronization or retry guidance stays visible |
| Atlassian local Sync outcome | `failed` | danger | bounded local failure and same-action retry remain visible |
| Atlassian URL-derived structure reference | `available` | success | current local Session or Local Context evidence remains visible beside the stable URL-derived provenance cue |
| Atlassian URL-derived structure reference | `unavailable` | warning | retained reference remains visible while its current local evidence source cannot be read |
| Atlassian URL-derived structure reference | `archived` | neutral | direct history remains inspectable after all owning evidence has disappeared; default inventory and Search exclude it |

### Derived And Transient UI States

- Source inventory shows **healthy** when `error_count` is zero and **error** when it is nonzero. These are derived labels, not persisted source states.
- Checkpoint review-needed treatment uses warning and a text label; it is not a Checkpoint status value.
- Loading uses a bounded skeleton or progress region on `--surface-muted`.
- Scanning or working uses info treatment and explicit working text.
- Empty uses neutral treatment, a concise explanation, and at most one primary recovery action.
- Auto Work uses warning plus `품질 미평가` for inferred experimental groups;
  this is not a work lifecycle or confirmation state. Sample coverage, unassigned
  wording, expired/changed evidence and refresh failures remain separate labels.
- Full-history affinity uses neutral `current`/`empty`/`missing`, info `busy`,
  warning `stale`/`expired`/`selection-stale`/`unavailable`, and danger `invalid`
  treatment with explicit text. `current` means source-revalidated, not correct
  work organization. Similarity edges are undirected; group labels are source
  examples, never confirmed categories. Selection uses brand plus `선택됨` and
  `aria-current`, independently of source origin or inferred authority.
- Disabled controls retain their label and use disabled action tokens and opacity.
- Focus and selection remain visible independently of hover.
- Workflow Focus `selected` uses a brand boundary plus the visible `선택됨`
  label and `aria-pressed`; `related-path` uses emphasized directional edges,
  while unrelated retained context may use muted opacity without disappearing.
- Workflow Focus `unconnected` and `partial` use neutral and warning treatment
  with explicit explanatory text and retained/observed totals. Neither is a
  persisted lifecycle state, and `unconnected` never means completed.
- Workflow Focus `missing`, `ineligible`, and `unexpected-error` use bounded
  neutral, warning, and danger treatment respectively, always with a local
  Session or Sessions destination and no implied source refresh.
- Workflow Focus `user-confirmed` uses a persistent structural boundary and
  explicit authority text on the affected Episode or relation; color, glow, or
  transient success feedback never carries confirmation alone. A correction
  failure leaves the prior map visible and places recovery beside its owning
  form.

Running and working indicators may animate with motion tokens. Under `prefers-reduced-motion: reduce`, they become static labeled indicators and transitions resolve with `--duration-instant`.

## 9. Core Components

### Buttons And Links

- **Primary:** `--action-primary-bg`, `--action-primary-fg`, `--radius-control`, control spacing roles, and `--control-min-height`. One primary action is allowed per action group.
- **Secondary:** `--action-secondary-bg`, `--action-secondary-fg`, and `--action-secondary-border`.
- **Ghost/text:** transparent surface with `--action-ghost-fg`; used for low-risk utilities and secondary navigation.
- **Danger:** `--action-danger-bg` and `--action-danger-fg`; used only when the action is destructive or removes persisted organization.
- **Disabled:** disabled action tokens; disabled state is never represented by opacity alone.
- All variants use the shared focus ring. Link text uses `--text-link` and remains distinguishable without color alone when embedded in body copy.

### Inputs And Forms

- Inputs use `--surface-default`, `--text-primary`, `--border-default`, `--radius-control`, and control spacing roles.
- Focus uses `--focus-ring` and `--focus-ring-soft`; error uses danger text and border tokens.
- Labels remain visible when fields contain values. Placeholder text does not replace a label.
- Form groups align labels, controls, helper text, and errors. Two-column forms become one column at the narrow breakpoint.
- Monospace is limited to paths, identifiers, code, and machine-oriented values.
- General-settings dropdowns share the same compact width, below-trigger menu, disclosure cue and selected checkmark. `--settings-select-width` caps the control at six touch-control height units (240px at the default scale); the control and matching menu shrink to the available pane width. Helper text keeps the wider form reading measure. The source-tool and Context-kind selectors share this below-trigger menu. Settings fields and action buttons use the desktop 32px control role, 40px at the narrow breakpoint, and centered action labels. The dedicated Sync pane groups Session and Local Context schedules, each with a single dropdown for 10/20/30/60 minutes, then Off. Sync sizes the same control family to the label, disclosure and selected marker (about 79px at the default scale), expanding for longer saved values; its menu matches that width. Off preserves the saved interval; choosing minutes enables that schedule. Omit the range/runtime help sentence.

### Cards And Panels

- Cards use `--surface-default`, `--border-subtle`, `--radius-card`, `--space-card`, and `--elevation-card`.
- Panels use `--surface-default`, `--radius-panel`, and `--space-panel`; they may omit elevation when the border or surrounding surface already establishes containment.
- Hover may move from resting to raised elevation without layout shift.
- Selected cards use brand border treatment plus an explicit selected label or control state.

### Lists, Tables, And Grids

- Lists use row spacing roles and `--divider-row`; the final row does not duplicate the next surface boundary.
- Session profile and Local Context settings use separate, compact rows without an enclosing rounded
  frame or shared dividers. Each row uses the white/default surface, subtle border
  and resting card elevation. Keep the whole row untinted in hover, focus and drag;
  control-level focus rings, row gaps, a visible
  drag handle and a clear insertion line expose independent movement. While dragging,
  the whole row follows the pointer over a reserved slot and neighboring rows
  transition into position using the shared motion roles. Scroll the pane near its
  edges; cancellation restores the original order. Keyboard movement uses the same
  visual continuity. Reduced-motion preference removes decorative transitions.
  Keep separate Edit and
  Unregister actions per registered profile and a separate Add action. Row buttons
  use compact label type and control-gap inline padding, retaining shared minimum
  control heights; narrow rows place actions below the identity. Keep names and collection paths primary;
  show errors and disabled registration state without repeating healthy machine
  status. Add/Edit replaces the list with the shared form inside the same pane.
  Make agent home the primary path and show its derived record location. Keep
  custom session folders in a disclosure, open when an override exists; retain
  same-source confirmation beside a changed collection path. Use Tool, Profile name,
  Home, Custom session folder and Session folder labels. Red textual required markers
  match actual input requirements. The name placeholder follows the selected tool,
  without replacing entered names. Unregister uses a compact named confirmation
  dialog with Cancel initially focused, explicit consequences and row-focus return.
  Keep the underlying settings dialog inert while that confirmation is open.
  Field labels, focus, validation and save/skip authority remain intact in first-use setup.
- Local Context settings reuse the row identity/path/action family. Omit routine
  document counts and healthy status; keep pending, unreadable, missing and failed
  states visible. Add opens a separate in-pane editor with Cancel; leaving or
  reclicking the category clears the draft, while wizard Back retains it. The optional
  Notes action appears in the editor only when Notes is not registered. Context
  unregister uses the same named in-app confirmation family from settings and the
  explorer, preserving Cancel-first focus, busy/error behavior and focus return.
- Dense tables use stable column zones, a subtle header surface, and row labels that remain available when secondary columns hide.
- At the narrow breakpoint, a table either keeps the minimum meaningful columns or converts each row into a labeled card. Horizontal scrolling is reserved for data whose column comparison is essential.
- Variable titles and summaries truncate only inside an explicit bounded zone. Full values remain available through the destination, disclosure, or accessible label.
- Repeated cards align footer metadata independently of variable body length.

### Navigation, Tabs, Chips, And Status Badges

- Navigation items share one geometry and active-state treatment within their region.
- Tabs represent mutually exclusive views; filters or tags use chips. A visual chip must not imply filtering unless it is interactive.
- Status badges use only the six semantic status families from Section 6 and always include readable text.
- Pills are limited to counts, compact filters, and status tokens; ordinary buttons and fields use `--radius-control`.

### User-managed Session profile cues

Session record cues follow the [provider/profile semantics](#6-semantic-tokens)
above. Settings use a compact diagonal
tag trigger and a vertical menu of horizontal tags with the point and hole on the
left. Match the menu frame to the trigger background's left and right edges, and
match the horizontal/diagonal painted glyph widths and both edges. Choices retain
accessible color names and radio selection without color-name hover tooltips;
a profile-colored outline and quiet fill indicate the selected color without a
check column. Keyboard focus remains distinct from selection, including arrow-key
navigation after a pointer open. Decorative tag glyphs pass pointer hits through
to the owning button so WebKit does not infer keyboard focus from an SVG hit.
The frame uses the
trigger's control width (32px by default, 40px in the narrow layout); choices fill
the space inside its border. Keep content-sized height and no inter-choice gap or
padding. Fine-pointer choices are 24px high (control height minus control gap);
coarse-pointer choices retain 40px height. This compact palette exception does not
resize other controls. Short-window scrolling has no width-consuming scrollbar
gutter; all choices remain reachable by scrolling and keyboard focus.
Source filter toggles use saved names without color dots or badges; names distinguish
same-provider profiles. TOML array order governs profile filters with All first.
Color choices use the profile roles above. The compact palette opens directly below
its tag trigger, above surrounding content; viewport space bounds its own scrolling.
Outside interaction, Escape, category change and movement of the anchor close it.
Up/Down and Home/End move through choices; Escape returns focus to the trigger.
Selection closes the palette and preserves existing saved-color/readback behavior;
reordering supports both a drag handle and keyboard, returns focus to that handle
and preserves the active numeric filter.

### Search And Filters

- Global search remains available from the shared header.
- Atlassian is the bounded exception that replaces the shared-header query
  with one surface-local query while its route is active. The shared header
  keeps its normal height, navigation alignment, and surrounding geometry so
  entering or leaving Atlassian does not read as a shell replacement. No
  Atlassian state may expose both query owners at once.
- Page search and filters preserve the user's query and selection when navigating between list and detail views whenever the route supports it.
- A zero-result state distinguishes “no data exists” from “no data matches these filters.”
- Filter rails become in-flow controls before they reduce the primary content column below a readable width.

### Dialogs And Drawers

- Dialogs use `--surface-overlay`, `--surface-scrim`, `--radius-dialog`, and `--elevation-overlay`.
- Drawers use `--radius-sheet` on exposed corners and `--drawer-max-width`.
- Overlays trap focus, expose an accessible name, close through an explicit action, and restore focus to the trigger.
- Destructive confirmation states state the affected object and consequence.
- Settings use a compact centered dialog: `--settings-width` and `--settings-height`
  cap it at 18 by 14 touch-control height units (720 by 560px at the default scale),
  shrinking within the viewport. The desktop category rail uses four such units
  (160px). The header and close action stay visible while the content pane owns
  vertical scrolling. At the shared 700px narrow breakpoint, categories become a
  horizontal scrollable row. Changing categories starts the new pane at its top;
  controls and text size retain the shared geometry. Leaving or reclicking the Session-source category discards its unsaved editor and returns to its list; wizard Back retains its draft.
  Save/error feedback is brought into view in the scrolling pane.
- The About category uses a quiet identity row: existing LocalBrain mark, product
  name and application version. Keep the shared settings shell and type roles;
  omit operational paragraphs and reference-only licensing/build claims.
- First-use setup extends the same compact settings dialog above the real main
  surface. Keep a quiet header, a single content stage and a stable footer with
  Previous/Next/Skip above four small progress dots. Current progress uses shape
  and tone plus `aria-current` and accessible step names; dots are indicators,
  not shortcuts past form saves. Use existing control, type, spacing and surface
  tokens. Crossfade the content with a small directional offset using shared
  motion roles, isolate both panels during the handoff and focus the new heading
  afterward. Reduced motion swaps immediately. The main surface is inert before
  initialization. Optional skip and Set up later remain visible; failed writes
  retain the current step. At the shared narrow breakpoint, forms become one
  column and the footer can wrap without horizontal overflow.

### Empty, Loading, Error, And Working States

- Empty states explain what is absent and provide one relevant recovery path.
- Loading and working states remain inside the owning panel, list, or console; the persistent shell stays stable.
- Errors preserve the user's entered data and show a retry or correction path when recovery is possible.
- Skeletons match the approximate final content shape and do not pulse under reduced motion.

### Technical Content And Run Console

- Paths, identifiers, source excerpts, and Run output use mono type roles.
- The Run console uses `--surface-code`, `--text-inverse`, reading line height, and an independently scrollable output region inside the page.
- Markdown reading code uses the separate `--surface-code-reading`, `--surface-code-reading-header`, and `--text-code-*` roles. Its calmer syntax palette supports sustained reading and does not repurpose brand, status, provenance, or Run-console semantics.
- Learning-article code reuses those reading roles, with a language caption, line numbers, literal excerpt range and local horizontal overflow. Diff +/− markers carry change meaning independently of syntax color. Articles use the existing reading-width bound, `--type-prose-size` for sustained prose and native section typography. Numbered sections and connected paragraphs form the main reading flow; a quiet contents/reference rail sits alongside on desktop and references follow the article at the shared compact breakpoint. Heading levels follow the containing page.
- Console status, cancellation, errors, and completion remain outside or above the output stream so they do not disappear in long logs.
- Raw local paths wrap or truncate safely and never force the page wider than its container.

## 10. Core UI Patterns

### Persistent Shell

- Navigation and header remain visually stable across route changes; only the
  active location and contextual actions change.

### Workstream Hierarchy

- Workstream identity and status lead; Threads, checkpoint state, linked
  resources, Suggestions, and Runs follow in that order of responsibility.

### Browse And Inventory

- Headings, filters, counts, rows or cards, and bounded empty states form one
  scan path.
- Pinned Sessions uses one compact workspace heading per group, places
  Git-backed Project groups before non-Git path groups, alphabetizes within
  those sections by the displayed home-abbreviated path (fallback: workspace
  label), and keeps Session activity ordering inside each group. The
  heading owns repeated Project/path context; each row retains source, title,
  optional Session branch, and activity date without an empty branch
  placeholder. Group boundaries and row boundaries have single ownership
  rather than forming a double divider.
- A desktop Pinned Session list keeps its normal left card inset while its
  grouped rows and boundaries own a `--space-section` right inset independent
  of the scrollbar lane; narrow in-flow presentation drops the extra inset with
  the nested scroller.

Sessions Chart follows the [Sessions Chart Design](surfaces/sessions-chart.md) companion for its complete layout, geometry, controls, interaction and fallback rules. [Sessions](../project/sessions.md) owns source, API and preference contracts.

### Detail And Read

Session and Subsession metadata, copy feedback and conversation role/completion appearance follow [Session Reading Design](surfaces/session-reading.md).

- The Search family uses one shared-header query with the existing global
  placeholder and no visible mode labels. A visually hidden label preserves
  accessibility. Enter and the adjacent Search action submit the same query to
  the shared `/natural-search` route. Keyword search is the default; AI search
  is an explicit mode under the [search contract](../project/natural-language-search.md#product-surface).
  The header adds no mode controls. The input and action remain reachable at
  narrow widths. Existing Atlassian header scope is preserved.
- AI-search results represent original Sessions or Local Context documents,
  with source cues and up to three linked evidence excerpts. Preparation, coverage
  and recovery stay next to the search form. Status updates preserve query,
  focus and results. Evidence readers show original-text provenance and a query
  return link; scores never appear as answer probabilities. Molecules do not
  create a user-visible document taxonomy.

- Title and source metadata precede the body; evidence and actions stay
  adjacent without shrinking the reading column.
- A primary Session's `관련 자료` rail presents only directly observed
  references. Its title has no duplicate aggregate count; the direct group
  retains its total and initially shows up to 100 retained rows. Material kinds
  have one alphabetically ordered heading each, with references ordered by
  oldest occurrence within each kind. The rail and Session header contain no
  Workstream/Thread membership strip, indirect organization material or
  organization badge. Existing organization links remain owned by their feature.
- The rail uses a descending heading scale from rail title to relationship
  group to material kind and ends each material-kind section with a stronger
  boundary while individual items rely on spacing instead of row rules.
- On desktop, its material content owns a `--space-section` right inset
  independent of the scrollbar lane while the normal left inset remains
  `--space-card`; compact in-flow presentation drops the extra right inset with
  the nested scroller. Retained overflow uses one reversible disclosure whose
  collapse control follows the expanded rows in DOM, visual, and keyboard-focus
  order. On desktop, the rail stays viewport-bounded and its material body
  scrolls independently while the document continues to own the primary
  reading scroll.

### Explorer

- Auto Work's full-history affinity view is a temporal flow canvas beside
  original evidence: actual message time runs left-to-right on one shared scale,
  while similarity groups form curved, inspectable strands. Each knot aggregates
  one strand's source occurrences in a period. Its capped size encodes occurrence
  volume, not distinct Sessions, cohesion, confidence or importance. Knots encode
  observed activity, not planned duration; empty intervals use interrupted/dashed traces.
  Unknown time stays explicitly unplaced. Vertical proximity and cross-strand
  curves are affinity only, never causal branch/merge arrows or confirmed identity.
  Group → subgroup → Session is observational scope, not a persisted work hierarchy.
  Selection preserves geometry; expansion and neighborhood zoom are explicit.
  Pan/zoom/fit/reset, a period evidence lens, and keyboard paths accompany complete
  paginated text navigation. The canvas is continuous: list pages never partition its matching strands or
  connections, nor reset its camera. Native bounded scrolling and visible time
  navigation reveal offscreen time and rows without shrinking labels.
  Motion confirms camera/focus changes and respects
  reduced motion; there is no perpetual jitter. Ordinary page scroll is not
  captured by zoom. The sampled comparator remains separately labeled.
- Hierarchy, inventory, and preview preserve selection context; panes collapse
  into sequential regions on narrow screens.
- Local Contexts use source/directory/document containment.
- Atlassian keeps `All`, `Jira`, and `Wiki` as reversible top scopes, then
  begins the hierarchy at `모든 도메인` followed by normalized Site domain
  without repeating Service as a parent. Each Site uses only persisted
  Project/Space children, deterministic canonical-URL container hints, and one
  honest `소속 미확인` child.
- Persisted containment and read-only URL hints remain visibly distinguishable
  when labels collide; Jira and Wiki remain distinguishable in `All` through a
  compact non-color-only cue. A URL hint never visually claims a confirmed or
  persisted Space, and the hierarchy does not imply a nested Confluence Page or
  Jira issue tree. `Wiki` remains a presentation label for stored Confluence
  identity.
- Wide layouts keep hierarchy, one mixed list of links/documents and
  URL-derived structure references, and the selected entity's read-first detail
  adjacent with intentional scroll ownership. Compact layouts keep the list
  primary and move hierarchy/detail into bounded disclosures. Narrow layouts
  are list-first with explicit sheets or sequential destinations.
- Unsupported pane state normalizes at breakpoint changes without hiding the
  selected link/document or structure reference, losing the mutually exclusive
  selection, or losing the matching full-detail destination.
- Structure-reference detail remains read-only and keeps its URL-derived
  provenance and availability/lifecycle state separate from Item editing,
  Refresh, and Connections authority.

### Atlassian Action Separation

- Local evidence Sync, one-URL manual Add, optional Connections and connected
  discovery, and remote Refresh are four distinct actions. Their labels,
  prerequisites, progress, completion, and recovery must not imply the same I/O
  or consequence. Local Browse, search, detail, Add, and Sync never require
  remote readiness.

### Atlassian Ordinary Terminology

- Jira-only context uses `링크`, Wiki-only context uses `문서`, and mixed
  context uses `링크/문서` across Explorer, Add, preview, full detail, Sync,
  Connections, Refresh, shared Search, and live announcements. `Item` remains
  an internal schema/API/diagnostic term and may remain in historical artifacts,
  but it is not ordinary task copy.

### Execution

- Configuration, queued/running state, output, artifacts, and terminal result
  remain distinguishable throughout the Run lifecycle.

### Workflow Focus

- Episode cards form a stable time-directed spine and fixed branch lanes;
  evidence remains grouped inside the selected Episode's adjacent Trace.
  Selection may illuminate ancestry and descendants but does not move nodes.
  Wide direction is left-to-right, compact direction is top-to-bottom, and
  narrow/no-script/render-failure presentation uses the complete textual
  lineage.
- Canvas controls follow the technical-content zoom/reset/fit and
  scroll-ownership contract. Consequential corrections live in contextual
  Trace disclosures, show exact before/after and supersession before one
  explicit submit, and become sequential ordinary forms at narrow widths; they
  do not use a modal, canvas gesture, or hidden optimistic mutation.

### Provenance Cues

- Imported source, inferred relation, user confirmation, and unavailable
  evidence use stable labels and placement across screen families.

## 11. Mobile Evolution Rules

- At the compact breakpoint, secondary rails enter document flow, multi-column dashboards become one column or two balanced columns, and sticky contextual rails become static without retaining a nested desktop scroller.
- At the narrow breakpoint, navigation becomes horizontal, grids and forms become one column, nonessential table columns hide, and split panes become sequential regions.
- Narrow layouts use `--control-min-height-touch`; desktop layouts use `--control-min-height`.
- Type roles, status vocabulary, action hierarchy, provenance cues, and radius families remain unchanged across widths.
- Text does not shrink to preserve desktop geometry. Content order and optional metadata simplify first.
- No desktop-only hover interaction may be the sole route to an essential action or full value.

## 12. Accessibility And Interaction Rules

- Text and essential icons meet WCAG AA contrast against their owning surface.
- Keyboard focus is always visible and follows the same order as the visual reading path.
- Status, selection, validation, and availability never depend on color alone.
- Touch-oriented controls use the narrow minimum control height and retain adequate separation.
- `prefers-reduced-motion` removes nonessential translation, pulsing, and animated skeletons.
- Shell, header, and content transitions do not flash a blank or intermediate implementation state during ordinary navigation.
- Korean, English, long identifiers, and mixed-script content remain contained without clipping.

## 13. Implementation Rules

- Primitive values are defined once in a shared token layer and are not referenced by component selectors.
- Semantic tokens consume primitive values; shell geometry is declared only in the semantic layer.
- Components consume semantic tokens only. If a role is missing, add a reusable semantic alias before implementing the component.
- Templates contain structure, state classes, and content; they do not contain design values or page-local inline styling.
- Breakpoint behavior follows Section 7 and Section 11. A page does not introduce a private breakpoint without a constitution update.
- New domain states are added to Section 8 before they are rendered.
- Current code and schema remain implementation truth for behavior. A durable visual rule changes here before implementation adopts a different contract.

## 14. AI Guardrails

AI may:

- extend an existing screen family using the locked token and component vocabulary
- add semantic aliases when a reusable role is genuinely missing
- adapt layouts for real content length, state, and provenance constraints
- use Design Evaluation as a reusable review layer

AI may not:

- treat the Figma source, `DESIGN.md`, or one existing screen as the complete system
- introduce commerce patterns, speculative controls, unsupported state values, or external write behavior
- invent raw colors, spacing, radii, shadows, motion, or private breakpoints in a component
- replace LocalBrain's navigation or Workstream hierarchy with a generic dashboard pattern
- hide provenance, errors, or unavailable evidence to make a screen look cleaner

Any durable change to visual DNA, primitive families, semantic roles, shell geometry, state mapping, component families, accessibility rules, or screen families requires a constitution update and [governance version entry](../../plans/design/design-system-change-history.md#design-system-version-history).

## 15. Durable Screen Families

| Family | Current surfaces | Durable constraints |
|---|---|---|
| Overview and dashboard | Dashboard, Sessions Dashboard | Dashboard shows one daily work-based article: context, preserved code, numbered explanatory sections, takeaway, then a collapsed optional question. A desktop contents/reference rail supports reading; compact screens place references below. Explicit reading and assisted-practice actions retain their separate meanings; selection guidance and complete evidence belong to library/reader; metrics are not decorative |
| Browse and inventory | 자동 작업, Workstreams, Sessions, Projects, Sources, Search | supports filtering, long labels, empty results, source identity, and stable row/card metadata; Auto Work keeps inferred groups separate from user-defined Workstreams and uses source-backed adjacent or sequential detail |
| Detail and read | Lesson, Session, Subsession, Document, local Resource | prioritizes readable body width, source metadata, deep links and long technical content; lesson response precedes feedback, with explicit explanation-first access and self-assessment; code/command lessons keep essential conditions and numbered source visible beside reasoning, stack at the shared compact breakpoint, contain long lines locally, and use document flow for tall content; unsaved draft and saved response states stay distinct |
| Workstream workspace | Workstream detail | preserves Workstream → Thread → evidence hierarchy and separates confirmed organization from Suggestions |
| Explorer | Auto Work full-history affinity, Atlassian, Local Contexts, Schema, Session Workflow Focus | preserves source, subject, or Episode selection; hierarchy/tree/table/time orientation; progressive preview or Trace; unreadable, missing, honestly unassigned, unconnected, partial, and diagram-unavailable states; affinity remains undirected observation rather than persisted work identity, Workflow Focus keeps artifacts subordinate to Episodes on fixed lanes, and Atlassian keeps top service scopes outside its domain-first hierarchy |
| Run and console | maintenance Run | represents the complete Run lifecycle, cancellation, output, artifacts, and terminal result |

New routes fit one of these families or justify a constitution change. A new feature does not create a new visual family merely because its data is new.

## 16. System Evolution Rules

- Add a primitive only when the current primitive families cannot express a durable need.
- Add a semantic alias when at least two components share a role or one fundamental screen family requires the role consistently.
- Add a component variant only when purpose or state changes; one-off polish is not a variant.
- Keep brand, information, success, warning, and danger meanings distinct even when they share visual ancestry.
