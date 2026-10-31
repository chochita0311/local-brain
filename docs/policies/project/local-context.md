# Local Context

This contract owns registered folder/file/Apple Notes collection and document reading responsibilities. [Desktop App And Settings](desktop-app-and-settings.md#local-context-settings-presentation) owns source settings; [Markdown Rendering](markdown-rendering.md) owns syntax, trust and source-local references.

## Local Context Sources

The `context_roots` registry owns folders, individual files, and Apple Notes sources shown in Local Contexts.

- Folder registration scans supported content recursively.
- Overlapping parent and child folder roots are rejected to keep document ownership unambiguous.
- Hidden and generated directories such as `.git`, `node_modules`, `dist`, and `build` are excluded.
- Removing a source disables browsing and search and clears its derived Atlassian URL sightings without deleting original local files or stable Atlassian Items.
- Re-adding a previously removed path restores and refreshes that source.
- Individual text files are registered independently from folder roots.
- PDF text is currently indexed only when macOS Spotlight exposes readable content.
- Unsupported files remain registered with an `unreadable` state and do not create preview documents.
- Apple Notes indexing records account, folder, title, plaintext, and modification time after macOS grants Automation access.

## Implementation Ownership

- `src/localbrain/local_context/service.py`: Local Context source registration and browsing behavior

- `src/localbrain/rendering/markdown.py`: shared safe Markdown and approved Obsidian-style parsing, derived render state, local code and MathML rendering, attachment deferral, and reusable consumer output governed by the [Markdown Rendering Contract](markdown-rendering.md)

- `src/localbrain/local_context/references.py`: one-FOLDERS-root Markdown and wikilink resolution, stable anchor identity, and bounded note-fragment extraction
