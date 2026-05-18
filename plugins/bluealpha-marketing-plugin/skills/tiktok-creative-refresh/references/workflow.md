# TikTok Creative Refresh — Detailed Workflow

The full creative refresh pipeline for TikTok: detect fatigue, learn from winners, produce a production-ready brief for net-new creative, and define the launch + measurement plan. Equivalent to the Google Ads `brand-refresh-pipeline` skill, but TikTok-flavored — TikTok is a creative-first platform where the ad *is* the targeting.

This skill is analysis and brief generation. It does not produce video. The deliverable is a brief a creative team or production partner can execute against.

## Phase 1: Creative Health Scan

1. **Resolve advertiser & pull active ads:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   tiktok_ads_get_tiktok_ads(
     advertiser_id=<id>,
     primary_status="STATUS_DELIVERY_OK",
     page_size=1000
   )
   ```
   Capture: `ad_id`, `ad_name`, `adgroup_id`, `campaign_id`, `create_time`.

2. **Pull creative performance (last 30 days), top 100 by spend, with names:**
   ```
   tiktok_ads_get_tiktok_creative_insights(
     advertiser_id=<id>,
     start_date=<30_days_ago>,
     end_date=<today>,
     metrics=["spend", "impressions", "clicks", "ctr", "cpm",
              "video_play_actions", "video_views_p25", "video_views_p50",
              "video_views_p75", "video_views_p100",
              "conversion", "cost_per_conversion", "conversion_rate"],
     order_field="spend",
     order_type="DESC",
     include_names=True,
     page_size=100
   )
   ```
   `order_field="spend"` returns top spenders in a single call. `include_names=True` attaches `ad_name`, `adgroup_name`, `campaign_name` inline — ad-name encoding (e.g., `"Klover_CompleteTutorial_Hook-3_UGC_15s"`) is the primary signal for identifying creative attributes downstream.

3. **If `tiktok-creative-fatigue-watchdog` has been run recently**, use its output directly to skip duplicate work. Otherwise compute fatigue signals in-line (same logic — hook rate, hold rate, completion, CTR decay vs. prior 30 days).

4. **Build the active creative inventory** with: severity tier, age, spend, hook/hold/completion rates, CTR, CPA, status.

## Phase 2: Winning Creative Audit

The most important step. Before generating new creative, deeply understand what's working.

1. **Identify the winning cohort:**
   - Top 20% of active ads by spend AND CPA in the bottom half (i.e., efficient at scale)
   - Or, for low-volume accounts: top 5 ads by conversions

2. **For each winner, extract metadata via the ads endpoint** (if creative URLs or names are available):
   - Ad name often encodes format, hook style, or test variant (e.g., "Klover_CompleteTutorial_Hook-3_UGC_15s")
   - Cross-reference with `creative_insights` for performance
   - Note: the TikTok MCP doesn't expose raw video URLs in this version — the user (or their creative team) will need to pull videos from the TikTok Ads Manager UI for visual review

3. **Identify the attribute pattern in winners:**
   - **Hook style** — what's happening in the first 3 seconds? (Patterns: question/curiosity, problem-statement, transformation, talking-head, product-reveal, social-proof)
   - **Format** — UGC (user-generated style), polished brand, Spark Ads (boosted organic), creator partnership
   - **Length** — 15s / 30s / 60s (TikTok currently favors 21-34s for conversion, 9-15s for upper-funnel)
   - **CTA placement** — first 5s / mid / end / multiple
   - **Voice** — VO, on-camera, silent + captions, music-only
   - **On-screen text density** — heavy / moderate / sparse
   - **Music** — trending sound, licensed track, original, none

4. **Build the "Winning Profile":**
   - 3-5 attributes that consistently appear in winners
   - 2-3 attributes that consistently appear in losers (to avoid)
   - Note where this disagrees with brand guidelines — TikTok rewards UGC-style content even for premium brands, which can conflict with brand voice expectations

## Phase 3: Brand Voice & Compliance Check

TikTok creative needs to thread the needle between performance patterns and brand requirements.

1. **If brand guidelines are provided**, audit the winning profile against them:
   - Does the high-performing hook style violate any brand voice rules?
   - Are there claim restrictions (regulated industries: credit, health, alcohol) the winners might cross?
   - Are there visual identity requirements (logo placement, color palette) that constrain format choices?

2. **For regulated verticals (credit, health, alcohol, gambling):**
   - Flag any claim made in winning creative that requires substantiation or disclaimer
   - Note: TikTok's Special Industries tag (e.g., `special_industries: ["CREDIT"]` on the campaign) imposes additional ad policy review — new creative must comply or it'll be rejected after launch

3. **Identify "safe to replicate" attributes** vs. "needs creative team decision":
   - Hook structure, length, CTA placement → usually safe to replicate
   - Specific claims, talent choices, visual treatments → require brand/legal input

## Phase 4: Generate the Refresh Brief

Produce a production-ready brief. This is the deliverable.

1. **Brief structure:**

```
TIKTOK CREATIVE REFRESH BRIEF
Client: <name>     Date: <today>
Refresh trigger: <fatigue severity / aged inventory / new launch>

WHY WE'RE REFRESHING
[2-3 sentences. Reference the fatigue data: which ads, what severity, estimated wasted spend.]

WHAT'S WORKING (preserve)
- Hook style: <e.g., "First-person problem statement: 'I was missing rent every month until...'">
- Format: <e.g., "UGC-style, single creator, vertical 9:16">
- Length: <e.g., "21-28 seconds">
- CTA: <e.g., "Spoken CTA at 18-22 second mark + on-screen text in last 3 seconds">
- Voice: <e.g., "On-camera talking head with overlay captions">

WHAT'S NOT WORKING (avoid)
- <Specific anti-patterns observed in fatigued or bottom-tier creative>

CONCEPTS TO PRODUCE — 5 variants

Concept 1: <Name>
- Hook (0-3s): <specific opening line / visual>
- Body (3-20s): <story arc>
- CTA (20-28s): <call to action>
- Format: <UGC / polished / Spark>
- Length: <Xs>
- Music/audio direction: <trending / licensed / VO only>
- On-screen text: <key copy beats>
- Brand requirements: <logo placement, disclaimers if regulated>

[Repeat for Concepts 2-5, varying ONE attribute per concept to enable learning]

WHY 5 VARIANTS
TikTok's algorithm needs creative variety to optimize. Submitting 1 "perfect" ad starves
the system of comparison data. The goal is 3-5 distinct concepts so the platform can pick a winner.

TESTING PLAN
- Launch all 5 concepts in 1 adgroup with even budget split for 7 days
- Pause anything with hook rate <12% by day 4
- Scale winners (top 2 by CPA) into separate adgroups at day 10
- Pre-stage 5 more concepts for week-3 refresh

COMPLIANCE NOTES
[If regulated vertical: required disclaimers, claim restrictions, etc.]
```

2. **Always brief 5 variants, not 1.** TikTok rewards variety. 1 ad starves the optimizer.

3. **Vary one attribute per concept**, not many. This is how you learn. If you change hook + format + length + music between concepts, you won't know what drove the win.

## Phase 5: Launch & Refresh Specification

Document the operational plan.

1. **Pause list:**
   - All Critical-tier ads from the fatigue scan — paused at launch of new creative
   - All ads >45 days old in the top spend tier
   - For each: pause reason, recent spend, replacement concept ID

2. **Launch list:**
   - 5 new concepts per fatigued adgroup
   - Suggested initial budget split: equal across concepts for first 7 days
   - Recommended bid strategy: keep the existing one — don't change bidding and creative simultaneously

3. **Sequencing:**
   - **Day 0:** Launch new creative concepts (paused or live depending on user preference). Old creative continues running.
   - **Day 7:** Pause clear losers (hook rate <12%, no conversions). Old creative still running.
   - **Day 14:** Scale winners. Begin pausing legacy creative in the same adgroup.
   - **Day 21:** All legacy fatigued creative paused. New creative is the new baseline.

4. **Why staggered, not all-at-once:** TikTok's adgroup-level learning gets reset when you swap creative wholesale. Layering reduces the disruption.

## Phase 6: Measurement & Learnings Loop

1. **Baseline the refresh:**
   - Pre-refresh weekly CPA, CTR, hook rate at the campaign level
   - Pre-refresh creative concentration (% spend on top 3 ads)

2. **Check-ins:**
   - **Day 7:** Initial signals on each new concept. Hook rate is the leading indicator. Don't kill on day-2 data — give 7 days.
   - **Day 14:** Compare new creative cohort vs. old. Has campaign CPA moved? Has hook rate stabilized at a higher level?
   - **Day 30:** Full performance read. Did the refresh drop CPA, hold scale, both, neither?

3. **Document the winners** for the next cycle:
   - Which concept won, by which metric
   - What attribute change drove the win (this is where the learning compounds — over 6 months you build a creative principles doc specific to the client)

4. **If MMM is available, validate that the refresh produced incremental contribution:**
   ```
   meridian_get_raw_weekly_contributions(model_id, channel="tiktok")
   ```
   - Did the MMM contribution from TikTok improve after the refresh? Or did platform-reported CPA improve while MMM contribution stayed flat?
   - Mismatch = the refresh helped efficiency on the surface but didn't unlock more revenue. This is a critical leadership read.

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Scope** — full account / specific campaigns (default: campaigns with fatigue severity High or Critical)
3. **Brand guidelines** — voice, claim restrictions, visual identity (optional but recommended)
4. **Vertical** — regulated industries trigger additional compliance flags
5. **Production capacity** — how many concepts can the creative team produce in the next 2 weeks (default: 5; adjust the brief accordingly)
6. **Previous refresh briefs** — for tracking what's been tried (optional)

## Output

Deliver to the user:

1. **Fatigue Read** — what's failing and why
2. **Winning Profile** — attributes shared by current top performers
3. **5-Concept Brief** — production-ready, with variation logic explained
4. **Pause/Launch Plan** — sequencing across 21 days
5. **Compliance Notes** — vertical-specific requirements
6. **Measurement Plan** — what to check at days 7/14/30
7. **MMM Validation Plan** — what success looks like in the model

## Important Notes

- **TikTok creative dies in 14-21 days at scale.** Treat the refresh cycle as continuous, not episodic. The healthiest accounts have a creative refresh pipeline shipping 5-10 new variants every 2 weeks.
- **Don't refresh winners.** The instinct is to "improve" a winning ad. Don't — let it run until it actually decays. Refresh resources go to replacing the dying creative.
- **Always brief 5, never 1.** A single new ad gives TikTok nothing to learn from. The optimizer expects choice.
- **Vary one attribute per variant.** This is how the next cycle's brief becomes more targeted. Random variation gives you 5 random ads; structured variation gives you a learning system.
- **Brand voice often loses to TikTok-native patterns.** Premium brands that resist UGC-style creative consistently underperform on TikTok. If the winning profile says "talking-head UGC with handheld camera," that's the right brief — even if the brand book says "polished cinematography." Flag this tension to the user; let them decide.
- **iOS app campaigns:** Platform-reported CPA is unreliable. Don't kill iOS-targeted creative based on platform CPA alone — use the MMM or run an incrementality test (`tiktok-incrementality-test`).
- **Cross-skill handoffs:** Fatigue detection upstream → `tiktok-creative-fatigue-watchdog`. New content/launch to promote → `tiktok-content-to-campaign`. Validate that the refresh actually drove incremental revenue → `tiktok-incrementality-test` or `mmm-attribution-reconciler`.
