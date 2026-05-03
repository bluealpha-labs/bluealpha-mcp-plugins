# Brand Refresh Pipeline Workflow Phases

## Phase 1: Creative Health Scan

Run a comprehensive creative fatigue and performance analysis across the account.

1. **Detect creative fatigue** using the Google Ads MCP's `detect_creative_fatigue` tool:
   - Run across all enabled campaigns, or specific campaigns if the user names them
   - This returns ads showing fatigue signals: declining CTR trend, declining conversion rate, high impression frequency, and age-based staleness
   - Capture the fatigue severity for each ad (critical, high, moderate, low)

2. **Analyze creative performance** using `analyze_creatives`:
   - Pull performance data for all RSAs across the account
   - Identify top-performing and bottom-performing headlines and descriptions
   - Note which asset combinations Google is serving most (these are the "winners" to preserve)
   - Note which assets are being suppressed by Google's rotation (these are candidates for replacement)

3. **Pull the raw ad data** for context using `execute_query`:
   ```
   SELECT
     ad_group_ad.ad.responsive_search_ad.headlines,
     ad_group_ad.ad.responsive_search_ad.descriptions,
     ad_group_ad.ad.final_urls,
     ad_group_ad.status,
     ad_group.name,
     campaign.name,
     metrics.impressions,
     metrics.clicks,
     metrics.ctr,
     metrics.conversions,
     metrics.cost_micros
   FROM ad_group_ad
   WHERE segments.date BETWEEN '{90_days_ago}' AND '{today}'
     AND campaign.status = 'ENABLED'
     AND ad_group_ad.status = 'ENABLED'
     AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
   ```

4. **Prioritize which ads to refresh** based on a combined score:
   - **Refresh urgency = Fatigue severity × Campaign importance**
   - Campaign importance comes from spend level, conversion volume, or (if MMM is available) channel contribution
   - Present the prioritized list to the user: "Here are your most fatigued ads, ordered by how much they're costing you"

5. **Handle the low-volume scenario.** If most or all ads come back as INSUFFICIENT_DATA (below minimum thresholds for fatigue detection — typically <1,000 impressions or <50 clicks):
   - **Don't skip the skill.** Low-volume accounts still benefit from a brand voice audit and creative recommendations.
   - **Shift the focus** from "detect and replace fatigued creative" to "audit existing copy and prepare for scale." The output becomes: are these ads well-written and on-brand for when volume does increase?
   - **Diagnose why volume is low.** Common causes: budget too small, campaign structure too broad (one ad group serving too many keywords kills relevance), keyword match types too restrictive, or bids too low. Flag these for other skills (SEO-to-Paid Bridge for restructuring, Auto-Optimize for budget allocation).
   - **Still proceed to Phase 2 and 3** — brand voice audit and fresh creative generation are valuable regardless of volume. Frame recommendations as "prepare this copy for when the restructured campaigns launch" rather than "replace fatigued ads."
   - **Set the fatigue monitoring threshold.** Tell the user: "Once you're spending $X/day per campaign, run this pipeline monthly. At current volume, the creative isn't the bottleneck — the structure and budget are."

## Phase 2: Brand Voice Audit

Before writing new copy, understand what the current brand voice is and where existing ads deviate from it.

1. **Run a brand review** using the marketing plugin's `/brand-review` skill:
   - Feed in the current ad headlines and descriptions from Phase 1
   - The brand review will flag deviations from brand voice, inconsistent messaging, outdated claims, and missing proof points
   - If the user has a brand style guide or messaging pillars, incorporate those

2. **Extract the brand voice profile** from the review:
   - Tone: (e.g., authoritative but approachable, technical but accessible)
   - Key messaging pillars: (e.g., speed, accuracy, ease of use)
   - Proof points to always include: (e.g., "3 weeks not 3 months", "built by ex-Tesla team")
   - Language to avoid: (e.g., jargon, competitor names in ad copy, unsubstantiated superlatives)
   - Current promotions or offers to feature

3. **Identify what's working** — don't throw out the baby with the bathwater:
   - Headlines with high CTR in the analyze_creatives data should be preserved or adapted
   - Descriptions that drive conversions should stay in rotation
   - Only replace assets that are underperforming or that the brand review flagged as off-voice

## Phase 3: Generate Fresh Creative

Write new headlines and descriptions that are on-brand, performance-informed, and differentiated from the stale copy.

1. **Use the marketing plugin's `/content-creation` or `/draft-content` skill** to generate new ad copy:
   - Provide context: the brand voice profile, the competitive landscape, the campaign's target keywords, and the landing page
   - Request multiple variants — aim for 15 headlines and 4 descriptions per RSA
   - Specify that this is Google Ads RSA copy (character limits: 30 chars per headline, 90 chars per description)

2. **Apply performance learnings:**
   - If the top-performing headline theme was "speed," generate more speed-oriented variants
   - If descriptions mentioning a specific proof point converted well, include that proof point in new descriptions
   - Avoid repeating the exact same messaging angle across all headlines — Google's RSA system needs variety to test combinations

3. **Structure the new RSAs:**
   - **Pin Headline 1** to the strongest differentiator or CTA (this always shows)
   - **Headlines 2-5:** Benefit-driven, each highlighting a different value prop
   - **Headlines 6-10:** Social proof, urgency, or promotional angles
   - **Headlines 11-15:** Question-based or curiosity-driven variants for testing
   - **Description 1:** Primary value proposition + CTA
   - **Description 2:** Proof point or case study stat + CTA
   - **Description 3:** Promotional offer or urgency driver
   - **Description 4:** Alternative angle or audience-specific message

4. **Run the brand review on the new copy** before deploying:
   - Feed the generated headlines and descriptions back through `/brand-review`
   - Fix any deviations flagged
   - This prevents the classic mistake of writing high-performing but off-brand copy

## Phase 4: Creative Refresh Specification

Document the complete refresh plan for handoff to the execution pipeline.

1. **New RSA ads specification** for each ad group that needs a refresh:
   - Final URL: Use the same URL as the existing ad unless the landing page is also being refreshed
   - Headlines: 15 headlines total, with H1 (pinned) being the strongest differentiator
   - Descriptions: 4 descriptions with CTAs, proof points, and promotional angles
   - Include all headlines and descriptions to give Google maximum rotation flexibility

2. **Ads to pause:**
   - Only critical/high fatigue ads should be paused
   - Preserve history by pausing rather than deleting
   - Leave moderate fatigue ads running alongside new ones — Google's rotation will naturally shift impressions

3. **Deployment sequencing:**
   - Create new ads first (so ad groups are never empty)
   - Then pause old ads
   - For full refresh campaigns, pause all old ads once new ones are live

4. **Refresh specification document:**
   - Side-by-side comparison: old headlines/descriptions vs. new ones
   - Rationale for each new asset (based on performance data, brand voice audit, competitive intelligence)
   - Which ads will be paused and which created
   - Expected timeline for measuring improvement

## Phase 5: Measurement & Creative Lifecycle

Set up the monitoring framework for the refreshed creative.

1. **Baseline the refresh:**
   - Record the CTR, conversion rate, and CPC of the fatigued ads at time of pause
   - These are the benchmarks the new ads need to beat within 2-3 weeks

2. **Set a check-in schedule:**
   - **Day 7:** Are the new ads accumulating impressions? Is Google rotating assets or suppressing some?
   - **Day 14:** Compare new ad CTR vs. baseline. If it's lower, investigate — maybe a headline isn't resonating
   - **Day 30:** Full performance comparison. The refresh should show measurable CTR improvement by now

3. **Ongoing fatigue monitoring:**
   - Recommend running `detect_creative_fatigue` monthly as a routine health check
   - Suggest the user set up a recurring task: "Run brand refresh pipeline every 6-8 weeks on top campaigns"
   - If the auto-optimize skill is available, suggest connecting it for continuous monitoring

4. **MMM validation (if available):**
   - After 4+ weeks, check if the refreshed campaigns show improved contribution in the MMM
   - Compare marginal ROI before vs. after the refresh
   - If contribution improved, document the refresh as a successful intervention
   - If contribution stayed flat despite CTR improvement, the bottleneck is elsewhere (landing page, offer, audience)

## Inputs

Gather from the user before starting:

1. **Google Ads customer ID** — which account to audit (required; use `list_accessible_customers` if unknown)
2. **Scope** — all campaigns, specific campaigns, or a spend threshold (optional; default to all enabled campaigns)
3. **Brand guidelines** — style guide, messaging pillars, tone of voice (optional; the brand-review skill will infer if not provided)
4. **Current promotions** — any offers to feature in new ad copy (optional)
5. **Landing pages** — any new or updated landing pages to link to (optional; default to existing final URLs)
6. **MMM model** — for prioritizing which campaigns to refresh based on contribution (optional)

## Output

Deliver to the user:

1. **Creative Fatigue Report** — which ads are fatigued, severity levels, estimated wasted spend
2. **Brand Voice Audit** — how current ads align (or don't) with brand messaging
3. **Refreshed RSA Copy** — new headlines and descriptions for each ad group, with rationale
4. **Deployment Summary** — what was created, what was paused, before/after comparison
5. **Measurement Plan** — check-in schedule, baselines, and success criteria
6. **Cross-skill recommendations** — if the issue is bigger than just creative (e.g., landing page problems, campaign structure issues, audience targeting), flag it for the appropriate skill

## Important Notes

- **Don't refresh what's working.** The goal is surgical replacement of fatigued assets, not a wholesale rewrite. If a headline has strong CTR, keep it in the new RSA even if it's "old." Fatigue is about audience exhaustion, not age alone.
- **Respect Google's learning period.** After deploying new RSAs, Google needs 1-2 weeks to test asset combinations. Don't make further changes during this period — let the algorithm do its job.
- **Character limits are hard constraints.** Headlines must be ≤30 characters, descriptions ≤90 characters. Check every piece of copy before deployment. A single character-limit violation will reject the entire ad.
- **Creative is only one lever.** If CTR is declining but the landing page hasn't been updated in months, fresh ad copy will only partially solve the problem. Flag landing page issues explicitly — they're outside this skill's scope but critical to call out.
