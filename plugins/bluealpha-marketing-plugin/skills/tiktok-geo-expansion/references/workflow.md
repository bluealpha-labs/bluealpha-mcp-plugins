# TikTok Geo Expansion — Detailed Workflow

Identify new geographic markets worth testing on TikTok by combining current geo performance with the platform's targeting taxonomy. Equivalent to the Google Ads `geo-expansion-scout`, but adapted for TikTok's coarser geo controls (country → region → city) and its placement-aware delivery.

This skill is analysis and recommendation only. It produces a tested-market shortlist + campaign spec, ready to hand off for build.

## Phase 1: Current Geo Performance Analysis

Understand where the account is winning before scouting new ground.

1. **Resolve advertiser & pull current geo performance:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_AD",
     dimensions=["country_code"],
     metrics=["spend", "impressions", "clicks", "ctr", "cpm",
              "conversion", "cost_per_conversion", "conversion_rate"],
     start_date=<30_days_ago>,
     end_date=<today>
   )
   ```

2. **For US-focused accounts, get the sub-country read via the AUDIENCE report:**
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
   **iOS attribution caveat:** for iOS app-promotion accounts, expect a `dma_id: "0"` and `province_id: "-1"` bucket containing ~60-80% of SKAdNetwork-attributed conversions. Pull these out before computing geo tiers — they distort the per-DMA / per-state read. See `tiktok-audience-intelligence` Phase 2 for the attribution-split pattern.

3. **Classify current geos into tiers:**

   | Tier | Criteria | Strategic implication |
   |---|---|---|
   | **Star** | Conversion rate above account median AND spend share >5% | Core markets. Protect, scale incrementally. |
   | **Opportunity** | Conversion rate above median BUT spend share <2% | Underinvested winners. First place to look for headroom before expanding. |
   | **Volume** | Conversion rate below median BUT high spend share | Scale-driven, may improve with audience refinement or creative localization |
   | **Drain** | Conversion rate below median AND spend share >2% | Below-the-line waste — reduce or exclude |

4. **Identify the coverage gap:**
   - What countries / regions are in the user's target geography but have <$100 spend / 30 days?
   - Where is the campaign technically targeting but not delivering (a pacing issue, not a market issue — that goes to `tiktok-auto-optimize`)?

## Phase 2: Candidate Market Identification

Find new markets worth testing.

1. **Start with the user's expansion goals:**
   - National expansion (new states / DMAs)?
   - International expansion (new countries)?
   - Vertical-specific (e.g., college markets, urban DMAs, tier-1 metros only)?
   - What's the expansion budget? (determines test breadth)

2. **Pull the TikTok targeting taxonomy at the appropriate level:**
   ```
   tiktok_ads_get_tiktok_targeting_regions(
     advertiser_id=<id>,
     objective_type="<existing_campaign_objective>",
     level_range="TO_PROVINCE"  // or TO_COUNTRY, TO_CITY depending on expansion scope
   )
   ```
   This returns the region hierarchy with TikTok location IDs needed for targeting setup.

3. **For domestic (US) expansion, score candidate states/regions:**
   - Demographic similarity to Star markets (younger skew = better TikTok fit; older skew = TikTok fits less well)
   - Population size / TikTok user density (TikTok skews younger, so a state's population isn't a perfect proxy — note this and adjust)
   - Competitive density (no auction insights endpoint in this MCP — pull qualitative read from BlueAlpha competitive agent if available)
   - Vertical relevance (e.g., for app-install campaigns, mobile penetration; for retail, store coverage)

4. **For international expansion, additional considerations:**
   - Language localization required? (TikTok ads in English to non-English markets convert at ~40% of native-language ads)
   - Creative compliance per market (TikTok has region-specific ad policy variations)
   - Payment / fulfillment infrastructure ready?
   - SKAdNetwork / privacy regulation impact (e.g., EU app campaigns have additional attribution loss)

5. **Score and rank candidate markets:**

   | Factor | Weight | Source |
   |---|---|---|
   | Demographic similarity to Star markets | 30% | Public demographic data + user input |
   | TikTok user density / cohort fit | 25% | Heuristic + market research |
   | Vertical/business relevance | 20% | User input |
   | Localization cost | 15% | Creative + landing page assessment |
   | Competitive density | 10% | Qualitative read |

   Rank candidates, recommend top 3-5 for initial testing.

## Phase 3: Expansion Campaign Specification

Define the campaign(s) for the top markets.

1. **Campaign structure approaches:**

   **Approach A — Dedicated geo campaigns** (recommended for 1-3 new markets):
   - One campaign per market with explicit `location_ids` targeting
   - Independent budget, independent learning, independent measurement
   - Easier to isolate market-level performance

   **Approach B — Single campaign with multi-region targeting** (for 4+ markets, broad expansion):
   - Use TikTok's automatic geo optimization within the campaign
   - Simpler operation, less granular control
   - Works well with Smart+ automation

2. **Spec template per market:**

   ```
   Campaign name: GeoTest_<market>_<YYYYMM>
   Objective: <match existing campaign objective>
   Budget: $50-100/day for 7-14 days (test phase)
   Bid strategy: <match existing campaigns>
   Geo targeting: [<location_ids from tiktok_ads_get_tiktok_targeting_regions>]
   Placement: TikTok-only initially (don't multi-place during test)
   Audience: Mirror best-performing audience from Star markets
   Creative: Start with the proven winning creative cohort from Star markets

   Localization checklist:
   - Language: <yes/no/partial>
   - On-screen text: <localized?>
   - Voiceover: <localized?>
   - Currency / units: <localized?>
   - Cultural references: <flagged for review>
   - Compliance: <any regional ad policy concerns>
   ```

3. **Negative geo on existing campaigns:**
   - For a clean test, add negative location targeting on existing campaigns to exclude the new market
   - Otherwise the test will be polluted by the existing campaign cannibalizing the new market's results
   - Document the negative-targeting addition for post-test cleanup

4. **If MMM is available, pre-test the incrementality assumption:**
   ```
   meridian_simulate_budget_reallocation(model_id, scenario=<adding new market budget>)
   ```
   The MMM can't predict per-market results, but it can flag if TikTok as a channel is saturated — if so, expanding to new geos may just spread the same incremental conversions across more markets.

## Phase 4: Test Measurement Framework

How to read the test data.

1. **Phases:**
   - **Days 1-7:** Learning. Monitor delivery, don't judge performance yet.
   - **Days 8-14:** Early signal. Compare CPM, CTR, hook rate to Star markets.
   - **Days 15-30:** Performance read. Compare conversion rate, CPA, ROAS.
   - **Day 30+:** Scale decision.

2. **Decision framework per market:**

   | Signal | Action |
   |---|---|
   | CPA within 25% of Star markets + conversion volume growing | **Scale:** Move to a permanent dedicated campaign, increase budget 50% |
   | CPA within 25% but volume low | **Optimize:** Broaden audience or test new creative localized to the market |
   | CPA 25-50% worse, improving week-over-week | **Hold:** Give 2 more weeks before deciding |
   | CPA >50% worse with no improvement trend | **Cut:** Pause campaign, document learning, redirect budget |
   | <5 conversions after 14 days with reasonable spend | **Cut + investigate:** Likely a fundamental fit problem (demand, localization, payment) |

3. **If MMM is available, validate at day 60:**
   - Did total TikTok contribution grow, or did it stay flat (= cannibalization)?
   - Did the expansion markets show up in the MMM's geo-attributed contribution (where available)?

## Phase 5: Reporting

1. **Geo Expansion Report:**

   ```
   GEO EXPANSION REPORT — TikTok
   Account: <name>     Period: <date range>

   CURRENT GEO MAP
   - Star markets (n): [list]
   - Opportunity markets (n): [list]
   - Volume markets (n): [list]
   - Drain markets (n): [list]

   COVERAGE GAPS
   [Target geos with <$100 spend in last 30 days, with reason]

   EXPANSION CANDIDATES — RANKED
   1. <Market>: score X/100. Why: [...]. Test budget: $X/day. Localization need: [yes/no].
   2. <Market>: ...

   EXPANSION CAMPAIGN SPECS
   [One spec per top-3 candidate, ready to build]

   MEASUREMENT PLAN
   - Days 1-7: Learning
   - Days 8-14: Early signal checkpoint
   - Days 15-30: Performance evaluation
   - Day 30+: Scale decision
   - MMM validation: Day 60+ (if model available)

   DRAIN CLEANUP
   [Drain-tier markets to exclude in current campaigns — funds the test]
   ```

2. **Recommend the right order:**
   - Clean up Drain markets FIRST (frees test budget)
   - Then launch top 1-2 expansion tests (don't try to launch 5 simultaneously — too much variation, no learning)
   - After 30-day reads on the first wave, evaluate and launch next wave

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Expansion scope** — national (new US states) / international (new countries) / regional (e.g., specific metros)
3. **Expansion budget** — total $/month for test markets
4. **Localization capacity** — can creative be localized, by when?
5. **Business constraints** — fulfillment / shipping / payment infrastructure per market
6. **MMM model** — for incrementality framing (optional)
7. **Existing exclusions** — markets already ruled out (don't re-recommend)

## Output

1. **Current Geo Tier Map** — Star/Opportunity/Volume/Drain
2. **Coverage Gap Analysis** — where the account is technically targeting but not delivering
3. **Candidate Market Ranking** — top 5 with composite scores
4. **Campaign Specs** — top 3 ready-to-build
5. **Negative Geo Cleanup List** — Drain markets to exclude in existing campaigns
6. **Measurement Plan** — phased reads with decision criteria
7. **MMM Validation Plan** — what success looks like in the model

## Important Notes

- **TikTok geo is coarser than Google.** You target at country → region/state → city. There's no DMA-level granularity in most markets. Set expectations accordingly — geo tests on TikTok are state-level (US) or country-level (international), not metro-level.
- **TikTok user density isn't population density.** TikTok skews young (18-34 over-indexed). A state with high overall population but older demographics (e.g., Florida average age) may be a weaker TikTok market than a smaller state with younger demographics (e.g., Texas tier-1 metros). Don't use population as the only proxy.
- **Don't multi-place during a geo test.** Run the test on TikTok placement only. Adding Pangle / Global App Bundle muddies the read — those placements have very different audience composition.
- **Test budget needs to clear the learning threshold.** TikTok needs ~$50/day per adgroup for 7-14 days to exit learning. Sub-threshold geo tests produce noise, not data.
- **iOS app campaigns require longer tests.** SKAdNetwork attribution delays reads by 24-48 hours and underreports conversions. Plan for 21-day reads instead of 14-day reads in iOS test markets, and validate against MMM where possible.
- **Don't expand to a market until Drain markets are cleaned up.** It's mathematically irresponsible to launch a new market test while bleeding $X/week on a known-Drain market. Always sequence: clean → test → scale.
- **Cross-skill handoffs:** Drain market cleanup → `tiktok-auto-optimize` for execution recommendations. Localized creative briefs for new markets → `tiktok-creative-refresh`. Validating incremental contribution from a new market → `tiktok-incrementality-test`. Audience targeting strategy for the new market → `tiktok-audience-intelligence`.
