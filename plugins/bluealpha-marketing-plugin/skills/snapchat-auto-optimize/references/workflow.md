# Snapchat Auto-Optimize: Detailed Workflow

> **Tool bindings are verified.** Every call below uses the exact tool ids and arguments in
> `references/snapchat-mcp-tools.md`; read it first. Run tools through the BlueAlpha connector:
> `search` to find them, then `execute(tool_id, arguments)`, passing `user_message` every time. Batch independent
> reads into one `execute(calls=[...])`.

The full optimization cycle for a Snapchat Ads account, the Snapchat counterpart of `auto-optimize` (Google),
`tiktok-auto-optimize` and `meta-auto-optimize`. Run it weekly on high-spend accounts, every two weeks otherwise. The
output is a scorecard and a risk-tiered list of changes.

The skill is analysis-first. It can apply pause, budget, bid and rename changes when the user asks and has write
access, following "Applying changes" in the tool reference (Phase 7).

## Phase 1: Resolve the account

1. List the accounts and confirm which one, unless the user named it:
   ```
   execute(tool_id="snapchat_ads.list_snapchat_ad_accounts", arguments={})
   ```
   Note the account's `currency`, `timezone`, `roles` and `organization_id`.
   - **The windows below are calendar days in the account's timezone.** Today is partial, so the
     last 7 days end yesterday.
   - **Roles:** `roles: ["reports"]` can read but not change anything. Note it now, since it decides
     whether Phase 7 is possible at all.

## Phase 2: Structural audit

1. **Pull the structure.** Read campaigns and ad squads in one batch:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_campaigns", arguments: {ad_account_id, status: "ACTIVE"}},
     {tool_id: "snapchat_ads.get_snapchat_ad_squads", arguments: {ad_account_id, limit: 100}}
   ])
   ```
   Then read ads one live campaign at a time. An account-wide ad listing on a long-running account is large and
   stops at `limit`:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_ads", arguments={ad_account_id, campaign_id: <live campaign id>, limit: 100})
   ```
   If a listing comes back with `complete: false`, narrow it by campaign and say which campaigns were read.

2. **Find what's actually live.**
   - `status: ACTIVE` only means not paused.
   - An entity delivers only when its `delivery_status` is `["VALID"]`.
   - Everything else carries `INVALID_*` codes, such as `INVALID_END_TIME` or `INVALID_NOT_EFFECTIVE_ACTIVE`.
     Report them exactly as Snap gives them.
   - Score only VALID campaigns and ad squads. List ACTIVE-but-invalid ones separately as hygiene; old accounts
     often have many.

3. **Capture per campaign:**
   - `objective_v2_properties` (`objective_v2_type`, `promotion_type`);
   - `pacing_level` (`CAMPAIGN` = Smart Budgets);
   - `daily_budget` or `lifetime_spend_cap`, `buy_model`, start and end time.

   **Per ad squad:**
   - `optimization_goal`, `bid_strategy`, `bid`;
   - `daily_budget` or `lifetime_budget`, `pacing_type`;
   - `targeting_reach_status`, `enable_targeting_expansion` and `auto_expansion_options`;
   - `targeting.regulated_content`, `event_sources`, `pixel_id`.

   **Per ad:**
   - `review_status` and `review_status_reasons`, `creative_id`, `delivery_status`.

4. **Score each live campaign on five dimensions, 0-20 each, total 100:**

   | Dimension | What to check | Snapchat specifics |
   |---|---|---|
   | **Objective and goal alignment** | Does each ad squad's `optimization_goal` serve the campaign's objective and the business goal? | An app campaign optimizing `APP_INSTALLS` when the business is paid on purchases or sign-ups optimizes the cheap event, not the valuable one. A sales or web campaign on `SWIPES` or `IMPRESSIONS` buys attention, not conversions. |
   | **Bid strategy fit** | Does `bid_strategy` match the volume and goal? | `AUTO_BID` suits new or low-volume ad squads. `TARGET_COST` needs steady volume, and its `bid` is a cost target: compare it with the cost per result actually achieved (Phase 4). `LOWEST_COST_WITH_MAX_BID` with a cap below the market price throttles delivery. |
   | **Learning and volume** | Do ad squads get enough results to optimize? | Count each ad squad's goal-matched results over the last 7 days (Phase 4 pull). Snap's guidance is roughly 50 optimization events a week for stable delivery: treat it as a guide, not a hard line. Many ad squads splitting a small volume is fragmentation. |
   | **Delivery health** | Is anything blocked? | Ads not `APPROVED` (with `review_status_reasons`); ad squads whose `targeting_reach_status` isn't `VALID`; end times passed; ACTIVE ad squads with no VALID ad. |
   | **Creative depth** | Enough approved, delivering ads per ad squad? | Fewer than 3 VALID ads per ad squad leaves the system little to choose from; one ad carrying an ad squad is a single point of failure. |

5. **Sort campaigns into buckets:**
   - **Fix:** score under 60, or any blocker (rejected ads, invalid reach, goal mismatch, one-ad ad squads).
   - **Tune:** 60-89.
   - **Scale:** 90 and above; a candidate for more budget if Phase 4 agrees.

6. **Show the structural scorecard before any recommendation.** Never fix silently.

## Phase 3: Pacing and underspend

1. **Pull the last 7 days of spend per ad squad, one campaign at a time** (on an account, a breakdown only goes down
   to campaigns):
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={
     ad_account_id, level: "campaign", entity_id: <campaign_id>, granularity: "TOTAL",
     start_date: <7 days ago>, end_date: <yesterday>, breakdown: "ad_squad", include_names: true,
     fields: ["spend", "impressions", "swipes"]})
   ```
   Batch the campaigns into one `execute(calls=[...])`.

2. **Work out pacing.** Pacing = (spend ÷ 7) ÷ daily budget. Use the campaign's budget for a Smart Budgets campaign,
   and the ad squad's otherwise.

   | Pacing | Reading |
   |---|---|
   | < 0.5 | Severe underspend |
   | 0.5-0.8 | Mild underspend |
   | 0.8-1.2 | Healthy |
   | > 1.2 | Overspend, or a lifetime budget running out early |

3. **For each underspender, find the layer:**

   | Layer | Symptom | Check |
   |---|---|---|
   | **L1: Delivery blocked** | No impressions | `delivery_status` codes; ads not approved; end time passed |
   | **L2: Bid too tight** | Some impressions, pacing < 0.5 | `LOWEST_COST_WITH_MAX_BID` or `TARGET_COST` set below what results cost (Phase 4) |
   | **L3: Audience too narrow** | Low impressions on any bid | `targeting_reach_status`; narrow age, geo or device targeting; many `EXCLUDE` segments; `regulated_content` restrictions |
   | **L4: Not enough volume** | Spends, but results erratic | Well under about 50 goal results a week (Phase 2 dimension 3) |
   | **L5: Auction pressure** | Cost per thousand impressions rising | CPM = spend ÷ impressions × 1,000, last 7 days against the 7 before; over 20% up on unchanged targeting |

4. **Report:** the total daily budget going unspent, by layer, with the five worst ad squads, each with its cause and
   the money per day left unspent.

## Phase 4: Results and budget reallocation

1. **Pull 30 days of results per ad squad.** For each campaign, request the result metric of each ad squad's goal
   from the table in the tool reference:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={
     ad_account_id, level: "campaign", entity_id: <campaign_id>, granularity: "TOTAL",
     start_date: <30 days ago>, end_date: <yesterday>, breakdown: "ad_squad", include_names: true,
     fields: ["spend", "impressions", "swipes", <result metric>, <its value metric, if any>]})
   ```
   Repeat for the 7 days used in Phase 2, and for the 14 days before, to see the trend.

2. **Work out each ad squad's economics:**
   - cost per result = spend ÷ results;
   - ROAS = value ÷ spend, only when `conversion_purchases_value` is above 0. Otherwise say ROAS is unavailable
     because no purchase values are sent.

   Compare ad squads only with others on the same goal. Never compare cost per install with cost per purchase.

3. **Sort by efficiency, within each goal:**

   | Tier | Criteria | Move |
   |---|---|---|
   | **Scale** | Cost per result at or under the goal's median (or the user's target), and results rising over 14 days | +15-20% budget |
   | **Hold** | At or under median, flat | Keep |
   | **Optimize** | Over median but improving | Keep; recheck next cycle |
   | **Cut** | Over 1.5× median and not improving | -20% or pause |

   For `TARGET_COST` ad squads, also compare the achieved cost per result with the `bid` target:
   - **well under the target:** room to scale;
   - **at or over it:** the target is binding delivery.

4. **Check the direction against the MMM, if there is one.** `search` for "MMM channel ROI" and "budget reallocation
   simulation". If a model covers Snapchat:
   - read its ROI and response curve for Snapchat, and simulate the proposed shift;
   - where the MMM and the platform agree, move with confidence;
   - where the MMM says Snapchat is saturated, don't add budget, whatever the platform says;
   - where the MMM says it's under-invested, reset the platform cost expectations.

   With no model, say so: Snapchat's numbers are platform-attributed (28-day swipe, 1-day view by default) and
   over-credit Snapchat.

5. **Size the moves:**
   - **Keep each change at or under 20% a cycle.** Snapchat's write guardrails warn above 20%, and big changes can
     disturb delivery.
   - **Leave recently changed ad squads alone.** Don't touch one launched or changed in the last 7 days;
     `snapchat-change-impact-review` shows what changed.
   - **Keep the account's total flat** unless the user wants to scale.
   - **Respect Smart Budgets.** In a Smart Budgets campaign, move the campaign's budget, not an ad squad's.

## Phase 5: Creative health (light)

1. **Pull the last 14 days per ad** for the live campaigns:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={
     ad_account_id, level: "campaign", entity_id: <campaign_id>, granularity: "TOTAL",
     start_date: <14 days ago>, end_date: <yesterday>, breakdown: "ad", include_names: true,
     fields: ["spend", "impressions", "swipes", "video_views", "video_views_15s"]})
   ```
   Then pull `frequency` per campaign: `granularity: "TOTAL"` with `fields: ["frequency", "uniques"]` and no
   breakdown.

2. **Basic signals:**
   - **Swipe rate** = swipes ÷ impressions (`swipe_up_percent` is the same fraction).
   - **15-second view rate** = `video_views_15s` ÷ `video_views`.
   - **Spend concentration:** the share of spend on the top 3 ads.
   - **VALID ads per ad squad.**
   - **Frequency** over 2 a week on a broad audience is a saturation risk to watch (Snap's own 2019 research
     suggested about 2 exposures a week).

3. **Hand off:**
   - falling swipe rate with rising frequency, or top spenders running for weeks → `snapchat-creative-fatigue-watchdog`;
   - ad squads with under 3 VALID ads → `snapchat-creative-refresh`.

## Phase 6: Snapchat settings audit

| Setting | When it's right | When it's wrong |
|---|---|---|
| Targeting expansion (`enable_targeting_expansion`, `auto_expansion_options`) | Broad prospecting with enough volume | A tightly validated audience that's winning: expansion moves spend to cheaper, weaker reach |
| Smart Budgets (`pacing_level: CAMPAIGN`) | Several comparable ad squads with enough volume | Small campaigns, or ad squads kept apart on purpose for measurement |
| `TARGET_COST` | Steady volume and a known target cost | New ad squads, or a target far from the achieved cost |
| `pacing_type: ACCELERATED` | Short bursts (launches, events) | Always-on campaigns: spends early in the day |
| `brand_safety_config` `FULL_INVENTORY` | Performance with no brand constraints | Regulated or brand-strict advertisers |

Flag each setting that costs efficiency for this account, with the evidence.

## Phase 7: Action plan, and applying it

1. **Group the changes by risk:**
   - **Low:**
     - pause what's clearly failing (no goal results in 14 days with spend over $500, for example);
     - renames for clarity.
   - **Medium:** budget moves up to 20%; loosening a bid that's throttling delivery; creative hand-offs.
   - **Needs discussion:** objective or goal changes (a new ad squad, since Snap doesn't let a goal change),
     Smart Budgets on or off, targeting changes, budget moves over 20%.

2. **Size the impact of each change:** money wasted now, results projected at the current cost per result, and what
   the change risks.

3. **Offer to apply.** Offer only if the user asks, or accepts the offer. Only pause, budget, bid and rename changes
   qualify, from the Low and Medium groups. Follow "Applying changes" in the tool reference exactly:
   - one change per `execute`, shown first and confirmed;
   - Smart Budgets and `AUTO_BID` rules checked first;
   - the outcome reported as given, stopping on anything but `applied`.

   Everything else stays a recommendation for the user to make in Ads Manager.

## Phase 8: Recurring cycle

- **Weekly:** accounts spending over $25K a month on Snapchat.
- **Every two weeks:** $5K-$25K a month.
- **Monthly:** under $5K a month.

Each cycle opens with the last one's report:
- Did the Fix campaigns improve?
- Did the moves pay off? Compare each changed ad squad's cost per result before and after, over at least 7 days.
- Are the same ad squads still short of volume? That's structural, not tactical.

Suggest the `schedule` skill to run it automatically.

## Inputs

1. **Ad account:** required (`snapchat_ads.list_snapchat_ad_accounts` if unknown).
2. **Scope:** whole account, specific campaigns, or one objective (default: whole account).
3. **Risk tolerance:** conservative, moderate or aggressive (default: moderate).
4. **Target cost per result or ROAS:** anchors the tiers (optional, valuable).
5. **MMM model:** for budget direction (optional, strongly recommended).
6. **Previous cycle's report:** for trends (optional).

## Output

1. **Account scorecard:** per campaign and overall, plus ACTIVE-but-not-delivering hygiene.
2. **Underspend diagnosis:** by layer, money per day unspent, volume census.
3. **Budget plan:** Scale, Hold, Optimize, Cut, within each goal.
4. **Creative health snapshot:** swipe rate, 15-second view rate, frequency, hand-offs.
5. **Settings audit.**
6. **Risk-tiered change list,** with what can be applied and what can't.
7. **Applied changes,** if any: each with its outcome as the tool reported it.
8. **Next cycle plan,** with the metric each change should move.

## Important notes

- **Conversion numbers for the last day or two aren't final.** Pass on the response's `notes` whenever results
  include days after `conversion_data_processed_end_time`.
- **Snapchat attributes to itself.** Defaults are 28-day swipe and 1-day view. iOS app results also depend on
  SKAdNetwork enrolment (`skadnetwork_properties` on ad squads, `mobile_app_properties` on campaigns). Don't cut iOS
  app campaigns on platform cost alone: check the MMM, or run `snapchat-incrementality-test`.
- **Don't add budget behind tired creative.** Run the Phase 5 check before recommending increases.
- **Hand-offs to the other Snapchat skills:**
  - performance read → `snapchat-performance-digest`;
  - creative → `snapchat-creative-fatigue-watchdog`, `snapchat-creative-refresh`;
  - audiences → `snapchat-audience-intelligence`;
  - geos → `snapchat-geo-expansion`;
  - "what changed?" → `snapchat-change-impact-review`;
  - catalogs and dynamic ads → `snapchat-dynamic-ads-audit`;
  - lead forms → `snapchat-lead-gen-auditor`;
  - conversion trust → `snapchat-pixel-signal-health`;
  - lift → `snapchat-incrementality-test`;
  - everything → `snapchat-full-monty`.
