Sessions Dashboard summarizes usage recorded by your connected AI sources. Use it to compare activity over time and understand estimated costs.

## Read a period

1. Open [Sessions Dashboard](/sessions-dashboard).
2. Choose **All** or one source profile, then a history range or start/end dates.
3. Read the summary and switch the history metric between tokens and cost.
4. Use **By Source**, **By Model**, or **By Project** to inspect composition within that scope.

The selected time zone controls date boundaries and day, week, or month grouping. Changing it can move an activity into a different displayed period; it does not rewrite the original record. See [Settings](/help/settings).

## Understand costs and coverage

Costs are estimates from locally recorded usage and available pricing evidence. They are not your provider's invoice or a guarantee of billed spend.

**Partial** means only part of the selected usage can be priced. An unavailable cost is not zero, and a missing token history does not mean there was no work. Read the displayed coverage notices alongside the numbers. Changing a filter may leave no matching usage even when other periods or sources contain records.

## What Project means

**By Project** includes ordinary work Sessions and their work subsessions. It uses the recorded Git root or launch-folder attribution, including the home folder when applicable. Ordinary work without attribution appears as **Unassigned project** (`프로젝트 미지정`).

Analysis and Maintenance usage is excluded from Project rows, totals, and share percentages. Eligible usage from those activities remains in overall totals, history, and Source/Model composition. Those totals can therefore differ from Project totals.

Project attribution is preserved from the usage record. It is not necessarily the same grouping as the working paths in Sessions or the recorded launch folders in Chart; a shorter displayed path does not reassign past usage.

## Coverage and updates

Check the selected source, dates, and time zone first. Confirm the source is registered and readable in [Settings](/help/settings), then use Session synchronization if needed. Reopen the dashboard after collection. If usage exists but a metric is unavailable, collecting again cannot guarantee missing pricing or usage evidence will appear.

LocalBrain reads Codex usage from the registered profile's original `.jsonl` and `.jsonl.zst` Session files. Compressed history is collected directly; you do not need to extract it. Check both forms before treating an original as missing. If neither form is available, already collected usage remains in the database. Missing usage that was never collected cannot be reconstructed from the conversation list or a total-token counter; that recovery needs the original files or a backup.

After synchronization, dashboard usage and normalized Codex conversation details are read from the local database. Compressed originals are decoded during synchronization, without creating extracted transcript files. If `name.jsonl` and `name.jsonl.zst` are both files in the same directory, only `name.jsonl` is collected; their contents are not merged or compared for freshness. Switching between these two forms preserves the same native Session and its existing pins and frozen Usage facts. This pairing rule applies within each registered source and does not combine personal and company profiles.

Continue with [Sessions](/help/sessions) to read the conversations behind the activity. [Settings](/help/settings) explains source registration and synchronization.
