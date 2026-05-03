# Geo Expansion Scout — Detailed Workflow

## Phase 1: Current Geo Performance Analysis

Understand where the account is currently performing before looking for new markets.

1. **Pull geographic performance data:**
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT geographic_view.country_criterion_id, geographic_view.location_type, metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros, metrics.search_impression_share FROM geographic_view WHERE segments.date BETWEEN '<30_days_ago>' AND '<today>'"
   )
   ```

2. **Pull user location report** (where people physically are vs. where they're "interested in"):
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT geographic_view.country_criterion_id, geographic_view.location_type, metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros FROM geographic_view WHERE segments.date BETWEEN '<30_days_ago>' AND '<today>' AND geographic_view.location_type = 'LOCATION_OF_PRESENCE'"
   )
   ```
   The distinction matters: LOCATION_OF_PRESENCE shows where users physically are, while AREA_OF_INTEREST shows where they're searching about. For geo expansion, physical presence is the more reliable signal.

3. **Classify current markets into performance tiers:**

   | Tier | Criteria | Implication |
   |------|----------|-------------|
   | **Star** | Above-average conversion rate AND above-average volume | Core markets. Protect and potentially increase spend here. |
   | **Opportunity** | Above-average conversion rate BUT below-average volume | High potential. Low impression share = room to grow in existing markets before expanding. |
   | **Volume** | Below-average conversion rate BUT high volume | Scale markets. May improve with better targeting or creative. |
   | **Drain** | Below-average conversion rate AND below-average volume | Question marks. May warrant budget reduction or exclusion. |

4. **Identify the coverage gap:**
   - What percentage of the user's target geography is currently covered?
   - Which major metros/states/regions have zero ad spend?
   - Are there markets getting impressions via "interest" but no physical presence targeting?

## Phase 2: Market Opportunity Identification

Find new markets worth testing.

1. **Start with the user's expansion goals:**
   - Are they looking to expand nationally? Regionally? Into specific states/cities?
   - Is there a business reason to target specific locations? (new office, partner market, event, etc.)
   - What's the expansion budget? (This determines how many new markets to test simultaneously)

2. **Resolve candidate locations to Google Ads criterion IDs:**
   ```
   suggest_geo_targets(location_names=["Austin", "Denver", "Portland", "Nashville", "Raleigh"])
   ```
   This returns the geo target constants needed for targeting and also confirms the canonical location names and types (city, state, DMA, country).

3. **Estimate keyword volume by candidate market:**
   ```
   generate_keyword_ideas(
     customer_id=<id>,
     url=<user_website>,
     # Filter by each candidate geo to see location-specific volume
   )
   ```
   Compare search volume across candidate markets for the user's core keywords. Markets with higher volume and lower competition are better expansion candidates.

4. **Pull competitive density by market** (if the user has existing campaigns):
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT campaign.name, metrics.search_impression_share, metrics.search_rank_lost_impression_share, metrics.search_budget_lost_impression_share FROM campaign WHERE segments.date BETWEEN '<30_days_ago>' AND '<today>' AND campaign.status = 'ENABLED'"
   )
   ```
   Cross-reference impression share data with geographic performance to see where competition is lighter.

5. **If MMM is available, predict incremental impact by market:**
   ```
   get_saturation_curves(model_id)
   simulate_budget_reallocation(model_id, scenario=<expansion_budget_allocation>)
   ```
   The key question: will adding new markets drive truly incremental conversions, or just spread the same conversions across more geography? If the MMM shows the current markets are saturated (flat saturation curve), new markets are more likely to be incremental.

6. **Score and rank candidate markets:**

   | Factor | Weight | Source |
   |--------|--------|--------|
   | Keyword search volume | 25% | generate_keyword_ideas |
   | Competition level | 20% | generate_keyword_ideas competition metric |
   | Similarity to Star markets | 20% | Demographic/economic comparison |
   | MMM predicted incrementality | 20% | simulate_budget_reallocation (if available) |
   | Business alignment | 15% | User input (proximity to offices, partner markets, etc.) |

   Rank markets by composite score. Recommend the top 3-5 for initial testing.

## Phase 3: Expansion Campaign Specification

Define the campaign strategy and specifications for the top markets.

1. **Campaign structure recommendations for geo expansion:**

   **Approach A — Dedicated Geo Campaigns (recommended for 1-3 markets):**
   - One campaign per market with explicit geo targeting
   - Allows independent budget control and performance measurement per market
   - Easier to isolate underperforming markets without affecting others

   **Approach B — Single Campaign with Location Bid Modifiers (for 4+ markets):**
   - One campaign targeting all new markets
   - Use location bid modifiers to control spend by market
   - Simpler to manage but harder to isolate per-market performance

2. **Campaign specification strategy:**

   a. **Budget planning:**
      - Recommended naming: "GeoTest_<market_name>_<date>"
      - Recommended test budget: $15-30/day per market for Search, $10-20/day for Display/Video
      - Budget allocation: Sufficient for 4-6 week test period

   b. **Campaign structure:**
      - Recommended naming: "GeoTest_<market_name>_NonBrand"
      - Initial status: PAUSED pending user approval
      - Advertising channel type: SEARCH (or DISPLAY/VIDEO as appropriate)
      - Bidding strategy: MAXIMIZE_CONVERSIONS recommended

   c. **Geo targeting specification:**
      - Location targeting: Set to PRESENCE only (not PRESENCE_OR_INTEREST)
      - Negative targeting: Exclude new market from existing national campaigns to avoid test cannibalization
      - Documentation: Record all geo criterion IDs for setup

   d. **Ad group and keyword strategy:**
      - Ad group naming: "GeoTest_<market>_<theme>"
      - Keywords: Core keywords from existing high-performing campaigns, plus market-specific terms identified in Phase 2
      - Match types: Recommended PHRASE match to balance reach and relevance in test markets

   e. **Ad copy strategy:**
      - Adapt the user's best-performing existing ad copy
      - Localization: Use market-specific landing pages if available; otherwise use main site
      - A/B opportunity: Test headlines reflecting market-specific messaging if data supports it

   f. **Expansion plan presentation:**
      - Present complete specification for user review: market name, campaign name, budget, keywords, ad copy, geo targeting
      - Show estimated performance based on benchmark markets
      - Obtain user approval before campaign setup

   g. **Specification documentation:**
      - Create comprehensive spec file with all campaign settings, geo criterion IDs, keywords, ad copy, and step-by-step setup instructions for manual implementation if needed

## Phase 4: Performance Measurement

Track expansion market performance against existing markets.

1. **Set up a measurement framework:**
   - **Week 1-2:** Learning period. Monitor for delivery issues but don't judge performance.
   - **Week 3-4:** Early signal. Compare CPC, CTR, and impression share to existing markets.
   - **Week 5-8:** Performance evaluation. Measure conversion rate, CPA, and ROAS vs. existing markets.
   - **Week 9+:** Scale decision. Markets within 20% of existing market CPA → keep and consider scaling. Markets >50% worse → cut.

2. **Pull comparative performance:**
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT campaign.name, metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros, metrics.search_impression_share FROM campaign WHERE campaign.name LIKE 'GeoTest%' AND segments.date BETWEEN '<start>' AND '<end>'"
   )
   ```

3. **Decision framework per market:**

   | Signal | Action |
   |--------|--------|
   | CPA within 20% of existing markets + growing volume | **Scale:** Increase budget by 30%, expand keyword coverage |
   | CPA within 20% but low volume | **Optimize:** Broaden match types, add keywords, test new ad copy |
   | CPA 20-50% worse but improving week-over-week | **Hold:** Give it 2 more weeks, the learning period may not be over |
   | CPA >50% worse with no improvement trend | **Cut:** Pause the campaign, reallocate budget to Star or Opportunity markets |
   | Zero conversions after 2 weeks with reasonable spend | **Cut:** The market may not have demand for this product/service |

4. **If MMM is available, validate expansion incrementality:**
   After 6-8 weeks, compare:
   - Did total conversions increase, or did they just redistribute from existing markets?
   - Did the MMM-predicted incrementality match actual results?
   - Is the expansion market showing up in the contribution breakdown?

## Phase 5: Expansion Reporting

Compile the geographic intelligence into an actionable report.

1. **Current market performance map:**
   - All markets classified (Star / Opportunity / Volume / Drain)
   - Spend distribution by geography
   - Impression share by geography (where are you under-covering?)

2. **Expansion opportunity assessment:**
   - Ranked list of candidate markets with composite scores
   - Volume estimates per market
   - Expected CPA range based on competition data
   - MMM incrementality predictions (if available)

3. **Expansion campaigns launched:**
   - Campaign specs per market (budget, keywords, geo targeting)
   - Early performance signals (if enough time has passed)
   - Recommended next steps per market

4. **Budget recommendations:**
   - How much to allocate to expansion testing
   - Which existing Drain markets to reduce (to fund expansion)
   - Phased rollout plan: test 3-5 markets → evaluate after 4-6 weeks → expand winners, cut losers → test next batch

5. **Long-term geo strategy:**
   - Recommended cadence for geo performance reviews (monthly for active expansion, quarterly for steady state)
   - Markets to test in the next wave
   - Seasonal considerations (some markets perform differently by quarter — tourism markets, college towns, etc.)
