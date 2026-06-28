# Meta Creative Fatigue Watchdog — Detailed Workflow

> **Verified tool bindings (June 2026, tested live on a production account).** Meta is exposed on the BlueAlpha
> connector as `facebook_ads_*` (not `meta_ads_*`). Resolve the account with
> `facebook_ads_list_facebook_ad_accounts()` -> `act_<id>`. Pull config with
> `facebook_ads_list_facebook_campaigns(ad_account_id)` / `facebook_ads_list_facebook_ad_sets(campaign_id)`
> / `facebook_ads_list_facebook_ads(ad_set_id)`. Pull ALL performance with
> `facebook_ads_get_facebook_insights(object_id, level, breakdowns, date_preset|time_range)` —
> `object_id` is `act_<id>` (account) or a bare campaign/adset/ad id; `level` in
> account|campaign|adset|ad; there is NO `fields` arg. Conversions live in the `actions[]`
> array (action_type "purchase"/"lead"); revenue in `action_values[]` — never sum all actions.
> Account-wide or breakdown pulls are large and save to a file: crunch via jq/python in a
> subagent and return only the ranked slice. Full reference: meta-auto-optimize/references/meta-mcp-tools.md. Inline code blocks below are illustrative; the only valid args are those in the verified reference (e.g. get_facebook_insights takes object_id/level/breakdowns/date_preset|time_range, NOT fields/effective_status/limit).



Meta creative fatigues differently from search: the dominant tell is **frequency** climbing
while **first-time impressions** and **thumb-stop** fall, with CPM rising as the auction
penalizes a stale ad. Meta's UI buries the upstream signals; this skill surfaces them, fuses
them with BlueAlpha's own fatigue engine, and produces a prioritized refresh queue.

Read-only: detect, classify, recommend. Execution (pause/replace) routes through the
BlueAlpha pipeline.

## Phase 0: Pull BlueAlpha's fatigue engine first (live)

BlueAlpha already runs a Meta-aware creative-fatigue pipeline. Start there — it is the
fastest, highest-signal read and it is live in the connector.

1. **Resolve the client `data_key`** and pull the latest alerts:
   ```
   creative_fatigue_cf_get_alerts(platform="meta", mode="summary", detection_date=<most_recent>)
   ```
   If `detection_date` is unknown, the tool requires one — use today or the last business day,
   then widen to a range `"YYYY-MM-DD,YYYY-MM-DD"` if empty.
2. **For forensic rows:**
   ```
   creative_fatigue_cf_get_alerts(platform="meta", mode="rows",
       detection_date=<date>, severity_min="warning", limit=50)
   ```
3. **Concept reference** for any category you need to explain:
   ```
   creative_fatigue_cf_get_pipeline_reference()
   ```
   Categories returned: `true_decay`, `ghost_fatigue`, `cpm_penalty`, `market_shift`,
   `audience_saturated`, `early_saturation`, `ctr_crash`, `ctr_decay_unconfirmed`,
   `roas_decline`, `reach_decline`. Severity ladder: `monitor < early_warning < warning < critical`.
4. **At-risk spend** (quantify the prize):
   ```
   creative_fatigue_cf_get_savings(platform="meta", detection_date=<date>, mode="summary")
   ```

Treat the engine's output as the spine of the report. The raw read below enriches it and
catches anything below the engine's alerting floor.

## Phase 1: Raw ad inventory & performance (facebook_ads_*)

1. **Active ads** (for age + which creatives are in market):
   ```
   facebook_ads_list_facebook_ads(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=1000)
   ```
   Capture `id`, `name`, `adset_id`, `campaign_id`, `created_time`, `creative` summary.

2. **Recent window (last 14d), top 100 by spend:**
   ```
   facebook_ads_get_facebook_insights(
     object_id=<act_id>, level="ad",
     fields=["spend","impressions","reach","frequency","clicks","ctr","cpm",
             "inline_link_clicks","outbound_clicks",
             "video_p25_watched_actions","video_p50_watched_actions",
             "video_p75_watched_actions","video_p100_watched_actions",
             "video_thruplay_watched_actions","actions","action_values","purchase_roas",
             "quality_ranking","engagement_rate_ranking","conversion_rate_ranking"],
     date_preset="last_14d", include_names=True, sort=["spend_descending"], limit=100)
   ```
3. **Prior window (days 15-28)** with the same fields via `time_range` for trend deltas.
4. **Daily breakdown** for the top 20 by spend (slope analysis) via `time_range` spanning 28d.

## Phase 2: Compute fatigue signals (per ad, both windows)

| Signal | Formula / source | Meta read |
|---|---|---|
| **Frequency** | provided (`impressions/reach`) | THE primary signal. >2.5-3.0 in a 7d prospecting window = saturation; retargeting tolerates higher |
| **First-time-impression ratio** | reach growth vs impressions growth | flattening reach at rising impressions = you're re-hitting the same people |
| **Thumb-stop rate** | `video_p25_watched_actions / impressions` (or ThruPlay/impr) | <20% weak hook; falling = creative losing its open |
| **Hold / completion** | `video_p50` and `video_p100 / impressions` | retention decay |
| **Link CTR** | `inline_link_clicks` or `outbound_clicks / impressions` | <0.5% weak; >20% relative drop = fatigue |
| **CPM trend** | provided | rising CPM at flat targeting = auction penalizing the creative (`cpm_penalty`) |
| **Relevance diagnostics** | `quality_ranking`, `engagement_rate_ranking`, `conversion_rate_ranking` | any sliding to `BELOW_AVERAGE_*` = Meta down-ranking the ad |
| **Age** | days since `created_time` | >21d at high spend = stale by default |

Trend deltas = recent vs prior; flag any signal decaying >15% relative. Fit a linear slope on
frequency↑ and CTR↓ for top-spend ads — rising frequency usually leads CTR collapse by days.

## Phase 3: Severity classification (reconcile with the engine)

| Tier | Criteria (raw read) | Engine equivalent | Action |
|---|---|---|---|
| **Critical** | Frequency >3.0 AND link-CTR dropped >25% rel AND top-20% spend | `critical` / `true_decay` / `audience_saturated` | Pause/replace this week |
| **High** | Frequency 2.5-3.0 OR CTR dropped 15-25% rel OR relevance → BELOW_AVERAGE, with >$1K/wk | `warning` / `cpm_penalty` / `ctr_crash` | Replace within 2 weeks; pre-stage creative |
| **Moderate** | One signal decaying, age <21d, spend <$1K/wk | `early_warning` / `early_saturation` | Watch; recheck next cycle |
| **Healthy** | No decay >15%, frequency <2.0, CTR >0.5% | `monitor` / none | Leave it |

Two nuances: (1) **`ghost_fatigue`** — platform metrics look fine but incremental value is
gone; reconcile against MMM/incrementality before declaring "healthy". (2) Distinguish
**audience saturation** (rotate audience or expand) from **creative decay** (new creative) —
frequency-driven fatigue at stable CTR is an audience problem, falling thumb-stop at stable
frequency is a creative problem.

## Phase 4: Output

1. **Refresh queue** — top N ads ranked by at-risk spend, each with: severity, the 1-2
   signals that fired, engine category, age, weekly spend, recommended action.
2. **Account fatigue summary** — tier counts, total at-risk weekly spend (from
   `cf_get_savings` + raw), frequency distribution.
3. **Root-cause split** — audience saturation vs creative decay vs auction penalty, so the
   fix routes correctly.
4. **Handoffs:** Critical/High volume >25% of weekly spend → `meta-creative-refresh` for the
   brief. Audience-driven → `meta-audience-intelligence` / `meta-advantage-plus-audit`.
   Placement-specific decay → `meta-placement-performance`. Suspected ghost fatigue →
   `meta-incrementality-test`.

## Important Notes

- **Frequency is the headline Meta signal** — lead with it. A 21-day-old ad at frequency 4.0
  is fatigued even if CTR hasn't cracked yet; the crack is days away.
- **The BlueAlpha engine is the differentiator.** A raw frequency/CTR read is table stakes;
  the `creative_fatigue_*` categories (ghost_fatigue, cpm_penalty, audience_saturated) encode
  causal reasoning the platform UI can't. Lead the report with the engine, enrich with raw.
- **Don't refresh against an audience problem.** New creative into a saturated audience just
  resets frequency briefly. If frequency is the only fired signal, rotate/expand audience first.
- **Meta video metrics are arrays of action objects** — parse the value out before math.
- **Relevance diagnostics need a minimum impression volume** to populate; absence isn't health.
