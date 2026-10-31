# Source Claim Trial Operations

Use the [shared model-tool prerequisites and private storage rules](model-tools.md) before these operations.

## Operations

The separate [source-claim adapter](../source-claims-and-work-state.md#model-aware-v2-and-synthetic-adapter)
extracts historical claims, proposes scoped work bindings and lifecycle effects,
then computes reported state with a pure deterministic projector. Model-inferred
fulfillment is distinct from a source explicitly reporting completion. A completed
check does not complete its parent effort.

```bash
uv run --no-sync python scripts/evaluate-source-claims.py --describe
uv run --no-sync python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/source-claim-trial
uv run --no-sync python scripts/evaluate-source-claims.py \
  --model-root /absolute/private/models/qwen3-8b \
  --output /absolute/private/source-claim-trial --replay
```

Use the existing compatible model runtime. This is one frozen 8B/MPS-eager,
non-thinking candidate, not training or a new model installation. Twenty-eight
synthetic development histories allow at most 84 generation calls; the original
ten holdout cases allow 20 additional calls only after all development gates and
a report-bound primary semantic review. `--holdout` cannot bypass that gate.
Each call is bounded to 8,192 combined/2,048 generated tokens and 60 soft seconds.
The whole candidate allows at most 104 generation calls, including the gated
holdout allowance, and a 120-minute cumulative active-run launch gate, including model load,
verification and preflight. Reservations and elapsed time survive clean resume;
these ceilings are not a fresh allowance for a closed or exhausted candidate.
Input is never truncated.

Reference-conditioned binding receives correct claims/targets for diagnosis;
end-to-end generation must discover them from raw source. Neither technical tests
nor conditional results establish extraction quality. Completed failures replay
without generation. The owned report uses the existing 30-day inactivity rule;
changed config, corrupt/unclean state and expired trial budgets refuse reuse.
No private input argument, all-Session job, server/UI update or organization write
is added. The [owning trial Run](../../../plans/run/run-20260923-112-source-claim-extraction-and-binding-trial.md#retained-admission-disposition)
owns the frozen candidate's admission and consumed allowance. A replay or
documentation cleanup does not reopen a candidate, renew consumed calls or reset
its budget. Any new generation must remain within an existing, unexhausted
approval. This
command is an evaluation tool, not an admitted work extractor.
