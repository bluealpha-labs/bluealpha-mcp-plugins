# MMM Channel Deep Dive — Detailed Workflow

The job: produce the single-channel report card. Everything the MMM knows about one channel — average ROI, marginal ROI, where it sits on the saturation curve, how long its effect lingers, how stable its contribution is over time, and how much of the answer is data vs. prior assumption. This is the artifact a channel owner brings to a quarterly review when defending or repositioning their budget.

## Phase 0: Scope

1. **Get the channel and model:**
   ```
   list_models()
   get_model_summary(model=<kpi_name>)
   ```
   Confirm the requested channel name exists in the model's channel list. Channel names in MMMs are sometimes more granular than user terminology (e.g., "Meta Prospecting" vs "Meta"). If there's ambiguity, ask the user which to deep-dive on.

2. **Anchor on current state:**
   ```
   query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
   ```
   Pull the row for the target channel: current weekly spend, revenue, ROI, share of paid revenue. This is the "starting point" for the rest of the analysis.

## Phase 1: ROI Picture

Both kinds. Average ROI tells you how the channel has performed in aggregate; marginal ROI tells you what the next dollar is worth.

```
get_raw_channel_roi(model=<kpi_name>, channels=[<channel>], credible_interval=0.9)
get_marginal_roi(model=<kpi_name>, channels=[<channel>], credible_interval=0.9)
```

Report both with their 90% credible intervals:

| Metric | Median | 90% CI |
|---|---|---|
| Average ROI | $X.XX | [low, high] |
| Marginal ROI | $X.XX | [low, high] |

Compare the two. The pattern reveals where the channel sits:

| Pattern | Interpretation |
|---|---|
| **mROI ≈ average ROI** | Channel is in linear region. Not yet diminishing. |
| **mROI < average ROI** | Channel is in diminishing-returns region. Adding spend earns less than the typical dollar. |
| **mROI >> average ROI** | Suspicious — usually means the channel is small enough that the prior dominates the mROI estimate. Check `mmm-health-check` for this channel before trusting. |
| **mROI < 1** | The next dollar loses money. Cut signal. |
| **mROI > 5** | The next dollar is highly productive. Scale signal — but verify with an incrementality test before a large move. |

Check the `rpk` sidecar on the mROI response. If `scale=1.0` fallback, note the channel's revenue conversion isn't registered and the dollar-denominated mROI may be biased.

## Phase 2: Saturation Position

```
get_raw_saturation_curves(model=<kpi_name>, channels=[<channel>])
```

Capture:
- **Current saturation %** — where the channel sits on its curve at current spend
- **Half-saturation EC** — the spend level at which the channel is 50% saturated
- **Hill slope** — how sharply the curve transitions from steep to flat

Translate to plain language:
- *"At $120K/week, Meta is at 78% saturation. Half-saturation point is $52K/week. The curve flattens sharply past $100K — most of the available lift is already captured."*

Project response at three operating points (current, +25%, +50%):
```
get_reconciled_response_curves(model=<kpi_name>, period="week", top_n=null)
```
Filter to the target channel from the result. For each operating point, report projected incremental KPI and (if RPK is set) projected weekly revenue.

## Phase 3: Adstock / Decay

```
get_adstock_parameters(model=<kpi_name>, channels=[<channel>])
```

Capture:
- **Half-life** — weeks until 50% of a spend pulse's effect remains
- **Effective duration** — weeks until 95% has decayed (typically 4-5 half-lives)
- **Decay alpha** — the underlying parameter

Translate:
- *"Adstock half-life is 2.1 weeks. A spend pulse this week is still contributing meaningfully 4-6 weeks out. Steady-state on a sustained spend change takes about 9 weeks."*

If the half-life looks off for the channel's category (Paid Search should be <1 week, brand TV should be 4+ weeks, etc.), flag it as a channel-specific health concern. This often indicates the channel is conflated with another in the decomposition.

## Phase 4: Weekly Contribution History

```
get_raw_weekly_contributions(model=<kpi_name>, channels=[<channel>], last_n_weeks=26)
```

Get the channel's incremental KPI contribution week-by-week for the trailing 26 weeks. Look for:

1. **Stable contribution** — week-over-week contribution roughly tracks week-over-week spend. This is a healthy decomposition.
2. **Noisy contribution** — wild week-to-week swings that don't track spend changes. Often indicates the model is fitting noise into this channel. Note for credibility caveats.
3. **Trend** — is the channel's contribution declining, flat, or rising over the trailing window? Compare to its spend trend. Rising spend + declining contribution = the channel is fatiguing or the market is shifting. Declining spend + rising contribution per dollar = creative or audience improvements paying off.
4. **Step changes** — sharp jumps in contribution that correspond to known events (creative refresh, new audience, market expansion). Validate the model picked up the right step.

Summarize in a short prose paragraph plus a trend line description.

## Phase 5: Trust Diagnostics

How much of the above is data and how much is the prior?

```
get_prior_posterior_comparison(model=<kpi_name>, channels=[<channel>], credible_interval=0.9)
get_channel_priors(model=<kpi_name>, channels=[<channel>])
```

For each parameter on this channel (ROI prior, adstock alpha, half-saturation EC, Hill slope, beta effectiveness):
- **Prior median** and CI
- **Posterior median** and CI
- **Overlap coefficient** — high overlap means data didn't move the estimate
- **Data influence** — how much the posterior shifted

Bucket parameters as **data-driven**, **partially-informed**, or **prior-dominated**. Surface any prior-dominated parameter as a caveat — every downstream number on this channel that depends on that parameter inherits the caveat.

## Phase 6: The Channel Verdict

Pull it all together into a one-paragraph verdict per channel. Format:

> *"<Channel> is currently spending $X/week (Y% of paid revenue share). Average ROI is Z.Zx, but marginal ROI has fallen to W.Wx — the channel is at 78% saturation, with most of the curve's lift already captured. Adstock half-life is 2.1 weeks, so a spend change here shows up in roughly 4-6 weeks. The decomposition is data-driven on ROI and saturation parameters, but the adstock estimate is prior-influenced. Recent contribution trend is declining over the trailing 12 weeks, against rising spend — fatigue signal. Recommended action: <cut / hold / scale / test>, because <reason>."*

The verdict should land on one of four actions:

| Action | When |
|---|---|
| **Scale** | mROI is high, saturation is below 60%, contribution is stable or rising |
| **Hold** | mROI is moderate, saturation is 60-80%, no clear trend either way |
| **Cut** | mROI is below 1, OR saturation is above 90% AND average ROI has been falling |
| **Test** | Trust diagnostics are weak (prior-dominated) OR contribution is noisy — recommend an incrementality test before any spend change |

## Phase 7: Output

Deliver to the user:

1. **The current-state line** — spend, revenue, ROI, share
2. **The ROI table** — average and marginal with credible intervals, with the pattern interpretation
3. **The saturation read** — current %, half-saturation point, response projection at +25% and +50%
4. **The adstock read** — half-life, effective duration, ramp implications
5. **The 26-week contribution chart** described in prose with trend and any step changes called out
6. **The trust subtable** — which parameters are data-driven vs prior-dominated
7. **The one-paragraph verdict** with a clear cut / hold / scale / test recommendation
8. **Cross-skill recommendation** — if scaling, suggest `mmm-launch-timing` for ramp expectations; if cutting, suggest `mmm-budget-reallocator` for where to redirect; if testing, suggest the incrementality test runner

## Inputs to Ask For

1. **Model / KPI** — which model (required)
2. **Channel** — which specific channel to deep-dive on (required)
3. **History window** — default trailing 26 weeks for the contribution chart (optional)
4. **Audience** — exec verdict vs. analyst full readout (optional; default: full)

## Important Notes

- **One channel at a time.** This skill is intentionally narrow. Comparing channels is what the saturation report does. Multi-channel comparisons here dilute the deep-dive — if the user wants a comparison, hand off to `mmm-saturation-report` or `mmm-performance-digest`.
- **A prior-dominated channel produces a thin deep-dive.** If most of the channel's parameters are prior-dominated, the deep dive ends up being "the model assumed X." Be honest with the user. The action is to run more spend variation on the channel (so future training periods have signal) or to set a tighter, better-informed prior.
- **Watch for confounded pairs.** If two channels in the model move together perfectly (e.g., separately modeled Meta and Instagram, or two display partners always purchased together), the per-channel decomposition isn't reliable even though the aggregate is. Note this if the channel under review has a known confound partner.
- **The verdict is a model verdict, not a market verdict.** It reflects what the MMM thinks. If recent qualitative signals (creative win, platform algorithm change, competitor move) suggest the channel is materially different from its training-period self, the verdict needs to be adjusted by the user. Surface the trailing-window contribution chart so the user can spot recency that the model hasn't fully ingested.
- **Pair with `mmm-health-check`.** If the model's overall trust grade is B or worse, lead the deep dive with that grade. A C-grade model's channel deep-dive is best read as "what does the model want to be true" rather than "what is true."
