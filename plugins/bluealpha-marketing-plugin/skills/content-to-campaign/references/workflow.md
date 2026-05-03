# Content-to-Campaign Workflow Phases

## Phase 1: Content Analysis

Start by deeply understanding the content being promoted.

1. **Fetch and analyze the content:**
   - If the user provides a URL, fetch the page and extract: title, headings, key topics, target audience, CTAs, and primary value proposition
   - If the user provides a file (PDF, doc, etc.), read and analyze it the same way
   - If the content is a case study, extract: client name/industry, problem solved, metrics/results, methodology used
   - If the content is a blog post/guide, extract: primary topic, subtopics, expertise level (beginner/intermediate/advanced), and key takeaways

2. **Classify the content by funnel stage:**
   - **Top of Funnel (Awareness):** Educational content, thought leadership, industry trends. Searchers here are learning, not buying. Ad copy should promise insight/education, not demos.
   - **Middle of Funnel (Consideration):** Comparison pages, how-to guides, webinars. Searchers are evaluating options. Ad copy should emphasize differentiators and proof.
   - **Bottom of Funnel (Decision):** Case studies, pricing pages, product demos, ROI calculators. Searchers are ready to act. Ad copy should drive conversion with urgency and proof points.

3. **Extract the content's "keyword DNA":**
   - What questions does this content answer?
   - What problems does it solve?
   - What terms would someone search before needing this content?
   - What terms does this content use that match commercial search intent?

## Phase 2: Keyword Research & Mapping

Build the keyword universe that connects searchers to this specific content.

1. **Generate keyword ideas** using the Google Ads MCP:
   - Use `generate_keyword_ideas` with the content URL as a seed: `url="https://example.com/the-content-page"`
   - Also seed with the key topics extracted in Phase 1
   - Request volume, competition, and bid estimates

2. **Filter and segment keywords by intent match:**
   - **Direct Match:** Keywords that exactly describe what the content covers (e.g., content about "incrementality testing" → keyword "incrementality testing")
   - **Problem Match:** Keywords describing the problem the content solves (e.g., content about incrementality → "how to measure ad effectiveness", "is my ad spend wasted")
   - **Audience Match:** Keywords the target audience searches during their buyer journey (e.g., CMO reading about measurement → "marketing measurement tools", "prove marketing ROI")

3. **Check for existing coverage** using `execute_query`:
   - Are any of these keywords already active in other campaigns?
   - Is the content URL already used as a final URL in existing ads?
   - Avoid creating duplicate campaigns that compete with existing ones

4. **Estimate the opportunity:**
   - Total addressable search volume from the keyword list
   - Expected CPC range based on keyword planner data
   - Rough traffic projections at different budget levels (e.g., "$30/day should capture ~X clicks/month based on average CPC of $Y")

## Phase 3: Campaign Build

Create the campaign structure optimized for the specific content type.

1. **Choose the campaign structure based on content type:**

   **For a single blog post / article:**
   - One campaign, 2-3 ad groups segmented by intent (Direct, Problem, Audience)
   - Lower daily budget ($15-30) since this is content promotion, not direct response
   - Maximize Clicks bidding to start — the goal is traffic, not conversions (unless there's a strong CTA)

   **For a case study:**
   - One campaign, 2-3 ad groups: [Industry]_Keywords, [Problem]_Keywords, [Competitor]_Alternative
   - Moderate budget ($25-50) since case studies convert well
   - Maximize Conversions if conversion tracking is set up

   **For a comparison / vs. page:**
   - One campaign, ad groups per competitor or comparison dimension
   - Higher budget ($30-75) since these are high-intent bottom-funnel
   - Maximize Conversions with tCPA if enough conversion data exists

   **For a landing page / product page:**
   - One campaign with tightly themed ad groups by product feature or use case
   - Budget based on the user's overall paid strategy
   - This is closer to a standard search campaign than content promotion

2. **Campaign architecture specification:**
   Document the complete campaign structure for handoff to the execution pipeline:

   **Budget and campaign structure:**
   - Daily budget amount and cadence (appropriate for content type: $15-30 for blog, $25-50 for case study, $30-75 for comparison page)
   - Campaign naming: `YYYY-MM_[Brand]_content_google_[content-slug]`
   - Ad groups per keyword segment: Direct Match, Problem Match, Audience Match (or industry/competitor-specific for case studies)
   - Initial bidding: Maximize Clicks for first 2 weeks, then switch to Maximize Conversions

   **Keyword structure:**
   - Match types: PHRASE match for most content promotion keywords, EXACT for high-intent bottom-funnel terms
   - Segmentation: Keyword lists organized by intent type (Direct, Problem, Audience)
   - Negative keywords: Brand terms, "free" (if content is gated), cross-negatives between ad groups

   **Targeting:**
   - Geographic: Match existing campaign geos or default to US
   - Language: Match existing language settings or default to English

   **RSA specifications:**
   - Final URL: The specific content page (never a homepage)
   - Headlines: 12-15 headlines per RSA, with H1 (pinned) being the strongest intent-match or result-focused headline
   - Descriptions: 4 descriptions with CTAs, proof points, and content-specific angles

   Compile the full content campaign blueprint into a structured specification document.

## Phase 4: Write the Ad Copy

This deserves its own phase because content-to-campaign ad copy has specific rules.

1. **The ad must bridge search intent to content value.** The searcher doesn't know your content exists — they have a question or problem. The ad needs to:
   - Acknowledge the question/problem in the headline (match their intent)
   - Promise the answer/solution is in the content (create the click incentive)
   - Not oversell — if it's an article, don't make it sound like a product page

2. **Tailor ad copy to content type:**

   **Blog post / guide:**
   - H1: Question-based or curiosity-driven ("How to [Thing They Want]")
   - H2-H3: Key takeaway or surprising stat from the content
   - D1: What they'll learn + reading time or scope indicator
   - CTA: "Read the Guide", "Learn How", "See the Research"

   **Case study:**
   - H1: Result headline ("[Client] Cut $2.12M in Wasted Spend")
   - H2-H3: Method or industry relevance
   - D1: Challenge → Solution → Result in one sentence
   - CTA: "Read the Case Study", "See How They Did It"

   **Comparison / vs. page:**
   - H1: "[Product A] vs [Product B]: Honest Breakdown"
   - H2-H3: Key differentiators
   - D1: "Compare features, pricing, and real user results side by side."
   - CTA: "See the Comparison", "Compare Now"

   **Webinar / event:**
   - H1: Topic + value prop ("Master [Topic] in 45 Minutes")
   - H2-H3: Speaker credentials or past attendee stats
   - D1: Date/time + what they'll learn
   - CTA: "Register Free", "Save Your Spot"

3. **Generate multiple variants** using the marketing plugin's `/content-creation` or `/draft-content` skill:
   - At least 12-15 headlines and 4 descriptions per RSA
   - Pin the strongest intent-matching headline to H1
   - Include at least one headline with a number or stat from the content

4. **Run a brand review** on the ad copy before deploying — make sure it matches the brand voice, even when promoting content.

## Phase 5: Measurement & Content Lifecycle

1. **Set up tracking:**
   - Ensure UTM parameters are in the final URL: `?utm_source=google&utm_medium=cpc&utm_campaign=[campaign-name]`
   - If the content has a form or CTA, verify conversion tracking is firing
   - If it's ungated content (blog post), measure engagement: time on page, scroll depth, next-page navigation

2. **Performance benchmarks (content promotion):**
   - Good CTR for content promotion: 3-5% (lower than product ads since intent is informational)
   - Good CPC: Should be near the low end of keyword planner estimates (content ads compete less aggressively)
   - Success metric: Cost per engaged visitor (cost / visitors who spend 30+ seconds on page)

3. **Content lifecycle management:**
   - **Week 1-2:** Ramp up, gather data, optimize bids
   - **Week 3-4:** Evaluate performance. Is the content converting? Is it driving downstream pipeline?
   - **Month 2+:** If performance is strong, keep running. If it plateaus, refresh the ad copy (hand off to brand-refresh-pipeline skill)
   - **Evergreen content:** Can run indefinitely with quarterly copy refreshes
   - **Time-sensitive content** (webinar, event, seasonal): Set end dates on the campaign and pause automatically

4. **MMM validation (if available):**
   - After 4+ weeks, check if content promotion campaigns show up in the MMM contribution breakdown
   - Compare contribution to spend — is the content promotion channel efficient?
   - Use insights to decide which content types deserve paid amplification vs. organic-only distribution

## Inputs

Gather from the user before starting:

1. **Content to promote** — URL, document, or description of the content (required)
2. **Google Ads customer ID** — which account to build in (required; use `list_accessible_customers` if unknown)
3. **Goal** — traffic/awareness, lead generation, demo requests, or other conversion goal (optional; infer from content type if not provided)
4. **Budget** — daily or monthly budget for promotion (optional; suggest based on keyword CPC data)
5. **Target audience** — any specific audience, industry, or persona to target (optional; infer from content)
6. **Duration** — how long to run the promotion (optional; evergreen vs. time-bound)
7. **MMM model** — for measuring promotion contribution (optional)

## Output

Deliver to the user:

1. **Content Analysis** — what the content covers, funnel stage, keyword DNA
2. **Keyword Map** — keywords segmented by intent type with volume and CPC estimates
3. **Campaign Spec** — campaigns, ad groups, keywords, ads, targeting
4. **Ad Copy** — full RSA headlines and descriptions with rationale for each
5. **Budget Projection** — expected clicks, CPC, and traffic at the proposed budget
6. **Measurement Plan** — what to track, when to check, when to pause or scale

## Important Notes

- **Content quality matters more than campaign quality.** If the content is thin, poorly written, or doesn't deliver on the ad's promise, no amount of targeting optimization will save the campaign. If the content needs work, say so before building campaigns around it.
- **Match the landing page to the ad promise.** If the ad headline says "See How [Client] Cut $2M in Waste," the landing page better open with that story — not a generic homepage. Always use the specific content URL as the final URL, never a homepage.
- **Content promotion CPA is different from product CPA.** A $50 cost-per-reader on a blog post sounds expensive until that reader converts to a demo request 2 weeks later. Set expectations: content campaigns are measured by engagement and downstream pipeline, not immediate conversions.
- **Don't promote everything.** This skill works best for high-value, high-intent content: case studies, comparison pages, definitive guides, bottom-funnel content. Promoting a thin listicle or a generic "About Us" page wastes money. Be honest with the user about which content deserves paid amplification.
- **Cross-skill handoffs:** If the content analysis reveals keyword gaps where no content exists yet, flag it for the SEO-to-Paid Bridge skill. If the content competes with a specific competitor, suggest the Competitive Conquest skill. If the ad copy needs a brand voice check, route through the Brand Refresh Pipeline.
