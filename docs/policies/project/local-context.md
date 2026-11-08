# Local Context

This contract owns registered folder/file/Apple Notes collection and document reading responsibilities. [Desktop App And Settings](desktop-app-and-settings.md#local-context-settings-presentation) owns source settings; [Markdown Rendering](markdown-rendering.md) owns syntax, trust and source-local references.

## Local Context Sources

The `context_roots` registry owns folders, individual files, and Apple Notes sources shown in Local Contexts.

- Folder registration scans supported content recursively.
- Overlapping parent and child folder roots are rejected to keep document ownership unambiguous.
- Hidden and generated directories such as `.git`, `node_modules`, `dist`, and `build` are excluded.
- Folder collection prunes excluded directories before descending, retains the
  sorted case-sensitive `*.md` path set, does not follow directory symlinks,
  and preserves cancellation and per-source failure/deletion boundaries.
- Removing a source disables browsing and search and clears its derived Atlassian URL sightings without deleting original local files or stable Atlassian Items.
- Re-adding a previously removed path restores and refreshes that source.
- Individual text files are registered independently from folder roots.
- PDF text is currently indexed only when macOS Spotlight exposes readable content.
- Unsupported files remain registered with an `unreadable` state and do not create preview documents.
- Apple Notes indexing records account, folder, title, plaintext, and modification time after macOS grants Automation access.

## Document Reading

For a Document in an enabled folder source, reference preparation currently
loads the same registered root's document identities and bodies in one scoped
bulk read, including documents without a link from the opened Document. This
builds the name/path lookup used by links, target anchors and note embeds; it
does not discover roots or walk linked files. Ordinary links do not recursively
open every destination. Nested embeds use the existing bounded-depth/cycle
rules in [Markdown Rendering](markdown-rendering.md). This describes reading,
independently from scheduled folder collection.

## Implementation Ownership

- `src/localbrain/local_context/service.py`: Local Context source registration and browsing behavior

- `src/localbrain/rendering/markdown.py`: shared safe Markdown and approved Obsidian-style parsing, derived render state, local code and MathML rendering, attachment deferral, and reusable consumer output governed by the [Markdown Rendering Contract](markdown-rendering.md)

- `src/localbrain/local_context/references.py`: one-FOLDERS-root Markdown and wikilink resolution, stable anchor identity, and bounded note-fragment extraction
