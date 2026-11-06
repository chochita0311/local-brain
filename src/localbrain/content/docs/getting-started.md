LocalBrain organizes AI coding conversations and project documents so you can browse, revisit, and search past work.

## Install and launch

For the initial trial, get the repository and ask your coding agent to build and
install LocalBrain using the [README installation entry](https://github.com/chochita0311/local-brain#install-from-source-with-an-agent).
Then launch the built application. If you receive a finished app instead, install
and launch that app. Build-tool instructions stay in the repository; ordinary use
of the installed app needs no source checkout or manually started development server.

## Set up your sources

The first-use window follows **Welcome → Sessions → Documents → Search**.

1. Connect a Codex or Claude Code profile to browse its conversations. [Settings](/help/settings) explains the agent Home and Session folder fields.
2. Connect a document folder, an individual file, or optional Apple Notes to use [Local Contexts](/help/local-contexts).
3. Start with keyword search. Installing an [AI search model](/help/search) is optional.
4. Finish with **Start** or the final **Skip**, or choose **Set up later** to configure sources later.

In the Session and Document steps, **Next** saves pending input, **Back** keeps it, and **Skip** leaves the current draft unregistered. If you quit before finishing setup, it opens again next time; already saved sources remain.

Open Settings with the gear (`설정`) or **⌘,**.

## Find your first material

After registering a Session source, open [Sessions](/sessions) and choose **Sync** (`동기화`) to collect it immediately. Automatic Session and document collection runs while the application is running; see [Settings](/help/settings).

Open a Session to read its conversation, or open [Local Contexts](/context) to select a document. Use the shared search field to find a remembered phrase. Source registration is explicit: finding or choosing a folder alone does not connect it.

## Move between screens

Toggle the sidebar beside the LocalBrain brand. Collapsing keeps the menu icons
reachable. On the Mac app, Back, Forward and search share the window titlebar;
in a browser they stay in the page toolbar. **←** retraces visits across Sessions,
details, documents, Search and Docs, retaining filters, selection and reading
position. **→** returns along that same history after Back; a new visit discards
the forward branch. The sidebar toggle keeps its state across visits in the current
window. Hover or keyboard-focus an available navigation icon for its name and separate
shortcut keys; Escape dismisses the hint. Search has no extra hover help. Disabled
Back/Forward retain their name/key hint and show a not-allowed cursor.

| Action | Mac | Other desktop browsers |
| --- | --- | --- |
| Back / Forward | `⌘[` / `⌘]` | `Alt+←` / `Alt+→` |
| Toggle sidebar | `⌘⇧S` | `Ctrl+Shift+S` |
| Focus search | `⌘K` | `Ctrl+K` |

It keeps the current window's latest **50 points including the current screen**
(up to 49 backward steps) and is unavailable at the first retained point. Reloads
and background updates add no point. Fully quitting starts a new history next launch.

## Close and update the application

Closing the window leaves the application running. Open its application icon to show the window again. Choose **Quit** or press **⌘Q** to exit completely and stop synchronization and downloads.

Before updating, quit LocalBrain completely, install the updated application, and reopen it. Replacing or removing the application does not delete saved data or settings. [Settings](/help/settings) explains backup and restore.

For a source-built installation, update the repository and ask your agent to
rebuild and replace the app while preserving saved data and settings. Pulling
source alone does not update the installed application.

## Explore the guides

- [Settings](/help/settings): preferences, sources, synchronization, storage, and backups.
- [Sessions](/help/sessions): conversations, projects, pins, and the activity chart.
- [Sessions Dashboard](/help/sessions-dashboard): usage and estimated costs.
- [Local Contexts](/help/local-contexts): document sources and reading.
- [Search](/help/search): keyword and AI search.
