Search finds original conversations and registered documents. Use keyword search for matching terms or an optional AI model to search by meaning.

## Start with keywords

1. Enter a remembered term or phrase in the shared search field and submit it.
2. Keep **Keyword search** selected to search without a model. Using fewer distinctive terms can help; multiple keyword terms must match together.
3. Open a result or its evidence link to read the original conversation or document. Use the return link or browser Back to revisit the results.

Search covers eligible primary work Sessions from registered sources and readable, enabled Local Contexts. Subsessions are excluded from search; open them through their parent in [Sessions](/help/sessions). An unregistered source, unreadable document, or material outside the supported scope is not included. Application-managed data and caches are excluded.

## Enable optional AI search

1. Open **Settings → Search Model** (`검색 모델`).
2. Choose **Download model** (`모델 다운로드`). The current model is **Qwen3-Embedding-0.6B**, approximately **1.21 GB**; indexing and temporary work need additional disk space and memory.
3. After a successful download, preparation starts automatically. Wait for AI search to finish preparing.
4. Select **AI search** on the Search screen and describe the material you want to find.

Use **Prepare AI search** (`AI 검색 준비`) to start or retry preparation for an installed model when needed.

Model downloads require an internet connection and use the system's trusted certificates. Queries and documents are processed by LocalBrain and are not sent to a remote AI service. Downloaded model weights are stored separately from application backups.

If a download fails, check the connection, available storage, and network certificate configuration, then retry the download. Keep certificate validation enabled. Model files, the search index, and temporary processing need more space than the download alone.

You can cancel an active download or preparation; completed download pieces can remain for resuming. Disabling AI search leaves keyword search available. Enabled AI search updates its index as collected material changes.

## Read preparation and result states

- **Disabled or model missing:** use keyword search. Download the model if it is missing, or prepare an installed model to enable AI search.
- **Preparing:** wait for readiness or cancel the operation. The status explains current preparation coverage.
- **Partial or failed:** inspect the notice and readable-source coverage, then use the provided preparation/retry action when appropriate.
- **No results:** the search completed without a match under the current criteria. Try a clearer description or fewer constraints; this is different from the engine not being ready. Successful preparation does not guarantee a matching result.

The app does not silently switch an AI query to keywords on failure or an empty result. Choose the keyword tab yourself; it preserves your query. Result excerpts are evidence links into the original material, not a generated answer replacing it.

For source registration, see [Settings](/help/settings). To connect and read documents, see [Local Contexts](/help/local-contexts).
