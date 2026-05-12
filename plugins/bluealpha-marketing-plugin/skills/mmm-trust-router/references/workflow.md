# MMM Trust Router — Detailed Workflow

The job: for each channel in the model, decide whether the user can act on the MMM directly, needs to validate with an incrementality test first, or shouldn't be making MMM-based decisions on that channel at all. This is the answer to "which channels can I trust?" — and it's different from `mmm-health-check`, which grades the whole model. A B-grade model can still have channels you trust fully, and an A-grade model can have a single channel the data can't speak to.

This skill exists because every MMM conversation eventually arrives at the same question — *"do I actually need to test this, or can I just move the money?"* — and the answer is per-channel.

## The Three Buckets

| Route | Meaning | Action |
|---|---|---|
| **Trust MMM** | Data influence is high, posterior CIs are tight, the channel sits inside the spend range the model has seen, and there's no confound channel. | Act directly on MMM recommendations. Reallocations, ramp plans, deep-dive verdicts on this channel are decision-grade. |
| **Validate first** | The model has an opinion but it's not strong enough to bet large on. Wide CIs, moderate data influence, or a proposed move that crosses outside the training range. | Run an incrementality test before any meaningful spend change. Hand off the channel + expected lift to `incrementality-test-runner` as the test prior. |
| **Model insufficient** | The model didn't get enough signal during training to say anything credible about this channel. Prior dominance, flat training-period spend, or a perfectly correlated confound channel. | Don't act on MMM output for this channel. Either run a structured spend test to generate signal, or remove the channel from MMM-driven decisions until next training cycle. |

## Phase 0: Load Model and Anchor on Current State

```
list_models()
get_model_summary(model=<kpi_name>)
query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
```

Capture the channel list, training period bounds, and current per-channel weekly spend. The current spend is critical — the "is this recommendation inside or outside the training range" check needs to compare to historical min/max spend per channel.

## Phase 1: Compute the Six Confidence Inputs

For each channel, gather the six signals that drive the routing decision.

### Input 1 — Credible Interval Width

```
get_raw_channel_roi(model=<kpi_name>, credible_interval=0.9)
get_marginal_roi(model=<kpi_name>, credible_interval=0.9)
```

For both average and marginal ROI, compute the relative CI width:

> relative_CI_width = (high − low) / median

| Relative CI width | Confidence | Read |
|---|---|---|
| **< 0.4** | High | Posterior is tight. The estimate is well-identified. |
| **0.4 - 0.8** | Medium | Some uncertainty, but actionable for moderate shifts. |
| **> 0.8** | Low | Estimate is wide. A 90% CI of "between 1.5x and 4.2x ROI" is not a decision-grade number. |

A channel with high relative CI on mROI but tight CI on average ROI usually means the channel has been run at a stable spend level — the average is well-known, the marginal is not. That's a "validate first" pattern.

### Input 2 — Prior-Posterior Overlap

```
get_prior_posterior_comparison(model=<kpi_name>, credible_interval=0.9)
```

Per channel, capture the overlap coefficient and data influence score. High overlap = data didn't move the estimate = the model is returning the prior.

| Overlap coefficient | Confidence | Read |
|---|---|---|
| **< 0.3** | High | The data substantially moved the estimate away from the prior. |
| **0.3 - 0.6** | Medium | Prior and data both contributing. |
| **> 0.6** | Low | The posterior is essentially the prior. Whatever the model "says" about this channel is mostly what was assumed. |

Pull the priors too — `get_channel_priors` — to surface what the assumption was for any low-confidence channel. Informative narrow priors + low data influence = "we got back exactly what we put in" and that's the worst case.

### Input 3 — Training-Period Spend Variation

```
get_raw_weekly_contributions(model=<kpi_name>, channels=[<channel>], last_n_weeks=null)
```

For each channel, pull the full training-period weekly spend history. Compute:

- **Spend coefficient of variation** = stdev(weekly_spend) / mean(weekly_spend)
- **Number of distinct spend levels** (rough bins, e.g. ±20% buckets)
- **Min and max weekly spend** in training

| Spend CV | Confidence | Read |
|---|---|---|
| **> 0.4** | High | Spend varied meaningfully during training. The model has data points across a range of spend levels — it can identify the response curve. |
| **0.2 - 0.4** | Medium | Some variation but mostly flat. Saturation curve in particular is loosely identified. |
| **< 0.2** | Low | Spend was nearly constant during training. The model *cannot* learn the response curve from this — anything it claims about marginal response is extrapolation. |

This is the most common reason a channel ends up in "Model insufficient." Flat training-period spend physically cannot identify a response function.

### Input 4 — Confound / Correlation with Other Channels

```
get_reconciled_channel_contributions(model=<kpi_name>, last_n_weeks=null, top_n=null)
```

Compute pairwise Pearson correlations between each channel's weekly contribution and every other channel's weekly spend (and contribution). For each channel, the relevant signal is its highest pairwise correlation:

| Max pairwise correlation with another channel | Confidence | Read |
|---|---|---|
| **< 0.5** | High | Channel moves independently. Its decomposition is identifiable. |
| **0.5 - 0.8** | Medium | Partial confound. Aggregate ROI of the channel + confound pair is reliable; individual splits are loose. |
| **> 0.8** | Low | The channel is essentially indistinguishable from the confound. The per-channel attribution is not identifiable — the model is making an arbitrary split between two perfectly correlated signals. |

When a channel scores Low here, name the confound partner in the output. The user needs to know *which* channel they're confounded with so they can decide whether to break the correlation (e.g., flight one without the other) or merge the two channels in the model.

### Input 5 — Operating Point Inside Training Range

For each channel:
- Current weekly spend (from Phase 0)
- Min and max weekly spend observed in training (from Input 3)

| Operating point | Confidence | Read |
|---|---|---|
| **Inside training range** | High | The model has seen this spend level. Predictions interpolate. |
| **Slightly above max or below min (within 25%)** | Medium | Model is mildly extrapolating but stays close to seen territory. |
| **More than 25% above max or below min** | Low | Heavy extrapolation. The saturation curve at this point is shaped entirely by the Hill prior, not by data. |

This input is conditional on the proposed action. If the user is asking "can I trust the MMM" without a specific shift in mind, use the current operating point. If a proposed shift is on the table, recompute for the target spend level. The trust routing can differ — a channel may be "Trust MMM" at current spend but "Validate first" if you want to triple it.

### Input 6 — Adstock Parameter Convergence

```
get_adstock_parameters(model=<kpi_name>, channels=[<channel>])
```

The adstock decay parameter has its own posterior. If the half-life CI is wide, the model didn't pin down how long the channel's effect lingers, and any spend-change projection inherits that uncertainty.

Compute relative CI width on the half-life:

> relative_HL_CI_width = (high − low) / median

| Half-life relative CI width | Confidence |
|---|---|
| **< 0.5** | High |
| **0.5 - 1.0** | Medium |
| **> 1.0** | Low |

A low-confidence adstock estimate doesn't disqualify a channel by itself — average ROI may still be well-identified — but it does block confidence in any launch-timing or ramp recommendation.

## Phase 2: Compute the Routing Decision

For each channel, the six inputs each rate as High / Medium / Low confidence. Combine into a routing decision:

```
If ANY of (CI width, prior overlap, spend CV, channel correlation) is Low:
    → "Model insufficient"
Elif TWO OR MORE of the six inputs are Low:
    → "Model insufficient"
Elif ANY input is Low OR THREE OR MORE inputs are Medium:
    → "Validate first"
Elif ALL inputs are High OR (5 High + 1 Medium):
    → "Trust MMM"
Else:
    → "Validate first"
```

The asymmetry is intentional. Any single Low signal on the "core four" (CI width, prior overlap, spend CV, channel correlation) is enough to push a channel out of "Trust MMM." These four are the foundations — if any one fails, the others don't compensate.

Compute a 0–1 confidence score per channel as the count-weighted average of input scores (High = 1.0, Medium = 0.5, Low = 0.0) for the final ranking.

## Phase 3: The Routed Channel Table

The headline deliverable:

| Channel | Route | Confidence | Why | Recommended action |
|---|---|---|---|---|
| Google Search | Trust MMM | 0.92 | All inputs High | Act on reallocator output directly. |
| Meta | Trust MMM | 0.78 | CI medium, others high | Act, but cap shifts at 20% per cycle. |
| YouTube | Validate first | 0.58 | mROI CI wide; current spend at top of training range | Run geo holdout before scaling above $50K/wk. |
| TikTok | Validate first | 0.42 | Spend CV medium, prior partially driving | Run a low-cost test to confirm direction before any shift > 15%. |
| Connected TV | Model insufficient | 0.18 | Flat training-period spend (CV < 0.1) | Pre-test action: 4-week structured spend ramp to generate signal. |
| Display | Model insufficient | 0.22 | Correlation with Programmatic Video = 0.91 | Can't separate from Programmatic Video. Recommend merging the channels in the next model build, or flighting them independently for one training cycle. |

For each row, include a one-sentence reason citing the specific failing inputs. The user needs to know *why* a channel routed where it did — handing them a routing without the rationale invites pushback.

## Phase 4: Action Recommendations by Bucket

### Trust MMM channels
1. Hand these channels' recommendations directly to `mmm-budget-reallocator` for execution.
2. The `mmm-launch-timing` skill's projections are reliable for these channels.
3. The `mmm-channel-deep-dive` verdicts are decision-grade.

### Validate first channels
1. For each channel, pull the MMM's predicted lift at the proposed new spend level — this becomes the test prior.
2. Hand off to `incrementality-test-runner` with:
   - Channel under test
   - Expected lift (from MMM's response curve at the new spend)
   - Minimum detectable effect = MMM expected lift × 0.5 (test needs to detect at half the model's prediction)
   - Test duration suggestion based on the channel's adstock half-life (typically 4 + 2× half-life weeks)
3. Pause any reallocation onto this channel until the test resolves.

### Model insufficient channels
1. **If due to flat training spend:** recommend a structured spend test — 4-6 weeks of materially different spend levels (e.g., 50%, 100%, 150% of historical) to generate identification signal. Then retrain.
2. **If due to confound:** recommend flighting one of the correlated pair independently for one training cycle, OR merging the two channels into a single channel in the next model build.
3. **If due to prior dominance with no path to fix:** the user should not be making MMM-based decisions on this channel until they can generate signal. Recommend platform-attribution data + judgment as the interim approach.

## Phase 5: Conditional Re-Routing

If the user is asking the routing question in the context of a specific proposed shift, re-run Input 5 (operating point) against the target spend level for the affected channels. A channel can route differently for different shift magnitudes:

- "Move Meta +10%" → all six inputs evaluate at near-current spend → likely "Trust MMM"
- "Move Meta +50%" → operating point now outside training range → may downgrade to "Validate first"

Show both the unconditional routing (current spend) AND the conditional routing (proposed spend) when relevant. The user often wants to know "if I just stay near current spend, can I trust this?" separately from "if I make this bold move, can I trust the projection?"

## Phase 6: Output

Deliver to the user:

1. **The routed channel table** with bucket, confidence score, reason, and recommended action per channel
2. **The "Trust MMM" list** — channels where reallocator/launch-timing/deep-dive outputs can be acted on directly
3. **The "Validate first" list** — channels needing tests, with pre-staged test priors per channel (channel, expected lift, suggested test duration)
4. **The "Model insufficient" list** — channels to exclude from MMM-driven decisions, with the path to fix (structured spend test, channel merge, or wait for next retraining window)
5. **Conditional re-routing** if a specific proposed shift is under discussion
6. **A one-paragraph summary** for the marketing leader: how much of the paid mix is decision-grade right now, how much needs validation, and what's blocked entirely

## Inputs to Ask For

1. **Model / KPI** — which model (required; use `list_models` if unknown)
2. **Proposed shift** — if asking the question in the context of a specific budget change, the from-to spend levels (optional)
3. **Test budget** — for the validate-first hand-off, what budget is available for the test (optional; default: ask for it on hand-off)
4. **Stakeholder audience** — operator (full table) vs. leader (paragraph summary only) (optional)

## Important Notes

- **The four "core" inputs are veto power.** A Low on CI width, prior overlap, spend CV, or channel correlation is enough to disqualify a channel from "Trust MMM" no matter what the other inputs say. These four are about whether the underlying decomposition is identifiable. The other two (operating point, adstock) are about whether a specific projection is reliable — narrower in scope.
- **"Trust MMM" is a license to act, not a guarantee.** Even a high-confidence channel can have outlier weeks, creative changes, or external market shifts the model hasn't ingested. Trust MMM means act without first running a test; it doesn't mean stop watching.
- **"Validate first" is the most common route.** Production MMMs typically route 30-50% of channels here. That's normal. Marketers used to "the MMM says X, ship it" cultures often need this framing — the MMM is one input; some channels demand causal confirmation before a budget bet.
- **"Model insufficient" channels need an intervention, not a recommendation.** If you find yourself routing a channel here repeatedly across quarterly check-ins, the fix is structural — generate spend variation, break a confound, or merge channels — not "run another test."
- **Re-run this skill after any major spend change.** Confidence routings reflect what the model has seen. A new channel that's been flighting for three weeks may move from "Model insufficient" to "Validate first" once enough variation is in the training data.
- **Hand-off pattern:** trust-router → reallocator (Trust MMM) → execution; trust-router → incrementality-test-runner (Validate first) → reallocator after test resolves; trust-router → spend-ramp planning (Model insufficient) → wait for next training cycle.
