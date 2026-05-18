# TikTok Creative Fatigue Watchdog — Detailed Workflow

TikTok creative dies faster than any other paid channel. A winning ad that's been running 10 days is often already past peak. The platform UI surfaces CTR decay but buries the upstream signals — hook rate (% of impressions that watch past 3 seconds), hold rate (% that make it halfway), and completion rate. This skill is a fast, narrow read designed to be run weekly and hand off to `tiktok-creative-refresh` when severity is high.

This skill is read-only. It detects, classifies, and recommends. Execution (pause/replace) routes through the BlueAlpha pipeline.

## Phase 1: Creative Performance Snapshot

Pull the data needed to compute fatigue signals.

1. **Resolve the advertiser** if not provided:
   ```
   tiktok_ads_list_tiktok_advertisers()
   ```
   If the user names a client, match to the `advertiser_name`. Confirm with the user before continuing.

2. **Pull the active ad inventory** so we know which creatives are in market:
   ```
   tiktok_ads_get_tiktok_ads(
     advertiser_id=<id>,
     primary_status="STATUS_DELIVERY_OK",
     page_size=1000
   )
   ```
   Capture: `ad_id`, `ad_name`, `adgroup_id`, `campaign_id`, `create_time` (for age calculation), `status`. If the account has >1000 active ads, paginate.

3. **Pull creative-level performance for the recent window (last 14 days), top 100 by spend:**
   ```
   tiktok_ads_get_tiktok_creative_insights(
     advertiser_id=<id>,
     start_date=<14_days_ago>,
     end_date=<today>,
     metrics=["spend", "impressions", "clicks", "ctr", "cpm",
              "video_play_actions", "video_views_p25", "video_views_p50",
              "video_views_p75", "video_views_p100",
              "conversion", "cost_per_conversion", "conversion_rate"],
     order_field="spend",
     order_type="DESC",
     include_names=True,
     page_size=100
   )
   ```
   `order_field="spend"` returns top spenders in a single call (was a 67-page paginate problem in earlier MCP versions). `include_names=True` attaches `ad_name`, `adgroup_name`, `campaign_name` inline — no separate join needed.

4. **Pull the same metrics for the prior window (days 15-28)** to enable trend comparison:
   ```
   tiktok_ads_get_tiktok_creative_insights(
     advertiser_id=<id>,
     start_date=<28_days_ago>,
     end_date=<15_days_ago>,
     metrics=[<same as above>],
     order_field="spend",
     order_type="DESC",
     include_names=True,
     page_size=100
   )
   ```

5. **Pull a daily breakdown for high-spend ads** (top 20 by spend in the recent window) for slope analysis:
   ```
   tiktok_ads_get_tiktok_creative_insights(
     advertiser_id=<id>,
     ad_ids=<top_20_ad_ids>,
     start_date=<28_days_ago>,
     end_date=<today>,
     metrics=[<same>],
     include_daily_breakdown=True,
     page_size=100
   )
   ```

6. **Notes on the data:**
   - TikTok returns metric values as **strings** — always parse to float/int before math
   - `ctr` is returned as a percentage value (e.g., `0.44` means 0.44%, not 44%)
   - Conversion metric is `conversion` (singular). `conversions` (plural) is invalid for this MCP.
   - `video_play_actions` is total play starts, not impressions. Use `impressions` as the denominator for hook/hold/completion to match TikTok's official definitions.

## Phase 2: Compute Fatigue Signals

For each ad with >=1,000 impressions in the recent window, compute the fatigue signal panel.

1. **Derived metrics (compute these per ad, both windows):**

   | Signal | Formula | What it tells you |
   |---|---|---|
   | **Hook rate** | `video_views_p25 / impressions` | % that watched past ~3 seconds. <15% = bad hook. >25% = strong. |
   | **Hold rate** | `video_views_p50 / impressions` | % that made it halfway. <5% = weak retention. |
   | **Completion rate** | `video_views_p100 / impressions` | % that watched in full. <1% = poor. >3% = excellent. |
   | **CTR** | provided | <0.5% = weak. >1.5% = strong (varies by vertical). |
   | **CPM** | provided | Rising CPM at flat hook rate = auction is punishing the creative |

2. **Trend deltas (recent vs prior window):**
   - `hook_rate_delta = hook_rate_recent - hook_rate_prior`
   - Same pattern for hold_rate, completion_rate, ctr, cpm
   - Flag any signal that decayed >15% relative to its prior value (e.g., hook rate dropped from 22% to 18% = -18% relative decay)

3. **Slope analysis for top-spend ads:**
   - Using the daily breakdown, fit a simple linear trend on `hook_rate` and `ctr` over the last 14-21 days
   - A negative slope on hook rate is the earliest fatigue warning — it usually leads CTR by 3-5 days
   - Compute the # of consecutive declining days for each signal

4. **Age factor:**
   - Days since `create_time`
   - Ads >21 days old at high spend are stale by default — even if metrics look okay, they're at risk

5. **Frequency proxy:**
   - High `impressions / video_play_actions` ratio (>1.3) suggests TikTok is force-rotating the ad and audience is seeing it without playing — a classic late-stage fatigue tell

## Phase 3: Severity Classification

Bucket each ad into one of four severity tiers based on the signal panel.

| Tier | Criteria | Action |
|---|---|---|
| **Critical** | Hook rate dropped >25% relative AND ad is in top 20% of spend | Pause this week. Replacement is overdue. |
| **High** | Hook rate dropped 15-25% relative OR CTR dropped >20% relative OR completion rate <1% AND >$1K weekly spend | Replace within 2 weeks. Pre-stage new creative. |
| **Moderate** | Any single signal decaying but ad age <21 days and spend <$1K/week | Watch. Re-check next cycle. |
| **Healthy** | No signal decay >15%, hook rate >15%, CTR >0.5% | Leave it. Don't fix what isn't broken. |

**Two important nuances:**

- **High-spend dominates.** A 30% hook-rate decay on an ad spending $50/week is noise. The same decay on a $5K/week ad is critical. Always weight severity by spend share.
- **Insufficient data is real.** Ads with <1,000 impressions in the recent window get classified as `INSUFFICIENT_DATA`. Don't force a fatigue call on these — recommend either more budget to reach the threshold or pausing if they've been live >14 days without traction.

## Phase 4: Wasted Spend Estimate & Refresh Brief

Quantify the cost of inaction and produce the handoff brief.

1. **Estimate wasted spend** for Critical + High tier ads:
   - For each ad, compute the gap between its current CTR and its prior-window CTR
   - Estimated wasted clicks = `(prior_ctr - recent_ctr) × recent_impressions / 100`
   - Estimated wasted spend = `wasted_clicks × recent_cpc`
   - Sum across all Critical+High ads. This is the headline number for leadership.

2. **Produce the refresh prioritization table:**
   - Columns: Ad ID, ad name (truncated), severity, recent spend, hook rate decay, CTR decay, days old, estimated wasted spend
   - Sort by estimated wasted spend descending
   - Top 10 rows are the immediate refresh queue

3. **Hand off to `tiktok-creative-refresh`** if there are 3+ Critical or High tier ads. Pass:
   - The list of Critical/High ad IDs
   - The winning creative attributes from healthy ads (hook style, format inferred from completion rates, length proxy from completion/play_actions ratio)
   - The estimated wasted-spend number to anchor the urgency

4. **If MMM is available, validate before scaling the refresh:**
   ```
   meridian_get_raw_channel_roi(model_id)
   meridian_get_raw_saturation_curves(model_id)
   ```
   If MMM shows TikTok is saturated, replacing fatigued creative will help *efficiency* but won't unlock more revenue. Flag this — leadership often misreads "creative refresh" as "this will grow TikTok."

## Phase 5: Output & Monitoring Cadence

1. **Deliverable to the user:**
   - **Fatigue Watchdog Report** with: severity counts (Critical / High / Moderate / Healthy / Insufficient), top 10 refresh queue, estimated weekly wasted spend, hook/hold/completion distribution snapshot
   - **Refresh brief handoff payload** (if triggered)
   - **Healthy creative profile** — what attributes the survivors share (this is the unlock for creative briefs)

2. **Suggested cadence:**
   - High-spend accounts (>$50K/mo on TikTok): run weekly, ideally Monday
   - Mid-spend ($10K-$50K/mo): run bi-weekly
   - Low-spend (<$10K/mo): run monthly, focus on age + insufficient-data flags instead of trend deltas

3. **Suggest scheduling** via the `schedule` skill if the user wants this on autopilot.

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — TikTok advertiser to audit (required; use `tiktok_ads_list_tiktok_advertisers` if unknown)
2. **Lookback window** — default 14 days recent vs 14 days prior (optional)
3. **Spend threshold** — minimum weekly spend per ad to include in severity grading (default $250/week, lower for small accounts)
4. **MMM model** — for incrementality cross-check (optional; `meridian_list_models` to find)

## Output

Deliver to the user:

1. **Severity Scorecard** — counts and weekly spend share by tier
2. **Refresh Queue** — top 10 ads to replace, with estimated wasted spend per ad
3. **Hook/Hold/Completion Snapshot** — distribution across the account
4. **Healthy Creative Profile** — what's surviving and why
5. **Wasted Spend Estimate** — single-number headline for leadership
6. **Cross-skill handoff** to `tiktok-creative-refresh` when severity is high

## Important Notes

- **Hook rate leads CTR.** Watch hook rate first — a 3-day slide in hook rate is your earliest signal, often 5-7 days before CTR follows. If you wait for CTR decay, you've already wasted 4-5 days of spend.
- **TikTok rewards iteration, not perfection.** Don't refresh one winning ad — replace it with 3-5 variants. The platform's optimizer needs variety.
- **The platform UI hides hook rate by default.** Most clients have never looked at it. Lead with hook rate in the report — it's both diagnostic and educational.
- **Don't conflate "old" with "fatigued."** A 60-day-old ad with steady hook rate and CTR is doing better than any 7-day-old replacement could. Age is a risk factor, not a verdict.
- **Conversion-rate decay is downstream.** TikTok attribution is platform-reported, so conversion-rate decay can lag (or be wrong) by 1-2 weeks. Lead with engagement metrics; treat conversion drift as confirmation, not the primary signal.
- **Cross-skill handoffs:** Severe creative fatigue → `tiktok-creative-refresh`. Account-wide CTR/hook decay → likely audience issue, handoff to `tiktok-audience-intelligence`. Spend falling despite healthy creatives → `tiktok-auto-optimize` for structure/pacing diagnosis.
