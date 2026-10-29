Settings manages application preferences, connected sources, search, synchronization, and storage. Open it with the gear (`설정`) or **⌘,**.

## At a glance

| Section | What it controls | How changes apply |
| --- | --- | --- |
| General (`일반`) | Startup screen and time zone | Selection saves automatically; timing is described below. |
| Session Sources (`세션 소스`) | Codex and Claude Code profiles and record locations | Add or save a profile explicitly. |
| Local Context | Selected folders, files, and optional Apple Notes | Add a source explicitly. |
| Search Model (`검색 모델`) | Optional local AI search | Download, prepare, cancel, or disable explicitly. |
| Synchronization (`동기화`) | Independent Session and document schedules | Selection saves automatically. |
| Google Drive | Google account, shared root, selected uploads and received folders | Save a root, then select targets and run manually or enable automatic sync. |
| Storage (`저장공간`) | Locations, size, backup, restore, and cache cleanup | Start each operation explicitly. |

Jump to [General](#General), [Session sources](#Session-sources), [Local Context](#Local-Context), [Search model](#Search-model), [Synchronization](#Synchronization), [Google Drive](#Google-Drive), or [Storage](#Storage).

## General

Choose **Sessions Dashboard**, **Sessions**, or **Local Context** as your startup screen. The default is Sessions; a change applies on the next app launch.

Time zone offers **UTC** and **Asia/Seoul**. A different valid value saved previously remains until you replace it. On the next navigation or reload, the choice changes Session, conversation, and chart time displays and the dashboard's date ranges and daily, weekly, or monthly grouping. A record near midnight may move to a different displayed date. Original timestamps, the system clock, and saved synchronization intervals stay unchanged. Google Drive recalculates its next fixed execution time in the selected time zone; existing Session and Local Context collection timers keep their own elapsed-time behavior.

For example, an activity at **00:30 on the 19th in Asia/Seoul** is **15:30 on the 18th in UTC**, so the dashboard groups it under the corresponding local date.

Saved preferences are retained between launches. Defaults apply to settings that have not been configured.

## Session sources

1. Choose **Add profile** (`프로필 추가`) and select **Tool**: Codex or Claude Code.
2. Enter a **Profile name** and agent **Home**. The normal record folder is `sessions` under a Codex home or `projects` under a Claude Code home.
3. If records live elsewhere, expand **Custom session folder** and choose the actual **Session folder**. Home is optional with an explicit custom record folder. This override stays fixed when Home changes; **Use default folder** restores the normal relationship.
4. Choose **Add** or **Save**. Browse and detected-profile suggestions only fill the editor; they do not register or collect anything by themselves.

Only the registered record folder is collected, not the full agent Home. Multiple profiles are supported; duplicate or overlapping record folders are rejected. Editing a label preserves the source's identity. Moving an existing profile's record location requires confirmation that it is the same profile and matching records at the new location.

Canceling or leaving this category discards an unsaved editor; Back in first-use setup preserves it. Drag a row handle, or use its arrow keys, to save source order.

**Unregister** requires confirmation. It excludes the source from collection and ordinary search, while keeping imported records and original files. The retained source can be registered again.

## Local Context

Use **Add** to select a folder or file, then confirm registration. Apple Notes is optional and may request macOS permission. Folder collection reads supported Markdown documents; individual text, Markdown, and supported PDFs can also be connected. See [Local Contexts](/help/local-contexts) for reading and format limits.

Source order uses the same row-handle interaction. Canceling or leaving the editor discards its draft; setup Back preserves it.

**Unregister** requires confirmation. It stops collection and removes the source from search and browsing, clearing its search entries. LocalBrain keeps its saved source details and imported documents so you can register it again. Original files and Apple Notes stay unchanged.

## Search model

Keyword search works without a model. After a successful embedding-model download, AI search preparation starts automatically. The [Search guide](/help/search) explains setup, download requirements, and preparation states.

The **Context Search answer models** section manages **Qwen3-4B** (about8GB) and **Qwen3-8B** (about16GB). Connect an existing shared cache or explicitly download a missing model. **Check installation** verifies an existing app registration. These actions do not prepare an embedding index. Choose the answer model on Context Search;8B needs more memory.

Public originals stay in the shared Hugging Face Hub cache (normally `~/.cache/huggingface/hub`, respecting the configured Hugging Face cache). App registration metadata stays in LocalBrain data; inference/kernel caches stay in LocalBrain cache. Connecting a complete cached model avoids another download. Status discovery checks local presence; the worker verifies integrity before use. App cache cleanup preserves shared originals.

## Synchronization

Sessions and Local Context have separate schedules. Defaults are **10 minutes after Session collection finishes** and **30 minutes after Local Context collection finishes**.

Select **10, 20, 30, or 60 minutes**, or **Off** (`끄기`), for either source type. Selection saves that schedule only. Off keeps its interval and imported material; choosing minutes enables it. A valid previously saved custom interval remains displayed until changed. Changes affect the next scheduling decision, without interrupting an active collection.

Only connected sources are read while the application is running. **Quit** stops collection; closing the window leaves it running. Sessions also has a manual Sync button. Background completion keeps the current view in place; reopen or reload it to see new material. Enabled AI search updates its index when collected material changes.

## Google Drive

Open **Settings → Google Drive**. Enter the **full shared-root folder URL** and the name of **your publishing folder** beneath it, then choose **Save and check connection**. LocalBrain saves the destination, reuses your existing gcloud login and checks the shared root in sequence. It does not upload files during this check. A URL identifies a folder; it does not grant access. You can register and switch between roots.

Each PC needs **Google Cloud CLI (`gcloud`)**. Install it using [Google's installation guide](https://docs.cloud.google.com/sdk/docs/install-sdk), then sign into your own account with Drive access:

```bash
gcloud auth login --enable-gdrive-access --force
```

You can run this command in a terminal, or open **Account and login options** and choose **Google login** in this tab. LocalBrain's login action leaves gcloud's global active account and Application Default Credentials unchanged. If you have already logged in with Drive access, saving the destination reuses it without opening a browser. For a saved destination, **Check connection** repeats the account and shared-root checks. After a browser login, choose **Check connection** to continue. The optional **Google account** field in the account options selects a specific account. When left blank, a saved connection uses its bound account; a new connection uses the current or only available gcloud account. If the choice is ambiguous, enter the account explicitly. The app confirms the Google account before saving the connection and keeps that account fixed even if you later change gcloud's active account.

The requested Google permission is **full Drive access** (`https://www.googleapis.com/auth/drive`): reading and writing files accessible to your account. This is broader than the root you enter. LocalBrain performs actual synchronization only within your configured root and selections; shared-folder permissions still apply. No new Cloud project, LocalBrain OAuth Client or downloaded Client JSON is needed for this SDK flow. Google Cloud CLI retains credentials and handles token refresh; LocalBrain keeps access tokens only briefly in memory. A real reauthentication request requires your deliberate login; schedules never keep opening a browser. [Google's Drive authentication flow](https://docs.cloud.google.com/sdk/docs/authenticate#add_google_drive_to_your_scope).

After the first successful connection check, the upload sources and other publisher folders appear. Choose **Browse root folder** to refresh the list later. Schedules and run controls appear for selected folders; upload scheduling appears after selecting a source. **Connection diagnostics** retains the separate authentication, API and root observations. A later access failure preserves saved selections and keeps their controls available. Opening Settings displays saved observations and does not contact Google. Authentication, API communication, root access, most recent result, last successful synchronization and next scheduled time are separate observations. Read access does not prove that an upload can be edited or moved to Trash. On supported macOS installations, Drive HTTPS uses the system trust store with certificate verification enabled. A certificate failure calls for checking device trust/network settings rather than repeating Google login. A failed request tells you which operation needs attention; a missing item response alone cannot tell whether a folder was removed or your account lacks access.

### Publish your files

Check existing Local Context **files or folders** under **Upload my material**. A selected folder includes its entire structure, hidden settings and attachments; the Context collector's supported text formats do not filter this transfer. Apple Notes has no filesystem source here and is not offered for upload. Choose **Upload now**, or enable **Automatic execution** after selecting items.

Your local files are authoritative. After the first copy, changed file contents and changes to names, locations, folder structure and deletions are reflected in your own publishing area. Upload deletion moves the corresponding Drive item to Google's Trash. LocalBrain does not permanently delete it, empty Trash or set a custom retention period. Google's normal Trash policy and any organizational retention rules apply. Edits in your published Drive copy are not imported into your originals.

If a published file or source folder is removed from Drive, the next sync restores a readable trashed item or rebuilds a missing copy when its parent can be listed and written and no same-name item exists. Access or listing failures preserve copies and show an error; an unavailable old item is never deleted as part of rebuilding. Unchanged files still receive a content comparison, but their bytes are not staged or uploaded again.

While uploading, the result area shows the current phase, checked items versus the source total, newly transferred files, items not updated, the latest worker relative path and the latest progress time. Known remote file states are checked in groups, and independent files can be processed up to eight at a time after their parent folders are confirmed. Connections are reused during the run to reduce repeated setup. The progress area distinguishes remote-state checks and shows the number of active items. The displayed path and received bytes belong to the latest worker event; the path can switch while several files are active. Received bytes are shown when acknowledged by Google. Checked items include folders and unchanged files, and may include items with an error; this count does not mean every item was transferred successfully. After processing, LocalBrain still checks source changes and deletions. **Synchronization complete** and the updated **Last success** time confirm a fully completed run. Partial results require inspecting **Per-item results**. A long pause in progress is not proof of a stalled worker; network requests and a large current file can still be pending. No completion time is estimated.

### Receive other folders

Check whole publisher folders under **Receive material**, then choose **Receive now** or enable each folder's automatic execution. Your own publishing folder is excluded. Each received folder has its own interval and automatic switch. The selected Drive folder is authoritative: new and changed files, names, locations and confirmed deletions or trashed items update its managed local copy. Confirmed incoming deletion removes the local copy directly; no separate recovery bin is created. Access failure, incomplete listings and uncertain absence preserve copies and show an error.

Received files are stored privately under Application data, in `external-sources/google-drive/<connection-id>/<publisher-id>/`. Each folder's result shows its local destination. They are not registered as Local Contexts or indexed automatically. You control later copying, offline use and backups; the app does not recall copies already received.

### Schedules and limits

Automatic execution initially is **off**. The upload default is **6 hours**; each received folder defaults to **24 hours**. Choose **15 or 30 minutes**, or **1, 3, 6, 12 or 24 hours** independently. These are fixed clock times in the app's selected time zone: 15 minutes runs at :00/:15/:30/:45, and 6 hours at 00:00/06:00/12:00/18:00. Longer intervals are phased from midnight. Manual runs do not shift these times. A missed slot after sleep or Quit is skipped; reopening at 10:20 with a 15-minute schedule waits until 10:30. The backend must be running; closing a native window or browser alone does not stop a running backend.

The **LocalBrain file limit is 100 MB (100,000,000 bytes)** for uploads and downloads, including exactly that size. This is an app limit, not Google's file-size limit. Larger files are skipped while other eligible files continue. An existing copy remains when a file grows past the limit. Per-item results show exclusions and partial failures; these do not count as a fully successful synchronization. Google-native documents and shortcuts are not automatically exported or followed. Unsafe paths and links are not followed outside the selected source.

Uncheck a source or received folder to stop its sync while keeping existing copies. Turning automatic execution off stops future scheduled runs; manual execution remains available. Network or access failure preserves selections, intervals, enabled switches, existing copies and last success. When access returns, the prior schedule continues at its next fixed slot. Ordinary access failure neither deletes gcloud credentials nor revokes Google consent.

## Storage

Storage displays application data and cache locations and their sizes.

| Stored material | Purpose |
| --- | --- |
| Application data | Imported records and application settings. |
| Cache | Generated data that can be rebuilt. |
| Model files | Downloaded models kept in a separate model cache. |

Original Session and document files remain at their registered source locations.

### Back up

The built-in backup does not include Google Drive connection state, OAuth credentials, resumable-transfer state or downloaded Drive folders. Google credentials stay with Google Cloud CLI and are not included. Received copies may be backed up separately by you.

Choose **Save backup** in **Settings → Storage** to create a backup ZIP. It includes a database snapshot, general settings, source settings, search settings, and model registration metadata. It excludes original Session and document files, model weights, caches, logs, and external authentication information.

Backups contain saved application data. Keep backup archives separate from application installation files.

### Restore

1. Use a backup from the **same LocalBrain installation and computer**, with a database schema matching the installed application. Restore a different-schema backup using the application version that created it.
2. Expand **Restore from backup**, select the ZIP, and explicitly confirm replacement of saved data and settings.
3. Choose **Schedule restore**, quit all running LocalBrain instances completely, and restart the application. The replacement takes effect at startup.

A pre-restore copy is kept in the data directory's `recovery` folder, and the application rolls back if restoration fails. Restoring a backup does not restore excluded original files or download model weights.

### Clear caches

**Clear cache** removes inactive search caches and expired analysis caches created by LocalBrain. Original material and downloaded model files are preserved. The search cache can be rebuilt when AI search is enabled.
