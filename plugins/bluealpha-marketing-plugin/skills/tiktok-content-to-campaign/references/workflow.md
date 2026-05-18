# TikTok Content-to-Campaign — Detailed Workflow

Convert a content piece — blog post, product launch, news mention, organic video, case study — into a production-ready TikTok paid campaign spec. The output is everything a media buyer needs: objective, budget, targeting, placement, creative brief, KPIs, and measurement plan.

Equivalent to the Google Ads `content-to-campaign` skill, but adapted for TikTok's creative-first dynamics. The biggest difference: on TikTok the *ad* matters more than the targeting, so the creative brief takes more of the workload.

This skill produces a brief; it doesn't run the campaign. Execution routes through the BlueAlpha pipeline.

## Phase 1: Content Analysis

Understand the content before designing the campaign.

1. **Gather the content piece:**
   - URL, file path, or pasted text
   - For video content: get duration, format (vertical/horizontal/square), key visual beats, any music rights status
   - For written content: get the headline, top 3 takeaways, the implicit call-to-action

2. **Classify the content type:**

   | Type | TikTok fit | Typical objective |
   |---|---|---|
   | Product launch | High — TikTok loves "first look" / "reveal" formats | `APP_PROMOTION` or `WEB_CONVERSIONS` |
   | Blog / article (educational) | Medium — needs strong hook translation | `TRAFFIC` (early) → `WEB_CONVERSIONS` (proven) |
   | Case study | Medium — works as social proof if there's a face | `LEAD_GENERATION` or `WEB_CONVERSIONS` |
   | Customer testimonial / UGC | High — native TikTok format | `WEB_CONVERSIONS` or `REACH` |
   | News / PR moment | High — short window, time-sensitive | `REACH` for top-of-funnel, `WEB_CONVERSIONS` for traffic |
   | Event / webinar | Medium — needs immediate-action hook | `LEAD_GENERATION` |
   | How-to / tutorial | High — native to TikTok feed | `TRAFFIC` or `WEB_CONVERSIONS` |

3. **Identify the desired action:**
   - Purchase? Sign-up? App install? Article read? Subscribe?
   - This determines the campaign objective and the KPI

4. **Audit the source content for TikTok constraints:**
   - **Length:** If video, can it be cut to 21-34 seconds (TikTok's conversion sweet spot)?
   - **Aspect ratio:** Is the source vertical (9:16) or does it need re-edit?
   - **Music rights:** Is the source music licensed for paid ads? If not, flag for re-edit with TikTok-licensed track.
   - **Compliance:** Does the content make claims that need substantiation under TikTok ad policy? Regulated verticals (credit, health, alcohol) require extra review.
   - **Spoken language:** Is captioning needed? (TikTok users default to sound-on, but ~30% watch without — captions matter).

## Phase 2: TikTok Fit Assessment & Audience Strategy

Decide whether and how to bring this content to TikTok.

1. **Fit screen:**
   - Is the target audience on TikTok? (TikTok skews 18-34; B2B-leaning content for 45+ buyers is a hard pass)
   - Does the content's message work in 21-34 seconds with sound-on?
   - Is the action TikTok-friendly? (e.g., quick install / sign-up = good; complex B2B form fill with required demo = mediocre)

2. **If fit is weak**, recommend an alternative channel or a TikTok-native re-conception:
   - The blog post might work better re-written as a 3-tip carousel for LinkedIn
   - The case study might need a face + voice to work on TikTok — flag the production need
   - Don't force-fit content that won't perform

3. **Audience strategy:**
   - **Phase 1 (Discovery):** Broad interest targeting matching the content theme + demographic overlay (age/gender) based on the user's known winning segments
   - **Phase 2 (Validation):** Once early winners surface, narrow to lookalike audiences from converters
   - **Phase 3 (Scale):** Open up further with Smart+ once the creative + audience baseline is proven

4. **Pull the TikTok interest taxonomy** to match content themes to targetable interests:
   ```
   tiktok_ads_get_tiktok_interest_categories(
     advertiser_id=<id>,
     version=2
   )
   ```
   Map 2-4 interest categories that align with the content's topic. Don't over-stack — TikTok's optimizer prefers broader audiences.

5. **For geo targeting**, default to the client's existing winning geos. For new-market content (e.g., a launch in a new region), use `tiktok_ads_get_tiktok_targeting_regions` to get location IDs.

## Phase 3: Campaign Spec

Build the actual campaign configuration.

```
TIKTOK CONTENT-TO-CAMPAIGN SPEC
Content: <title or URL>
Date: <today>
Client: <name>

OBJECTIVE
Type: <APP_PROMOTION / WEB_CONVERSIONS / TRAFFIC / LEAD_GENERATION / REACH>
Rationale: <why this objective fits the content's action>

CAMPAIGN STRUCTURE
Campaign name: <ContentName>_<Channel>_<YYYYMM>
Budget mode: <BUDGET_MODE_DAY for testing / BUDGET_MODE_TOTAL for time-bound launches>
Daily budget: $<X> (test phase: $50-150/day; scale phase: based on performance)
Automation: <Manual / Smart+ — recommend Manual for new content tests so you can read the signal>

AD GROUP STRUCTURE
[1-3 ad groups, each with a distinct audience/placement strategy]

Ad Group 1 — Discovery
- Audience size target: 3M-10M
- Demographics: <age range>, <gender>
- Interests: [2-4 from taxonomy]
- Placement: PLACEMENT_TIKTOK only
- Bid: lowest-cost / cost-cap matching existing campaigns
- Budget: $X/day

Ad Group 2 — Lookalike (optional, if customer data available)
- Source: existing converter list
- Lookalike expansion: 1-3% similarity
- Placement: PLACEMENT_TIKTOK
- Budget: $X/day

Ad Group 3 — Retargeting (optional, if pixel volume sufficient)
- Audience: site visitors / video viewers from past 30 days
- Placement: PLACEMENT_TIKTOK
- Budget: $X/day (typically smaller — retargeting pool is small)

GEO TARGETING
[List of TikTok location IDs from get_tiktok_targeting_regions]

LANDING
Landing URL: <where this content lives>
Tracking: <UTM params, pixel events to fire>
LP fit check: Is the landing page mobile-optimized? TikTok traffic is 99% mobile.

KPIs
Primary: <CPA / install volume / lead volume>
Target: <based on existing campaign benchmarks or content-specific goal>
Secondary: <CTR, hook rate, completion rate>
Floor: <below what number we pause>

DURATION
Test phase: <7-14 days>
Decision date: <date>
Scale criteria: <if CPA <= $X and volume >= Y, scale 50%>
Cut criteria: <if CPA >= $Z by day 10 with no improving trend>
```

## Phase 4: Creative Brief

The most important section — TikTok ads are creative-first.

1. **Produce 5 distinct creative concepts**, all derived from the source content but varying ONE attribute per concept:

```
CONCEPT 1 — Hook variant A: <Curiosity / Question hook>
- 0-3s: <opening line / visual>
- 3-20s: <body>
- 20-28s: <CTA>
- Length: 21-28s
- Format: UGC-style talking head
- Music: <trending sound suggestion or licensed>
- CTA: <spoken + on-screen text>
- Source content reference: <which beat of the original content this draws from>

CONCEPT 2 — Hook variant B: <Problem-statement hook>
[Vary ONLY the hook, keep everything else the same as Concept 1]

CONCEPT 3 — Format variant: Polished brand
[Keep Concept 1's hook, change format to polished/cinematic]

CONCEPT 4 — Length variant: 9-15s short
[Keep Concept 1's hook + format, compress to 9-15 seconds]

CONCEPT 5 — Spark Ads boost
[Identify an existing organic TikTok post (the user's, a creator partner's, or a piece of UGC) that aligns with the content theme — recommend boosting via Spark Ads instead of producing new creative]
```

2. **Why 5 concepts:** TikTok's optimizer needs variety. 1 ad starves the system. 5 distinct concepts let you learn which dimension (hook / format / length / native vs. branded) matters most for this content.

3. **Compliance flags (for regulated verticals):**
   - Required disclaimers
   - Restricted claims
   - Required visual elements

## Phase 5: Measurement Plan

How to read the campaign once live.

1. **Phase reads:**

   | Day | Check | Decision |
   |---|---|---|
   | Day 3 | Delivery and learning — are all 5 concepts getting impressions? | If any concept has <500 impressions, check for review/disapproval |
   | Day 7 | Creative shake-out — which concepts have hook rate >15% and CTR >0.5%? | Pause bottom 2; reallocate budget to winners |
   | Day 10 | CPA read — is the campaign tracking to the KPI target? | If yes, scale +30%; if no, investigate |
   | Day 14 | Full evaluation | Scale / hold / cut decision |
   | Day 28 | Refresh check | If campaign is still live, check for fatigue signals — handoff to `tiktok-creative-fatigue-watchdog` |

2. **If MMM is available, validate that the new campaign isn't cannibalizing existing TikTok contribution:**
   ```
   meridian_get_raw_weekly_contributions(model_id, channel="tiktok")
   ```
   Compare TikTok contribution before vs. after launch. If platform-reported conversions grew but MMM contribution stayed flat = the new campaign is taking credit for existing TikTok conversions.

3. **For high-stakes content launches (product launches, time-sensitive moments), recommend pre-staging an incrementality test via `tiktok-incrementality-test`** — geo holdout one region during the launch to measure causal lift.

## Phase 6: Handoff

1. **Deliverable to the user:**
   - Campaign spec (Phase 3)
   - Creative brief with 5 concepts (Phase 4)
   - Measurement plan (Phase 5)
   - Compliance notes
   - Cross-skill handoffs

2. **Cross-skill handoffs:**
   - Creative production assistance → `tiktok-creative-refresh` (deeper brief generation, refresh-style)
   - Audience refinement once data lands → `tiktok-audience-intelligence`
   - Measuring true incrementality → `tiktok-incrementality-test`
   - Ongoing account integration → `tiktok-auto-optimize`

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Content piece** — URL, file, or pasted text (required)
3. **Desired action** — purchase / install / sign-up / read / subscribe (required)
4. **Budget** — total $ for the campaign / time window
5. **Duration** — launch + scale timeline
6. **Vertical** — regulated industries trigger compliance flags
7. **Brand guidelines** — voice, claim restrictions, visual identity
8. **Existing TikTok audience data** — winning interests, demos, geos (from `tiktok-audience-intelligence` if available)
9. **Production capacity** — can the creative team produce 5 variants? In what timeframe?
10. **MMM model** — for incrementality framing (optional)

## Output

1. **Content Fit Assessment** — does this belong on TikTok?
2. **Campaign Spec** — objective, structure, budget, geo, audience
3. **5-Concept Creative Brief** — production-ready
4. **Measurement Plan** — phase reads with decision criteria
5. **Compliance Notes** — vertical-specific requirements
6. **Cross-skill Handoffs**

## Important Notes

- **Not all content belongs on TikTok.** B2B for 45+ buyers, complex enterprise sales, long-form thought leadership — these usually don't translate. Flag the fit issue; recommend an alternative channel instead of force-fitting.
- **The content is the hook, not the ad.** A blog post's headline isn't the TikTok hook. The TikTok hook is whatever stops the scroll in the first 3 seconds — usually a face, a question, or a visual cliffhanger. Translate the content's *insight*, not its *form*.
- **Spark Ads beat new productions for organic-native content.** If there's an existing organic TikTok post that aligns with the content, boost it via Spark Ads. Native posts that were tested in the organic feed have higher hook rates than ads designed to look native.
- **Start with PLACEMENT_TIKTOK only.** Adding Pangle or Global App Bundle in a content launch muddies the read. Prove the core TikTok placement first, then expand.
- **Don't go Smart+ for content launches.** Smart+ campaigns hide the audience / placement / creative attribution you need to learn from a launch. Use manual for the first 14-21 days; move to Smart+ once the winning creative + audience pattern is identified.
- **Time-sensitive content needs front-loaded measurement.** For a news / PR / event launch, the entire conversion window may be 7 days. Run a daily read instead of a weekly one; have the kill / scale criteria ready before launch.
- **Cross-skill handoffs:** Creative production → `tiktok-creative-refresh`. Audience-fit refinement post-launch → `tiktok-audience-intelligence`. Incrementality validation → `tiktok-incrementality-test`. Ongoing account optimization → `tiktok-auto-optimize`.
