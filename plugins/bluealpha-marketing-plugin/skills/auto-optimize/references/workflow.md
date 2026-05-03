# Auto-Optimize Workflow Phases

## Phase 1: Structural Audit

Start with the big picture — is the account built correctly?

1. **Run `audit_campaign_structure`** on the account:
   ```
   audit_campaign_structure(customer_id, days=30)
   ```
   This scores each campaign 0-110 across structure (20), bid strategy (20), budget health (20), targeting (20), extensions (20), and performance (±10).

   - **Score < 60:** Campaign needs restructuring. Major issues in foundation.
   - **Score 60-89:** Campaign needs specific fixes. Functional but leaving performance on the table.
   - **Score 90+:** Campaign is healthy. Ready to scale if budget allows.

2. **Categorize campaigns** into three buckets:
   - **Fix:** Score < 60 or critical issues flagged. Address these first — no point optimizing bids on a broken structure.
   - **Tune:** Score 60-89. Working but can improve. Budget reallocation and recommendation application go here.
   - **Scale:** Score 90+. These are the winners. If budget is available, move more money here.

3. **Present the structural scorecard** to the user before taking action. Don't start fixing things silently — show the audit results and get alignment on priorities.

## Phase 2: Underspend Diagnosis

Identify why campaigns aren't spending their full budget — this is the most common "silent" performance issue.

1. **Run `diagnose_underspend`** on the account:
   ```
   diagnose_underspend(customer_id)
   ```
   This runs a 5-layer diagnostic:
   - **Layer 1 — Hard Issues:** Campaign status, ad disapprovals, end dates, shared budget conflicts
   - **Layer 2 — Limited Reach:** Geo restrictions, ad scheduling, demographics, keyword match types too narrow
   - **Layer 3 — Bidding:** Impression share lost to rank, target CPA/ROAS set too aggressively
   - **Layer 4 — Quality:** Ad strength, Quality Score, landing page relevance
   - **Layer 5 — Other:** Conversion lag, learning period, seasonal patterns

2. **Prioritize fixes by severity:**
   - Hard issues (Layer 1) block everything — fix these immediately
   - Reach and bidding issues (Layers 2-3) are the most common causes of underspend
   - Quality issues (Layer 4) are slower to fix but have the highest long-term impact

3. **Layer 1 fixes to recommend:**
   - Disapproved ads: Identify policy violations and recommend new compliant ad copy
   - Paused campaigns that should be active: Flag for user confirmation and reactivation
   - Expired end dates: Identify and recommend extension or removal
   - Shared budget conflicts: Identify and recommend budget increase or split

## Phase 3: Budget Reallocation

Move budget from underperformers to outperformers — the single highest-ROI optimization action.

1. **Run `analyze_budget_reallocation`** on the account:
   ```
   analyze_budget_reallocation(customer_id, days=30)
   ```
   This classifies campaigns by bid strategy, checks budget/reach/quality constraints, and recommends budget moves from -30% to +30%.

2. **If MMM is available, cross-reference with incrementality data:**
   ```
   get_marginal_roi(model_id)
   get_saturation_curves(model_id)
   simulate_budget_reallocation(model_id, scenario=<proposed_changes>)
   ```
   The key insight: Google Ads might say Campaign A has 5x ROAS and Campaign B has 2x ROAS, suggesting you should move all budget to A. But the MMM might show that Campaign A is saturated (flat saturation curve) while Campaign B has steep marginal returns. In that case, the platform data is misleading and the MMM should win.

   **Decision hierarchy:**
   - If MMM and Google Ads agree → high confidence, execute the reallocation
   - If MMM disagrees with Google Ads → trust the MMM for budget direction, use Google Ads data for tactical execution (bid adjustments, targeting)
   - If no MMM available → use Google Ads data with the caveat that platform attribution overweights last-touch

3. **Budget reallocation recommendations:**
   - Campaigns to increase: Which campaigns show highest efficiency and have headroom to scale (increases capped at 30% per cycle)
   - Campaigns to decrease: Which campaigns show lower efficiency or are saturating
   - Campaigns to preserve: Which campaigns are newly launched (< 2 weeks) or have learning periods active
   - Decision framework: Always require user confirmation before any budget changes > $10/day

## Phase 4: Google Recommendations Review

Google's optimization recommendations are a mixed bag — some are genuinely useful, others are just Google trying to increase your spend. This phase reviews them with a critical eye.

1. **Pull recommendations:**
   ```
   get_recommendations(customer_id)
   ```

2. **Categorize each recommendation:**

   **Usually safe to apply:**
   - Keyword match type expansions (exact → phrase) on proven keywords
   - Responsive search ad improvements (adding more headlines/descriptions)
   - Removing redundant keywords
   - Fixing disapproved ads

   **Apply with caution:**
   - Bid strategy changes (switching to tCPA/tROAS) — only if there are 15+ conversions in the last 30 days
   - Budget increases — only if the campaign is already profitable and not saturated
   - New keyword suggestions — check relevance carefully, Google often suggests tangentially related terms

   **Usually decline:**
   - "Upgrade to broad match" for all keywords — destroys targeting precision
   - "Remove all negative keywords" — these exist for a reason
   - "Switch to Performance Max" — only appropriate if the user is ready for a fundamental campaign type change
   - Auto-apply anything — recommendations should always be human-reviewed

3. **Recommendation evaluation and summary:**
   - List all recommendations pulled
   - Flag each as "safe to apply", "apply with caution", or "usually decline"
   - Present summary: which are recommended for execution and which should be dismissed, with rationale

## Phase 5: Creative Health Check

Run the creative analysis to catch fatigue before it wastes budget.

1. **Run `detect_creative_fatigue`:**
   ```
   detect_creative_fatigue(customer_id)
   ```

2. **Run `analyze_creatives`:**
   ```
   analyze_creatives(customer_id, days=30)
   ```

3. **For fatigued or bottom-tier ads:**
   - If fatigue severity is critical/high → hand off to the brand-refresh-pipeline skill for full creative refresh
   - If the ad is bottom 20% by performance but not fatigued → test pausing it and letting Google rotate to better-performing ads
   - If most ads in a campaign are underperforming → the issue is likely audience or landing page, not creative. Flag this.

4. **For insufficient data scenarios** (common in low-spend accounts):
   - Note the gap but don't force creative changes
   - Recommend reaching the minimum threshold (1,000 impressions per ad) before the next optimization cycle
   - Focus the cycle's effort on structure and budget instead

## Phase 6: Optimization Plan & Report

Compile all findings and recommendations into a single optimization report.

1. **Optimization plan summary** with:
   - **Structural Scorecard:** Campaign-by-campaign scores with trend vs. last cycle
   - **Layer 1 Fixes (Hard Issues):** Disapprovals, paused campaigns, expired dates, shared budget conflicts — all with recommended fixes
   - **Layer 2-3 Fixes (Reach & Bidding):** Targeting gaps, match type restrictions, impression share issues — recommendations for addressing
   - **Budget Reallocation Plan:** Which campaigns to increase (up to 30%), which to decrease, which to preserve — with MMM validation if available
   - **Recommendations Review:** Which Google Ads recommendations to apply, dismiss, and why
   - **Creative Health Assessment:** Fatigue levels, refresh recommendations, insufficiency flags

2. **Generate the optimization report** with:
   - **Structural Scorecard:** Campaign-by-campaign scores with trend vs. last cycle
   - **Changes Recommended:** Every recommended change grouped by risk level:
     - **Auto-approve:** Low-risk fixes (fixing disapprovals, removing redundant keywords)
     - **Recommend:** Medium-risk optimizations (budget shifts < 20%, bid adjustments)
     - **Needs Discussion:** High-risk changes (campaign structure overhauls, bid strategy switches, budget increases > 30%)
   - **Budget Impact:** Net change in daily budget, projected impact on spend/conversions
   - **Creative Status:** Fatigue levels, refresh needs by campaign
   - **MMM Cross-Check:** (if available) Whether the optimizations align with incrementality data
   - **Next Cycle Recommendations:** What to watch for before the next optimization run

3. **Present the full action plan** to the user for approval and handoff to execution pipeline. Group changes by risk level and get explicit confirmation on high-risk items.

## Running as a Recurring Cycle

This skill is designed to be run regularly. Recommended cadence:

- **Weekly:** For accounts spending $5K+/month — run the full cycle every Monday
- **Bi-weekly:** For accounts spending $1K-$5K/month — enough to catch issues without over-optimizing
- **Monthly:** For accounts spending < $1K/month — changes need more time to accumulate data

Each cycle should reference the previous cycle's report to track trends:
- Are structural scores improving?
- Are underspend issues being resolved?
- Are budget reallocations producing the expected lift?
- Are creative fatigue patterns emerging?

Suggest setting this up as a scheduled task if the user wants automated recurring optimization.

## Inputs

Gather from the user before starting:

1. **Google Ads customer ID** — which account to optimize (required; use `list_accessible_customers` if unknown)
2. **Scope** — full account, specific campaigns, or specific channel type (optional; default to full account)
3. **Risk tolerance** — conservative (only low-risk changes), moderate (budget shifts up to 20%), aggressive (full restructuring) (optional; default to moderate)
4. **MMM model** — for incrementality-informed budget decisions (optional; `list_models` to find available models)
5. **Previous cycle report** — if this is a recurring run, reference the last report for trend tracking (optional)
6. **Budget constraints** — max daily spend, campaign-level caps (optional)

## Output

Deliver to the user:

1. **Account Health Scorecard** — overall score + per-campaign breakdown
2. **Underspend Diagnosis** — what's blocked and why, with fixes applied or recommended
3. **Budget Reallocation Plan** — where money moved, with MMM validation if available
4. **Recommendations Summary** — what was applied, dismissed, and why
5. **Creative Status** — fatigue levels, refresh needs
6. **Action Log** — every change made, with before/after values
7. **Next Cycle Plan** — what to watch for, when to run again

## Important Notes

- **Don't optimize everything at once.** Each change needs 1-2 weeks to show its effect. If you change the budget AND the bid strategy AND the keywords AND the creative in one cycle, you'll never know what worked. Prioritize the highest-impact change and let it run before making the next one.
- **Platform ROAS lies (sometimes).** Google Ads attributes conversions using its own model, which overweights Google's contribution. The MMM cross-check exists specifically to catch this. When available, always validate budget decisions against the MMM before executing.
- **Automation score ≠ account health.** Google rewards you for accepting its recommendations with a higher optimization score. But many of those recommendations serve Google's interests (more spend, broader targeting) rather than yours. This skill evaluates recommendations independently — a 70% optimization score with high-quality campaigns beats a 95% score achieved by blindly accepting everything.
- **Respect the learning period.** After any bid strategy change, Google needs 7-14 days to recalibrate. Don't run another optimization cycle during this period — you'll get misleading data and make bad decisions. Flag active learning periods in the report.
- **Cross-skill handoffs:** If the audit reveals structural issues too large for this skill (e.g., campaigns need to be rebuilt from scratch), hand off to SEO-to-Paid Bridge or Competitive Conquest. If creative fatigue is detected, hand off to Brand Refresh Pipeline. If the account needs new content to promote, suggest Content-to-Campaign.
