# TikTok Performance Digest — Detailed Workflow

A weekly or monthly narrative read on TikTok performance, formatted for forwarding to leadership without edits. Same shape as the `mmm-performance-digest` skill but scoped to TikTok as a paid channel.

The output is a story: what happened, what drove it, what to watch next. Not a metrics dump.

## Phase 1: Period Selection & Data Pull

1. **Clarify the period:**
   - Default: last 7 full days vs. prior 7 (weekly digest)
   - Monthly: month-to-date vs. prior month-to-date through same day
   - Always compare like-for-like (don't compare 7 days to 14 days)

2. **Resolve the advertiser:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   ```
   Match user-named client to `advertiser_name`.

3. **Pull top-line account performance for both periods:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_ADVERTISER",
     dimensions=["advertiser_id"],
     metrics=["spend", "impressions", "clicks", "ctr", "cpc", "cpm",
              "conversion", "cost_per_conversion", "conversion_rate"],
     start_date=<period_start>,
     end_date=<period_end>
   )
   ```
   Run twice: once for current period, once for prior.

4. **Pull campaign-level performance with names + objective + revenue value, in a single call:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_CAMPAIGN",
     dimensions=["campaign_id"],
     metrics=["spend", "impressions", "clicks", "ctr", "cpc", "cpm",
              "conversion", "cost_per_conversion", "conversion_rate",
              "total_purchase", "total_purchase_value", "value_per_total_purchase"],
     start_date=<period_start>,
     end_date=<period_end>,
     order_field="spend",
     order_type="DESC",
     include_names=True,
     page_size=50
   )
   ```
   `include_names=True` returns `campaign_name` and `objective_type` inline — no separate `get_tiktok_campaigns` join needed. The `total_*` revenue metrics give a value-side read alongside the conversion-count read; non-purchase-tracking accounts will see zeros, which is informative.

6. **Pull daily breakdown for trend chart data:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     dimensions=["stat_time_day"],
     metrics=["spend", "impressions", "conversion", "cost_per_conversion"],
     start_date=<28_days_ago>,
     end_date=<today>
   )
   ```
   Last 28 days gives enough context to spot acceleration vs. deceleration.

## Phase 2: Compute Headline Metrics

Parse string-typed metric values to floats. Compute period-over-period deltas for:

| Metric | Why it leads the digest |
|---|---|
| Spend | The first number leadership looks at |
| Conversions | The outcome metric |
| Cost per conversion (CPA) | Efficiency — the second number leadership looks at |
| Conversion rate | Quality of traffic |
| CTR | Creative health proxy |
| CPM | Auction dynamics — rising CPM at flat CTR = the market got more expensive |

For each metric, compute: absolute current, absolute prior, absolute delta, % delta.

**Reading the deltas:**
- Spend up + CPA flat = scale event (good)
- Spend up + CPA up = paying more for the same outcome (investigate)
- Spend flat + CPA down = efficiency win (creative or auction tailwind)
- Spend down + CPA up = something broken (creative fatigue, audience exhaustion, competitive pressure)
- Spend down + CPA down = quality concentration (often happens when budget caps bind)

## Phase 3: Drivers Analysis

The "what drove it" section. This is the part leadership actually reads.

1. **Top contributors to spend change:**
   - Sort campaigns by absolute spend delta (period over period)
   - Top 3 increases and top 3 decreases
   - For each, note CPA direction and whether the spend change was deliberate (budget change) or organic (auction dynamics)

2. **Top contributors to conversion change:**
   - Same exercise on conversion volume delta
   - Often differs from spend drivers — a campaign can scale spend without adding conversions

3. **Efficiency winners and losers:**
   - Campaigns where CPA dropped >15% week-over-week — what changed?
   - Campaigns where CPA rose >15% — same question
   - If a campaign appears in both the spend-up and CPA-up lists, that's the headline issue

4. **Creative pulse (lightweight):**
   - Pull top 10 ads by spend in the current period via creative-insights
   - Note ages (`create_time`) and hook rates (`video_views_p25 / impressions`)
   - If top spenders are all >21 days old with declining hook rates, flag a fatigue risk — but don't run the full fatigue analysis here. Refer to `tiktok-creative-fatigue-watchdog`.

5. **If MMM is available, get the incrementality cross-check:**
   ```
   meridian_get_raw_channel_roi(model_id, channel="tiktok")
   meridian_get_raw_weekly_contributions(model_id, channel="tiktok")
   ```
   - Did TikTok's platform-reported conversions track the MMM contribution this period? Mismatch is the lead for the next conversation.
   - This is the BlueAlpha differentiator — platform digests without MMM context overstate TikTok's contribution.

## Phase 4: Compose the Narrative

The output format. Each section is 2-4 sentences max — leadership doesn't read long.

```
TikTok Performance Digest — <Client>
Period: <date range> vs. <prior date range>

HEADLINE
[One sentence. Example: "TikTok spend grew 18% to $X this week while CPA held at $Y — efficient scale,
driven by the launch of the iOS Checkout-2 campaign."]

WHAT HAPPENED
- Spend: $X (Δ +X% / -X%)
- Conversions: X (Δ +X% / -X%)
- CPA: $X (Δ +X% / -X%)
- CTR: X.XX% (Δ +X% / -X%)
- CPM: $X (Δ +X% / -X%)

WHAT DROVE IT
[2-4 bullet points. Name campaigns by name, not ID. Quantify each driver.]
- [Top spend driver: campaign + delta + CPA direction]
- [Top conversion driver: campaign + delta]
- [Notable efficiency move: a CPA win or loss > 15%]
- [Creative pulse: if top spenders are aging, say so]

WHAT TO WATCH
[2-3 bullets. Forward-looking. What changes next week, what's a risk.]
- [Risk #1: e.g., "Creative is aging; recommend triggering creative-refresh next week"]
- [Risk #2: e.g., "If MMM shows lower TikTok contribution next read, the platform-reported 18% growth is overstated"]
- [Opportunity: e.g., "The Checkout-2 campaign has room to scale — recommend +$X/day"]

MMM CROSS-CHECK (if available)
[One sentence. e.g., "MMM contribution from TikTok was flat at $X this week despite platform spend growth.
This suggests the new campaign is cannibalizing existing TikTok conversions, not adding incremental ones."]
```

## Phase 5: Cadence & Distribution

1. **Suggested cadence:**
   - **Weekly:** $50K+/mo TikTok accounts. Run every Monday for prior 7 days.
   - **Bi-weekly:** $10K-$50K/mo. Less noise.
   - **Monthly:** <$10K/mo or when TikTok is not the primary channel.

2. **Suggest scheduling** via the `schedule` skill — this is the highest-value skill to automate because the leadership-facing report has a recurring deadline.

3. **Cross-skill handoffs from the digest:**
   - Creative aging flag → `tiktok-creative-fatigue-watchdog`
   - CPA blowout in a single campaign → `tiktok-auto-optimize` (scoped to that campaign)
   - MMM disagrees with platform-reported lift → `mmm-attribution-reconciler`
   - New market opportunity surfaced → `tiktok-geo-expansion`

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required (use `tiktok_ads_list_tiktok_advertisers` if unknown)
2. **Period** — weekly (default) / monthly / custom range
3. **Audience for the digest** — internal team vs. C-suite (changes the tone, not the content)
4. **MMM model** — for incrementality cross-check (optional)
5. **Prior digest** — to track narrative continuity ("last week we flagged X; this week...")

## Output

A formatted digest in the structure above. Always include:

1. **Headline** — one sentence with the most important fact
2. **What Happened** — top-line metrics with deltas
3. **What Drove It** — named campaign drivers, quantified
4. **What to Watch** — 2-3 forward-looking items
5. **MMM Cross-Check** — if a model is available
6. **Cross-skill recommendations** — what to do next

## Important Notes

- **Lead with the verdict.** The headline sentence is the only part most readers will absorb. Get it right.
- **Name names.** Use campaign names from `tiktok_ads_get_tiktok_campaigns`, never IDs. Leadership doesn't know what "1864955515077361" is.
- **Don't editorialize on small deltas.** A 3% CPA shift week-over-week is noise. Don't write narrative around it. Reserve narrative weight for >10% moves.
- **Platform numbers are the surface read.** If the user has an MMM, the BlueAlpha digest's job is to flag where the platform-reported story disagrees with MMM contribution. That's the entire reason to use BlueAlpha instead of the TikTok native dashboard.
- **TikTok's attribution window matters.** TikTok defaults to 7-day click + 1-day view. Conversion deltas in a recent 7-day window will revise upward over the next 2-3 days as late-attribution conversions land. Note this when current-period conversions are <90% of prior-period (it might just be unsettled data, not a real drop).
- **One digest per advertiser.** If the client has multiple TikTok advertiser accounts (e.g., Klover has only 1, but Mas Movil has 3), run the digest separately for each. Don't aggregate — the campaigns serve different objectives and the narrative gets muddled.
