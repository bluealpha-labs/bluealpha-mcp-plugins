# TikTok Incrementality Test — Detailed Workflow

Design and monitor a geo-holdout incrementality test on TikTok. This is the BlueAlpha measurement wedge applied to a channel that famously inflates platform-reported ROAS. TikTok's 7-day click + 1-day view attribution captures conversions that would have happened anyway — this skill is how you find out which channels are driving real lift vs. taking credit.

Proof points to anchor the conversation: BlueAlpha's incrementality work on Cann showed zero lift on AppLovin (saved $480K). On Klover, the same approach cut Meta iOS 50% with no lost conversions. The same playbook applies to TikTok.

This skill is design + monitoring + analysis. Test setup execution routes through the BlueAlpha pipeline.

## Phase 1: Test Design

Define what you're testing and how.

1. **Clarify the test hypothesis:**
   - Is the test about the *channel* (is TikTok driving lift at all)?
   - Is it about a *campaign* (does this specific TikTok campaign drive incremental conversions)?
   - Is it about a *creative cohort* (does this set of creative drive lift)?
   - Is it about a *placement* (is Pangle / Global App Bundle inventory incremental)?
   - What's the primary KPI: conversions, revenue, app installs, sign-ups?
   - What's the test duration? Minimum 4 weeks; ideally 6-8 for statistical power.

2. **If MMM is available, pull baseline priors:**
   ```
   meridian_get_raw_channel_roi(model_id, channel="tiktok")
   meridian_get_raw_contribution_breakdown(model_id)
   meridian_get_raw_saturation_curves(model_id, channel="tiktok")
   ```
   Use the MMM's TikTok contribution estimate to:
   - Set the expected lift (the test should confirm or challenge the MMM)
   - Identify saturation status (flat curve = harder to detect lift, longer test required)
   - Pre-stage a sample-size calculation against the MMM's predicted effect size

3. **Choose the geo-split design:**

   **Design A — Matched market pairs:**
   - For accounts with US national or multi-country coverage
   - Pair similar markets (population, demographic match, prior TikTok conversion rate)
   - One market = test (TikTok stays on), pair = control (TikTok off or budget-suppressed)
   - Statistical advantage: pairing reduces variance
   - Requires 4-6 matched pairs for sufficient power

   **Design B — Regional holdout:**
   - Pick 2-5 countries (international) or states (US) as holdout
   - Rest of geography continues running TikTok
   - Simpler, lower-power than matched pairs
   - Works well when matched pairs aren't available

   **Design C — Budget suppression instead of full pause:**
   - Reduce TikTok spend in control regions by 80-90% rather than zero
   - Cleaner business-wise (no full pause objection) but less statistically clean
   - Use when full pause would cause political resistance from the client

4. **Resolve geo targets to TikTok location IDs:**
   ```
   tiktok_ads_get_tiktok_targeting_regions(
     advertiser_id=<id>,
     objective_type=<existing_campaign_objective>,
     level_range="TO_PROVINCE"  // or TO_COUNTRY for international
   )
   ```
   Map each test and control market to its TikTok location ID.

5. **Document the test plan:**
   ```
   TIKTOK INCREMENTALITY TEST PLAN

   Hypothesis: <e.g., "TikTok drives 15-25% incremental lift on Klover sign-ups in iOS markets">
   Test scope: <channel / campaign / creative / placement>
   Primary KPI: <conversions / revenue / installs>

   Geo design: <matched-pairs / regional-holdout / budget-suppression>
   Test regions: [<location_id list>] with names
   Control regions: [<location_id list>] with names
   Pair matching rationale (if applicable): <similarity criteria used>

   Duration: <X weeks> (minimum 4, target 6-8)
   Pre-test baseline period: <2 weeks before test start, used as control reference>

   Spend during test:
     - Test regions: <target daily $> per campaign
     - Control regions: <$0 / suppressed budget / unchanged for non-TikTok>

   Required power: <X% lift detectable at p<0.05 with current conversion baseline>
   Success criteria: <e.g., "p<0.10 and observed lift >5% to maintain or scale TikTok">

   Contamination risks: <e.g., national TV running concurrently, viral organic content, paid search retargeting from TikTok-exposed users>
   ```

## Phase 2: Test Configuration Strategy

The campaign-level setup. This is a recommendation spec — execution routes through BlueAlpha pipeline.

1. **For testing existing campaigns (most common):**

   - **Test region campaigns:** No changes. They continue running as-is.
   - **Control region campaigns:** Add negative geo targeting via `location_ids` exclusion to remove control regions from delivery
   - **Pre-test documentation:** Capture each campaign's current geo configuration for post-test restoration

2. **For testing a new campaign / new creative cohort:**

   - **Test campaign:** Create new campaign with `location_ids` set to test regions only
   - **Control:** Existing campaigns stay running everywhere — the new campaign just doesn't deliver in control regions
   - **Targeting:** `PRESENCE` location type (not interest-based) — TikTok's location targeting is presence-by-default, but verify
   - **Initial status:** PAUSED until BlueAlpha pipeline executes the live activation

3. **For testing a placement (e.g., is Pangle incremental?):**

   - Configure test region adgroups with placement excluded (e.g., remove `PLACEMENT_PANGLE`)
   - Configure control region adgroups identically EXCEPT with placement included
   - This is technically a placement test with geo as the unit of randomization

4. **Configuration spec presentation:**
   - Present complete test plan to user: scope, geo splits, budgets, duration, expected costs
   - Confirm understanding: control regions will see reduced or zero TikTok ads during the test
   - Explicitly call out the opportunity cost: control regions will likely see fewer conversions during the test, which is the *point* — that's how we measure lift
   - Obtain user approval before any campaign changes go live

## Phase 3: Test Monitoring & Integrity Checks

A contaminated test is worse than no test. Run integrity checks on a strict cadence.

1. **Daily for the first week, every 2-3 days after:**

   Pull test vs. control performance. For US-only tests, the AUDIENCE report's `province_id` or `dma_id` dimension gives sub-country granularity:
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_CAMPAIGN",
     dimensions=["campaign_id", "country_code"],
     metrics=["spend", "impressions", "clicks", "conversion", "cost_per_conversion", "total_purchase_value"],
     start_date=<test_start>,
     end_date=<today>,
     include_names=True,
     filters=[{"field_name": "campaign_ids", "filter_type": "IN", "filter_value": <test_campaign_ids>}]
   )
   // For US sub-country splits (matched-pair states / DMAs):
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     report_type="AUDIENCE",
     dimensions=["province_id"],  // or "dma_id"
     metrics=["spend", "impressions", "conversion", "cost_per_conversion"],
     start_date=<test_start>,
     end_date=<today>,
     filters=[{"field_name": "campaign_ids", "filter_type": "IN", "filter_value": <test_campaign_ids>}]
   )
   ```
   **iOS attribution caveat:** for iOS app-promotion tests, expect the `province_id: "-1"` and `dma_id: "0"` buckets to contain ~60-80% of SKAdNetwork-attributed conversions without device-level signal. Pull these out before computing geo-level lift — they aren't usable for matched-market comparisons. If iOS attribution loss is >50%, escalate to MMM-validated lift instead of relying on platform-reported geo-level conversions.

2. **Priority-tiered integrity checks:**

   | Priority | Check | What it catches |
   |---|---|---|
   | **P-0** | Campaign / adgroup status — has any test entity been paused, rejected, or set to learning-paused? | Test campaign offline mid-test |
   | **P-1** | Geo leakage — are TikTok impressions appearing in control regions? | Targeting bypass / region misconfiguration |
   | **P-2** | Budget pacing — is test spend within ±20% of plan? | Pacing surprise that distorts the result |
   | **P-3** | Zero or near-zero impressions in test regions | Delivery failure |
   | **W-1** | CPM volatility — has TikTok auction shifted >25% vs. pre-test baseline? | External market change that confounds the read |
   | **W-2** | CTR / hook rate change — has creative performance shifted? | Mid-test creative refresh contaminating the test |
   | **W-3** | Conversion sparsity — accumulating <50% of expected daily conversions | Low statistical power; may need to extend |

3. **Response protocol by priority:**

   - **P-0:** Immediate. Re-enable via BlueAlpha pipeline. Note downtime for analysis adjustment.
   - **P-1:** Critical. Pull region-level impression data:
     ```
     tiktok_ads_get_tiktok_insights(
       advertiser_id=<id>,
       data_level="AUCTION_CAMPAIGN",
       dimensions=["campaign_id", "country_code"],
       metrics=["impressions", "spend"],
       start_date=<test_start>,
       end_date=<today>
     )
     ```
     If impressions show in control regions: fix targeting, note contamination period, adjust analysis to exclude affected days.
   - **P-2:** Investigate pacing — auction dynamics, budget cap binding, or learning-phase reset?
   - **P-3:** Run the underspend diagnostic flow from `tiktok-auto-optimize`.
   - **W-1 to W-3:** Log. Don't intervene unless persistent (>3 consecutive days of warning).

4. **Monitoring log:**
   - Timestamp every check
   - Document any intervention
   - Track contaminated days
   - This log is essential for the post-test analysis — a test contaminated for 3 of 28 days needs the analysis to account for that

## Phase 4: Post-Test Analysis

After the test window closes, measure the lift and draw the conclusion.

1. **Pull final test-period performance, sliced by region:**
   ```
   tiktok_ads_get_tiktok_insights(
     advertiser_id=<id>,
     data_level="AUCTION_CAMPAIGN",
     dimensions=["campaign_id", "country_code"],
     metrics=["spend", "impressions", "clicks", "conversion", "cost_per_conversion", "conversion_rate"],
     start_date=<test_start>,
     end_date=<test_end>
   )
   ```
   Note: this captures TikTok's own attribution. For "true" lift, you need source-of-truth conversions from the user's data warehouse or MMM — not just TikTok's reported numbers.

2. **Source-of-truth conversion data:**
   - Pull total conversions in test vs. control regions from the user's CDP / data warehouse / MMM
   - Compare to TikTok-reported conversions in the same regions
   - The gap is informative: if TikTok claims 1000 conversions in test regions but warehouse shows the test-region total only grew by 700 vs. control, TikTok's attribution is over-counting by 30%

3. **Compute lift:**
   - **Conversion lift** = (Test region per-capita conversion rate - Control region per-capita conversion rate) / Control region per-capita conversion rate
   - **Revenue lift** = same formula with revenue
   - **iROAS** (incremental ROAS) = Incremental revenue / TikTok spend in test regions

4. **Statistical significance:**
   - Two-sample proportion test (for binary conversion events) or two-sample t-test (for revenue)
   - Report p-value and 90% / 95% confidence interval
   - p>0.10 = inconclusive. Decide: extend test or accept that the channel's lift is small/zero.

5. **If MMM is available, compare results to model predictions:**
   ```
   meridian_get_raw_channel_roi(model_id, channel="tiktok")
   meridian_get_raw_contribution_breakdown(model_id)
   ```

   | Test result vs. MMM | Interpretation |
   |---|---|
   | Test lift matches MMM | Both methods agree. High confidence. Act on the MMM going forward. |
   | Test lift > MMM prediction | MMM may be undervaluing TikTok. Send to modeling team for recalibration. |
   | Test lift < MMM prediction | MMM may be overvaluing TikTok. Send to modeling team. |
   | Test lift = 0, platform CPA looks fine | Classic platform over-attribution. This is the Cann / Klover finding. |

6. **Report deliverable:**

   ```
   TIKTOK INCREMENTALITY TEST — RESULTS

   Hypothesis: <restated>
   Design: <geo split, duration>

   RESULTS
   - Measured lift: <X%> (95% CI: <Y, Z>)
   - p-value: <p>
   - iROAS: <X>
   - Source-of-truth conversion gap: <test_region_lift_actual vs. tiktok_reported>

   MMM CROSS-CHECK
   <Statement on agreement / disagreement with the model>

   PLATFORM ATTRIBUTION VERDICT
   <Is TikTok over-attributing? By how much?>

   INTEGRITY LOG
   - Contaminated days: <n>
   - Pacing variance: <%>
   - Notable interventions: <list>

   RECOMMENDATION
   - <Scale / maintain / cut / retest>

   COST OF TEST
   <$ in control regions during the test window — the opportunity cost>
   ```

## Phase 5: Teardown & Next Steps

1. **Restore configuration:**
   - Remove negative geo targeting added to existing campaigns
   - Re-enable control region campaigns if they were paused
   - Delete test-only campaigns if they were spun up for the experiment
   - Capture before/after state for the audit trail

2. **Apply the learning:**
   - If TikTok proved incremental: maintain spend, supported by causal evidence. Update the MMM priors.
   - If TikTok showed no lift: reduce spend; redirect to channels with proven incrementality.
   - If inconclusive: redesign — longer duration, larger geo split, or focus on a specific campaign/cohort.

3. **MMM feedback loop:**
   - Document the test in the MMM system: hypothesis, design, measured lift, iROAS, recommendation.
   - This becomes a calibration anchor for the next model refresh.

4. **Next test in the roadmap:**
   - Is there a follow-up question? (e.g., "TikTok proved incremental nationally — is Pangle specifically incremental, or is TikTok placement carrying everything?")
   - Recommend the next test in the sequence. Hand off to `mmm-test-roadmap` if a quarterly testing plan is in scope.

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Test hypothesis** — what's being tested
3. **Test scope** — channel / campaign / creative cohort / placement
4. **Test duration** — minimum 4 weeks, recommended 6-8
5. **Geo design preference** — matched pairs / regional holdout / budget suppression
6. **Available geos** — what the user has data presence in
7. **MMM model** — for priors and post-test comparison (strongly recommended)
8. **Source-of-truth conversion data source** — CDP / warehouse / GA / MMM
9. **Cross-channel context** — what other paid channels are running in test/control regions (contamination risk)

## Output

1. **Test Plan Document** — full design with geo IDs, durations, success criteria
2. **Pre-Test Configuration Spec** — what changes during test
3. **Monitoring Schedule** — check cadence + integrity checklist
4. **Final Results Report** — lift, iROAS, statistical significance, MMM cross-check
5. **Teardown Plan** — restoration steps
6. **Next-Test Recommendation**

## Important Notes

- **Platform-reported TikTok ROAS systematically overstates incremental contribution.** This is the central reason to run incrementality tests on TikTok. Expect 20-50% over-attribution in most accounts. The proof point at Cann was AppLovin showing zero lift despite strong platform-reported ROAS — same dynamic applies to TikTok.
- **iOS app campaigns are the highest-value test target.** SKAdNetwork makes platform iOS attribution especially unreliable. If the client runs iOS app-install campaigns, prioritize iOS for the first incrementality test.
- **6-8 week tests beat 4-week tests.** TikTok adstock + lagged conversion means a 4-week test under-detects the channel's contribution. Always recommend 6+ weeks unless the user has urgency constraints.
- **Don't test multiple things at once.** If you change creative AND budget AND placement during a "test," you can't attribute the result. Hold all non-test variables constant.
- **Cross-channel contamination is the silent killer.** If the client runs national TV, podcast ads, or other location-independent media during the test, those drive conversions in both test and control regions and dilute the lift signal. Always document concurrent channels.
- **Budget suppression beats full holdout in client-facing politics.** Most clients won't agree to fully pause TikTok in 5 markets for 8 weeks. A 90% budget reduction is statistically only ~10% less powerful and is much easier to sell. Default to budget suppression for the first test.
- **Cross-skill handoffs:** Once the test is designed, hand off to BlueAlpha pipeline for execution. Once results are in, hand off to `mmm-attribution-reconciler` if MMM and test disagree, or `mmm-test-roadmap` for the next-test sequence.
