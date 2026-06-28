# Meta Auto-Optimize — Detailed Workflow

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



The full optimization cycle for a Meta (Facebook + Instagram) Ads account, equivalent to the
`auto-optimize` skill for Google Ads and `tiktok-auto-optimize` for TikTok. Designed to run
weekly (high-spend) or bi-weekly. Output is an actionable scorecard + recommended changes,
risk-tiered.

This skill is analysis and recommendation only. Execution (campaign edits, budget changes,
pauses) routes through the BlueAlpha pipeline.

**Tool surface:** see `references/meta-mcp-tools.md` for the inferred `facebook_ads_*` tool names
and the data-handling rules. Tool names are inferred from the `tiktok_ads_*` convention and
must be verified against the live connector.

## Phase 1: Structural Audit

Before optimizing the levers, check the foundations.

1. **Resolve ad account & pull campaigns:**
   ```
   facebook_ads_list_facebook_ad_accounts()
   facebook_ads_list_facebook_campaigns(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=200)
   ```
   Capture per campaign: `name`, `id`, `objective`, `buying_type`, `daily_budget` /
   `lifetime_budget`, `budget_optimization` (is this CBO / Advantage Campaign Budget?),
   `bid_strategy`, `special_ad_categories`, `created_time`, `effective_status`,
   `is_advantage_plus` / smart-promotion flag (Advantage+ Sales / App campaign).

2. **Pull ad sets and ads for active campaigns:**
   ```
   facebook_ads_list_facebook_ad_sets(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=500)
   facebook_ads_list_facebook_ads(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=1000)
   ```
   Capture ad-set: `optimization_goal`, `billing_event`, `bid_strategy`, `daily_budget`,
   `attribution_spec`, `targeting` summary, `learning_stage_info` (status =
   `LEARNING` / `SUCCESS` / `LEARNING_LIMITED`), `created_time`.

3. **Score each campaign across 5 dimensions (0-20 each, total 100):**

   | Dimension | What to check | Meta-specific gotchas |
   |---|---|---|
   | **Objective alignment** | Does the ODAX objective match the real goal? | `OUTCOME_SALES` for purchases, `OUTCOME_LEADS` for lead gen, `OUTCOME_ENGAGEMENT`/`OUTCOME_AWARENESS` only for upper funnel, `OUTCOME_TRAFFIC` only when there's no conversion event. A sales business running Traffic to "get cheap clicks" is the #1 silent waste. Also check the **ad-set `optimization_goal`** — `LINK_CLICKS` or `LANDING_PAGE_VIEWS` under a sales objective means you're optimizing for the wrong event. |
   | **Budget structure (CBO vs ABO)** | Advantage Campaign Budget vs ad-set budgets | CBO (Advantage Campaign Budget) lets Meta move money to the winning ad set, but starves good ad sets in small accounts and hides per-segment economics. ABO gives control but needs manual rebalancing. Neither is "right" — flag mismatches: CBO with one dominant ad set eating 90% (collapse to ABO), or ABO with 10 ad sets each below the 50-conversion threshold (consolidate). |
   | **Learning phase & fragmentation** | Are ad sets exiting learning? | Meta needs **~50 optimization events per ad set per 7 days** to exit learning. Count ad sets stuck in `LEARNING_LIMITED`. Fragmentation (too many ad sets / too many ads splitting conversions) is the #1 cause of perpetual learning. If conversions/ad set/week < 50, recommend consolidation. |
   | **Bid strategy alignment** | Cost controls match the goal? | `LOWEST_COST_WITHOUT_CAP` (Highest volume) for scale/prospecting; `COST_CAP` / `BID_CAP` / `LOWEST_COST_WITH_MIN_ROAS` (ROAS goal) for efficiency. A cost cap set too low silently throttles delivery to zero — a classic "why won't it spend" cause. |
   | **Creative count & Advantage+ Creative** | Enough creative variety per ad set? | Target 3-6 active ads per ad set. <3 = the optimizer can't optimize. Check whether Advantage+ Creative enhancements are on/off and whether that's appropriate (great for DR scale, risky for tightly-controlled brand). |

4. **Categorize campaigns into action buckets:**
   - **Fix:** Score <60 or critical issues (objective/optimization-goal mismatch, cost cap
     throttling delivery, single-ad ad sets, perpetual `LEARNING_LIMITED`, fragmentation).
   - **Tune:** Score 60-89. Functional but leaving performance on the table.
   - **Scale:** Score 90+. Healthy. Candidates for budget increase if headroom exists.

5. **Present the structural scorecard** before making recommendations. Don't fix silently.

## Phase 2: Pacing & Underspend Diagnosis

The most common silent failure on Meta: budget set but ad sets not delivering (stuck in
learning, cost cap too low, audience too small, or in review).

1. **Pull last-7-day spend per campaign vs its budget:**
   ```
   facebook_ads_get_facebook_insights(
     object_id=<act_id>, level="campaign",
     fields=["spend","impressions"], date_preset="last_7d",
     include_names=True)
   ```
   Compute `actual_daily_spend = spend / 7`. Compare to the campaign (CBO) or summed ad-set
   (ABO) budget. Pacing ratio = actual_daily / budget. <0.5 severe underspend; 0.5-0.8 mild;
   0.8-1.2 healthy; >1.2 lifetime budget exhausting early.

2. **For underspending campaigns, diagnose the layer:**

   | Layer | Symptom | Check via |
   |---|---|---|
   | **L1 — Delivery blocked** | Zero impressions today | `effective_status` = `WITH_ISSUES` / `DISAPPROVED` / `IN_PROCESS`; ad-set `learning_stage_info`; check `special_ad_categories` (housing/employment/credit/social-issue restrict targeting) |
   | **L2 — Audience too small / cost cap** | Some impressions, pacing <0.5 | Ad-set est. audience size; `bid_strategy`=COST_CAP/BID_CAP with a cap below market clearing price throttles to zero |
   | **L3 — Stuck in learning** | Spending but volatile, no stable CPA | `learning_stage_info.status` = `LEARNING_LIMITED`; conversions/ad set/week < 50 |
   | **L4 — Creative throttled** | Impressions concentrated on 1 ad | Ad-level insights; if top ad has >70% of impressions, the rest are throttled — usually fine (Meta picked a winner) unless the winner is fatiguing |
   | **L5 — Auction pressure / overlap** | CPM rising weekly | Compare CPM last 7d vs prior 7d; >20% rise on flat targeting = competitive surge or **audience overlap** between your own ad sets bidding against each other |

3. **Surface the underspend report:** total daily budget not being spent, by layer, top 5
   worst offenders with diagnosed root cause and $/day left on the table.

## Phase 3: Budget Reallocation

Highest-ROI move: shift budget from underperformers to outperformers.

1. **Pull 30-day campaign performance:**
   ```
   facebook_ads_get_facebook_insights(
     object_id=<act_id>, level="campaign",
     fields=["spend","impressions","actions","action_values","purchase_roas",
             "cost_per_action_type","ctr","cpm","frequency"],
     date_preset="last_30d", include_names=True)
   ```
   Resolve the correct conversion `action_type` for each campaign's objective before
   computing CPA/ROAS (see meta-mcp-tools.md).

2. **Classify by efficiency tier:**

   | Tier | Criteria | Action |
   |---|---|---|
   | **Scale** | CPA <= account median (or ROAS >= target) AND conversion volume rising 14d-over-14d | +20-30% budget |
   | **Hold** | At/below median CPA, volume flat | Maintain |
   | **Optimize** | Above median but trending down (improving) | Maintain, recheck next cycle |
   | **Cut** | CPA > 1.5x median AND no improvement | -20-50% or pause |

3. **If MMM is available, validate budget direction:**
   ```
   meridian_list_models()
   meridian_get_raw_channel_roi(model=<kpi>, channels=["meta"])   # or "facebook"
   meridian_get_reconciled_response_curves(model=<kpi>)
   meridian_simulate_budget_reallocation(... proposed shifts ...)
   ```
   Decision hierarchy: MMM + platform agree → high-confidence move. MMM says Meta saturated
   but platform says scale → trust the MMM, don't add budget. MMM says Meta under-invested
   but platform CPA rising → trust the MMM, reset per-conversion expectations. No MMM → use
   platform with the caveat that Meta over-attributes its own contribution (7d-click/1d-view).

4. **Cap-check moves:** per-campaign moves capped at +30%/-30% per cycle (avoids learning
   resets). **A budget change >~20-30% on Meta re-triggers the learning phase** — call this
   out explicitly. For ad sets in learning (<7 days from launch or last major edit), no
   changes. Keep total account change net-neutral unless the user authorizes scale.

## Phase 4: Creative Health

Lightweight read; hand off to the deep-dive skills.

1. **Quick fatigue scan:**
   ```
   facebook_ads_get_facebook_insights(
     object_id=<act_id>, level="ad",
     fields=["spend","impressions","reach","frequency","ctr","cpm",
             "video_p25_watched_actions","video_p100_watched_actions",
             "video_thruplay_watched_actions","actions","quality_ranking",
             "engagement_rate_ranking","conversion_rate_ranking"],
     date_preset="last_14d", include_names=True, sort=["spend_descending"], limit=100)
   ```

2. **Compute basic signals:** active ads per ad set (target 3-6); **frequency** (>2.5-3.0 in
   a 7-day window on prospecting = saturation risk); thumb-stop rate
   (`video_thruplay_watched_actions` or p25 / impressions); spend concentration (% on top 5
   ads); relevance diagnostics trending to `BELOW_AVERAGE`.

3. **Decide handoff:** rising frequency + falling CTR/relevance, or top spenders >21 days old
   → hand off to `meta-creative-fatigue-watchdog`. Ad sets with <3 active ads → flag for
   `meta-creative-refresh`. Placement-driven weakness → `meta-placement-performance`.

## Phase 5: Settings & Recommendations Audit

Meta surfaces native recommendations and auto-applies "Advantage" features. Evaluate them
critically.

| Meta-pushed pattern | When it's right | When it's wrong |
|---|---|---|
| Advantage+ Audience (auto-expand) | Prospecting at scale, broad DR | When a tightly-validated audience is winning — expansion bleeds budget to broad |
| Advantage Campaign Budget (CBO) | Many comparable ad sets, enough volume | Small accounts where it starves good ad sets / hides economics |
| Advantage+ Creative enhancements | DR scale, tolerant brand | Regulated/brand-strict accounts (text overlays, filters alter the asset) |
| "Consolidate / it's fragmented" | True when ad sets are sub-50 conversions | Not when ad sets are deliberately separated for measurement |
| Auto-applied recommendations toggle | Rarely | Usually OFF for managed accounts — silently changes settings |

Flag any campaign that has accepted a platform-preferred setting costing efficiency.

## Phase 6: Action Plan Compilation

1. **Group by risk:**
   - **Auto-approve (low):** pause obvious failures (zero conversions in 14d at >$500 spend),
     re-enable disapproved ads after compliance fix, fix optimization-goal mismatches.
   - **Recommend (medium):** budget shifts up to 20%, cost-cap loosening, single ad-set
     audience consolidation, creative handoffs.
   - **Needs discussion (high):** CBO↔ABO restructures, objective changes, Advantage+
     enable/disable, budget shifts >30%, ad-set consolidation that resets learning.

2. **Quantify expected impact** per recommendation ($ wasted now, projected conversions at
   current CPA, learning-reset cost).

3. **Deliver with explicit confirmation required on Needs Discussion items.**

## Phase 7: Recurring Cycle

- **Weekly:** $25K+/mo Meta accounts (Monday).
- **Bi-weekly:** $5K-$25K/mo.
- **Monthly:** <$5K/mo.

Each cycle references the previous report: did Fix-tier campaigns improve their score? did
the reallocation produce expected lift? are the same ad sets still in `LEARNING_LIMITED`
(structural, not tactical)? Suggest the `schedule` skill to automate.

## Inputs

1. **Ad account** — required (`facebook_ads_list_facebook_ad_accounts` if unknown)
2. **Scope** — full account / specific campaigns / objective (default: full account)
3. **Risk tolerance** — conservative / moderate / aggressive (default: moderate)
4. **Target CPA/ROAS** — to anchor tiering (optional but valuable)
5. **MMM model** — for budget direction validation (optional, strongly recommended)
6. **Previous cycle report** — for trend tracking (optional)

## Output

1. **Account Scorecard** — per campaign + overall
2. **Underspend Diagnosis** — by layer, $ left on the table, learning-phase census
3. **Budget Reallocation Plan** — scale / hold / optimize / cut
4. **Creative Health Snapshot** — frequency, fatigue flags, concentration, handoffs
5. **Settings Audit** — Advantage features & recommendations to roll back/keep
6. **Risk-Tiered Action Plan** — auto-approve / recommend / needs-discussion
7. **Next Cycle Plan**

## Important Notes

- **Meta's learning phase is ~50 events / ad set / 7 days.** Big edits reset it. Don't make
  changes on top of changes; let an edit settle ~7 days before judging.
- **Fragmentation is the silent killer.** More ad sets and more campaigns split the
  conversion volume so nothing exits learning. Consolidation usually beats expansion.
- **Platform CPA/ROAS over-credits Meta** (7d-click/1d-view + modeled conversions). The MMM
  cross-check is mandatory where Meta is >15% of paid spend. See `meta-capi-signal-health`
  for whether the signal feeding these numbers is even trustworthy.
- **iOS / SKAN attribution is delayed and modeled.** Don't kill iOS-heavy app campaigns on
  platform CPA alone — use MMM or an incrementality test (`meta-incrementality-test`).
- **Don't reallocate against creative weakness.** If conversions are low because creative is
  fatigued, more budget just buys more impressions for a tired ad. Run the creative health
  check before recommending increases.
- **Cross-skill handoffs:** creative → `meta-creative-fatigue-watchdog` / `meta-creative-refresh`;
  audience → `meta-audience-intelligence`; placements → `meta-placement-performance`;
  Advantage+ → `meta-advantage-plus-audit`; signal/CAPI → `meta-capi-signal-health`;
  incrementality → `meta-incrementality-test`; geo → `meta-geo-expansion`; launch →
  `meta-content-to-campaign`.
