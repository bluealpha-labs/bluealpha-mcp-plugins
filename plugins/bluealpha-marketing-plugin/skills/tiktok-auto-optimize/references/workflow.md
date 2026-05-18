# TikTok Auto-Optimize — Detailed Workflow

The full optimization cycle for a TikTok Ads account, equivalent to the `auto-optimize` skill for Google Ads. Designed to be run weekly (high-spend) or bi-weekly. Output is an actionable scorecard + recommended changes, with risk-tiered grouping.

This skill is analysis and recommendation only. Execution (campaign edits, budget changes, pauses) routes through the BlueAlpha pipeline.

**MCP capabilities used:** BASIC report for entity-level (`campaign_id`, `adgroup_id`, `ad_id`, `country_code`, `stat_time_day`); AUDIENCE report (`report_type="AUDIENCE"`) for placement / demographic / DMA / interest slicing when needed; `include_names=true` to attach campaign/adgroup/ad names and objective_type to insights rows in a single call.

## Phase 1: Structural Audit

Before optimizing the levers, check the foundations.

1. **Resolve advertiser & pull campaigns:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   tiktok_ads_get_tiktok_campaigns(
     advertiser_id=<id>,
     primary_status="STATUS_DELIVERY_OK",
     page_size=200
   )
   ```
   Capture for each campaign: `campaign_name`, `campaign_id`, `objective_type`, `budget_mode`, `budget`, `campaign_automation_type`, `secondary_status`, `create_time`, `is_smart_performance_campaign`.

2. **Pull ad groups for active campaigns:**
   ```
   tiktok_ads_get_tiktok_adgroups(
     advertiser_id=<id>,
     primary_status="STATUS_DELIVERY_OK",
     page_size=500
   )
   ```

3. **Score each campaign across 5 dimensions (0-20 each, total 100):**

   | Dimension | What to check | TikTok-specific gotchas |
   |---|---|---|
   | **Objective alignment** | Does objective match the actual goal? | `APP_PROMOTION` for app installs, `WEB_CONVERSIONS` for site conversions, `TRAFFIC` only when there's no conversion event. Misaligned objectives are the #1 silent waste. |
   | **Budget structure** | Budget mode + amount appropriate? | `BUDGET_MODE_INFINITE` only works if adgroup-level budgets are set. Otherwise it's a runaway. Daily vs. lifetime — lifetime usually pacing-trapped. |
   | **Automation level** | Smart+ / Smart Performance / manual appropriate? | `UPGRADED_SMART_PLUS` is TikTok's newest automation tier. Strong for app installs at scale, weak for low-volume web conversions. Match the tool to the data volume. |
   | **Targeting breadth** | Adgroup audience definition reasonable? | Over-narrow targeting on TikTok is the #1 cause of underdelivery. The platform wants 3M+ audience size to optimize. |
   | **Creative count** | At least 3-5 active ads per adgroup? | TikTok needs creative variety. <3 active ads = the optimizer can't actually optimize. |

4. **Categorize campaigns into action buckets:**
   - **Fix:** Score <60 or critical issues (e.g., objective mismatch, single-ad adgroups, frozen pacing)
   - **Tune:** Score 60-89. Functional but leaving performance on the table.
   - **Scale:** Score 90+. Healthy. Candidates for budget increase if headroom exists.

5. **Present the structural scorecard** to the user before making any recommendations. Don't fix silently.

## Phase 2: Pacing & Underspend Diagnosis

The most common silent failure on TikTok: budget set but ad groups not actually delivering.

1. **Pull last-7-day spend per campaign vs. its budget:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_CAMPAIGN",
     dimensions=["campaign_id"],
     metrics=["spend", "impressions"],
     start_date=<7_days_ago>,
     end_date=<today>
   )
   ```
   For each campaign, compute: `actual_daily_spend = spend / 7`. Compare to `budget` from campaign data.
   - Pacing ratio = actual_daily / budget
   - <0.5 = severe underspend
   - 0.5-0.8 = mild underspend
   - 0.8-1.2 = healthy
   - >1.2 = lifetime budget exhausting

2. **For underspending campaigns, diagnose the layer:**

   | Layer | Symptom | Check via |
   |---|---|---|
   | **L1 — Delivery blocked** | Zero impressions today | `tiktok_ads_get_tiktok_adgroups` → `secondary_status` for review/disapproved/learning-paused states |
   | **L2 — Targeting too narrow** | Some impressions but pacing <0.5 | Pull adgroup targeting; flag audience sizes <500K or interest stacks of >5 interests AND&'d together |
   | **L3 — Bid too low** | Impressions but no learning exit | Check `bid_type` and `bid_price` per adgroup; cross-reference against vertical CPM benchmarks |
   | **L4 — Creative throttled** | Impressions concentrated to 1-2 ads | Pull ad-level insights via creative-insights, look for impression distribution; if top 1 ad has >70% of impressions, the rest are throttled |
   | **L5 — Auction pressure** | CPM rising weekly | Compare CPM trend last 7d vs. prior 7d; >20% rise on flat targeting = competitive surge |

3. **Surface the underspend report:**
   - Total daily budget not being spent
   - By layer: how many campaigns affected, total daily $ lost
   - Top 5 worst offenders with diagnosed root cause

## Phase 3: Budget Reallocation

The highest-ROI optimization move: move budget from underperformers to outperformers.

1. **Pull 30-day campaign performance for reallocation analysis:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_CAMPAIGN",
     dimensions=["campaign_id"],
     metrics=["spend", "conversion", "cost_per_conversion", "conversion_rate", "ctr", "cpm"],
     start_date=<30_days_ago>,
     end_date=<today>,
     order_field="spend",
     order_type="DESC"
   )
   ```

2. **Classify campaigns by efficiency tier:**

   | Tier | Criteria | Action |
   |---|---|---|
   | **Scale** | CPA <= account median AND conversion volume rising 14d-over-14d | Increase budget +20-30% |
   | **Hold** | CPA <= account median AND conversion volume flat | Maintain |
   | **Optimize** | CPA > account median but trending down (improving) | Maintain, recheck next cycle |
   | **Cut** | CPA > 1.5x account median AND no improvement trend | Reduce budget -20-50% or pause |

3. **If MMM is available, validate budget direction:**
   ```
   meridian_get_raw_channel_roi(model_id, channel="tiktok")
   meridian_get_raw_saturation_curves(model_id, channel="tiktok")
   meridian_simulate_budget_reallocation(model_id, scenario=<proposed_shifts>)
   ```

   **Decision hierarchy:**
   - MMM and platform agree → high-confidence reallocation
   - MMM says TikTok is saturated but platform says scale → trust the MMM, don't add budget
   - MMM says TikTok is under-invested but platform CPA is rising → trust the MMM, reduce per-conversion expectations
   - No MMM → use platform with the caveat that TikTok over-attributes its own contribution

4. **Recommended moves, cap-checked:**
   - Per-campaign budget moves capped at +30% / -30% per cycle (avoids learning-phase resets)
   - Total account budget change should be net-neutral unless user explicitly authorizes scale
   - For campaigns in learning phase (<14 days from launch or last major edit): no budget changes

## Phase 4: Creative Health

Pull the lightweight creative read. Hand off to other skills for deep dives.

1. **Quick fatigue scan:**
   ```
   tiktok_ads_get_tiktok_creative_insights(
     advertiser_id=<id>,
     start_date=<14_days_ago>,
     end_date=<today>,
     metrics=["spend", "impressions", "ctr", "video_views_p25", "video_views_p50",
              "video_views_p100", "conversion", "cost_per_conversion"],
     page_size=100
   )
   ```

2. **Compute basic creative health signals:**
   - Active ads per adgroup (target: 3-5 minimum)
   - Top 10 ads by spend: ages from `create_time`, hook rates from `video_views_p25 / impressions`
   - Spend concentration: % of total spend on top 5 ads (>60% = portfolio risk)

3. **Decide handoff:**
   - 3+ ads with hook rate decay >15% or top spenders >21 days old → hand off to `tiktok-creative-fatigue-watchdog`
   - Adgroups with <3 active ads → flag for `tiktok-creative-refresh` to brief new variants
   - Spend concentrated to one ad → recommend new variants to diversify

## Phase 5: Recommendations Review

TikTok also surfaces native recommendations. Evaluate them with the same critical eye as Google's recommendations.

1. **There is no recommendations endpoint** in the current TikTok MCP. Instead, audit for common TikTok-pushed patterns the marketer should be cautious about:

   | TikTok-pushed pattern | When it's right | When it's wrong |
   |---|---|---|
   | "Upgrade to Smart+" / Smart Performance Campaign | High-volume app install accounts | Low-volume web conversion accounts — kills the ability to diagnose what's working |
   | "Expand targeting" / Auto-targeting | When current targeting is saturated | When current targeting is winning — auto-targeting bleeds budget to broader audiences |
   | "Increase budget" alerts | Campaign is hitting budget cap with strong CPA | Campaign is failing to spend — budget isn't the problem |
   | Suggested interest expansion | Cohort-validated additions only | Auto-suggested interests often have no audience overlap with the winning segment |

2. **Audit current settings against these patterns** — flag any campaign that has accepted a "platform-preferred" setting that's costing the user efficiency.

## Phase 6: Action Plan Compilation

Compile everything into a single risk-tiered action plan.

1. **Group recommendations by risk level:**

   - **Auto-approve (low risk):** Pause obvious failures (zero conversions in 14d at >$500 spend), enable disapproved ads after compliance fix
   - **Recommend (medium risk):** Budget shifts up to 20%, bid adjustments, single-adgroup audience expansions
   - **Needs discussion (high risk):** Campaign restructures, objective changes, Smart+ enablement/disablement, budget shifts >30%

2. **Quantify expected impact per recommendation:**
   - For budget moves: projected change in spend, projected change in conversions (using current campaign CPA)
   - For pacing fixes: dollars currently being left on the table
   - For creative handoffs: estimated wasted spend from the fatigue read

3. **Deliver the report with explicit confirmation required on Needs Discussion items.**

## Phase 7: Recurring Cycle

This skill should run on a recurring schedule.

- **Weekly:** Accounts spending $25K+/month on TikTok. Run every Monday.
- **Bi-weekly:** $5K-$25K/month accounts.
- **Monthly:** <$5K/month accounts.

Each cycle should reference the previous report:
- Did Fix-tier campaigns improve their structural score?
- Did the budget reallocation produce expected lift?
- Are pacing issues persisting in the same campaigns (suggests structural problem, not tactical)?

Suggest the `schedule` skill for automation.

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required (use `tiktok_ads_list_tiktok_advertisers` if unknown)
2. **Scope** — full account / specific campaigns / specific objective (default: full account)
3. **Risk tolerance** — conservative / moderate / aggressive (default: moderate)
4. **MMM model** — for budget direction validation (optional)
5. **Previous cycle report** — for trend tracking (optional)
6. **Budget constraints** — max daily spend, campaign caps (optional)

## Output

Deliver to the user:

1. **Account Scorecard** — score per campaign + overall
2. **Underspend Diagnosis** — by-layer breakdown, $ left on the table
3. **Budget Reallocation Plan** — campaigns to scale / hold / optimize / cut
4. **Creative Health Snapshot** — fatigue flags, spend concentration, handoffs
5. **Settings Audit** — TikTok-pushed patterns to roll back
6. **Risk-Tiered Action Plan** — auto-approve / recommend / needs-discussion
7. **Next Cycle Plan** — what to watch

## Important Notes

- **TikTok's learning phase is 7 days, not 14.** After a budget change, audience change, or creative change that triggers a learning-phase reset, give it a full 7 days before judging. Cycling weekly is fine as long as you don't make changes on top of changes.
- **Smart+ campaigns deserve special handling.** They're black-box optimized — you can't run conventional structural audits on them. Treat them as a single unit: is it hitting target CPA at scale or not? If not, the only lever is the creative pool and the budget. Don't try to micro-optimize the audience or bid strategy.
- **Platform CPA is unreliable, especially on TikTok.** TikTok defaults to 7-day click + 1-day view attribution, which over-credits TikTok for conversions that would have happened anyway. The MMM cross-check is mandatory for accounts where TikTok is >15% of paid spend.
- **Don't reallocate against creative weakness.** If a campaign has low conversions because its creative is fatigued, more budget won't help — it'll just buy more impressions for the same bad creative. Always run the creative health check before recommending budget increases.
- **iOS attribution is broken.** For iOS app-promotion campaigns (`IOS14_CAMPAIGN`), expect platform-reported conversion data to be 30-60% lower than reality due to SKAdNetwork. Don't kill iOS campaigns based on platform CPA alone — use the MMM or run an incrementality test.
- **Cross-skill handoffs:** Creative weakness → `tiktok-creative-fatigue-watchdog` or `tiktok-creative-refresh`. Audience signal issues → `tiktok-audience-intelligence`. Need to validate a campaign's actual incrementality → `tiktok-incrementality-test`. Underspend in specific geos → `tiktok-geo-expansion`. New content to promote → `tiktok-content-to-campaign`.
