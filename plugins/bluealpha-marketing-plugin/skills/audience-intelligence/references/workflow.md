# Audience Intelligence — Detailed Workflow

## Phase 1: Audience Performance Scan

Pull the full audience landscape across the account.

1. **Run `analyze_audiences`** on the account:
   ```
   analyze_audiences(customer_id=<id>, days=30)
   ```
   This returns every audience segment with:
   - **Efficiency Score** (0-100): Weighted composite of profitability (55%), quality (22.5%), and scale (22.5%)
   - **Classification**: Scale & Efficient, Efficient but Small, Scale but Inefficient, Inefficient
   - **Audience type**: Observation vs. Targeting (critical distinction — Observation data is directional only, Targeting actually restricts delivery)
   - Metrics: impressions, clicks, conversions, cost, CTR, CPC, conversion rate, cost/conversion

2. **Run a 90-day comparison** to detect trends:
   ```
   analyze_audiences(customer_id=<id>, days=90)
   ```
   Compare the 30-day and 90-day scores to identify:
   - **Rising stars**: Audiences that improved significantly (score jumped 15+ points)
   - **Fading audiences**: Audiences that declined (score dropped 15+ points)
   - **Steady performers**: Consistent top-tier segments
   - **Consistent waste**: Audiences that have been inefficient across both windows

3. **Pull campaign-level audience breakdowns** for the top-spending campaigns:
   ```
   analyze_audiences(customer_id=<id>, campaign_name=<name>)
   ```
   This shows which audiences are driving each campaign's performance — critical for knowing where to apply bid adjustments.

## Phase 2: Audience Segmentation & Insights

Organize the raw data into actionable segments.

1. **Build the Audience Tier Map:**

   | Tier | Criteria | Action |
   |------|----------|--------|
   | **Gold** | Efficiency Score 80+ AND classification is "Scale & Efficient" | Increase bid modifier +20-40%, expand to similar audiences |
   | **Silver** | Efficiency Score 60-79 OR classification is "Efficient but Small" | Maintain current bids, test expanding to similar segments |
   | **Bronze** | Efficiency Score 40-59, some conversion activity | Monitor — may improve with creative or landing page changes |
   | **Cut** | Efficiency Score < 40 AND classification is "Inefficient" AND 90-day trend is flat/declining | Exclude from targeting or set -50% to -100% bid modifier |

2. **Identify the Observation vs. Targeting gap:**
   - Many accounts have audiences in Observation mode generating useful data that's never acted on
   - For Gold-tier Observation audiences: recommend switching to Targeting mode with a positive bid modifier
   - For Cut-tier Observation audiences with significant spend: recommend adding as negative audiences

3. **Cross-reference with demographic data** by querying demographic performance:
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT ad_group_criterion.age_range.type, ad_group_criterion.gender.type, metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros FROM age_range_view WHERE segments.date BETWEEN '<start>' AND '<end>'"
   )
   ```
   Layer demographic patterns on top of audience segments to build a full picture: "In-market for Marketing Software" + "Age 25-34" + "Male" might be your best converter, even if the audience alone looks average.

4. **If MMM is available, validate with incrementality data:**
   ```
   get_contribution_breakdown(model_id)
   get_channel_roi(model_id)
   ```
   The key question: are Gold-tier audiences actually driving incremental conversions, or are they just capturing demand that would have converted anyway? If the MMM shows Search is oversaturated, even "efficient" audiences may be mostly cannibalizing organic. Flag this.

## Phase 3: Competitive Audience Analysis

Understand the audience landscape beyond your own account.

1. **Pull auction insights** for top-performing audience segments:
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT auction_insights.display_domain, metrics.auction_insight_search_impression_share, metrics.auction_insight_search_overlap_rate, metrics.auction_insight_search_outranking_share FROM auction_insights WHERE segments.date BETWEEN '<start>' AND '<end>'"
   )
   ```
   See who else is competing for the same audience attention.

2. **Identify audience gaps:**
   - Audiences where competitors are present but the user has no coverage
   - High-volume audience segments with low competition
   - Audience + keyword combinations that are underserved

## Phase 4: Audience Optimization Recommendations

Define the optimization strategy based on the audience intelligence gathered in Phases 1-3.

**Recommended bid adjustment strategy:**

1. **For Gold-tier audiences — increase bids:**
   - Recommendation: Set bid modifier to +20% for audiences with score 80-89
   - Recommendation: Set bid modifier to +30% for audiences with score 90-95
   - Recommendation: Set bid modifier to +40% for audiences with score 95+
   - Strategy note: Cap at +40% to avoid overbidding on a single signal

2. **For Cut-tier audiences — reduce or exclude:**
   - Recommendation for Targeting mode audiences with >$100 spent and zero conversions in 90 days: Set bid modifier to -100% (effectively excluding)
   - Recommendation for Observation mode audiences: Monitor but leave in place (Observation doesn't affect delivery, and the data remains useful)
   - Strategic approach: For accounts struggling with overall efficiency, recommend -50% modifiers to Cut-tier audiences as an intermediate step before -100%

3. **For new audience opportunities — add Observation audiences:**
   - Identification: In-market and affinity audiences that align with the user's product but aren't currently attached
   - Recommendation: Add identified audiences in Observation mode first to collect data
   - Strategy: Plan 2-4 week data collection period before moving to Targeting mode

**Execution specification workflow:**
   - Document the current state for each Gold/Cut audience (audience name, current modifier, proposed modifier, rationale)
   - Identify new Observation audiences to add
   - Create a complete bid adjustment spec with all recommendations
   - Log all recommendations with before/after states for the final report
   - Prepare a structured recommendation document for user review and manual implementation if needed

## Phase 5: Measurement & Reporting

Compile everything into an actionable audience intelligence report.

1. **Account-level audience summary:**
   - Total audiences analyzed
   - Distribution across tiers (Gold / Silver / Bronze / Cut)
   - Estimated monthly spend on Cut-tier audiences (= wasted budget)
   - Top 5 audiences by efficiency score
   - Bottom 5 audiences by efficiency score

2. **Campaign-level breakdowns:**
   - For each major campaign: which audiences are driving performance vs. dragging it down
   - Audience overlap between campaigns (same audience appearing in multiple campaigns)
   - Recommendations per campaign

3. **Actions taken:**
   - Bid adjustments applied (audience, old modifier, new modifier)
   - Audiences excluded
   - New Observation audiences added
   - Estimated impact: budget saved from cuts, expected improvement from bid increases

4. **Next steps:**
   - Schedule a follow-up analysis in 2-4 weeks to measure the impact of changes
   - Audiences in Silver tier that need more data before a decision
   - New audience tests to run (based on competitor gaps or MMM insights)

5. **Cadence recommendation:**
   - Low-spend accounts (<$5K/mo): Monthly audience review
   - Mid-spend accounts ($5K-50K/mo): Bi-weekly audience review
   - High-spend accounts (>$50K/mo): Weekly audience review, with automated alerting on efficiency score drops >20%
