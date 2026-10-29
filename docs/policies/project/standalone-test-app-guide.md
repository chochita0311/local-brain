# LocalBrain macOS Test Distribution Guide

This guide covers the test artifact's first launch, supported environment and
evidence limits, manual replacement, and recipient validation. Ordinary usage
starts in **Docs → Getting Started** inside the app; **Docs → Settings** owns
source registration, synchronization, backup, restore and cache procedures.

## Requirements And Verified Scope

- Use an **Apple Silicon Mac**. The build targets **arm64** and declares **macOS 14**
  as its minimum. The declared minimum does not establish execution on every OS
  version. Check the artifact's `BUILD-INFO.md` for its actual build OS, app/ZIP
  sizes and verification results.
- Recipients need no Python, uv, Homebrew, source checkout or developer account to launch the app. Optional Google Drive synchronization requires Google Cloud CLI on that Mac and the user's Google login; **Docs → Settings → Google Drive** owns installation, permissions and connection checks.
- Keyword search needs no model. Optional AI search explicitly downloads public
  **Qwen3-Embedding-0.6B** weights, approximately **1.21 GB**, and prepares the local
  index. Indexes and temporary work need additional space according to the source
  material; model initialization and search need additional memory. This artifact
  does not guarantee every Apple Silicon memory configuration or large-data
  performance.
- The packaged app provides Sessions list, Chart, pins, detail and subsessions;
  Sessions Dashboard; Local Contexts; search; Context Search; settings including Google Drive; first-use setup; and bundled
  Docs. It excludes the top-level Dashboard/learning, Workstreams, Auto Work,
  Atlassian, Insights, Session workflow and Schema. Development web keeps its
  other routes; user settings cannot enable those features in the test app.
- Context Search uses separately installed Qwen3-4B or8B public assets, reusing a complete shared Hub cache. It reads enabled Local Context and already received Drive copies without an embedding prerequisite. Dialogue is transient and clears on screen/tab leave. Model and runtime memory requirements are separate from weight size; see **Docs → Search → Ask with Context Search**.

This artifact is an **internal, ad-hoc signed test build without Apple
notarization**. Its first-launch procedure and local checks do not establish the
normal-security public-release acceptance of a later signed/notarized build.

## Receive And Open

1. Download `LocalBrain-apple-silicon.zip` from the shared source and unzip it.
2. Open `LocalBrain.app` inside the extracted folder. Moving it to Applications is
   optional.
3. If macOS blocks first launch, use the app-specific **Open Anyway**
   (`확인 없이 열기`) action in **System Settings → Privacy & Security**, only for
   the file whose shared origin and checksum you have verified. If organizational
   Mac management does not permit it, ask the administrator to allow that app.
   Do not disable system-wide security settings. See
   [Apple's app-opening guidance](https://support.apple.com/en-au/102445).

## First-Use Checks And Recovery

The setup window opens above the main screen. It follows **Welcome → Sessions →
Documents → Search**, with Back, Next and Skip. **Next** saves pending source input;
validation or save errors keep the input and current step. **Back** preserves a
draft; **Skip** leaves it unregistered. Finish setup with the final **Start** or
**Skip** action, or choose **Set up later**. Quitting before completion opens
setup again next time and keeps sources already saved.

For a first-use check:

- Add a Codex or Claude Code profile through **Session Sources → Add profile**
  (`세션 소스 → 프로필 추가`). Codex reads `sessions` under its agent Home; Claude
  Code reads `projects`. Use **Custom session folder → Session folder** when
  transcripts live elsewhere. Choosing a folder or a detected profile only fills
  the editor; Add, Save or setup Next registers it. Reconnecting an existing
  profile at a different record location requires same-profile confirmation.
- Register any document folders or files you need under **Local Context**. Apple
  Notes is optional and needs macOS Automation permission. Folder collection is
  limited to supported Markdown; individual text/Markdown files are supported,
  and PDF bodies require Spotlight text. There is no OCR or separate PDF engine.
  A missing permission or unsupported file does not block other sources.
- Use the Sessions **Sync** (`동기화`) action to collect immediately. Open a
  conversation or document and try a remembered phrase in keyword search. Model
  download/preparation is optional and explicit; it is not required to finish
  setup or read Docs.
- Reopen settings with the gear or **⌘,**. Detailed editor, scheduling and source
  removal behavior belongs to the in-app Settings guide. Unregistering a Session profile requires
  confirmation and preserves imported records and original material.

Settings **About** (`앱 정보`) shows the LocalBrain name and running application
version; the initial test release is **v0.0.1**. App version is separate from the
settings/data-format versions. Confirm the received artifact against
`BUILD-INFO.md` rather than treating a data-format number as the app release.

### Older Startup Failure

If an early test artifact showed an authentication JSON error or garbled Korean,
replace it with an artifact containing the **2026-10-19 startup repair**. That
repair does not require deleting user data or model files.

### Model Download Connection

Model download keeps HTTPS certificate verification enabled and uses the trust
store trusted by this Mac. If a managed network rejects the connection, check the
Mac's certificate/network configuration and retry. LocalBrain neither copies a
company certificate nor disables security verification.

## Quit, Update And Local Data

Closing the red window button hides the app; its Dock icon reopens the existing
window. Use **⌘Q** to quit completely and stop its backend, downloads and
synchronization. The app does not start automatically at login. In development
browser use, closing a tab leaves collection running while the server is alive;
**Ctrl+C** stops the server and its schedules.

Fully quit LocalBrain before replacing the `.app`, then reopen it. Deleting or
replacing the application does not automatically remove data or settings. This
version does not provide live storage-location changes, transfer to another Mac
or automatic updates. Existing Session-source configuration, imported records,
pins and historical Usage attribution are preserved.

Default data/settings are in `~/Library/Application Support/LocalBrain`;
rebuildable private caches are in `~/Library/Caches/LocalBrain`. Public model
weights use the local shared Hugging Face cache. Search queries and local model
inference stay on the Mac. Explicitly selected Google Drive publishing uploads
the chosen original files to the configured root; receiving downloads selected
publisher folders. Other external writes retain their separate approval boundary.
**Settings → Storage** shows the actual locations
and sizes. Keep private backups separate from the program-sharing ZIP.

### Same-Installation, Same-Mac Recovery

A backup includes a database snapshot, general settings, source settings, search
settings and LocalBrain's model-registration metadata. It excludes original
Session/document files, public model weights, caches, logs and external
authentication information. Drive connections/checkpoints, received copies and
gcloud credentials are also excluded; they have separate storage/backup owners.
A backup ZIP contains private application data and
belongs in a private local location, separate from installation files.

Restore only a backup made by the **same LocalBrain installation on the same
computer**, with a database schema matching the installed app. Restore a
different-schema backup using the application version that created it. In
**Settings → Storage**, select the backup and explicitly confirm replacement of
saved data/settings, then schedule the restore. Quit every running LocalBrain
app **and any separate web server**, and restart. Replacement takes effect at
startup. A pre-restore copy remains in the data directory's `recovery` folder;
failure rolls back to that copy. Restore does not recover excluded originals or
download model weights. Follow **Docs → Settings → Storage** for the full
procedure and owned cache cleanup.

## Recipient Validation

Keep developer-Mac checks separate from a recipient actually downloading and
executing the **same ZIP** from the selected internal Drive delivery channel.
Record:

- Mac model/OS and the ZIP checksum;
- extraction and first launch;
- source registration and search;
- window close versus complete quit;
- manual app replacement and retained data/settings afterward.

There is no need to transfer original content or a private database for this
receipt. A local build or source/package test does not establish a teammate's
execution or compatibility across all supported OS/memory configurations.

## Maintainer Build Reference

Required tools, build commands and outputs belong to the
[GitHub Developer Guide](https://github.com/chochita0311/local-brain/blob/master/docs/policies/project/developer-guide.md#build-the-macos-app).
After building, check first launch, manual replacement and another Mac separately
under this guide's conditions. Program upload and teammate notification remain
separate delivery actions.
