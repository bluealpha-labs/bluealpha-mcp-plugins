# TikTok Audience Intelligence — Detailed Workflow

Audience analysis on TikTok plays out across overlapping dimensions: demographics (age/gender), geos (country / province / DMA), placements (TikTok / Pangle / Global App Bundle), interests, and connection types. This skill produces a tier map (which segments to scale, hold, optimize, cut) and a candidate-interest shortlist for new tests.

**Two read patterns:**
1. **AUDIENCE report (primary)** — `report_type="AUDIENCE"` on `get_tiktok_insights` exposes who TikTok's algorithm actually delivered the ad to. Valid dimensions: `age`, `gender`, `placement`, `province_id`, `dma_id`, `interest_category`, `ac` (connection type). This is the right read for Smart+ campaigns where targeting is algorithm-driven.
2. **Adgroup-config-join (fallback)** — When campaigns are manually configured with explicit `age_groups` / `interest_category_ids` / `placements` per adgroup, joining adgroup metadata to adgroup-level BASIC insights gives an interaction-aware read that captures audience × creative behavior.

Use the AUDIENCE report by default; fall back to the join pattern only when the user explicitly wants the audience-creative interaction view.

**Critical iOS attribution caveat:** for iOS app-promotion accounts (Klover-style), expect 60-80% of TikTok-reported conversions to land in "Unknown" buckets across all audience dimensions (`age: NONE`, `gender: NONE`, `dma_id: 0`, `province_id: -1`, `ac: UNKNOWN`). These are SKAdNetwork-attributed conversions that arrive without device-level signal. Phase 4 below handles the attribution split explicitly.

## Phase 1: Pull the AUDIENCE Reports

1. **Resolve advertiser:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   ```

2. **Demographic slice (age × gender):**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["age", "gender"],
     metrics=["spend", "impressions", "clicks", "ctr", "cpm",
              "conversion", "cost_per_conversion", "conversion_rate"],
     start_date=<30_days_ago>,
     end_date=<today>,
     page_size=50
   )
   ```
   Returns rows for each age × gender combination plus `NONE` buckets for un-attributed conversions.

3. **Placement slice:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["placement"],
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>
   )
   ```
   Values: `PLACEMENT_TIKTOK`, `PLACEMENT_PANGLE`, `PLACEMENT_GLOBAL_APP_BUNDLE`.

4. **Geo slices — country, then sub-country:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     dimensions=["country_code"],   // BASIC report
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>
   )
   ```
   For US accounts, also pull DMA and province:
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["dma_id"],
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>,
     order_field="spend",
     order_type="DESC",
     page_size=50
   )
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["province_id"],
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>,
     order_field="spend",
     order_type="DESC",
     page_size=50
   )
   ```

5. **Interest category slice:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["interest_category"],
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>,
     order_field="spend",
     order_type="DESC",
     page_size=30
   )
   ```
   Returns `interest_category` IDs and `interest_category_v2` IDs. Cross-reference with `get_tiktok_interest_categories` to map IDs to readable names.

6. **Connection type slice:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["ac"],
     metrics=[<same>],
     start_date=<30_days_ago>,
     end_date=<today>
   )
   ```
   Values: `WIFI`, `5G`, `4G`, `3G`, `2G`, `UNKNOWN`. WiFi vs cellular splits matter — WiFi typically converts better for at-home/planning-mode actions (e.g., financial app sign-ups).

7. **Adgroup-level BASIC insights with names** (used both for adgroup tier map AND for fallback adgroup-config-join):
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_ADGROUP",
     dimensions=["adgroup_id"],
     metrics=["spend", "impressions", "clicks", "ctr", "cpm",
              "conversion", "cost_per_conversion", "conversion_rate"],
     start_date=<30_days_ago>,
     end_date=<today>,
     order_field="spend",
     order_type="DESC",
     include_names=True,
     page_size=200
   )
   ```
   `include_names=True` returns `campaign_name`, `adgroup_name`, and `objective_type` inline — no separate join required.

## Phase 2: iOS SKAdNetwork Attribution Split

Before computing tier maps, identify and isolate the "Unknown" attribution buckets. These distort demographic reads if mixed with device-attributed conversions.

1. **Identify the unknown buckets** in each dimension:
   - Demographic: rows with `age: "NONE"` or `gender: "NONE"`
   - DMA: row with `dma_id: "0"`
   - Province: row with `province_id: "-1"`
   - Connection type: row with `ac: "UNKNOWN"`

2. **Compute the attribution split per dimension:**
   - `attributed_conv = sum(conversions in rows with concrete dimension values)`
   - `unknown_conv = sum(conversions in NONE / 0 / -1 / UNKNOWN rows)`
   - `attribution_completeness = attributed_conv / (attributed_conv + unknown_conv)`
   - For iOS-heavy accounts, expect 20-40% completeness. Pure-Android or web-conversion accounts should be 90%+.

3. **Report both numbers in the deliverable:**
   - The tier map is computed on **attributed conversions only** (the rows with concrete dimension values) — this is the demographic read leadership wants
   - The total platform-reported CPA is computed on **all conversions** (attributed + unknown) — this is the headline number TikTok shows in its UI
   - The gap between them is the SKAdNetwork attribution-loss indicator

4. **Decision flag:**
   - Completeness >70% → high confidence in demographic-level decisions
   - 40-70% → directional only, validate before scaling
   - <40% → demographic tier map is unreliable. Recommend running an incrementality test (`tiktok-incrementality-test`) instead of acting on the demographic read

## Phase 3: Compute Efficiency Score & Tier Map

Score each segment (using **attributed-only** conversions per Phase 2).

1. **Per-segment Efficiency Score (0-100):**
   - **Profitability (55%):** Inverse-normalized CPA against account median
   - **Quality (22.5%):** Conversion rate normalized against account median
   - **Scale (22.5%):** Spend share against the top segment in its dimension

2. **Apply minimum-volume thresholds:**
   - Spend < $200 in window → flag as `INSUFFICIENT_DATA`, don't score
   - <10 conversions → score is directional only

3. **Bucket into tiers:**

   | Tier | Criteria | Action |
   |---|---|---|
   | **Gold** | Score 80+ AND >$500 weekly spend | Scale — increase budget weight, expand to similar segments |
   | **Silver** | Score 60-79 | Hold and test expansion |
   | **Bronze** | Score 40-59 | Watch; may improve with creative or LP test |
   | **Cut** | Score <40 AND >$500 wasted weekly | Exclude or reduce |

4. **Cross-dimension intersection.** For Gold-tier segments in one dimension, observe how they distribute across other dimensions (e.g., does the winning age bucket cluster in specific DMAs? Specific placements?). The compound segments often have 30-50% better CPA than any single dimension alone.

## Phase 4: Adgroup-Config-Join Fallback (manual targeting accounts only)

Skip this phase entirely for Smart+ accounts. Run it when:
- The user explicitly wants an audience × creative interaction read
- Campaigns have meaningful manual targeting variation per adgroup
- AUDIENCE report completeness is too low (<40%) to be useful

1. **Pull adgroup configuration:**
   ```
   tiktok_ads_get_tiktok_adgroups(
     advertiser_id=<id>,
     primary_status="STATUS_DELIVERY_OK",
     page_size=500
   )
   ```
   Per adgroup: `age_groups`, `gender`, `placements`, `location_ids`, `interest_category_ids`, `audience_ids`, `excluded_audience_ids`, `optimization_event`, `campaign_automation_type`.

2. **Join adgroup config to adgroup performance** (from Phase 1, step 7).

3. **Aggregate up by attribute** (spend-weighted): for each `age_groups` value, `gender` value, `placement` etc., sum spend and conversions across the adgroups using that value. Compute attribute-level CPA.

4. **Compare to AUDIENCE report.** If the manual-targeting attribute analysis disagrees with the AUDIENCE report read, the disagreement is informative: the algorithm is delivering differently than the manual config implies.

## Phase 5: Interest Expansion Shortlist

Find adjacent interests worth testing.

1. **Pull full interest taxonomy:**
   ```
   tiktok_ads_get_tiktok_interest_categories(
     advertiser_id=<id>,
     version=2
   )
   ```

2. **Map currently-targeted interests** to taxonomy nodes (from adgroup `interest_category_ids`).

3. **Identify candidates:**
   - **Sibling adjacencies:** other sub-categories under the same parent as winning interests from Phase 3
   - **Cohort whitespace:** parent categories with zero adgroup coverage that are relevant to the vertical
   - **Performance-back-up:** interest IDs that appear in the AUDIENCE-report Gold tier but aren't in any current adgroup targeting (indicates Smart+ found them organically — formalize via dedicated adgroups)

4. **Score candidates:** adjacency strength + vertical relevance + estimated audience size + concentration in Gold-tier segments.

5. **Produce a test shortlist** of 5-10 candidate interests with suggested test budgets ($50-100/day for 7-14 days).

## Phase 6: Recommendations

1. **Demographic recommendations:**
   - Gold-tier age × gender combos: confirm campaigns aren't over-restricting; bid weight increases where applicable
   - Cut-tier combos consistently underperforming: exclude at adgroup level
   - iOS attribution-completeness gap: surface explicitly to leadership

2. **Geo recommendations:**
   - Gold DMAs / provinces: budget reallocation candidates
   - Cut DMAs / provinces: exclude in active campaigns

3. **Placement recommendations:**
   - If Pangle / Global App Bundle is Cut: disable
   - If TikTok placement is Gold but Pangle is Bronze: hold Pangle for app-install scale only

4. **Connection type:**
   - WiFi-skewed conversion patterns often indicate at-home / planning-mode buyers
   - 4G underperformance is common; consider dayparting or device-tier exclusions

5. **Adgroup-level:**
   - Cut adgroups: pause and document why
   - Gold adgroups: duplicate with broader targeting to find headroom

## Phase 7: MMM Validation & Report

1. **If MMM is available, cross-check:**
   ```
   meridian_get_raw_channel_roi(model_id, channel="tiktok")
   meridian_get_reconciled_channel_contributions(model_id)
   ```
   Even if a Gold tier segment looks efficient on platform CPA, is TikTok-as-a-channel actually driving incremental contribution? If MMM shows TikTok is saturated, scaling Gold segments improves platform metrics without unlocking revenue.

2. **Deliverable structure:**

   ```
   AUDIENCE INTELLIGENCE REPORT — TikTok
   Account: <name>   Period: <date range>

   EXECUTIVE SUMMARY
   [3-4 sentences: where audience is winning, leaking, what to change]

   ATTRIBUTION COMPLETENESS
   - Device-attributed conversions: X% (Y of Z)
   - Unknown / SKAdNetwork bucket: (100-X)%
   - Confidence level for demographic decisions: high / medium / low

   TIER MAP (Device-Attributed)
   - Gold (n segments): top performers
   - Silver (n): hold and test expansion
   - Bronze (n): watch
   - Cut (n): wasted spend = $X/week

   BY DIMENSION
   - Demographics (age × gender): [winners / losers]
   - DMAs: [top / bottom] (US-only)
   - Provinces / states: [top / bottom] (US-only)
   - Placements: [TikTok / Pangle / Global App]
   - Interest categories: [Gold IDs with names from taxonomy]
   - Connection types: [WiFi / 5G / 4G read]

   INTEREST EXPANSION SHORTLIST
   [5-10 candidates with rationale and test plan]

   RECOMMENDED CHANGES
   - Auto-approve: [demo exclusions, placement disabling, obvious cuts]
   - Recommend: [bid shifts, new interest tests <$100/day]
   - Needs discussion: [campaign restructures, large budget shifts]

   MMM CROSS-CHECK
   [Statement on whether audience moves are likely to be incremental]

   ADGROUP-CONFIG-JOIN APPENDIX
   [Only if Phase 4 was run]

   NEXT REVIEW
   [Cadence recommendation]
   ```

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Lookback window** — default 30 days (60 for low-volume accounts)
3. **Minimum spend threshold** — for scoring (default $200/segment/window)
4. **MMM model** — for incrementality validation (optional)
5. **Vertical / business context** — to filter interest expansion candidates
6. **Existing exclusions** — what's already been ruled out
7. **Targeting style** — Smart+ vs manual (determines whether to run Phase 4 fallback)

## Output

1. **Attribution Completeness** — gauge for demographic-decision confidence
2. **Tier Map** — Gold/Silver/Bronze/Cut by dimension
3. **Estimated Wasted Spend** — from Cut-tier segments
4. **Interest Expansion Shortlist** — 5-10 candidates with test budgets
5. **Demographic / Geo / Placement / Connection Recommendations**
6. **Adgroup-level Action Items**
7. **MMM Cross-Check Summary**
8. **Suggested Review Cadence**

## Important Notes

- **AUDIENCE report is primary for Smart+ accounts.** Adgroup-config-join is fallback for manual campaigns. Don't run both unless the user wants the interaction view.
- **iOS SKAdNetwork attribution loss is real and systematic.** Always surface the attribution-completeness gauge — leadership reading a 18-24 Male tier-map for an iOS account is acting on at most 20-40% of total conversions. Be honest about confidence levels.
- **Interest IDs aren't human-readable.** Always join with `get_tiktok_interest_categories` for the deliverable. Pre-cache the taxonomy if running the skill repeatedly.
- **TikTok geo bidding is coarse.** DMA-level reads work for the analysis, but bidding is country/region-level. Don't over-promise DMA-level optimization to the user.
- **`UNKNOWN` connection type often correlates with iOS** — same SKAdNetwork population that drives demographic `NONE` buckets. Treat as one phenomenon, not two.
- **Cross-skill handoffs:** Creative quality issues → `tiktok-creative-refresh` / `tiktok-creative-fatigue-watchdog`. New geos worth dedicated campaigns → `tiktok-geo-expansion`. Validating an audience scale-up is truly incremental → `tiktok-incrementality-test`. Account-wide health → `tiktok-auto-optimize`.
