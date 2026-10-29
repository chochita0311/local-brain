Search finds original conversations and registered documents. Use keyword search for matching terms or an optional AI model to search by meaning. **Context Search** is a separate question/answer screen for your Local Contexts and received Drive copies.

## Ask with Context Search

1. Open **Settings → Search Model** and connect or install **Qwen3-4B** or **Qwen3-8B** in the answer-model section. Complete public files already in the shared Hugging Face cache are reused.4B needs about8GB of model files;8B about16GB and more runtime memory. Initial verification/loading can take longer than later questions.
2. Open [Context Search](/context-search) below Sessions Dashboard and select an available answer model. It searches enabled/readable Local Contexts and already received Google Drive folders together; it does not search Sessions. The source disclosure shows included folders and received-copy status. Connect Local Context or receive a Drive folder first if the list is empty.
3. Ask about a topic, document or responsibility. The local model requests folder listing, literal text search and file reads; LocalBrain executes those read-only tools. No embedding installation, index preparation or model training is required.
4. Read the answer and expand **Checked evidence** (`확인한 근거`) for source names, relative files, line numbers and actual excerpts. Folder publisher, document author and mentioned/contact person can differ. A received copy reflects the last successful sync, not necessarily the current remote state. Missing matches and partial coverage do not prove that information does not exist.
5. Continue with a follow-up on the same screen or select another model for the next answer. **Stop generation** cancels current work; **New question** clears the conversation. Errors leave the question available to edit/retry.

Conversation and evidence exist only on the current screen: leaving it, opening Settings, switching away from the browser tab, refreshing or going Back/Forward clears them and cancels pending generation. There is no saved chat history. Public model originals remain shared; app registration and execution caches are separate. Questions/documents are not sent to an external AI.

Direct tools read UTF text files and current collected bodies for eligible non-filesystem sources. Binary/unreadable files are reported as unavailable; received binary files are not automatically converted. A search stops between files after5000attempts,32MiB of processed text or6seconds; directory enumeration has a separate bound. A file read uses at most2MiB, and each turn permits at most12tool calls in8rounds. Results and model input are also bounded. Refine the folder/file/topic when a limit or insufficient evidence is reported. Model answers can be mistaken; inspect the excerpts for consequential decisions.

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
