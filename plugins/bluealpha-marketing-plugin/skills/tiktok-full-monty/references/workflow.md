# TikTok Full Monty — Orchestrator Workflow

The complete BlueAlpha TikTok account workup. Runs the constituent TikTok skills in dependency order, composes the outputs into a single leadership-ready report, and produces a prioritized action plan.

Equivalent to the Google Ads `full-monty` skill. Designed for: new-client onboarding, quarterly account reviews, pre-renewal health checks, or any moment that calls for the whole picture.

This skill is heavy. Expect 15-25 tool calls and a multi-page output. Use the lighter, single-purpose TikTok skills for routine weekly work.

## Sequence (Dependency Order)

```
1. tiktok-performance-digest          (the headline numbers)
2. tiktok-auto-optimize               (structural & pacing audit)
3. tiktok-creative-fatigue-watchdog   (creative health)
4. tiktok-audience-intelligence       (who's converting)
5. tiktok-geo-expansion               (where to grow)
6. tiktok-creative-refresh            (only if fatigue is High/Critical)
7. tiktok-incrementality-test         (design the test — do not execute)
8. (optional) tiktok-content-to-campaign  (if user has a launch upcoming)
```

Each step feeds the next. The orchestrator's job is to compose, deduplicate, and prioritize — not to re-do work.

## Phase 1: Setup & Period Selection

1. **Resolve advertiser:**
   ```
   tiktok_ads_list_tiktok_advertisers()
   ```
   Confirm with the user.

2. **Set the period:**
   - Default for full-monty: trailing 30 days vs. prior 30 days
   - For quarterly review: trailing 90 days vs. prior 90 days
   - For new-client onboarding: trailing 90 days, no comparison

3. **Check for MMM availability:**
   ```
   meridian_list_models()
   ```
   If a TikTok-inclusive model exists, capture model_id for cross-checks throughout.

4. **Set the executive summary scaffold:**
   - Account name, period, total spend, total conversions, total CPA, key directional movement
   - This sits at the top of the final report — fill in as data lands

## Phase 2: Run the Performance Digest

Invoke `tiktok-performance-digest` first. This produces the headline numbers and the period-over-period story.

Capture from its output:
- Top-line metrics + deltas (spend, conversions, CPA, CTR, CPM, conversion rate)
- Top 3 spend drivers, top 3 efficiency winners/losers
- Creative pulse flag (aging creative warning)
- MMM cross-check (if available)

**Decision branch:** if the digest surfaces a campaign-level CPA blowout (>50% worse), flag it as a deep-dive target — auto-optimize and audience-intelligence will go further here.

## Phase 3: Run the Account Audit

Invoke `tiktok-auto-optimize`. This produces the structural and pacing read.

Capture:
- Structural scorecard per campaign
- Underspend diagnosis with $ left on the table
- Budget reallocation recommendations (campaigns to scale / hold / optimize / cut)
- Settings audit flags (Smart+ enablement decisions, auto-expansion features)
- Risk-tiered action plan

**Decision branch:** if total underspend exceeds 20% of the daily budget, surface that in the executive summary — it's a headline issue.

## Phase 4: Creative Health

Invoke `tiktok-creative-fatigue-watchdog`. Lighter weight than full creative-refresh.

Capture:
- Severity tier counts (Critical / High / Moderate / Healthy / Insufficient)
- Top 10 refresh queue with estimated wasted spend
- Healthy creative profile
- Total wasted weekly spend from Critical+High tier ads

**Decision branch:** if Critical+High tier represents >25% of weekly spend, automatically trigger Phase 8 (creative-refresh) to produce the brief. Otherwise note the recommendation without running the heavier refresh skill.

## Phase 5: Audience Intelligence

Invoke `tiktok-audience-intelligence`. Slice by demos, geos, placements, and adgroup configurations.

Capture:
- Tier map (Gold / Silver / Bronze / Cut)
- Estimated wasted spend on Cut-tier segments
- Interest expansion shortlist
- Cross-dimension intersection insights (e.g., "Female 25-34 in US on TikTok placement" patterns)
- MMM validation of audience reads

## Phase 6: Geo Expansion

Invoke `tiktok-geo-expansion`. Map current markets and surface expansion candidates.

Capture:
- Geo tier map (Star / Opportunity / Volume / Drain)
- Coverage gaps
- Top 5 expansion candidates with campaign specs
- Drain market cleanup list

**Decision branch:** if there are >2 Drain markets bleeding >$1K/week each, surface as urgent in the executive summary.

## Phase 7: Creative Refresh (Conditional)

Only run `tiktok-creative-refresh` if Phase 4 flagged High or Critical fatigue.

Capture:
- 5-concept refresh brief
- Pause/launch plan
- Compliance notes
- Measurement plan

If fatigue is Moderate or lower, skip — note the recommendation in the report instead of generating a full brief that isn't needed yet.

## Phase 8: Incrementality Test Design (Conditional)

Run `tiktok-incrementality-test` *design* (not execution) when at least one of these is true:
- The MMM and platform-reported numbers disagree by >20%
- TikTok represents >15% of total paid spend and has never been incrementality-tested
- Phase 5 surfaced a Gold-tier segment the user wants to scale aggressively (validate first)
- Phase 6 recommended a major new market expansion (validate first)

Capture:
- Recommended test hypothesis
- Design (matched pairs / regional holdout / budget suppression)
- Test region IDs
- Duration and required power
- Success criteria

If none of the triggers apply, document why no test is being designed this cycle.

## Phase 9: Content-to-Campaign (Optional)

Only if the user has a launch, content piece, or new campaign in mind. Ask explicitly:
> "Do you have a content piece, product launch, or campaign you want me to spec next?"

If yes, run `tiktok-content-to-campaign` and append the brief to the report.

If no, skip.

## Phase 10: Compose the Master Report

Stitch everything into a single, leadership-ready document.

```
TIKTOK ACCOUNT REVIEW — FULL MONTY
Client: <name>     Period: <date range>     Advertiser ID: <id>

EXECUTIVE SUMMARY (1 page)
- Headline: <one sentence on the period>
- Spend: $X (Δ%)
- Conversions: X (Δ%)
- CPA: $X (Δ%)
- Top 3 wins this period: [...]
- Top 3 issues: [...]
- Total addressable improvement: $X/week (from underspend + Cut audiences + Drain markets + fatigued creative)
- Recommended top 5 actions, ranked by impact

SECTION 1 — WHAT HAPPENED
[Performance Digest output, summarized to 1 page]

SECTION 2 — ACCOUNT HEALTH
[Auto-Optimize scorecard + underspend + budget reallocation, 1-2 pages]

SECTION 3 — CREATIVE
[Fatigue Watchdog summary + (if triggered) Refresh brief, 1-2 pages]

SECTION 4 — AUDIENCE
[Audience Intelligence tier map + interest expansion shortlist, 1-2 pages]

SECTION 5 — GEOGRAPHY
[Geo tier map + expansion candidates + Drain cleanup, 1 page]

SECTION 6 — MEASUREMENT
[Incrementality test design (if triggered) + MMM cross-checks throughout, 1 page]

SECTION 7 — LAUNCH PIPELINE (optional)
[Content-to-Campaign brief if user provided content]

APPENDIX
- Per-campaign performance table
- Per-adgroup performance table
- Full action plan with risk tiers (auto-approve / recommend / needs discussion)
- Quantified impact estimates per action
```

## Phase 11: Action Plan Synthesis

The final and most important step. Reconcile recommendations across all skills into a single, deduplicated, prioritized action list.

1. **Dedup:**
   - If both auto-optimize and creative-refresh recommend pausing the same ad, surface once
   - If both audience-intelligence and geo-expansion recommend the same negative-targeting cleanup, surface once

2. **Prioritize by expected impact:**
   - Quantify each action's $-impact (saved waste, projected scaled revenue, projected CPA improvement)
   - Sort actions by impact descending

3. **Risk-tier:**
   - **Auto-approve:** Pause clear failures, fix structural issues, exclude Cut segments, exclude Drain geos
   - **Recommend:** Budget reallocations <20%, new interest tests <$100/day, audience bid weight shifts
   - **Needs discussion:** Major campaign restructures, Smart+ enable/disable, large budget shifts, incrementality test launches, geo expansion launches, creative refreshes

4. **Present the action plan as the final page of the report**, with checkbox-style formatting so the user can mark what they want to execute.

## Phase 12: Next Cycle Recommendation

Suggest how to keep this momentum:

- **Weekly:** `tiktok-performance-digest` + `tiktok-creative-fatigue-watchdog`
- **Bi-weekly:** `tiktok-auto-optimize`
- **Monthly:** `tiktok-audience-intelligence` + `tiktok-geo-expansion`
- **Quarterly:** This full monty
- **As-needed:** `tiktok-content-to-campaign` (per launch), `tiktok-incrementality-test` (per test design / read)

Suggest using the `schedule` skill to automate the recurring digest and watchdog.

## Inputs

Gather from the user before starting:

1. **Advertiser ID** — required
2. **Period** — default last 30 days vs. prior 30; configurable to 90/90 for quarterly
3. **MMM model** — for incrementality cross-checks throughout (optional but strongly recommended)
4. **Risk tolerance** — conservative / moderate / aggressive (default: moderate)
5. **Launch pipeline** — any upcoming content or product launches (triggers Phase 9)
6. **Brand / vertical constraints** — affects compliance flags and creative briefs

## Output

A multi-page report with:

1. **Executive Summary** — single page, addressable improvement quantified
2. **What Happened** — period digest
3. **Account Health** — structural audit + underspend + budget reallocation
4. **Creative** — fatigue + (conditional) refresh brief
5. **Audience** — tier map + interest expansion shortlist
6. **Geography** — geo tier map + expansion candidates + drain cleanup
7. **Measurement** — incrementality test design (if triggered) + MMM cross-checks
8. **Launch Pipeline** — optional content-to-campaign brief
9. **Action Plan** — deduplicated, prioritized, risk-tiered
10. **Next Cycle Recommendation**

## Important Notes

- **This skill is expensive.** Expect 15-25+ tool calls and 5-10 minutes of run time. Use it for the moments that warrant it (onboarding, QBR, pre-renewal), not weekly work.
- **The MMM cross-check is the BlueAlpha differentiator.** A full-monty without MMM context is just a structured platform read — useful, but not differentiated. Always ask for MMM availability upfront and route through the model where possible.
- **Don't drown leadership in detail.** The Executive Summary is the only page most C-suite readers will absorb. Get the headline, the three issues, the $-addressable-improvement, and the top 5 actions right. The rest is appendix for operators.
- **Action plan is the deliverable.** A 20-page report without an action plan is a vanity exercise. The single most important page is the prioritized action list with quantified impact and risk tiers.
- **Don't auto-execute anything.** This skill recommends. Execution routes through the BlueAlpha pipeline with explicit user approval per action.
- **Coordinate the recurring cadence.** If this skill runs quarterly, the weekly/bi-weekly skills should already be running between cycles. The full monty's job is to step back and see what the routine cadence misses — not to replace it.
- **Cross-skill handoffs:** Each section's deeper questions hand back to the constituent skill. Don't try to re-do an audience analysis here when `tiktok-audience-intelligence` is the right tool.
