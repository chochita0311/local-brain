# In-App Documentation

## Purpose And Scope

In-app Docs are six bundled English guides for people using the distributed
LocalBrain app. This policy defines their content ownership, page boundaries,
reader behavior and delivery contract.

- English user guidance for the distributed app lives in `src/localbrain/content/docs/`. These Markdown bodies are the canonical content; do not copy the repository's policy or planning tree into the app.
- The root [README](../../../README.md) owns the public product overview, installation entry and short first-use path. It directs users to in-app Docs rather than accumulating screen contracts, development progress or build internals. The [Documentation Map](../../README.md) routes maintainers to internal owners; the [test distribution guide](standalone-test-app-guide.md) owns artifact-specific first-launch requirements and release verification limits.
- `src/localbrain/app/docs.py` owns the fixed page registry, titles, descriptions and corresponding content filenames. User input never selects a filesystem path.
- The six pages cover Getting Started, Settings, Sessions Dashboard, Sessions, Local Contexts and Search. They explain the distributed app as ordinary downloaded, installed software. Development-only functionality, unfinished-feature lists, personal-environment details and internal execution evidence remain outside the guide.
- Settings owns option meaning, registration and Storage procedures, including backup, restore and cache cleanup. Search owns model preparation, download requirements and readiness. Sessions, Local Contexts and Dashboard own visibility/coverage checks; Getting Started owns installation, quitting and updates. Other pages link to the owning explanation rather than repeating a separate Troubleshooting page.
- Preserve actual user-facing conditions and limits when generalizing prose, especially same-installation/computer/schema restore eligibility, explicit replacement and restart, recovery behavior, backup exclusions and original/model preservation. Neutral wording does not expand platform support.
- Search guidance distinguishes automatic preparation after a successful model download from manual preparation/retry for an installed model. It identifies eligible primary work Sessions and directs readers to the parent Session for subsessions, preserving existing registration/readability and search exclusions.
- Local Context source-removal guidance explains confirmation, stopped collection, exclusion from search/browsing, search-entry cleanup and retention of source details, imported documents and originals/Notes. Cleanup details for excluded integrations remain in internal behavior contracts rather than public app guidance. Session source removal retains its separate browsing and imported-record contract.

## Routes And Reading

- `/help` is Getting Started. The remaining routes are `/help/settings`, `/help/sessions-dashboard`, `/help/sessions`, `/help/local-contexts` and `/help/search`. The retired `/help/troubleshooting` route returns 404 and has no packaged body.
- The existing FastAPI `/docs` API-reference route is unchanged. Product Docs are a separate destination.
- A Docs link appears immediately above Settings in the shared sidebar footer. Both remain reachable in the compact layout. Docs use the existing app shell, reading tokens, local assets and current-page semantics.
- The reader has no per-guide Settings action or release-version badge. Shared app Settings remains available. The Settings guide omits About, app-versus-data-format version explanations and fixed path-label rules as part of its content boundary. Sessions explains home-directory path labels beside its conversation metadata, preserving the distinction between display, saved locations and historical Project attribution.
- First-use setup does not automatically cover a Docs page. Its Welcome step links to Getting Started; following that link does not complete onboarding or register a source. The existing explicit setup request and normal app startup retain their behavior.
- Body text is marked as English. Guidance uses existing UI names and quotes Korean control labels where that helps users find the current control; Docs do not translate the rest of the app.
- Unknown guide names return 404. A registered guide whose packaged content cannot be read returns a bounded unavailable state, without a source path or private fallback.

## Rendering And Link Authority

- Docs use the shared `render_markdown` renderer, `.markdown-body`, heading anchors and safe fallback behavior. Do not introduce a separate Markdown parser.
- Only this first-party consumer supplies `app_doc_routes`: the exact registered Docs and distributed-app destination links used in the guide. The shared renderer admits only recognized product path shapes from that set. It does not admit APIs, filesystem paths, arbitrary routes or executable schemes through this exception.
- Ordinary source-authored Sessions, Documents, Notes and reports retain their existing link rules when this argument is absent. The existing report-specific Session-route exception is unchanged.
- Docs links and section fragments must render as usable anchors. Reading does not fetch an external reference, resolve private files or register the guide as a Local Context source.

## Delivery And Privacy

- Content, templates, styles and required assets ship in the Python package. The existing PyInstaller `collect_data_files('localbrain')` recipe collects these package-owned files for the desktop app.
- Guide rendering reads package content, not repository-relative files. No checkout, model, network or registered personal source is required for ordinary reading.
- Desktop Docs routes retain the loopback, per-launch authentication and development-feature restrictions. A Docs request causes no source collection, model setup, preference change or personal search indexing.
- Keep examples synthetic. Add no telemetry or external content dependency. A release provides one guide matching its running version; update the relevant content in the same change as a public behavior change.
- A successful source/server or package-data check is not evidence that an older distributed `.app` has been rebuilt. Native release and recipient validation retain their existing owners.

## Validation

- Check route/authentication boundaries, fixed source lookup, shared link rendering and preserved source-authored Markdown behavior.
- Check all page bodies and links against current settings, search, source and recovery contracts, including exact defaults, optionality, preservation and stop conditions.
- Verify desktop and compact rendering, keyboard access, history, Settings entry and offline reading using a synthetic local runtime. Check package-data inclusion separately from a full native rebuild.

## Google CLI Setup Links

The Settings guide includes authored links to the official Google Cloud CLI installation and authentication guides because Drive connections depend on that installed CLI. These open only by user choice, do not preload remote content or carry account data, and do not add source registration, indexing or model work. The six guide routes remain fixed.
