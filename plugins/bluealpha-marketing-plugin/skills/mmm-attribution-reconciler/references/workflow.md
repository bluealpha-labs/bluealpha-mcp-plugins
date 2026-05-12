# MMM Attribution Reconciler — Detailed Workflow

The job: when Google Ads says one ROAS and the MMM says another, tell the user which to believe — and when neither is reliable enough on its own and the answer is to run an incrementality test. Closes the "platform ROAS lies (sometimes)" loop. The platform's view is last-touch heavy and overcredits the channel doing the closing; the MMM's view is incremental but can miss recent dynamics the platform sees first. The right answer per channel is often a blend, but the user needs to know which way each channel skews and how much.

## Phase 0: Frame the Reconciliation

Reconciliation can be run at three scopes. Confirm which:

- **Single-channel deep reconciliation** — "Why does Google Ads say Search has a 4x ROAS but MMM says 2x?" Maximum detail, single channel.
- **Multi-channel snapshot** — One row per channel across the paid mix. Mid-detail, lots of channels.
- **Time-series reconciliation** — How has the MMM vs platform gap evolved over the trailing quarter? Surfaces drift (platform increasingly over- or under-claiming).

Multi-channel snapshot is the most common ask. Default to that unless the user specifies otherwise.

## Phase 1: Gather MMM Side

```
list_models()
get_model_summary(model=<kpi_name>)
query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
get_marginal_roi(model=<kpi_name>)
```

Capture per channel:
- **MMM average ROI** — `query_reconciled_performance_table.ROI`
- **MMM marginal ROI** — `get_marginal_roi`
- **MMM weekly spend** — same source
- **MMM-attributed revenue** — same source

Use reconciled (dashboard-matching) numbers, not raw posterior. The point of reconciliation is to bridge the dashboard with the platform — using raw posterior numbers here just creates a second gap the user has to reason about.

## Phase 2: Gather Platform Side — Google Ads

Google Ads campaigns map to one or more MMM channels. The user needs to provide the mapping (or confirm a proposed one) — MMM channel "Google Search" usually rolls up multiple Google Ads campaigns.

```
list_accessible_customers()
execute_query_stream(customer_id=<id>, query="
  SELECT
    campaign.name,
    campaign.id,
    metrics.cost_micros,
    metrics.conversions_value,
    metrics.conversions
  FROM campaign
  WHERE segments.date BETWEEN '<start>' AND '<end>'
    AND campaign.status != 'REMOVED'
")
```

For each MMM channel that maps to Google Ads campaigns:
- **Platform spend** = sum of cost_micros / 1,000,000 across mapped campaigns
- **Platform-attributed revenue** = sum of conversions_value across mapped campaigns
- **Platform ROAS** = platform revenue / platform spend

Use the same date window as the MMM read (typically the trailing 4 weeks for snapshot, longer for trend).

## Phase 3: Gather Platform Side — Meta / Other Channels

Meta, TikTok, Pinterest, LinkedIn, programmatic platforms — the BlueAlpha MCP doesn't currently expose ad-platform APIs for these. Two options:

1. **Ask the user to paste platform numbers** — for each MMM channel that maps to a non-Google platform, ask for the trailing-period platform spend and platform-reported revenue. Capture: channel, platform spend, platform revenue, attribution model used (1-day click, 7-day click, 28-day click+view, etc.).

2. **Use the MMM weekly spend as the spend baseline** and ask only for platform-reported revenue. Less data to request from the user, but spend may drift slightly from what the platform reports due to taxes/fees/reconciliation lag.

For each non-Google channel, capture the same three numbers: platform spend, platform revenue, platform ROAS. Flag the attribution model used — a 28-day-click model will report much higher ROAS than a 7-day-click model on the same campaign, and the gap with MMM is meaningless without that context.

## Phase 4: Compute the Reconciliation

For each MMM channel:

| Metric | Source |
|---|---|
| Spend | MMM (authoritative) |
| MMM ROI | get_marginal_roi / reconciled_performance |
| Platform ROAS | Phase 2/3 |
| Gap (absolute) | MMM ROI − Platform ROAS |
| Gap (relative) | (MMM ROI − Platform ROAS) / Platform ROAS |
| Direction | "Platform overclaims" if Platform > MMM; "Platform underclaims" if MMM > Platform |

Bucket each channel by gap magnitude and direction:

| Gap pattern | Bucket | Interpretation |
|---|---|---|
| **Within ±20%** | Agree | Numbers reconcile within typical attribution noise. Use either; ship decisions. |
| **Platform overclaims by 20-50%** | Platform overclaims (moderate) | Common pattern on last-touch heavy channels (Branded Search, Retargeting). Platform is taking credit for incremental conversions that would have happened anyway. Trust MMM. |
| **Platform overclaims by >50%** | Platform overclaims (heavy) | Severe overclaiming. Usually Branded Search or Retargeting. The MMM read is right and platform-driven budget decisions on this channel are systematically over-funding it. |
| **Platform underclaims by 20-50%** | Platform underclaims (moderate) | Less common — usually happens with upper-funnel channels (YouTube, Display, CTV) where view-through conversions or assisted conversions aren't captured in the user's attribution settings. Trust MMM directionally. |
| **Platform underclaims by >50%** | Platform underclaims (heavy) | Strong signal that MMM is picking up halo / assist effects the platform misses. Trust MMM. |

## Phase 5: Route Disagreements to Trust-Router

For every channel that falls outside the ±20% agreement zone, the next question is "can we trust the MMM's read on this disagreement?" That's the trust-router's job.

For each disagreement channel:
1. Pull the channel's routing from `mmm-trust-router` (run it if not already available).
2. Combine reconciliation bucket × trust-router route to produce a final action:

| Reconciliation | Trust-router route | Action |
|---|---|---|
| Agree | Trust MMM | Ship decisions, both numbers agree |
| Agree | Validate first | Numbers agree, but MMM uncertainty is high — minor risk in acting |
| Agree | Model insufficient | Coincidence agreement on a channel the model can't see clearly — don't read into it |
| Platform overclaims, MMM lower | Trust MMM | Hard rebalance — cut platform-driven budget recommendations, MMM is right |
| Platform overclaims, MMM lower | Validate first | Strong directional signal but needs causal confirmation. Run the test. |
| Platform overclaims, MMM lower | Model insufficient | Neither source is reliable. Forced test needed. |
| Platform underclaims, MMM higher | Trust MMM | Platform is missing halo; act on MMM, but watch for over-attribution to upper funnel |
| Platform underclaims, MMM higher | Validate first | The MMM is claiming bigger impact than the platform — high upside if confirmed. Test it. |
| Platform underclaims, MMM higher | Model insufficient | Suspicious — the MMM "found" credit the platform can't see but the model itself isn't reliable. Likely a confound or prior artifact. |

The "Validate first × disagreement" cells are where the reconciler creates the most value — they're the channels where the disagreement is real and the resolution genuinely demands a test, not a debate. These should be among the top priorities on the `mmm-test-roadmap`.

## Phase 6: Time-Series Reconciliation (when scoped)

If the user asked for trend reconciliation rather than snapshot:

```
get_raw_weekly_contributions(model=<kpi_name>, last_n_weeks=26)
execute_query_stream(customer_id=<id>, query="
  SELECT segments.week, campaign.name, metrics.cost_micros, metrics.conversions_value
  FROM campaign
  WHERE segments.date BETWEEN '<26_weeks_ago>' AND '<today>'
")
```

Compute weekly MMM ROI vs. weekly platform ROAS over 26 weeks. Look for:

1. **Widening gap** — Platform overclaim getting larger over time. Usually means the platform attribution model is increasingly overcrediting due to creative changes, audience changes, or attribution-setting changes. Investigate the audit log on the platform side.
2. **Narrowing gap** — Disagreement resolving. Usually means a recent change (iOS update, cookie deprecation, attribution model swap) is bringing the platform read closer to the MMM.
3. **Sudden flip** — A single week where the gap inverts. Often an iOS 14.5-style event or a platform attribution release. Mark the week and contextualize.
4. **Persistent gap** — Steady disagreement over many weeks. The structural attribution gap. This is the level of platform over/under-claim baked into the channel's nature.

## Phase 7: Output

Deliver to the user:

1. **The reconciliation table** — one row per channel: MMM ROI, Platform ROAS, gap absolute, gap %, bucket, trust-router route, final action
2. **The "agree" channels** — these are the channels where either source is trustworthy enough to act on
3. **The "platform overclaims" channels** — where MMM should override platform-driven budget recommendations
4. **The "platform underclaims" channels** — where the MMM is finding incremental value the platform misses
5. **The "must test" channels** — disagreements × Validate-first or Model-insufficient. Hand off to `mmm-test-roadmap` for scheduling.
6. **The trend chart** (if scoped) — 26-week MMM-vs-platform reconciliation per channel, with annotation for major events
7. **A one-paragraph executive summary** — net direction of platform attribution bias across the mix, dollar impact of the top mis-attribution channels, recommended sequencing of tests to resolve

## Inputs to Ask For

1. **Model / KPI** — which MMM (required)
2. **Reconciliation scope** — single channel, multi-channel snapshot, or time-series (required)
3. **Google Ads customer ID** — for the platform-side pull (required if any Google channel is in scope)
4. **Channel-to-campaign mapping** — which Google Ads campaigns roll into which MMM channels (required; confirm with user even when a proposed mapping is obvious)
5. **Non-Google platform numbers** — for any Meta/TikTok/etc. channels, paste platform spend + revenue + attribution model used (required for those channels)
6. **Time window** — default trailing 4 weeks for snapshot, 26 weeks for trend (optional)

## Important Notes

- **Platform attribution settings drive the gap.** The same Meta campaign on 7-day-click vs 28-day-click+view will show wildly different ROAS. Always capture the attribution model in use on the platform side. If the user changed their attribution settings during the reconciliation window, the platform-side number is itself a moving target and the gap analysis needs to be windowed before/after the change.
- **Platform overclaim on Branded Search is structural, not a bug.** Branded Search captures conversions that would have happened anyway (the user typed your brand). The platform credits Branded Search fully; the MMM says most of those conversions are organic-baseline. Both are right within their definitions — the MMM is the right one for budget decisions because budget decisions are about incrementality.
- **Don't treat "MMM higher" as automatic vindication.** When MMM claims more credit than the platform, the most common explanations are (a) the platform is missing view-through / assist halo (legitimate), or (b) the MMM has a confounded decomposition crediting this channel for something it didn't do (artifact). The trust-router routing tells you which.
- **Reconcile spend before you reconcile revenue.** If platform-reported spend and MMM spend differ by more than 5%, you have a data-pipeline problem, not an attribution disagreement. Fix the spend reconciliation before reading anything into ROAS differences.
- **The reconciler is a routing engine, not a decision engine.** Its job is to point the user at the right next step (act / test / investigate), not to declare winners. Channels in the "must test" bucket should always be the top of the testing-roadmap stack.
- **Re-run quarterly.** Attribution gaps drift. Platform models update. iOS / cookie events shift the baseline. A reconciliation that was clean last quarter may need redoing now.
