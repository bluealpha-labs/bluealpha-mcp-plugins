# MMM Saturation Report — Detailed Workflow

The job: turn the model's Hill saturation curves into a plain-English read on which channels are running out of runway, which still have room, and what that means for the next planning conversation. Saturation is the single most important read on whether a budget shift is going to work — and the one most often missed.

## Phase 0: Load the Model

1. **Confirm which model:**
   ```
   list_models()
   get_model_summary(model=<kpi_name>)
   ```
   Note channels and time range. Saturation diagnostics are only as good as the model's training data — if a channel scaled 5x last quarter and the model only saw the lower spend levels, the saturation curve for that channel is extrapolation past the observed range.

2. **Anchor on current spend:**
   ```
   query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
   ```
   Per-channel current weekly spend. This is the operating point that you'll mark on each saturation curve.

## Phase 1: Raw Saturation Read

The raw saturation curves are the model's view of how incremental KPI scales with spend per channel — straight from the Hill function in the posterior.

1. **Pull raw saturation curves:**
   ```
   get_raw_saturation_curves(model=<kpi_name>)
   ```
   The response includes per-channel Hill parameters (EC = half-saturation, slope) plus the **current saturation percentage** — where the channel sits on its curve today.

2. **Bucket each channel:**

   | Saturation % | Bucket | Read |
   |---|---|---|
   | **< 40%** | Headroom | Curve still steep. Adding spend gets near-linear lift. |
   | **40-70%** | Mid-curve | Returns slowing but still meaningful. Best zone for incremental tests. |
   | **70-90%** | Saturating | Sharply diminishing. Each dollar earns materially less than the last. |
   | **> 90%** | Saturated | Approaching the asymptote. Cutting spend rarely loses much revenue; adding spend rarely gains any. |

3. **Cross-reference with marginal ROI:**
   ```
   get_marginal_roi(model=<kpi_name>)
   ```
   Saturation % and mROI should agree directionally — a 90%-saturated channel should have low mROI relative to its average. If they disagree (e.g., the curve says saturated but mROI says headroom), flag it: usually means the channel has very different short-term vs steady-state response, or the rpk fallback is biasing the mROI ranking. Check the `rpk` sidecar on the mROI response.

## Phase 2: Reconciled Response Curves

The dashboard-matching reconciled response curves answer the *spend question* directly: "what happens if I put another $X into channel Y?"

1. **Pull reconciled response curves for top spenders:**
   ```
   get_reconciled_response_curves(model=<kpi_name>, period="week", top_n=5)
   ```
   This returns projected incremental KPI at different spend levels per channel. The marginal slope of this curve at the channel's current spend point IS the headroom estimate.

2. **For each top-N channel, calculate the "what does the next $X buy me" estimate** at three operating points:
   - **+10% spend:** projected incremental KPI lift
   - **+25% spend:** projected incremental KPI lift
   - **+50% spend:** projected incremental KPI lift (flag if outside the observed spend range — call out as extrapolation)

3. **Translate to revenue.** The reconciled overview's `rpk` block converts KPI units to revenue:
   ```
   get_reconciled_overview(model=<kpi_name>)
   ```
   Multiply the incremental KPI projections by per-channel RPK to surface revenue lift in dollars. This is what the planner wants to see.

## Phase 3: The Headroom Table

This is the deliverable. One row per channel, sorted by available headroom in dollars.

| Channel | Current weekly spend | Saturation % | Bucket | mROI | Headroom estimate ($/week revenue at +25% spend) | Notes |
|---|---|---|---|---|---|---|
| YouTube | $40K | 32% | Headroom | $5.40 | +$22K | Largest unsaturated channel — primary scale candidate |
| Meta    | $120K | 78% | Saturating | $1.10 | +$4K | Bottom tercile mROI — top reallocation source candidate |
| Google Search | $80K | 88% | Saturating | $0.90 | +$1K | Effectively capped at current spend |
| TikTok | $15K | 22% | Headroom | $4.80 | +$8K | Small base — verify with test before large scale |
| ... | ... | ... | ... | ... | ... | ... |

## Phase 4: Strategic Read

Don't just hand over the table. Tell the user what it means.

1. **The scaling story:** rank the top 3 channels with the most headroom by revenue (not by saturation %, which doesn't account for channel size). These are the candidates for the next spend increase.

2. **The pruning story:** rank the top 3 channels with the highest spend AND highest saturation. These are the candidates for budget cuts. Cutting from these typically loses little — the curve is flat near the top.

3. **The "verify-before-you-scale" channels:** small-base channels with high posterior headroom carry uncertainty wide. Recommend a test before a large reallocation onto them. A channel currently running $5K/week with a saturation curve that says "another $50K/week earns 10x" is the model speaking far outside what it's seen.

4. **The "model has nothing to say" channels:** any channel where the posterior is heavily prior-dominated (run `mmm-health-check` to identify these) should be excluded from the headroom recommendation. Tell the user the model doesn't have signal on these.

## Phase 5: Output

Deliver to the user:

1. **The headroom table** with all channels, sorted by available headroom in revenue
2. **A scaling triplet** — three channels to put more money into, ranked
3. **A pruning triplet** — three channels to consider cutting
4. **Verify-before-scaling list** — small-base headroom channels that need an incrementality test before a big move
5. **Excluded channels** — those without enough signal to make a saturation read on

## Inputs to Ask For

1. **Model / KPI** — which model (required; use `list_models` if unknown)
2. **Time window** — default last 4 weeks for the current-spend anchor (optional)
3. **Channels to focus on** — if the user only cares about a subset (optional; default all)

## Important Notes

- **Saturation is a model construct, not an observed quantity.** The Hill function imposed by Meridian is the model's *assumption* about how response scales. If actual behavior is more linear (cold paid channels at low-spend) or more step-function (channels with audience exhaustion), the Hill curve smooths over those dynamics. The headroom estimates inherit this assumption.
- **Saturation % depends on where the channel is on its curve, not its absolute spend.** Two channels at the same dollar level can be at completely different saturation %. Don't compare saturation % across channels expecting it to map to "this channel is bigger."
- **The curve below historical min spend is also extrapolation.** Saturation curves are most reliable inside the observed spend range. Both ends — going way above or way below — are model extrapolation. Flag when the proposed operating point is outside the training range.
- **High mROI without headroom is suspicious.** If a channel shows high marginal ROI but the saturation % is 85%+, the model is saying "this channel earns a lot at the margin" while also saying "but you can't add much more without diminishing returns." That's coherent only over a narrow window — usually means the channel is small but profitable, and the headroom in dollars is tiny.
- **Hand off to `mmm-budget-reallocator`** when the user is ready to translate the headroom read into a specific proposed shift.
- **Hand off to the incrementality test runner** when scaling onto a verify-before-you-scale channel — the model's projection there needs causal confirmation.
