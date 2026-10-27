# Design Brief: Calm Professional Workspace

## Role

This file owns creative intent for LocalBrain. It explains the visual north star, source interpretation, and the reasons behind the design direction.

Durable tokens, component contracts, layout rules, state mappings, and implementation guardrails live in [Design Constitution](./docs/policies/design/design-constitution.md). Document ownership and promotion rules live in [Design Document Governance](./docs/policies/design/design-document-governance.md).

## Source Set And Interpretation

### Shared Visual Foundation

The starting point is a screen-plus-context source set:

- **Qoo10 Design System (AI)** supplies upstream palette, typography, spacing, shape, and component cues. It was reviewed through authenticated Figma access during the initial design pass on 2026-07-15. External file identifiers are intentionally not retained here.
- **LocalBrain's product policies, routes, templates, and current screens** supply product hierarchy, navigation, data density, state vocabulary, privacy needs, and responsive constraints.
- **This brief** records the creative interpretation. The constitution records the reconciled rules that survive beyond either source.

The upstream design system is a strong visual guide, not a complete LocalBrain specification. Commerce-specific concepts, unsupported states, and source-specific component assumptions do not transfer automatically. LocalBrain adds the feedback, accessibility, provenance, console, long-path, and dense-workflow rules needed by the product.

### First-Use Setup

The first-use setup adapts the owner's [Tesla homepage](https://www.tesla.com/)
reference (2026-10-23) for quiet centered hierarchy, stable navigation, bottom page
dots and a coherent crossfade. LocalBrain keeps its compact settings-dialog
geometry, neutral surfaces, warm actions, SF-oriented type and shared motion
tokens. The four actual steps determine the dot count; source registration and
explicit model-install authority determine navigation. No promotional imagery,
auto-advance or foreign theme is imported.

### Profile Settings And About

Session profile settings draw on the owner's [iPhone Duo reference](https://www.apple.com/iphone-duo/)
(2026-10-23): concise headings, deliberate whitespace, grouped surfaces and detail
revealed when requested. A compact overview leads to an editor within the same
pane. Agent home is primary; only a custom Session-folder override is placed in a
disclosure. Collection paths, errors and explicit registration authority remain
visible at their relevant decision points. LocalBrain keeps its control geometry
and restrained palette; Apple product imagery, promotional scale and pill-shaped
controls do not transfer.

The owner's [Notion reference](https://www.notion.com/ko), selected for
profile settings on 2026-10-25, contributes light, independently movable rows.
LocalBrain keeps its own shell, tokens and supported actions. Color-only tag
controls evoke familiar label palettes; source toggles stay textual while record
cues retain provider letters and colors.

The owner-supplied desktop About-dialog reference (2026-10-24) contributes only
its icon/name/version hierarchy and whitespace. LocalBrain uses its existing LB
mark and settings family; reference branding, license text and screenshots are
not product assets. The About pane keeps only identity and the actual version.

### Sessions Chart Exploration

The **Chochita Archive / Andromeda collection** (owner-selected, 2026-10-06)
contributes spatial point/card exploration, selection focus and camera interaction.
The owner's **Obsidian Graph view** reference contributes the feeling of tension
when pulling a point. Both are interaction references within LocalBrain's existing
creative direction: the shell, typography, palette and source cues remain native.
No star background, decorative links, note relationships, persistent free layout,
Obsidian styling or inferred work grouping is imported.

Recorded time supplies horizontal structure. Recorded-folder Project bands and
Git-like branch guides replace an irregular field: stored branch names and first
Session observations own the structure, while exact `HEAD` remains original
metadata rather than a named branch. Folders with only HEAD/missing values use one
line without an empty baseline; mixed named-branch folders keep those values on
one unassigned track. No actual Git ancestry or work inference is imported.
Tension is small, transient, bounded and local to one track around fixed homes and
recorded time anchors, with spring return.

Compact tracks and a whole-diagram overview use native checkbox Project
visibility. Footer annotations are omitted. The camera offers light resistance
near recorded date ends; overview keeps Project and branch names scaled with
their rows, suppresses crowded Session titles and returns to reading scale on
selection. These controls explore retained observations; they create no new
relationships or work classification.

Project filtering occupies the toolbar's date-navigation position. Directional
and date controls are omitted while drag, keys, zoom, fit and focus remain.
Confirmed Project choices persist across browser close in LocalBrain's private DB
and are shared across browsers; camera state remains local to the tab. The canvas
uses balanced end insets around centered source targets, visible-project endpoint
anchoring and more resisted travel before spring return, retaining compact branch
geometry. Only a genuine preference failure introduces contextual recovery copy.
Existing pinned Sessions use a static halo in the native pin color and the
established pin shape, without recoloring source cues or adding pulse. Two-segment
List/Chart omits a divider; the source header uses Dashboard separators and `All`.

Independent time zoom compresses history without shrinking Project and branch
spacing. The modifier gesture keeps the pointer's time and vertical orientation
stable; whole-chart controls retain overview behavior.

Temporary descriptions support inspecting a point before selection. A stronger
native information surface and border make hover apparent while source and pin
cues keep their meanings. Clicking holds a description; repeating the click or
choosing empty canvas releases it. A separate temporary card leaves an already
held description in place, including on narrow screens. The node and description
share a continuous hover passage so moving into the card is stable. Reading stays
temporary and local; leaving its pointer/focus ownership closes it after a short
grace. These point/card interactions introduce no new visual language.

## Creative North Star

**The Trusted Tool**

LocalBrain should feel like a well-made professional instrument that is already at hand when work resumes. It earns trust through density without chaos, hierarchy without decoration, and consistency without rigidity.

The closest physical analogy is a quality notebook beside a disciplined workbench: structured, quiet, evidence-rich, and ready to use.

## Tone And Feel

The interface should feel:

- professionally clear
- calm under information load
- structured without feeling bureaucratic
- neutral enough for source material to remain the subject
- precise about state, provenance, and consequence
- familiar to a desktop user returning after an interruption

The interface should never feel:

- playful, promotional, or commerce-led
- like a generic widget dashboard assembled from unrelated cards
- visually louder than the work context it contains
- dependent on animation to explain state
- vague about whether information is imported, inferred, confirmed, unavailable, or stale

## Color Direction

The canvas is a fine-grained cool neutral field with white content surfaces and restrained structural borders. A dark inverse surface is reserved for persistent navigation and focused technical contexts such as a live console; it is not a general content background.

A warm red-orange is the brand accent. It marks the strongest action or selection within an action group, not every interactive element. Destructive actions use a darker, separately named danger red so urgency is not confused with ordinary brand emphasis.

Feedback color has conventional meaning:

- green communicates healthy, available, accepted, or completed
- amber communicates paused, pending, interrupted, or attention required
- red communicates blocked, failed, unreadable, or destructive
- blue communicates links, informational focus, and queued or navigational context

Color never carries state alone. Every status also has a text label, icon, shape, or structural treatment.

## Typography Direction

LocalBrain uses the macOS system family without external font delivery:

- **SF Pro Display** direction for page and major section headings
- **SF Pro Text** direction for body, labels, controls, and dense rows
- **SFMono-compatible system monospace** for paths, identifiers, source excerpts, and Run output

The hierarchy is compact but not miniature. Micro text is reserved for nonessential metadata; actions, state labels, and body content remain readable without relying on hover or zoom.

## Composition And Density

The desktop shell is sidebar-primary. Navigation provides a stable orientation boundary while the workspace carries denser browse, detail, explorer, and execution surfaces.

Whitespace and typography establish grouping before cards or dividers. Borders are appropriate where they clarify dense rows, forms, panes, or containment, but they should not turn every region into a box. A page may contain several actions, yet each action group has only one clear primary action.

Long paths, titles, evidence excerpts, and generated summaries are normal content. Layouts must tolerate them through wrapping, truncation with disclosure, and stable metadata zones rather than by shrinking type.

## Shape, Surface, And Depth

Controls use modest corners, content containers use a slightly larger radius, and dialogs or sheets use the largest radius. Pills are reserved for compact counts, statuses, and filters.

Structural surfaces remain flat. Cards may use a quiet resting shadow, while overlays receive clearer elevation. Hover elevation is subtle and never shifts surrounding layout.

## Motion And Interaction

Motion confirms continuity; it does not decorate. Hover, focus, disclosure, and status transitions are short and restrained. Running or scanning states may use a small activity cue, but the label must remain understandable when motion is disabled.

Reduced-motion preferences remove nonessential translation and pulsing. Loading states stay inside the region that owns the work instead of replacing the whole shell.

## What This Is Not

- Not a mobile-first product; narrow layouts preserve access and readability without pretending to be the primary mode.
- Not a marketing surface; no hero treatment, promotional gradient, or decorative feature block belongs in the application shell.
- Not a commerce UI; upstream loyalty, shopping, and sub-brand patterns are outside the LocalBrain vocabulary.
- Not a speculative AI interface; suggestions and generated summaries remain reviewable evidence, not autonomous truth.
- Not a page-by-page visual experiment; new screens extend the constitution before introducing a new visual language.
