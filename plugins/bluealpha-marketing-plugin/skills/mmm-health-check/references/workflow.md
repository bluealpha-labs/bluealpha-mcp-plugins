# MMM Health Check — Detailed Workflow

The job: before any budget recommendation, reallocation, or "the model says X" claim, grade the model. Identify where the data is doing the work and where the priors are. Surface convergence problems, fit gaps, prior dominance, and stale training periods. The output is a trust-grade plus a list of channels the user should treat with caution.

This skill is for data scientists and analysts who need to defend MMM outputs internally — and for marketers who want to know whether the model they're acting on actually has signal.

## Phase 0: Model Inventory

```
list_models()
get_model_summary(model=<kpi_name>)
```

From the summary, capture:
- **Channels** — full list
- **Training time range** — when does the data end?
- **Sample count** — total posterior draws
- **Convergence diagnostics** — R-hat values, divergent transitions if exposed

Flag immediately:
- Training period ends >8 weeks ago → model is stale. Recommendations will reflect old market dynamics.
- R-hat > 1.05 on any key parameter → MCMC chains haven't converged. Treat all posterior numbers with caution.
- Sample count below 1,000 effective → posterior is undersampled, credible intervals are noisy.

## Phase 1: Training Configuration

```
get_model_settings(model=<kpi_name>)
```

This returns chains, draws, warmup/burn-in, holdout strategy, and sampler tuning. Read the response for:

1. **Holdout / test strategy.** Was a holdout actually used? A model with no holdout is still useful for description but can't be validated on out-of-sample predictions. If `holdout` reports `not_stored`, ask the modeler — the model may have been trained without proper validation persistence.
2. **MCMC config.** 4+ chains, ~1000+ warmup, ~1000+ draws per chain is the floor for trustworthy Meridian posteriors. Smaller configs work for sandboxing but shouldn't be used for production decisions.
3. **Sampler tuning.** If acceptance rates or step sizes were unusual, the modeler should know.

Report any setting flagged as `not_stored` separately — these are gaps in what the model can tell you about itself, not necessarily problems with the model.

## Phase 2: Prior-vs-Posterior Comparison

This is the most important diagnostic. For every channel, compare what the model assumed (prior) to what it ended up believing (posterior).

```
get_prior_posterior_comparison(model=<kpi_name>, credible_interval=0.9)
```

For each channel, the response gives:
- **Overlap coefficient** (0-1): how much the prior and posterior overlap. High overlap = data didn't move the estimate, prior is doing the heavy lifting.
- **Data influence score**: how much the posterior shifted from the prior.
- **Flag** if the parameter is **prior-dominated**.

Bucket the channels:

| Data influence | Read | Action |
|---|---|---|
| **High** (posterior pulled hard from prior) | Model has strong signal on this channel. Trust the ROI / saturation / mROI. | Use freely in recommendations. |
| **Medium** (some shift) | Model has decent signal but the prior is contributing. | Use with caveat — flag in any recommendation. |
| **Low** (posterior ≈ prior) | The model didn't learn anything new about this channel. The number you're reading is the prior. | Exclude from recommendations or surface with strong warning. |

Also pull the priors themselves to show what was assumed:
```
get_channel_priors(model=<kpi_name>)
```
ROI priors, adstock alpha priors, half-saturation EC priors, Hill slope priors. If informative priors were used (narrow distributions), be even more skeptical of prior-dominated channels — informative priors + low data influence = "we got back exactly what we put in."

## Phase 3: Fit Sanity Check

The model's revenue/KPI predictions should track observed reality. Compare model-implied performance against the observed period.

```
get_reconciled_revenue_comparison(model=<kpi_name>, current_last_n_weeks=4)
```

This compares two adjacent windows of reconciled performance. The reconciliation step itself is a fit signal — if the model's raw output had to be heavily adjusted to match observed totals, the underlying decomposition is shakier than the headline numbers suggest.

Also compare the model summary's reported fit metrics (if surfaced) against what the channel-level numbers add up to:
```
get_reconciled_overview(model=<kpi_name>)
```

Sanity checks:
- Does total reconciled revenue match the user's reported actuals? Within ±5% is fine, ±5-15% is worth a note, >15% is a flag.
- Does the baseline (organic) contribution look right? If baseline is >80% of revenue, the model is essentially saying paid media doesn't matter much — unusual unless the business is very organic-heavy. If baseline is <10%, the model may be over-attributing to paid.
- Are channel contributions stable week-to-week? Pull `get_reconciled_channel_contributions(model=<kpi_name>, last_n_weeks=12)` and look for wild swings in a single channel's weekly contribution that don't track its spend changes — usually means the model is fitting noise.

## Phase 4: Channel-Level Sanity

For the top-spend channels, do a quick sanity sniff-test against marketer intuition.

```
get_raw_channel_roi(model=<kpi_name>)
get_marginal_roi(model=<kpi_name>)
get_raw_saturation_curves(model=<kpi_name>)
```

Looking for:

1. **Implausibly high or low ROI.** A 50x ROI on a paid channel is almost always a model artifact, not reality. A 0.1x ROI on a high-effort channel may be true (channel underperforms) or may be confounded with a correlated channel. Flag extremes for the user to gut-check.
2. **mROI inconsistent with saturation.** A channel showing 95% saturation but high marginal ROI is internally inconsistent. Usually means the rpk fallback is biasing rankings — check the `rpk` sidecar on the mROI response.
3. **Adstock too long or too short.** Pull `get_adstock_parameters(model=<kpi_name>)`. Paid Search adstock half-life of 4 weeks is suspicious (Search effects are mostly same-week). TV adstock half-life of 1 week is suspicious (TV typically lags). Adstock that fights category intuition usually indicates a confounded channel or an over-flexible prior.
4. **Channel correlation hiding in the decomposition.** If two channels (e.g., Meta and Instagram, if separately modeled) move together perfectly in `get_reconciled_channel_contributions`, the model can't actually distinguish them. The aggregated contribution may be reliable; the per-channel split is not.

## Phase 5: Trust Grade

Compile the findings into a single trust grade with subgrades.

| Subgrade | Pass criteria |
|---|---|
| **Convergence** | R-hat < 1.05 on key params, no divergent transitions, effective sample size adequate |
| **Recency** | Training period ends within 8 weeks of today |
| **Holdout validation** | Holdout strategy documented, fit metrics available |
| **Prior independence** | <30% of channels flagged prior-dominated |
| **Decomposition coherence** | No two channels with perfect contribution correlation |
| **Reconciliation gap** | Total reconciled revenue within ±10% of actuals |
| **Channel-level plausibility** | No extreme/implausible ROIs, adstock matches category intuition |

Overall grade:
- **A** — all subgrades pass. Recommendations are trustworthy.
- **B** — 1-2 subgrades fail but core posterior is sound. Use with stated caveats.
- **C** — 3+ subgrades fail. Use only for descriptive purposes, not for budget recommendations.
- **F** — convergence or fit fails. Don't act on this model. Recommend retraining.

## Phase 6: Output

Deliver to the user:

1. **Overall trust grade** (A/B/C/F)
2. **Subgrade breakdown** — pass/fail per criterion with one-sentence rationale per fail
3. **Prior-dominated channel list** — which channels the model didn't learn much about
4. **Channel-level flags** — implausible ROIs, suspect adstock, correlated decompositions
5. **Recommended actions** — what to do before relying on this model (e.g., "retrain with longer window", "verify the Meta/Instagram split", "register RPK for the YouTube channel")
6. **The "use freely" channel list** — channels where data influence is high and sanity checks pass; recommendations on these channels carry full weight

## Inputs to Ask For

1. **Model / KPI** — which model (required; use `list_models` if unknown)
2. **Comparison window** — for the fit check, default last 4 weeks (optional)
3. **Stakeholder audience** — data scientist (full technical readout) vs. marketing exec (trust grade + caveats only) (optional)

## Important Notes

- **A B-grade model is still useful.** Most production MMMs land at B. The point of this skill is not to declare models broken, it's to make trust explicit so downstream recommendations can be properly caveated.
- **Prior dominance isn't always bad.** If a channel has very little spend variation in the training window, the data physically cannot move the prior much — the model is correctly saying "I have nothing to say here." The action is to recommend testing (incrementality, or scaling for a meaningful window) so future training periods have signal.
- **Holdout `not_stored` is a process gap, not a model defect.** It means the model was likely trained with a holdout but the artifact didn't persist that metadata. Flag and ask the modeler to re-run with persistence enabled rather than failing the grade.
- **Don't issue a trust grade without showing the work.** The user (especially a skeptical CFO) will want to see the subgrades. Lead with the grade, then immediately show the table.
- **Re-run this skill quarterly.** Models drift. A model that was A-grade in Q1 may be C-grade in Q3 if the training window hasn't been refreshed.
- **Hand off to `mmm-budget-reallocator` or `mmm-saturation-report`** with the trust grade attached. Recommendations downstream should always state the grade ("Per the B-grade model, the recommended shift is...").
