# Competitive Conquest Workflow Phases

## Phase 1: Competitive Intelligence Gathering

Start by invoking the marketing plugin's `/competitive-brief` skill. This produces a structured competitor analysis including positioning, messaging pillars, content gaps, and opportunities.

1. **Run the competitive brief** for the target competitor(s)
   - If the user named a specific competitor, focus on that one
   - If they said something general like "go after our competitors", research the top 2-3 competitors in their space
   - The brief should surface: competitor messaging themes, positioning gaps they haven't claimed, weaknesses in their product/offering, and keyword territories they own vs. don't own

2. **Extract actionable conquest angles** from the brief:
   - Messaging gaps: things competitors claim that the user does better (or competitors don't claim at all)
   - Positioning whitespace: territories no competitor has staked out
   - Proof points: specific data, features, or customer evidence that supports conquest messaging
   - Objection-busters: reasons someone searching for the competitor should consider switching

Save these angles — they'll drive the ad copy in Phase 3.

## Phase 2: Keyword Research & Opportunity Sizing

Use the Google Ads MCP to build the keyword universe for the conquest campaigns.

1. **Generate keyword ideas** using the Google Ads MCP's `generate_keyword_ideas` tool:
   - Seed with competitor brand names (e.g., "HelloFresh", "Home Chef")
   - Seed with competitor brand + modifier terms (e.g., "HelloFresh review", "HelloFresh alternative", "HelloFresh vs")
   - Seed with non-brand terms the competitive brief identified as competitor-dominated
   - Request volume, competition level, and bid estimates for all

2. **Segment keywords into tiers:**
   - **Tier 1 — Competitor Brand (High Intent):** Direct competitor brand queries. These convert well but are expensive and legally sensitive. Use for exact match only.
   - **Tier 2 — Competitor + Modifier (Consideration):** "vs", "alternative", "review", "cancel" queries. High intent, moderate competition. These are often the most profitable conquest keywords.
   - **Tier 3 — Category (Awareness):** Non-brand category terms the competitor dominates. Broader reach, lower intent, useful for awareness.

3. **Check existing coverage** by querying current campaigns:
   - Use `execute_query` to see if any of these keywords are already in active campaigns
   - Identify gaps — keywords the user should be bidding on but isn't
   - Identify conflicts — keywords that would compete with existing brand or non-brand campaigns

## Phase 3: Campaign Creation & Ad Copy

Build the conquest campaign structure in Google Ads.

1. **Campaign structure:**
   - Create one campaign per major competitor (or one combined campaign with competitor-specific ad groups, depending on budget)
   - Naming convention: `[Date]_[Brand]_conquest_google_[competitor]_[match-type]`
   - Bidding: Start with Maximize Conversions with a tCPA based on the user's existing non-brand CPA (or slightly higher, since conquest traffic typically converts at a lower rate)

2. **Ad group structure:**
   - One ad group per keyword tier per competitor
   - Example: `HelloFresh_Brand_Exact`, `HelloFresh_Alternative_Broad`, `HelloFresh_vs_Exact`

3. **Write RSAs using the competitive brief's messaging angles:**
   - Headlines should directly address why the user's product is better than the competitor
   - Use the proof points and objection-busters from Phase 1
   - Include at least one headline that calls out the competitor's weakness (without naming them directly in the ad, to stay within Google Ads policies)
   - Include promotional offers if available
   - Pin the most important differentiator message to Headline Position 1

   **Example RSA structure for a meal kit conquest:**
   ```
   Headlines:
   H1 (pinned): "100+ Weekly Meals — No Subscription"
   H2: "Chef-Designed Global Flavors"
   H3: "Ready in 5 Minutes or Less"
   H4: "Skip the Same Old Recipes"
   H5-H15: [additional benefit/proof/promo headlines]

   Descriptions:
   D1: "Tired of the same 20 meals every week? [Brand] offers 100+ options with zero subscription commitment. Try it today."
   D2: "Premium ingredients, chef-designed recipes, 3 flexible formats. Order what you want, when you want."
   D3-D4: [promo-focused, convenience-focused variants]
   ```

4. **Set targeting:**
   - Geographic: Match the user's existing campaign geos (pull from current campaigns via `execute_query`)
   - Audiences: Add competitor website visitors and in-market audiences as observation layers
   - Negative keywords: Exclude the user's own brand terms to avoid cannibalization

5. **Campaign specification and strategy:**
   Document the complete campaign structure for handoff to the execution pipeline:

   - **Budget:** Daily budget amount and cadence
   - **Campaign naming:** `[Date]_[Brand]_conquest_google_[competitor]_[match-type]`
   - **Ad group structure:** One ad group per keyword tier per competitor (Brand Exact, Consideration, Promo, etc.)
   - **Keyword structure:** Tier 1 (brand, exact match), Tier 2 (brand + modifier, phrase match), Tier 3 (category, broad)
   - **Negative keywords:** Own brand terms, competitor login/support terms, and other cannibalization preventers
   - **RSA copy specification:**
     - Headlines: 15 headlines total, with H1 (pinned) being the strongest differentiator
     - Descriptions: 4 descriptions with proof points, objection-busters, and promotional angles
     - Use the competitive angles from Phase 1 to guide copy direction
   - **Targeting:** Geographic locations and languages (match existing campaigns)
   - **Bidding:** Start with Maximize Conversions with tCPA based on user's non-brand CPA

   Compile the full campaign blueprint into a structured specification document.

## Phase 4: Measurement & Optimization (MMM Loop)

After launch, use the Meridian MMM to validate that the conquest spend is truly incremental.

1. **Baseline measurement:**
   - Before launch, pull the current contribution breakdown from the MMM to establish a baseline
   - Note the contribution of related channels (sem_nonbrand, brand_campaigns) to watch for cannibalization

2. **Post-launch tracking (2-4 weeks):**
   - After sufficient data accumulates, reload the MMM with updated data
   - Compare contribution breakdown before vs. after conquest launch
   - Key question: did total contribution increase, or did conquest just steal from existing non-brand?

3. **Optimization triggers:**
   - If MMM shows positive incremental contribution → scale the campaign (increase budgets, expand to more competitors)
   - If MMM shows cannibalization (non-brand contribution dropped by roughly the same amount conquest added) → refine targeting, tighten keyword match types, or reduce overlap
   - If MMM shows no measurable lift → pause and reallocate to higher-ROI channels

4. **Ongoing creative refresh:**
   - Run `detect_creative_fatigue` monthly on the conquest campaigns
   - When fatigue is detected, regenerate RSAs using updated competitive intelligence from a fresh `/competitive-brief` run
   - This keeps the messaging relevant as competitors evolve their own positioning

## Inputs

Gather from the user before starting:

1. **Target competitor(s)** — who to go after (required)
2. **Google Ads customer ID** — which account to build in (required; if unknown, use `list_accessible_customers` to help them find it)
3. **Budget** — daily or monthly budget for conquest (optional; if not provided, suggest starting at 10-15% of current non-brand spend)
4. **MMM model** — which Meridian model to use for measurement (optional; if not provided, list available models and let them choose, or skip the MMM phase)
5. **Promotional offers** — any current promos to feature in ads (optional)

## Output

At the end of the workflow, present the user with:

1. **Conquest strategy summary** — which competitors, which angles, which keywords
2. **Campaign structure** — campaigns, ad groups, keywords, and ads created
3. **Estimated reach** — impressions, clicks, and cost projections from keyword planner data
4. **Measurement plan** — when to check the MMM for incrementality, what to look for
5. **Next steps** — creative refresh schedule, expansion opportunities, optimization triggers

## Important Notes

- **Google Ads policies:** Never use a competitor's trademarked name in ad copy text (headlines/descriptions). You can bid on their brand terms as keywords, but the ad copy must differentiate without naming the competitor directly. Use phrases like "Looking for an Alternative?" rather than "Better than [Competitor]."
- **Budget guardrails:** Conquest campaigns typically have higher CPAs than brand campaigns. Set expectations with the user that a 2-3x CPA premium is normal for conquest, and the value comes from acquiring customers who would have otherwise gone to the competitor.
- **Cannibalization watch:** The biggest risk with conquest is that it steals from your own non-brand campaigns rather than taking from competitors. The MMM measurement in Phase 4 is specifically designed to catch this. Always run it.
