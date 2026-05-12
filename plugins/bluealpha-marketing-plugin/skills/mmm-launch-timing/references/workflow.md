# MMM Launch Timing — Detailed Workflow

The job: answer the question every marketer asks before a launch — *"if I turn this on now, when do I actually see it?"* — using the MMM's learned adstock decay and saturation curves. Produce a week-by-week impact ramp per channel, plus a clear time-to-peak / half-life / steady-state estimate so the user can plan reporting, attribution windows, and stakeholder expectations.

This skill exists because the MMM knows the answer and the dashboard doesn't surface it well. Adstock half-lives encode how long each channel's effect lingers — but a marketer asking "when do I see the lift" doesn't want to read a Hill function. They want a week-by-week chart.

## Phase 0: Frame the Question

There are two flavors of "when will I see impact." Get the right one before calculating.

### Flavor A — New launch / activate from zero
The channel is currently at $0 (or near-zero) spend and the user is turning it on. The relevant question: how fast does the first dollar's effect accumulate, and when does the channel hit steady-state impact at the target spend level?

### Flavor B — Spend change on an active channel
The channel is already on. The user is bumping spend up or down. The relevant question: how long until the channel's contribution shifts to its new steady-state, and what does the transition look like week-by-week?

Confirm the flavor and gather:
- **Channel(s)** — which channel(s) are changing
- **From spend** — current weekly spend (zero for new launches)
- **To spend** — target weekly spend
- **Launch week** — for calendar mapping

## Phase 1: Pull Adstock Parameters

```
get_adstock_parameters(model=<kpi_name>, channels=[<channel_list>])
```

Returns the carry-over decay rate (commonly alpha) per channel, plus the half-life — the number of weeks for a single spend pulse's effect to decay by half. Capture per channel:

- **Half-life** — weeks until 50% of one week's effect remains
- **Decay alpha** — the underlying geometric decay parameter
- **Approximate effective duration** — weeks until 95% of effect has decayed (≈ 4-5 half-lives)

Translate to plain English brackets for marketer reporting:

| Half-life | Bucket | Read |
|---|---|---|
| **< 1 week** | Same-week response | Effect shows up in days. Paid Search and direct-response Display typically live here. |
| **1-2 weeks** | Fast | Most paid social falls here. The first 2 weeks of a launch see 60-80% of steady-state. |
| **2-4 weeks** | Medium | YouTube and upper-funnel Display. Steady-state in roughly 8-12 weeks. |
| **> 4 weeks** | Slow | Brand TV, podcast, OOH. Steady-state takes a quarter or more. |

If the model's adstock for a channel doesn't match category intuition (e.g., Paid Search showing a 4-week half-life), surface it — usually means the channel is conflated with another in the decomposition. Recommend `mmm-health-check` before fully trusting the timing read.

## Phase 2: Pull Saturation Curves

```
get_raw_saturation_curves(model=<kpi_name>, channels=[<channel_list>])
get_reconciled_response_curves(model=<kpi_name>, period="week", top_n=null)
```

The adstock alone tells you the *temporal shape* of the response. The saturation curve tells you the *magnitude* at the target spend level. Multiply them.

For each channel and the target spend level:
- **Steady-state weekly incremental KPI** — read off the saturation curve at the target weekly spend. This is what the channel contributes per week once fully ramped.
- **Steady-state weekly revenue** — multiply by per-channel RPK from `get_reconciled_overview`.

For Flavor B (active channel changing spend), do this twice — at the current and at the target spend — so the delta is clean.

## Phase 3: Build the Ramp

The standard geometric adstock model implies that for a sustained spend change starting at week 0:

> Week-t fraction of steady-state ≈ 1 − alpha^(t+1)

Where alpha is the decay rate (alpha ≈ 0.5 → half-life of ~1 week, alpha ≈ 0.85 → half-life of ~4 weeks, etc.). Compute the fraction-of-steady-state per week for the first 12 weeks per channel.

Then multiply by the steady-state revenue from Phase 2 to get the **weekly incremental revenue ramp**.

For Flavor B, the formula is:
> Week-t revenue ≈ old_steady_state × alpha^(t+1) + new_steady_state × (1 − alpha^(t+1))

Present per channel:

| Week | Fraction of steady-state | Incremental weekly revenue |
|---|---|---|
| 1 | 50% | $X |
| 2 | 75% | $Y |
| 3 | 87% | $Z |
| 4 | 94% | … |
| 6 | 98% | … |
| 8 | 99% | … |

And the headline numbers:
- **Time to 50% (half-life)** — week N
- **Time to 80%** — week N
- **Time to 95% (steady-state)** — week N
- **Steady-state weekly revenue** — $Y

## Phase 4: Cross-Check Against History

A model-implied ramp is only as good as the model. Spot-check by pulling the actual weekly contributions for the channel in a comparable historical period:

```
get_raw_weekly_contributions(model=<kpi_name>, channels=[<channel>], last_n_weeks=26)
```

Look at any past period where the channel changed spend materially (Phase 0's `from spend` is roughly the historical baseline you're looking for a deviation from). Did the actual contribution ramp on the same timescale the model now predicts? If yes, trust the projection. If actual ramp was substantially faster or slower, the model's adstock is mis-calibrated and the projection should carry a "history disagrees by X weeks" caveat.

## Phase 5: The Combined Story

For each channel:

> *"YouTube. You're moving from $0 to $50K/week starting next Monday. The model's adstock half-life on this channel is 2.1 weeks, so you'll see roughly 50% of the steady-state lift after 2 weeks, 80% by week 5, and full effect (95%) around week 9. At $50K/week, steady-state means roughly $180K/week in incremental revenue. So your first week incremental is around $90K, ramping to $180K by Q2."*

Compare channels side-by-side when multiple are launching:

| Channel | To spend | Steady-state $/week | Week-1 contribution | Week-4 contribution | Week-8 contribution | Half-life |
|---|---|---|---|---|---|---|
| YouTube | $50K | $180K | $90K | $158K | $176K | 2.1 wk |
| Paid Search | $30K | $90K | $81K | $89K | $90K | 0.4 wk |
| TV | $200K | $300K | $60K | $187K | $282K | 4.5 wk |

## Phase 6: Reporting Implications

The user is going to be reporting up on this launch. Translate the timing read into stakeholder language:

1. **The "what should we see in week 1 report" answer** — first-week contribution per channel
2. **The "when is the new mix fully baked in" answer** — week of 95% steady-state
3. **The right comparison window** — never compare the first 4 weeks of a slow channel against pre-launch; you'll undercount. The right comparison is a window starting at least one half-life into the launch.
4. **The right attribution window** — if a click-attributed channel reports a 1-week impact and the MMM says 4 weeks, the platform is undercounting carry-over revenue. Note this for the user's reporting.

## Phase 7: Output

Deliver to the user:

1. **Per-channel headline triplet** — half-life, time to 80%, time to 95%
2. **The weekly ramp table** (8-12 weeks per channel)
3. **Side-by-side channel comparison** if multiple channels are launching
4. **The plain-English narrative** for each channel
5. **Reporting implications** — what to tell stakeholders to expect in week 1, week 4, week 8
6. **History-check note** — does the model's adstock match what's observable in past spend changes?

## Inputs to Ask For

1. **Model / KPI** — which model (required)
2. **Channel(s)** — which channel(s) the launch involves (required)
3. **From / To spend** — current and target weekly spend (required; "0" is valid for from)
4. **Launch week** — for calendar mapping in the output (optional; default: next Monday)
5. **Reporting cadence** — weekly, biweekly, monthly — to align the output to the user's review rhythm (optional)

## Important Notes

- **Adstock geometry is a simplification.** Real-world response can be more S-shaped (slow start, fast middle, plateau) or more spike-then-decay. The geometric assumption is the model's best fit but won't match a campaign whose creative ramps in (more S-shaped than geometric). Flag this when the user is launching with phased creative rollout.
- **The first dollar of a brand-new channel may not behave like the model predicts.** Cold-start effects (audience seeding, algorithm learning) often delay the response by 1-2 weeks beyond the model's prediction. Add a "+1-2 weeks for first-launch friction" caveat for Flavor A on any channel the account has never run before.
- **Big shifts violate the linear-ramp assumption.** If the spend change moves the channel across a different region of the saturation curve, the simple geometric ramp under-estimates the curvature. For shifts >50% of historical max, recommend Phase 4 history check more aggressively and consider running `mmm-budget-reallocator` for a model-based projection instead of the closed-form ramp.
- **Don't promise the steady-state number to a CFO.** Steady-state is the model's expected long-run value. The credible interval at the target spend can be wide (especially for unfamiliar spend levels). State the range, not just the point estimate.
- **The right next step** for a launch this skill projects: set up the incrementality test runner with a holdout in the same window. The MMM gives the prediction; the test gives the causal confirmation.
