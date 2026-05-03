# Competitive Counterpunch — Detailed Workflow

## Phase 1: Threat Detection & Diagnosis

Identify who's bidding on your terms and how much damage they're doing.

1. **Pull auction insights** to see who's competing:
   ```
   execute_query_stream(
     customer_id,
     "SELECT auction_insight.display_domain,
             metrics.auction_insight_search_impression_share,
             metrics.auction_insight_search_overlap_rate,
             metrics.auction_insight_search_position_above_rate,
             metrics.auction_insight_search_top_of_page_rate,
             metrics.auction_insight_search_outranking_share
      FROM campaign
      WHERE segments.date BETWEEN '{30_days_ago}' AND '{today}'
        AND campaign.id = {brand_campaign_id}"
   )
   ```
   This reveals which competitors are showing ads alongside yours, how often they appear above you, and their impression share.

2. **Check brand CPC trends** to quantify the cost impact:
   ```
   execute_query_stream(
     customer_id,
     "SELECT segments.date, metrics.average_cpc, metrics.impressions,
             metrics.clicks, metrics.search_impression_share,
             metrics.search_rank_lost_impression_share
      FROM campaign
      WHERE segments.date BETWEEN '{90_days_ago}' AND '{today}'
        AND campaign.id = {brand_campaign_id}"
   )
   ```
   Look for: CPC spikes correlating with new competitors entering the auction, impression share drops, and increasing rank-lost impression share.

3. **Identify the specific threat:**
   - **New competitor bidding on your brand:** Their domain appears in auction insights for your brand campaign. Immediate concern — they're intercepting people who already know you.
   - **Existing competitor increasing aggression:** Their overlap rate or position-above rate has increased. Gradual threat — they're escalating.
   - **Multiple competitors entering simultaneously:** Often happens after a product launch, funding round, or PR event. Requires a broader response.

4. **Assess severity:**
   - **Low:** Competitor has < 10% impression share overlap, appearing below you. Monitor but don't panic.
   - **Medium:** Competitor has 10-30% overlap, occasionally appearing above you. Brand CPC has increased 10-20%. Tactical response needed.
   - **High:** Competitor has 30%+ overlap, frequently appearing above you. Brand CPC has spiked 20%+, impression share is dropping. Full counterpunch.

## Phase 2: Competitive Intelligence (Fast)

Get just enough intel to craft a targeted response — this isn't a full competitive audit.

1. **Quick competitive research:**
   - Check the competitor's website to understand their current positioning
   - Run a web search for "[competitor] vs [your brand]" to see what comparison content exists
   - If time allows, invoke the marketing plugin's `/competitive-brief` for a fuller analysis

2. **Identify their likely angle:**
   - Are they bidding on your brand name specifically? (Direct brand attack)
   - Are they bidding on "[your brand] alternative" or "[your brand] vs"? (Consideration-stage interception)
   - Are they just broadly bidding on category terms and your brand is collateral? (Not a targeted attack)

3. **Extract counterpunch messaging angles:**
   - What do you do better than this specific competitor?
   - What proof points can you cite? (Faster, cheaper, more accurate, better support)
   - What's their weakness that your ad copy can implicitly address?

## Phase 3: Countermeasure Strategy & Recommendations

Based on the severity assessment, recommend a tailored defensive response strategy.

**Action strategy depends on severity:**

### Low Severity (Monitor):
- **Strategy:** Passive monitoring approach
- No immediate campaign changes recommended
- Recommendation: Set up an alert to run auction insights weekly and flag if the competitor's overlap rate exceeds 15%
- Ensure brand campaign is active with good extensions (recommend auto-optimize if not optimized)

### Medium Severity (Tactical Response):

**Recommended actions:**

1. **Increase brand bids** to reclaim top position:
   - Recommend bid increase of 20-30% to win back position without overpaying
   - Target: restore top-of-page impression share to 80%+

2. **Strengthen brand ad copy** with competitive differentiators:
   - Recommend pinning "Official [Brand] Site" to headline 1 to signal legitimacy vs. competitor ads
   - Ad copy should highlight proof points, key differentiators, and calls-to-action that address buyer hesitation

3. **Add brand + competitor negative keywords** to non-brand campaigns:
   - Strategy: Prevent budget bleed to competitor-related searches in non-brand campaigns
   - Recommendation: Add negative keywords for competitor brand names to cost-conscious segments

### High Severity (Full Counterpunch):

**Recommended strategy includes:**

1. **Launch a counter-conquest campaign** targeting the competitor's brand:
   - Campaign structure: Dedicated campaign targeting competitor brand terms + "[competitor] alternative" + "[competitor] vs [your brand]"
   - Ad copy strategy: Highlight your specific advantages over them
   - Geographic scope: Mirror competitor's bid territory

2. **Create comparison content** (flag for content-to-campaign skill):
   - Recommended landing page: "[Brand] vs [Competitor]" comparison page
   - Content should be factual, specific, and highlight measurable differences
   - This serves as the landing page for the counter-conquest campaign

3. **Increase brand campaign budget** if impression share is dropping:
   - Recommendation: Increase budget allocation to maintain share of voice in brand auctions
   - Amount: Sized to restore impression share to 80%+ of addressable market

4. **Add sitelink extensions** to the brand campaign:
   - Recommended extensions: "See Case Studies", "Compare Features", "Read Reviews", "Customer Success Stories"
   - Strategy: Provide additional SERP real estate and push competitor ads further down the page

5. **Approval workflow:** Present the full counterpunch plan to the user for review: what's being defended, what's being attacked, competitive context, and the budget impact.
   - If write tools are unavailable due to permission constraints, a complete counterpunch specification will be saved for manual implementation.

## Phase 4: Measurement & Escalation

1. **Track the counterpunch impact (weekly):**
   - Brand impression share: recovering? stable? still declining?
   - Brand CPC: stabilizing? still rising?
   - Auction insights: is the competitor's overlap rate decreasing?
   - Counter-conquest campaign (if launched): getting clicks on competitor's brand terms?

2. **Escalation triggers:**
   - If brand impression share doesn't recover within 2 weeks → increase bids again or expand brand keyword coverage
   - If competitor's overlap rate increases despite counterpunch → they're escalating. Consider a broader competitive campaign or non-search channels (display retargeting to competitor's audience)
   - If brand CPC exceeds 2x the pre-incursion level → the bidding war may not be worth it. Consider strategic retreat on expensive brand terms and investing in organic brand presence instead

3. **MMM validation (if available):**
   - Check whether the competitive incursion actually impacted business outcomes (conversions, revenue) or just platform metrics
   - Sometimes a competitor bidding on your brand doesn't steal conversions — your organic listing still captures the click. The MMM can reveal whether this is a real threat or a vanity concern
   - If MMM shows no revenue impact → scale down the counterpunch and save the budget
   - If MMM shows real revenue loss → full counterpunch is justified

4. **De-escalation criteria:**
   - Competitor exits the auction (overlap rate drops to 0) → pause counter-conquest, reduce brand bids to pre-incursion levels
   - Brand impression share recovers to 80%+ → maintain defensive posture but stop increasing bids
   - 90 days with no change → the competitive landscape has settled. Normalize the counterpunch into your standard campaign structure

## Important Notes

- **Don't overreact.** A competitor appearing once in auction insights at 5% overlap is not a crisis. The response should be proportional to the threat. Most "competitor bidding on our brand" alerts are low-severity and resolve on their own.
- **Brand bidding wars have no winner.** If you and a competitor keep outbidding each other on brand terms, the only winner is Google. The counterpunch strategy should aim to restore equilibrium (you win your brand auctions at a reasonable CPC), not to "destroy" the competitor's campaign. De-escalation criteria exist for a reason.
- **Legal considerations.** You can bid on a competitor's brand name as a keyword, but you cannot use their trademarked name in your ad copy text. The counterpunch follows the same rules as the competitive-conquest skill: bid on their terms, but differentiate in ad copy without naming them.
- **Cross-skill handoffs:** If the counterpunch reveals the need for new comparison content → content-to-campaign skill. If a full proactive conquest campaign is warranted → competitive-conquest skill. If the brand campaign needs structural fixes before it can defend effectively → auto-optimize skill.
