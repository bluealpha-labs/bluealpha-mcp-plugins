# The Full Monty — Detailed Workflow

## Phase 1: Account Health Baseline (Auto-Optimize)

**What runs:** `audit_campaign_structure`, `diagnose_underspend`, `analyze_budget_reallocation`, `get_recommendations`, `detect_creative_fatigue`, `analyze_creatives`

**Purpose:** Establish the current state before making any strategic changes. No point building new campaigns on a broken foundation.

**Key outputs for downstream phases:**
- Campaign structural scores → informs which campaigns to keep vs. rebuild
- Underspend diagnosis → identifies capacity for new spend
- Budget reallocation recommendations → establishes the budget envelope for new campaigns
- Current keyword coverage → feeds into the SEO-to-Paid Bridge gap analysis
- Creative health → feeds into Brand Refresh Pipeline

**Execute immediately:** Fix critical issues (disapproved ads, broken targeting, paused campaigns that should be active). These don't require strategic decisions — they're just broken.

**Hold for later:** Budget reallocation, bid strategy changes, recommendation applications. These should be informed by the strategic phases that follow.

## Phase 2: Competitive Landscape (Competitive Conquest + Counterpunch)

**What runs:** Marketing plugin `/competitive-brief`, Google Ads auction insights, `generate_keyword_ideas` for competitor terms

**Purpose:** Understand the competitive environment before building campaigns. Who are the competitors, where are they vulnerable, and are any of them targeting you?

**Key outputs for downstream phases:**
- Competitor messaging gaps → drives conquest campaign ad copy AND brand refresh messaging
- Competitor keyword territories → feeds into SEO-to-Paid Bridge overlap matrix
- Auction insights (if brand campaign exists) → determines if counterpunch is needed
- Conquest campaign specs → ready to build in Phase 5

**Hold for later:** Don't build conquest campaigns yet. The SEO-to-Paid Bridge analysis might reveal that some "conquest" keywords are actually better served by organic + bridge campaigns.

## Phase 3: Search Coverage Strategy (SEO-to-Paid Bridge)

**What runs:** Marketing plugin `/seo-audit`, Google Ads keyword queries, `generate_keyword_ideas` from domain URL

**Purpose:** Map the full search landscape — organic + paid + gaps — and decide where paid should play vs. where organic handles it.

**Key outputs for downstream phases:**
- Search coverage matrix → the master keyword strategy document
- Bridge campaign specs → ready to build in Phase 5
- Content gaps identified → feeds into Content-to-Campaign
- Keywords categorized by band (A/B/C/D) → informs budget allocation across all campaigns

**Cross-reference with Phase 2:** Some keywords flagged as "competitor-dominated" in the SEO-to-Paid Bridge analysis should be routed to the conquest campaigns from Phase 2 rather than treated as bridge opportunities. Deduplicate.

## Phase 4: Content Promotion (Content-to-Campaign)

**What runs:** Content analysis of key pages, `generate_keyword_ideas` from content URLs, campaign spec generation

**Purpose:** Identify high-value content that deserves paid amplification and build campaigns around it.

**Key inputs from previous phases:**
- Content gaps from Phase 3 → which existing content is underexposed?
- Competitive angles from Phase 2 → which case studies or comparison pages counter competitor positioning?
- Account capacity from Phase 1 → how much budget is available for content promotion?

**Key outputs:**
- Content promotion campaign specs → ready to build in Phase 5
- Content creation recommendations → new pages to build (outside this skill's scope, but flagged)

## Phase 5: Campaign Specification & Deployment Planning

**What this phase produces:** Comprehensive deployment specifications for all campaigns designed in Phases 2-4.

**Purpose:** Create a complete blueprint for coordinated campaign deployment, including all campaign structures, keyword strategies, ad copy, targeting, and budget allocations.

**Campaign specifications to create:**
1. **Conquest campaigns** (from Phase 2) — specs for targeting competitor brand terms
2. **Bridge campaigns** (from Phase 3) — specs for supplementing weak organic positions
3. **Content promotion campaigns** (from Phase 4) — specs for driving traffic to key content
4. **Counterpunch campaigns** (from Phase 2, if needed) — specs for defending brand terms
5. **Restructured existing campaigns** (from Phase 1, if needed) — specs for replacing broken structures

**Campaign structure planning:**
- Recommend cross-negative keyword strategy to prevent internal competition:
  - Brand campaigns exclude competitor terms
  - Conquest campaigns exclude own brand terms
  - Bridge campaigns exclude both brand and conquest terms
  - Content campaigns exclude all of the above

**Deployment preparation:** Generate a comprehensive deployment plan including every campaign spec, ad group structure, keyword list, ad copy, targeting parameters, and budget allocation. Present this plan to the user for review and approval before implementation.

## Phase 6: Creative Refresh (Brand Refresh Pipeline)

**What runs:** `detect_creative_fatigue`, `analyze_creatives`, marketing plugin `/brand-review` and `/content-creation`

**Purpose:** Ensure all ad copy — old and new — is on-brand, fresh, and optimized.

**Key inputs from previous phases:**
- Competitive messaging angles from Phase 2 → weave into ad copy
- Content analysis from Phase 4 → ad copy should bridge search intent to content
- Structural audit from Phase 1 → which existing ads need refresh?

**Actions:**
- Audit all existing ad copy for brand voice consistency
- Generate new RSAs for any campaigns created in Phase 5
- Refresh any fatigued ads identified in Phase 1
- Ensure every ad group has at least 2 RSAs for rotation

## Phase 7: Measurement Setup (MMM + Tracking)

**What runs:** MMM model loading, baseline metrics pull, measurement plan creation

**Purpose:** Establish the measurement framework so the impact of all these changes can be validated.

**If MMM is available:**
- Load the relevant model: `load_model(model_id)`
- Pull the pre-deployment contribution breakdown: `get_contribution_breakdown(model_id)`
- Pull marginal ROI by channel: `get_marginal_roi(model_id)`
- Pull saturation curves: `get_saturation_curves(model_id)`
- These become the baseline for measuring lift after deployment

**Regardless of MMM:**
- Record pre-deployment metrics for all campaigns: impressions, clicks, conversions, CPA, ROAS
- Set check-in dates: Day 7, Day 14, Day 30
- Define success criteria for each campaign type

## Phase 8: Unified Report & Next Steps

Compile everything into a single deliverable.

**The Full Monty Report includes:**

1. **Executive Summary** — 5 sentences on account health, competitive position, biggest opportunities, and actions taken
2. **Account Health Scorecard** — from Phase 1, with fixes applied
3. **Competitive Landscape** — from Phase 2, with conquest and counterpunch plans
4. **Search Coverage Matrix** — from Phase 3, the master keyword strategy
5. **Content Promotion Plan** — from Phase 4, which content gets paid amplification
6. **Campaign Deployment Log** — from Phase 5, every campaign created with specs
7. **Creative Audit** — from Phase 6, ad copy status and refreshes
8. **Measurement Baseline** — from Phase 7, pre-deployment metrics and check-in schedule
9. **Budget Summary** — total new spend, reallocation from existing, net budget change
10. **Next Steps** — what to do at Day 7, Day 14, Day 30, and ongoing cadence

## Important Notes

- **This takes time.** The Full Monty is a comprehensive session — expect it to take significantly longer than running any individual skill. Set expectations with the user upfront.
- **Don't skip phases.** The sequence is deliberate — each phase's output feeds the next. Skipping Phase 1 means building campaigns on a broken foundation. Skipping Phase 3 means the keyword strategy has blind spots.
- **Prioritize ruthlessly.** The Full Monty will surface more opportunities than can be executed at once. The report should rank everything by expected impact and recommend a phased rollout: deploy the top 3 campaigns this week, queue the next 3 for next month.
- **The user should review before anything goes live.** All specifications are created and the full plan is presented for user review. The Full Monty produces a lot of changes — the user needs to see the whole picture before enabling campaigns.
- **Schedule follow-up.** After the Full Monty, recommend scheduling the auto-optimize skill as a recurring weekly or bi-weekly check to maintain the gains and catch any issues early.
