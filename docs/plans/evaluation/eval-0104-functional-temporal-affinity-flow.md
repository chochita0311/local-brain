# EVAL-0104 Functional: Temporal Affinity Flow

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Feature: [FEAT-0104](../feature/feat-0104-temporal-affinity-flow.md)
- Spec: [SPEC-0104](../spec/spec-0104-temporal-affinity-flow.md)
- Run: [RUN-117](../run/run-20260924-117-continuous-affinity-canvas.md), attempt `1`
- Profile: `fullstack-product`; lanes: `backend`, `frontend`

## Current Continuous-Canvas Result

970 application tests ran: 967 passed and three unchanged optional semantic
runtime tests skipped. The simulation/model implementation is unchanged.
25 reader tests include the new three-page, scope and mixed-version fallback
checks. Full browser QA passes with 160 synthetic Sessions and 65 groups.

At exact 1440/920/700/320 all matching strands remain loaded and reachable.
Native horizontal wheel pans time without zoom; native vertical wheel moves
rows while the SVG viewport stays fixed. Earlier/later controls, whole-time fit,
reset, modifier zoom, pointer drag, keyboard reveal and bounds pass. Pages two
and three preserve geometry, connections, camera and list disclosure; browser
Back restores them. Existing period→source→return, three scales, rapid selection,
resize, long-title search, reduced motion, no-script and forced render failure
also pass with zero mutation requests and zero runtime exceptions.

Additional rendered probes cover 1,200 synthetic Sessions/257 groups (last row
and latest time reachable) and all-unknown dates (no invented ticks/knots,
unknown links and exact evidence retained). The actual loopback runtime checks
return only booleans: current report, full scope, page-three-invariant geometry
and edges, real cross-page affinity, native scrolling and no outer overflow.
Runtime restart is the asset/Python refresh boundary; no lifespan startup work.

Fixes: native scrollbars do not initiate custom pointer drag; whole-time fit
preserves row context. QA clicks now wait outside page scripting and respect
the sticky SVG viewport, so script-disabled checks do not await blocked frames.
No unverified required claim remains; semantic work continuity remains out of scope.

## Historical RUN-116 Evidence

The prior paging tests below verified text completeness, not whole-map continuity.

967 application tests ran: 964 passed, with three unchanged optional semantic-runtime skips.
No model/semantic engine changes require those extras in this Run. Existing
sample route, source reader, shared shell and privacy/organization regressions
remain covered. 22 reader tests include the new temporal projection checks.

`qa-affinity-browser.mjs` passes at exact 1440/920/700/320 widths. It checks
monotonic time placement, equal-time x equality, count conservation, curved paths,
explicit gaps, period evidence, moment lens, stable geometry on selection,
three scales, original source return with camera restoration, rapid last-selection
ownership, history, keyboard/pointer navigation, focus reveal for clipped knots,
resize preservation of the observed time window,
ordinary/modifier wheel ownership, fit/reset, all-edge disclosure, full paging,
long titles, reduced motion, no script and forced rendering failure. Zero
mutation requests or runtime exceptions were observed. Source-return checks wait
for the restored document/enhancement, not merely SSR evidence availability.

Additional real-browser unknown-time injection verifies no time ticks or dated
knots, reachable unknown links and exact unknown-period evidence; the synthetic
baseline was restored. The actual loopback runtime was restarted with lifespan
initialization disabled. Boolean-only checks pass current source validation,
temporal SVG/date axis/knots/curves, no overflow, complete period accounting and
exact period evidence. No private screenshots, titles or quotes are test evidence.

No unverified required claim remains. Semantic work identity/quality is outside
this Run and remains unassessed; this PASS is not model or grouping admission.
