# LocalBrain

Keep your AI coding conversations and project documents together on your Mac.
LocalBrain helps you find and revisit past work through Session history, local
documents, search, and usage history.

## What you can do

- **Revisit conversations.** Browse Codex and Claude Code Sessions, pin useful
  conversations, and explore recorded activity in List or Chart.
- **Connect documents.** Read folders, individual files, and Apple Notes in
  Local Contexts while keeping the originals in place.
- **Search past work.** Find Sessions and documents with keywords, or enable
  optional local AI search to search by meaning.
- **Understand usage.** Compare tokens, estimated costs, and activity by source,
  model, project, and period in Sessions Dashboard.

## Install on macOS

Requires an Apple Silicon Mac with macOS 14 or later.

1. Unzip `LocalBrain-apple-silicon.zip`.
2. Open `LocalBrain.app`. You can move it to Applications if you prefer.

See the [installation and first-launch guide](docs/policies/project/standalone-test-app-guide.md#받아서-실행하기)
for macOS security prompts and installation requirements.

## Get started

1. Follow the setup window to connect a Codex or Claude Code profile and any
   document sources you want to use. You can choose **Set up later**.
2. Open **Sessions** and select **Sync** (`동기화`) to collect your conversations,
   or open **Local Contexts** to read connected documents.
3. Use the shared search field to find a remembered phrase. Keyword search needs
   no model; AI search is an optional download in **Settings → Search Model**.

Open Settings with the gear or **⌘,** to manage sources, synchronization, and
backups. Closing the window leaves LocalBrain running; use **⌘Q** to quit.

Imported records, settings, and search indexes are stored locally on your Mac.
AI search processes your material locally.

## User guides

Open **Docs** in the app to read these guides offline.

| Guide | Covers |
| --- | --- |
| Getting Started | Setup, first use, quitting, and updates |
| Settings | Preferences, sources, synchronization, backups, and recovery |
| Sessions | Conversations, projects, pins, and Chart |
| Sessions Dashboard | Usage, estimated costs, and coverage |
| Local Contexts | Connecting and reading documents |
| Search | Keyword search, AI setup, and search readiness |

## Development

For source setup, the development web application, tests, and builds, use the
[Developer Guide](docs/policies/project/developer-guide.md). The
[Documentation Map](docs/README.md) routes contributors to product contracts,
architecture, design, and planning.
