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

## Install from source with an agent

For the initial trial, clone this repository, or update your existing checkout,
then open it with your coding agent and ask it to build and install LocalBrain.
The native build currently targets Apple Silicon and declares macOS 14 or later
as its app minimum.
Windows x86_64 with optional local AI search is planned; its port and native
build/runtime checks are still pending.

You can give your agent this request:

```text
이 저장소의 README와 설치 가이드를 읽고 LocalBrain 데스크톱 앱을 로컬 빌드·설치해 줘.
현재 OS/CPU와 필요한 도구를 확인하고, 저장소가 지원하는 빌드 절차를 사용해 줘.
기존 로컬 변경을 보존하고, 개인 데이터·설정·캐시는 저장소 밖에 유지해 줘.
개발용 웹 서버 대신 빌드된 앱을 열어 확인하고, 모델 가중치는 내가 선택할 때만 내려받아 줘.
소스 revision과 로컬 변경 여부, 앱 위치, 빌드·설치·실행 결과와 미확인 항목을 알려 줘.
현재 지원하지 않는 환경이면 성공으로 보고하지 말고 막힌 지점과 필요한 작업을 설명해 줘.
```

The [agent-assisted installation guide](docs/policies/project/installation-and-storage.md#agent-assisted-local-build)
owns the prerequisites, build/launch checks, storage boundaries and update steps.
The source installer needs build tools; running the finished app needs no Python
installation, checkout or manually started development server. Public model
weights remain an explicit optional download in Settings.

To update, quit LocalBrain completely, update the source while preserving local
changes, and ask the agent to rebuild and replace the app. Pulling source alone
does not update an existing app. Keep your data and settings in place.

### Prebuilt macOS test app alternative

The current ZIP is an ad-hoc signed test build without Apple notarization.
Requires an Apple Silicon Mac with macOS 14 or later.

1. Unzip `LocalBrain-apple-silicon.zip`.
2. Open `LocalBrain.app`. You can move it to Applications if you prefer.

See the [test-app first-launch guide](docs/policies/project/standalone-test-app-guide.md#receive-and-open)
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

Open **Docs** in the app to read these six guides offline. Korean is the default; choose **English** to switch the current guide.

| Guide | Covers |
| --- | --- |
| Getting Started | Setup, first use, quitting, and updates |
| Settings | Preferences, sources, synchronization, backups, and recovery |
| Sessions | Conversations, projects, pins, and Chart |
| Sessions Dashboard | Usage, estimated costs, and coverage |
| Local Contexts | Connecting and reading documents |
| Search | Keyword/meaning search, models, and readiness |

## Development

For source setup, the development web application, tests, and builds, use the
[Developer Guide](docs/policies/project/developer-guide.md). The
[Documentation Map](docs/README.md) routes contributors to product contracts,
architecture, design, and planning.
