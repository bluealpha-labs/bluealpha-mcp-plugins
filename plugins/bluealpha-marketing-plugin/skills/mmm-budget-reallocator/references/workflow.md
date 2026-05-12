# MMM Budget Reallocator — Detailed Workflow

The job: take a proposed budget change (or generate one) and tell the user — before they execute — what the model thinks happens to revenue, with credible intervals attached. This is the closed-loop "should I shift spend from A to B?" workflow that sits between the MMM and the activation layer.

## Phase 0: Establish the Model

You can't simulate against a model that isn't loaded.

1. **Confirm which model to use:**
   ```
   list_models()
   ```
   Each row shows a KPI name (e.g. "Net New Customers", "Revenue") and `is_sandbox`. If the user has only one production model, default to it. If multiple, ask which KPI is the planning target.

2. **Pull the model summary** to confirm scope:
   ```
   get_model_summary(model=<kpi_name>)
   ```
   Note the channel list, training time range, and any convergence flags. If R-hat values are bad or the model is stale (training period ends >8 weeks ago), warn the user — the reallocation projection inherits the model's flaws.

3. **Get the baseline performance picture:**
   ```
   query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
   ```
   This is the current spend mix and per-channel ROI. Save these spend levels — they're the "before" state for the reallocation table.

## Phase 1: Decide What to Reallocate

Two modes. Pick the one that matches the user's question.

### Mode A — User-Specified Shift

The user already has a proposed change. Examples:
- *"Move $50K/week from Meta to YouTube."*
- *"What if we cut TikTok by 30%?"*
- *"Bump up Google Search by $20K and pull it from Display."*

Translate to a `proposed_budgets` dict. Start with the current per-channel weekly spend from Phase 0, apply the user's deltas, and confirm the dollar amounts back to the user before simulating. Always show the proposed dict before running the simulation — silent reinterpretation of the user's ask is how you get the wrong answer.

### Mode B — Recommend a Shift

The user wants the model to suggest where to move money. The right primary signal is marginal ROI.

1. **Pull marginal ROI:**
   ```
   get_marginal_roi(model=<kpi_name>)
   ```
   Channels with **high mROI** have headroom — the next dollar earns more than the average dollar. Channels with **low mROI** are saturated — the next dollar earns less. Order channels by mROI descending.

2. **Cross-check with average ROI:**
   ```
   get_raw_channel_roi(model=<kpi_name>)
   ```
   A channel with high average ROI but low mROI is your classic "great channel but tapped out" pattern. A channel with low average ROI but high mROI is "looks bad but actually under-funded." Flag both patterns explicitly when you present the recommendation.

3. **Construct the reallocation:**
   - **Source** (cut): channels with the lowest mROI in the bottom tercile.
   - **Sink** (increase): channels with the highest mROI that aren't already saturated.
   - **Magnitude:** start conservative — propose a 10-20% shift on the largest-spend low-mROI channel. Larger shifts move spend into untested zones of the response curve; the projection's credible intervals will widen accordingly.

4. **Present the proposed budget table** to the user BEFORE simulating. Get explicit confirmation. The user should see:

   | Channel | Current weekly spend | Proposed weekly spend | Delta | Reason |
   |---|---|---|---|---|
   | Meta   | $120K | $96K  | -$24K | mROI bottom tercile |
   | YouTube | $40K | $64K  | +$24K | mROI top tercile, headroom on saturation curve |
   | (others) | unchanged | unchanged | $0 | |

## Phase 2: Simulate

Once the proposed budget is confirmed:

```
simulate_budget_reallocation(
  model=<kpi_name>,
  proposed_budgets={"Meta": 96000, "YouTube": 64000, ...},
  n_weeks=4,
  credible_interval=0.9
)
```

The result is the model's projection of incremental KPI / revenue under the new mix over the projection horizon, with credible intervals.

**Decision rules for the projection:**

- If the projected lift is **positive and the credible interval is entirely above zero** → the model has high confidence in the move. Recommend execution.
- If the projected lift is **positive but the credible interval crosses zero** → the move is favorable in expectation but the data isn't strong enough to call it. Recommend a smaller test shift or running the change with an incrementality test attached.
- If the projected lift is **negative** → the user's proposed shift moves money in the wrong direction per the model. Push back. Show the marginal ROI ordering as the alternative.
- If the projected lift is **trivially small** (under 1% of total revenue) → the reallocation isn't worth the operational cost of changing campaigns. Tell the user.

## Phase 3: Sensitivity Check

A single point estimate isn't enough. Re-run the simulation at two more magnitudes to map the response.

1. **Half the shift** — propose a budget dict that moves half as much money in the same direction. If the lift roughly halves, the model is behaving linearly in this zone. If lift collapses to near-zero, the original shift was sitting on a non-linear part of the saturation curve and may be sensitive to small changes.
2. **Double the shift** (if feasible given budget realities) — does the projected lift continue scaling or does it flatten? Flat → you've hit the saturation point of the sink channel. Halve the proposal.
3. **Reverse direction** as a sanity check — if you flip the source and sink, the model should project a clear loss. If it doesn't, the channels are too similar in the model's eyes (degenerate decomposition) and the reallocation isn't meaningful.

Present a 3-row sensitivity table:

| Scenario | Source delta | Sink delta | Projected revenue lift | 90% CI |
|---|---|---|---|---|
| Half shift | -$12K | +$12K | +$X | [low, high] |
| Proposed shift | -$24K | +$24K | +$Y | [low, high] |
| Double shift | -$48K | +$48K | +$Z | [low, high] |

## Phase 4: Translate to Execution

The MMM thinks in channels. The activation layer thinks in campaigns. Translate before handing off.

1. For each channel in the proposed shift, identify the campaigns that roll up into it. The user knows their own taxonomy — ask them to confirm: "Meta in the MMM = Meta Prospecting + Meta Retargeting + Meta Brand Awareness in Google Ads/Ads Manager. Correct?"
2. Distribute the channel-level delta across campaigns. Default heuristic: weight by current spend share. If the user wants a specific campaign to absorb the change, honor that — but note it in the output.
3. **Do not execute the change.** This skill stops at the recommendation. Execution routes through the activation layer.

## Phase 5: Output

Deliver to the user:

1. **The proposed reallocation table** with reasons per row
2. **The simulation result** — point estimate + 90% credible interval, in KPI units AND revenue if RPK is set
3. **The sensitivity table** (3 scenarios)
4. **A single recommendation line** — execute, run smaller, run with test, or reject — with one-sentence rationale
5. **Campaign-level translation** for the execution hand-off

## Inputs to Ask For

1. **Model / KPI** — which model to plan against (required; use `list_models` if unknown)
2. **Proposed change OR direction** — user-specified shift or "recommend something" (required)
3. **Projection horizon** — default 4 weeks; longer horizons widen credible intervals (optional)
4. **Total budget constraint** — is this a pure reallocation (sum stays constant), an absolute increase, or an absolute decrease? (optional; default: pure reallocation)
5. **Channel taxonomy mapping** — if the MMM channels don't 1:1 with the campaign taxonomy (optional)

## Important Notes

- **The model is not reality.** The projection is the model's best guess given everything it's seen. If the proposed budget moves into a zone the model has *never* observed (e.g., 3x the historical max spend on a channel), the credible intervals will be wide and the point estimate is extrapolation. Flag this when it happens — check the saturation curve for the sink channel and warn if the proposed spend is outside the training-data spend range.
- **mROI per-channel scaling matters.** The `get_marginal_roi` response includes an `rpk` sidecar — if it shows a fallback (scale=1.0), the channel's KPI-to-revenue conversion isn't registered and the mROI ordering may misrank channels with very different revenue-per-conversion. Surface this caveat to the user.
- **Prior-dominated channels are unreliable in simulation.** If a channel's posterior is just a copy of its prior (see `mmm-health-check`), the simulator is doing math on an assumption rather than learned dynamics. Recommend running `mmm-health-check` first when planning a large reallocation onto or off a channel flagged as prior-dominated.
- **Don't reallocate based on a single simulation.** The sensitivity check in Phase 3 exists for a reason. If a 50% smaller shift produces 90% of the projected lift, the user should ship the smaller shift first.
- **Reconciled vs raw.** The `query_reconciled_performance_table` numbers are reconciled to the dashboard. The simulator uses the raw posterior. Small gaps between them are normal — call them out if they exceed ~10%.
- **No execution from this skill.** This skill produces a recommendation. The user's campaign-management workflow does the actual reallocation.
