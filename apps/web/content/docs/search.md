Search finds original conversations and registered documents. It automatically uses AI when the local model is installed and AI search is enabled. Without the model, or while AI search is off, it uses keywords.

## Search your material

1. Enter a remembered term or phrase in the shared search field and submit it.
2. Describe what you want when AI search is enabled. In the model-free keyword state, multiple terms must match together; using fewer distinctive terms can help. There is no search-engine selector.
3. Open a result or its evidence link to read the original conversation or document. Use the return link or browser Back to revisit the results.

After searching, the page starts with the result count and results. Use the shared header field to search again. Notices appear only when preparation, a partial update, no available source material or failure affects search. Once preparation finishes, **Run the same search again** (`같은 검색 다시 실행`) reloads the results explicitly.

Search covers eligible primary work Sessions from registered sources and readable, enabled Local Contexts. Subsessions are excluded from search; open them through their parent in [Sessions](/help/sessions). An unregistered source, unreadable document, or material outside the supported scope is not included. Application-managed data and caches are excluded.

## Enable optional AI search

1. Open **Settings → Search Model** (`검색 모델`).
2. Choose **Download model** (`모델 다운로드`). The current model is **Qwen3-Embedding-0.6B**, approximately **1.21 GB**; indexing and temporary work need additional disk space and memory.
3. After a successful download, preparation starts automatically. Wait for AI search to finish preparing.
4. Describe the material in the search field. Installed, enabled AI search is used automatically.

For an installed model, use **Enable AI search** (`AI 검색 켜기`) to enable search. While enabled, use **Update index** (`색인 업데이트`) to reflect collected material again or retry preparation.

### Download requirements and recovery

Model downloads require an internet connection and use the system's trusted certificates. Queries and documents are processed by LocalBrain and are not sent to a remote AI service. Downloaded model weights are stored separately from application backups.

If a download fails, check the connection, available storage, and network certificate configuration, then retry the download. Keep certificate validation enabled. Model files, the search index, and temporary processing need more space than the download alone.

You can cancel an active download or preparation. An interrupted download can resume using completed file pieces. See [Settings model storage guidance](/help/settings) for reuse, storage locations, and what cache cleanup preserves. Disabling AI search leaves keyword search available.

### Automatic updates

While AI search is enabled and the app is running, the worker checks for changes every five seconds while waiting. It automatically updates the index when collected material changes. Original collection follows the Synchronization settings; when a change becomes searchable depends on the collection schedule and indexing time. Five seconds is a change-check interval, not a full-update completion interval. See [Settings synchronization guidance](/help/settings) for collection schedules and conditions.

## Adjust result relevance

Use **Settings → Search Model → Minimum relevance** (`최소 관련도`) to adjust the semantic cutoff. The range is **0–1**, with a default of **0.45**. Lower values admit broader matches; higher values require more similarity. The value is not an accuracy or answer probability.

Completing an input saves it automatically for the next search, without rebuilding the index. **Restore default** (`기본값 복원`) returns to 0.45. Existing exact-identifier support for code and filenames remains separate from this cutoff.

## Read preparation and result states

- **Disabled or model missing:** use keyword search. Download the model if it is missing, or prepare an installed model to enable AI search.
- **Preparing:** inspect the notice, wait for readiness or cancel the operation.
- **Partial or failed:** inspect the notice, then use the provided preparation/retry action when appropriate.
- **No results:** the search completed without a match under the current criteria. Try a clearer description or fewer constraints; this is different from the engine not being ready. Successful preparation does not guarantee a matching result.

The app does not silently switch an AI query to keywords on failure or an empty result. A model-settings change updates the search engine while preserving your current query; it waits until settings closes and you finish typing before changing the screen. Result excerpts are evidence links into the original material, not a generated answer replacing it.

Open the search page without a query to inspect preparation counts and detailed search coverage.

For source registration, see [Settings](/help/settings). To connect and read documents, see [Local Contexts](/help/local-contexts).
