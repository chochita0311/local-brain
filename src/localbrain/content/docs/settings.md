Settings manages application preferences, connected sources, search, synchronization, and storage. Open it with the gear (`설정`) or **⌘,**.

## At a glance

| Section | What it controls | How changes apply |
| --- | --- | --- |
| General (`일반`) | Startup screen and time zone | Selection saves automatically; timing is described below. |
| Session Sources (`세션 소스`) | Codex and Claude Code profiles and record locations | Add or save a profile explicitly. |
| Local Context | Selected folders, files, and optional Apple Notes | Add a source explicitly. |
| Search Model (`검색 모델`) | Optional local AI search | Download, prepare, cancel, or disable explicitly. |
| Synchronization (`동기화`) | Independent Session and document schedules | Selection saves automatically. |
| Storage (`저장공간`) | Locations, size, backup, restore, and cache cleanup | Start each operation explicitly. |

Jump to [General](#General), [Session sources](#Session-sources), [Local Context](#Local-Context), [Search model](#Search-model), [Synchronization](#Synchronization), or [Storage](#Storage).

## General

Choose **Sessions Dashboard**, **Sessions**, or **Local Context** as your startup screen. The default is Sessions; a change applies on the next app launch.

Time zone offers **UTC** and **Asia/Seoul**. A different valid value saved previously remains until you replace it. On the next navigation or reload, the choice changes Session, conversation, and chart time displays and the dashboard's date ranges and daily, weekly, or monthly grouping. A record near midnight may move to a different displayed date. Original timestamps, the system clock, and saved synchronization intervals stay unchanged.

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

Keyword search works without a model. After a successful model download, AI search preparation starts automatically. The [Search guide](/help/search) explains setup, download requirements, and preparation states.

## Synchronization

Sessions and Local Context have separate schedules. Defaults are **10 minutes after Session collection finishes** and **30 minutes after Local Context collection finishes**.

Select **10, 20, 30, or 60 minutes**, or **Off** (`끄기`), for either source type. Selection saves that schedule only. Off keeps its interval and imported material; choosing minutes enables it. A valid previously saved custom interval remains displayed until changed. Changes affect the next scheduling decision, without interrupting an active collection.

Only connected sources are read while the application is running. **Quit** stops collection; closing the window leaves it running. Sessions also has a manual Sync button. Background completion keeps the current view in place; reopen or reload it to see new material. Enabled AI search updates its index when collected material changes.

## Storage

Storage displays application data and cache locations and their sizes.

| Stored material | Purpose |
| --- | --- |
| Application data | Imported records and application settings. |
| Cache | Generated data that can be rebuilt. |
| Model files | Downloaded models kept in a separate model cache. |

Original Session and document files remain at their registered source locations.

### Back up

Choose **Save backup** in **Settings → Storage** to create a backup ZIP. It includes a database snapshot, general settings, source settings, search settings, and model registration metadata. It excludes original Session and document files, model weights, caches, logs, and external authentication information.

Backups contain saved application data. Keep backup archives separate from application installation files.

### Restore

1. Use a backup from the **same LocalBrain installation and computer**, with a database schema matching the installed application. Restore a different-schema backup using the application version that created it.
2. Expand **Restore from backup**, select the ZIP, and explicitly confirm replacement of saved data and settings.
3. Choose **Schedule restore**, quit all running LocalBrain instances completely, and restart the application. The replacement takes effect at startup.

A pre-restore copy is kept in the data directory's `recovery` folder, and the application rolls back if restoration fails. Restoring a backup does not restore excluded original files or download model weights.

### Clear caches

**Clear cache** removes inactive search caches and expired analysis caches created by LocalBrain. Original material and downloaded model files are preserved. The search cache can be rebuilt when AI search is enabled.
