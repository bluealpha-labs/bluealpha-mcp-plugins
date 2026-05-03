# SEO-to-Paid Bridge Workflow Phases

## Why This Matters

Most companies either bid on keywords they already rank #1 for (wasting money) or avoid bidding on keywords where they rank #8 (missing incremental traffic). The research is clear: paid + organic together on the same SERP produce more total clicks than either alone, but only when the organic position is weak (positions 4+). When you already own position 1 organically, adding a paid ad has diminishing returns — unless a competitor is bidding aggressively on those same terms.

This skill automates that analysis so the user gets a clear, prioritized action plan.

## Phase 1: Organic Landscape Audit

Start with the marketing plugin's `/seo-audit` skill to understand the user's organic search footprint.

1. **Run the SEO audit** for the user's domain:
   - Focus on keyword rankings, not technical SEO (unless they specifically ask for a full audit)
   - Extract: ranked keywords, current positions, estimated organic traffic per keyword, pages ranking, and any recent position changes
   - If the SEO audit skill isn't available or the user provides their own SEO data (e.g., a CSV from Ahrefs, SEMrush, or Google Search Console), use that instead

2. **Segment organic keywords by position band:**
   - **Band A — Dominant (positions 1-3):** Strong organic presence. Paid is only justified here if competitors are bidding aggressively on these terms or if the keyword has high commercial intent and you can't afford to lose a single click.
   - **Band B — Competitive (positions 4-7):** Organic is visible but not dominant. This is the sweet spot for paid support — adding ads here materially increases total click share.
   - **Band C — Fringe (positions 8-20):** Organic is barely visible. Paid can capture traffic while SEO efforts push rankings up over time. Treat these as "paid-first" keywords.
   - **Band D — Absent (no organic ranking):** Not ranking at all. If these are relevant terms, they need either SEO investment, paid coverage, or both.

3. **Flag high-value keywords** based on:
   - Search volume × commercial intent (informational queries rarely justify paid)
   - Conversion potential (do these queries indicate buying intent?)
   - Competitive density (are competitors already advertising here?)

## Phase 2: Paid Search Cross-Reference

Use the Google Ads MCP to pull current paid search performance and overlay it on the organic data.

1. **Pull current paid keyword data** using `execute_query`:
   ```
   SELECT
     ad_group_criterion.keyword.text,
     ad_group_criterion.keyword.match_type,
     metrics.impressions,
     metrics.clicks,
     metrics.cost_micros,
     metrics.conversions,
     metrics.average_cpc,
     campaign.name,
     campaign.status
   FROM keyword_view
   WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
     AND campaign.status = 'ENABLED'
   ```
   Use a 90-day lookback window.

2. **Build the overlap matrix** — for every keyword, determine its status:

   | Organic Rank | Paid Active? | Strategy |
   |---|---|---|
   | Positions 1-3 | Yes, spending | **Audit** — check if competitor is bidding. If not, consider pausing paid to save budget. |
   | Positions 1-3 | No | **Hold** — organic is covering it. Monitor for competitor incursion. |
   | Positions 4-7 | Yes, spending | **Optimize** — increase bid to capture more of the click share gap. |
   | Positions 4-7 | No | **Bridge** — create paid coverage. This is the highest-ROI opportunity. |
   | Positions 8-20 | Yes, spending | **Lean In** — paid is doing the heavy lifting while SEO catches up. Maintain or increase. |
   | Positions 8-20 | No | **Decide** — either invest in SEO to improve rank, or start paid coverage, or both. |
   | Not ranking | Yes, spending | **Paid Only** — no organic presence, paid is the only channel. Make sure it's performing. |
   | Not ranking | No | **Gap** — nobody's covering this keyword. Prioritize by volume and intent. |

3. **Generate keyword ideas** for adjacent opportunities the user isn't covering at all:
   - Use `generate_keyword_ideas` with the user's domain URL as a seed
   - Filter to keywords with commercial intent that aren't in either the organic or paid data
   - These represent true whitespace opportunities

## Phase 3: Unified Search Strategy & Campaign Build

Synthesize the analysis into a prioritized action plan and build the campaigns.

1. **Prioritize actions** into three buckets:

   **Quick Wins (do this week):**
   - Band B keywords with no paid coverage → create campaigns immediately
   - Paid keywords where organic is #1 and no competitor is bidding → pause to save budget
   - High-CPC paid keywords where organic is climbing (positions 8→5 trend) → reduce bids gradually

   **Strategic Investments (next 2-4 weeks):**
   - Band C keywords worth pursuing → launch paid campaigns as bridge coverage
   - Band D high-intent keywords → dual investment (new content for SEO + paid coverage now)
   - Competitor-dominated keywords identified in the SEO audit → consider conquest (hand off to competitive-conquest skill if appropriate)

   **Monitor & Decide (ongoing):**
   - Band A keywords with aggressive competitor bidding → test paid on/off and measure impact
   - Keywords with strong organic but declining positions → preemptive paid coverage before they slip

2. **Bridge campaign architecture specification:**
   Document the complete campaign structure for handoff to the execution pipeline:

   **Campaign structure for SEO bridge campaigns:**
   - Campaign naming: `[Date]_[Brand]_seo-bridge_google_[category]`
   - Organize ad groups by position band: `Band_B_Commercial`, `Band_C_Bridge`, `Band_D_Whitespace`
   - Match types: Use exact match for high-intent Band B terms, phrase match for Band C, broad match with careful negatives for Band D exploration
   - Bidding strategy: Start with Maximize Clicks for the first 2 weeks to gather data, then switch to Maximize Conversions once you have 15+ conversions
   - Initial bids: Set based on keyword planner estimates — conservative for Band B (where organic does some work), aggressive for Band C/D (where paid carries the load)

3. **Ad copy strategy:**
   - Organic snippets are informational — paid ads should emphasize action: CTAs, offers, urgency
   - If the organic page ranking is a blog post, the paid ad should link to a product/landing page (different intent, different destination)
   - If the organic page is already the product page, the paid ad should highlight something the meta description doesn't (price, promotion, differentiator)
   - Pin the strongest CTA or offer to Headline Position 1
   - Target: 10+ headlines and 3 descriptions per RSA for maximum rotation

4. **Negative keyword strategy:**
   - Exclude brand terms from non-brand bridge campaigns
   - Exclude keywords where you're deliberately letting organic carry the load
   - Cross-negative between bridge campaign ad groups to prevent overlap

5. **Actions to pause or reduce (existing wasteful coverage):**
   - Keywords flagged as "AUDIT" (organic Band A, no competitor bidding) should be paused or bid down
   - Consolidate bloated ad groups with overlapping keywords into the new, tightly themed structure

6. **Targeting and budget allocation:**
   - Geographic: Match user's existing campaign geos
   - Language: Default to user's existing language settings or US/English
   - Budget allocation: Tier 1 (Quick Wins) → largest allocation, Tier 2 (Strategic Investments) → moderate allocation, ongoing monitoring campaigns → minimal allocation

Compile the full bridge campaign blueprint and before/after budget impact into a structured specification document.

## Phase 4: Measurement — Combined Search Lift

After 2-4 weeks of the bridge campaigns running, measure whether the combined strategy is lifting total search performance.

1. **Google Ads performance pull:**
   - Pull impression share, click-through rate, and conversions for the bridge campaigns
   - Compare against the keywords' organic performance over the same period
   - Key metric: **Total Search Click Share** = organic clicks + paid clicks for the same queries

2. **MMM validation (if available):**
   - Load the Meridian model and compare contribution breakdown before vs. after the bridge campaigns launched
   - Specifically look at: did `sem_nonbrand` contribution increase without `organic` contribution dropping?
   - If organic contribution dropped by roughly what paid gained, you're cannibalizing — tighten the strategy
   - If total contribution increased, the bridge is working — consider expanding

3. **Optimization actions:**
   - Keywords where paid + organic together outperform either alone → maintain paid, this is the bridge working
   - Keywords where organic improved to positions 1-3 since launch → test pausing paid (the SEO caught up)
   - Keywords where paid is performing but organic isn't improving → increase SEO investment or accept paid as the long-term channel
   - Keywords with poor paid performance and weak organic → cut losses, focus elsewhere

## Inputs

Gather from the user before starting:

1. **Domain/website** — which site to audit organically (required)
2. **Google Ads customer ID** — which account to cross-reference and build in (required; use `list_accessible_customers` if unknown)
3. **SEO data source** — whether to run the seo-audit skill or use provided data like a CSV/export (optional; default to running the audit)
4. **Budget constraints** — how much new spend is available for bridge campaigns (optional; if not provided, frame recommendations as incremental above current spend)
5. **Priority focus** — any specific keywords, categories, or product lines to prioritize (optional)
6. **MMM model** — which Meridian model to use for measurement (optional; list available or skip)

## Output

Deliver to the user:

1. **Search Coverage Matrix** — a clear mapping of every important keyword showing organic rank, paid status, and recommended action
2. **Bridge Campaign Plan** — exact campaigns, ad groups, keywords, and ads to create
3. **Budget Reallocation Summary** — where to save (pausing wasteful paid), where to invest (new bridge coverage), net impact
4. **Measurement Plan** — when to check combined performance, what signals to look for, decision criteria for scaling or cutting
5. **Handoff Notes** — if any keywords should be routed to the competitive-conquest skill (competitor-dominated terms) or the content-to-campaign skill (content gap terms), flag them explicitly

## Important Notes

- **Don't assume paid always helps.** The whole point of this skill is to be surgical about where paid adds value. If organic is strong and no competitor is bidding, the right answer might be "don't spend money here." The user will trust the analysis more if it saves them money in some places while recommending spend in others.
- **Respect the SEO team's work.** If the user has an SEO team or strategy, the paid campaigns should complement it, not undermine it. Bridge campaigns for Band C keywords should be explicitly framed as temporary — "this covers you while SEO improves."
- **Watch for landing page conflicts.** Paid ads and organic results should ideally point to different pages (or the same page if it's the best conversion page). Never create a situation where the paid ad and organic result compete for the same click with the same page and the same messaging.
- **Cross-skill handoffs:** If the analysis reveals a competitor dominating a keyword space, suggest running the competitive-conquest skill. If it reveals content gaps where new pages need to be created, suggest the content-to-campaign skill. This skill focuses on the search coverage strategy — it doesn't build content or run conquest campaigns itself.
