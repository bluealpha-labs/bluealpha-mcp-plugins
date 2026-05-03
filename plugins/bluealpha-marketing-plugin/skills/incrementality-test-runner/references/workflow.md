# Incrementality Test Runner — Detailed Workflow

## Phase 1: Test Design

Define what you're testing and how.

1. **Clarify the test hypothesis:**
   - What channel/campaign/tactic is being tested? (e.g., "Does our nonbrand Search campaign drive incremental conversions?")
   - What's the expected effect size? (Use MMM contribution data as a prior)
   - What's the primary KPI? (conversions, revenue, sign-ups, etc.)
   - What's the test duration? (minimum 4 weeks, ideally 6-8 weeks for statistical power)

2. **If MMM is available, pull baseline predictions:**
   ```
   get_contribution_breakdown(model_id)
   get_channel_roi(model_id)
   get_saturation_curves(model_id)
   ```
   Use the MMM's channel contribution estimates to:
   - Set the expected lift (the MMM says Search contributes X% of conversions — the test should confirm or challenge this)
   - Identify if the channel is saturated (flat saturation curve = harder to detect lift because marginal impact is low)
   - Calculate required sample size based on expected effect size and baseline conversion rate

3. **Design the geo split:**

   **Option A — Matched Market Pairs:**
   Best for accounts with enough geographic diversity. Pair similar markets (by population, conversion rate, seasonality) and assign one to test, one to control.

   **Option B — Regional Holdout:**
   Simpler approach. Pick 2-4 DMAs or states as holdout (control) and run the rest as test. Works well when the account has national coverage.

   **Option C — Budget Suppression:**
   Instead of fully pausing in control regions, reduce budget by 80-90%. Less clean than a full holdout but avoids the "we can't afford to turn off ads in any market" objection.

4. **Resolve geo targets to Google Ads criterion IDs:**
   ```
   suggest_geo_targets(location_names=["San Francisco", "New York", "Chicago"])
   ```
   This returns the geo target constants (criterion IDs) needed for campaign targeting. Map each test and control market to its criterion ID.

5. **Document the test plan** before execution:
   - Hypothesis
   - Test regions (with criterion IDs)
   - Control regions (with criterion IDs)
   - Campaign(s) under test
   - Primary KPI + expected lift
   - Duration
   - Budget per region
   - Success criteria (what result would confirm/reject the hypothesis)
   - Contamination risks (e.g., national TV driving traffic to control regions)

## Phase 2: Test Campaign Configuration Strategy

Define the campaign configuration strategy for the test.

**Configuration approach for new campaign tests:**

1. **Campaign budget and naming strategy:**
   - Recommended budget name: "Incrementality_Test_<channel>_<date>"
   - Recommended daily budget: Sufficient to generate meaningful conversion volume over test period
   - Budget allocation: Appropriate split between test and control regions if using Budget Suppression

2. **Test campaign structure:**
   - Recommended campaign naming: "INCR_TEST_<channel>_test_regions"
   - Initial status: PAUSED until user approval
   - Recommended geo targeting: PRESENCE only (not PRESENCE_OR_INTEREST to avoid geo contamination)
   - For each test region: Add location targeting to specification

3. **Ad group, keyword, and ad strategy:**
   - Structure: Mirror existing high-performing campaign structures
   - Ad groups and keywords: Replicate proven keyword strategy for the test regions
   - Ad copy: Use existing best-performing ads to isolate the geographic test variable

4. **For testing existing campaigns — geo targeting modification strategy:**
   - Baseline: Pull current geo targeting configuration to document pre-test state
   - Strategy for control regions: Add negative location targeting to exclude control regions without creating new campaigns
   - Pre-test documentation: Record the baseline state for post-test restoration

**Configuration plan presentation:**
   - Present the complete test plan to user: campaign specs, geo splits, budgets, duration
   - Show estimated daily/weekly costs
   - Confirm user understanding that control regions will see reduced/no ads
   - Obtain user approval before enabling any campaigns
   - Prepare configuration specification document with all campaign settings, geo targets, criterion IDs, and setup instructions for manual implementation if needed

## Phase 3: Test Monitoring

Run integrity checks throughout the test — a contaminated test is worse than no test.

1. **Run `monitor_incrementality_test`** on a regular cadence:
   ```
   monitor_incrementality_test(
     customer_id=<id>,
     campaign_ids=["<test_campaign_id>"],
     control_regions=[<control_criterion_ids>],
     test_regions=[<test_criterion_ids>],
     target_daily_budget=<expected_daily_budget>,
     benchmark_cpm=<pre_test_cpm>,
     benchmark_cpc=<pre_test_cpc>
   )
   ```

2. **The tool runs prioritized checks:**

   | Priority | Check | What It Catches |
   |----------|-------|-----------------|
   | **P-0** | Entity Status | Campaign/ad group got paused or disapproved mid-test |
   | **P-1** | Change History | Someone edited targeting, bids, or budget during the test |
   | **P-2** | Geo Leakage | Ads serving in control regions (test contamination) |
   | **P-3** | Zero Impressions | Test campaign stopped serving entirely |
   | **W-1** | Budget Pacing | Spending significantly above/below target daily budget |
   | **W-2** | CPM/CPC Volatility | Cost metrics shifted >30% from benchmark (auction dynamics changed) |
   | **W-3** | Conversion Sparsity | Not enough conversions accumulating for statistical significance |

3. **Response protocol by alert priority:**

   - **P-0 (Entity Status):** Immediate action required. Flag for re-enablement via the execution pipeline. Every day of downtime extends the required test duration.

   - **P-1 (Change History):** Investigate who made the change and why. If the change is material (targeting, budget, bid strategy), the test may need to restart. If minor (ad copy tweak), note it and continue.

   - **P-2 (Geo Leakage):** Critical. Pull the geographic performance report to confirm:
     ```
     execute_query_stream(
       customer_id=<id>,
       query="SELECT geographic_view.country_criterion_id, geographic_view.location_type, metrics.impressions, metrics.clicks, metrics.cost_micros FROM geographic_view WHERE segments.date BETWEEN '<test_start>' AND '<today>' AND campaign.id = '<test_campaign_id>'"
     )
     ```
     If control regions are getting impressions: check targeting settings (PRESENCE vs PRESENCE_OR_INTEREST), check for geo-targeting expansion, fix and note the contamination period.

   - **P-3 (Zero Impressions):** Diagnose via `diagnose_underspend`. Could be budget exhaustion, disapprovals, or targeting too narrow.

   - **W-1 to W-3 (Warnings):** Log and monitor. These don't invalidate the test immediately but may affect statistical power. If budget pacing is off by >50% for 3+ consecutive days, intervene.

4. **Monitoring cadence:**
   - **Days 1-3:** Daily monitoring (catch setup issues early)
   - **Days 4-14:** Every 2-3 days
   - **Days 15+:** Weekly, unless an alert triggers more frequent checks

5. **Compile a monitoring log** with timestamps, alert history, and any interventions made. This is essential for interpreting results — if the test was contaminated for 5 of 30 days, the analysis needs to account for that.

## Phase 4: Post-Test Analysis

After the test period ends, measure the lift and draw conclusions.

1. **Pull test vs. control performance:**
   ```
   execute_query_stream(
     customer_id=<id>,
     query="SELECT geographic_view.country_criterion_id, metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros FROM geographic_view WHERE segments.date BETWEEN '<test_start>' AND '<test_end>' AND campaign.id IN ('<campaign_ids>')"
   )
   ```
   Aggregate by test vs. control regions.

2. **Calculate lift:**
   - **Conversion lift** = (Test region conversion rate - Control region conversion rate) / Control region conversion rate
   - **Revenue lift** = (Test region revenue per user - Control region revenue per user) / Control region revenue per user
   - **iROAS** (incremental ROAS) = Incremental revenue / Total ad spend in test regions

3. **Statistical significance check:**
   - Use a two-sample proportion test (or t-test for revenue) to confirm the lift is statistically significant
   - Report the p-value and confidence interval
   - If p > 0.05: the test is inconclusive. Either extend the test or accept that the channel's incremental impact is small/zero.

4. **If MMM is available, compare test results to model predictions:**
   ```
   get_contribution_breakdown(model_id)
   ```
   - Does the measured lift match the MMM's predicted contribution?
   - If the test shows higher lift than the MMM predicted → the model may be undervaluing this channel
   - If the test shows lower lift → the model may be overcrediting (common with last-touch attribution)
   - Either way, feed the test results back to the modeling team for recalibration

5. **Generate the test results report:**
   - Test design summary (hypothesis, duration, geo split)
   - Raw metrics: test vs. control side-by-side
   - Lift calculation with confidence intervals
   - MMM comparison (if available)
   - Monitoring log summary (any integrity issues)
   - Recommendation: scale, maintain, cut, or retest
   - Cost of the test (spend in control regions that could have been productive)

## Phase 5: Test Teardown Strategy & Next Steps

Recommend the cleanup and planning strategy for post-test actions.

1. **Recommended restoration approach:**
   - Remove negative geo targeting added to existing campaigns
   - Recommendation: Re-enable campaigns in control regions if they were paused
   - Recommendation: Delete test-specific campaigns if they were created solely for the experiment
   - Documentation: Capture before/after state for audit trail

2. **Learnings application strategy:**
   - If the test proved incrementality: Recommend maintaining or increasing spend, supported by causal evidence
   - If the test showed no lift: Recommend reducing spend and reallocating to channels that did prove incremental
   - If inconclusive: Recommend designing a higher-power test (longer duration, bigger geo split, or higher budget)

3. **Next testing plan:**
   - Identification: What's the next channel/campaign to test?
   - Optimization: Can you use the same geo split (saves setup time)?
   - Planning: Seasonal considerations for timing
   - Roadmap recommendation: Test one channel at a time, cycling through top budget lines over 6-12 months

4. **MMM feedback and decision logging:**
   - Create a record in the MMM system documenting:
     - Test completed for <channel>
     - Measured lift: <X>%
     - iROAS: <Y>
     - MMM predicted: <Z>%
     - Recommendation: <action>
   - This enables model recalibration and maintains decision tracking
