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
- **Ask your documents.** Choose Qwen3-4B or8B in Context Search to ask questions
  over your Local Contexts and received Drive folders, with document evidence.
  Conversation stays on this screen and clears when you leave.
- **Understand usage.** Compare tokens, estimated costs, and activity by source,
  model, project, and period in Sessions Dashboard.

## Install on macOS

Requires an Apple Silicon Mac with macOS 14 or later.

1. Unzip `LocalBrain-apple-silicon.zip`.
2. Open `LocalBrain.app`. You can move it to Applications if you prefer.

See the [installation and first-launch guide](docs/policies/project/standalone-test-app-guide.md#receive-and-open)
for macOS security prompts and installation requirements.

## Get started

1. Follow the setup window to connect a Codex or Claude Code profile and any
   document sources you want to use. You can choose **Set up later**.
2. Open **Sessions** and select **Sync** (`동기화`) to collect your conversations,
   or open **Local Contexts** to read connected documents.
3. Use the shared search field to find a remembered phrase. Keyword search needs
   no model; AI search is an optional download in **Settings → Search Model**.
4. For document answers, connect or install4B/8B in the same settings panel,
   then open **Context Search** below Sessions Dashboard. A complete shared Hub
   cache is reused; embedding preparation is not required for this screen.

Open Settings with the gear or **⌘,** to manage sources, synchronization, and
backups. Closing the window leaves LocalBrain running; use **⌘Q** to quit.

Imported records, settings, and search indexes are stored locally on your Mac.
AI search processes your material locally.

Google Drive is managed in its own Settings tab: publish checked Local Context files/folders and receive checked publisher folders using independent manual or fixed-time automatic sync. Files have a LocalBrain limit of 100 MB each. Each PC uses Google Cloud CLI (`gcloud`) to sign into its own account with full Drive access; app operations remain within the configured root and selections. See the bundled Settings guide and the [Google CLI setup guide](docs/policies/project/google-drive-sync.md#google-cli-authentication-and-distribution).

## User guides

Open **Docs** in the app to read these guides offline.

| Guide | Covers |
| --- | --- |
| Getting Started | Setup, first use, quitting, and updates |
| Settings | Preferences, sources, synchronization, Google Drive, backups, and recovery |
| Sessions | Conversations, projects, pins, and Chart |
| Sessions Dashboard | Usage, estimated costs, and coverage |
| Local Contexts | Connecting and reading documents |
| Search | Keyword/meaning search, Context Search answers, models, and readiness |

## Development

For source setup, the development web application, tests, and builds, use the
[Developer Guide](docs/policies/project/developer-guide.md). The
[Documentation Map](docs/README.md) routes contributors to product contracts,
architecture, design, and planning.
