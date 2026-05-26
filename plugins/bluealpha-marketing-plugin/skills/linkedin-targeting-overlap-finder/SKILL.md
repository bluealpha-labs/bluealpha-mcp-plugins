---
name: linkedin-targeting-overlap-finder
description: "Find LinkedIn campaign pairs that are bidding against each other in the auction because their targeting overlaps. Computes per-facet Jaccard similarity (seniorities, job functions, industries, titles, sizes, locations, matched audiences) and a weighted overall overlap score. Flags pairs > 60% overlap with daily-budget estimate of the auction overlap dollar value, then recommends consolidation, exclusion, or deliberate differentiation. Use whenever the user says 'audience overlap', 'targeting overlap', 'are my campaigns competing with each other', 'why is my CPC going up', 'auction overlap', 'consolidate my LinkedIn campaigns', or 'should these two campaigns be merged'. Use AFTER audience-health-check (which catches shared-URN overlap) to find the deeper attribute-level overlap."
---

# LinkedIn Targeting Overlap Finder

You identify pairs of LinkedIn campaigns whose targeting criteria overlap enough that they compete in the auction for the same impressions — even when they use entirely different matched audiences.

This is the deeper-cousin skill to audience-health-check. Audience-health detects when two campaigns share the *same* matched-audience URN. This skill detects when two campaigns target the *same people* through different targeting paths — e.g., Campaign A targets "VP Marketing in Tech, US, with matched-audience X" and Campaign B targets "VP Marketing in Tech, US, with matched-audience Y." If X and Y overlap (which is common for HubSpot lists vs lookalikes), the campaigns are bidding against each other, driving up CPM for both.

## What the skill produces

A ranked list of overlapping campaign pairs with:

1. **Per-facet Jaccard similarity** — seniority overlap, function overlap, industry overlap, title overlap, location overlap, company-size overlap, matched-audience overlap, dynamic-segment overlap.
2. **Weighted overall overlap score** — a single 0-100 number reflecting how much the two campaigns target the same population.
3. **Estimated auction-overlap dollars** — the daily budget at stake in the overlap (= `min(daily_budget_A, daily_budget_B) × overlap_score`).
4. **Recommendation per pair** — consolidate, exclude, differentiate, or accept (low overlap, no action).

Plus a summary section with:
* Top 5 overlapping pairs by auction-overlap dollars
* Account-wide overlap density (how many active campaigns are entangled)

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`.
* Bash/Python.

## Inputs

1. **Account ID.**
2. **Optional: overlap threshold.** Default: 0.6 Jaccard overall score. Pairs below this aren't flagged.

## Process

### Step 1 — Pull active campaigns

```
list_linkedin_campaigns(account_id)
```

Filter to ACTIVE campaigns only. PAUSED campaigns don't compete in the auction.

### Step 2 — Extract targeting facets per campaign

For each campaign, parse `targetingCriteria.include.and[].or` and build a dict keyed by facet name. The seven facets to compare:

* `seniorities` (e.g., `urn:li:seniority:5,6,7,8`)
* `jobFunctions` (`urn:li:function:15`)
* `industries` (`urn:li:industry:6,11,1673,...`)
* `titles` (`urn:li:title:N`)
* `locations` (`urn:li:geo:N`)
* `staffCountRanges` (`urn:li:staffCountRange:(51,200)`)
* `audienceMatchingSegments` (`urn:li:adSegment:N`)
* `dynamicSegments` (`urn:li:adSegment:N`)

Empty facets (campaign doesn't restrict on this attribute) mean "all values match." Two empty facets should NOT count as 100% overlap — they should count as a "neutral" facet (skipped in the average). Otherwise every pair of broad-targeting campaigns scores 1.0 trivially.

### Step 3 — Compute per-facet Jaccard similarity

For each facet present in BOTH campaigns:

```
jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

If a facet is empty in both campaigns, mark as `neutral` (skip in average). If only one has it set, mark as `0` (one campaign restricts, the other doesn't — they're targeting different populations).

### Step 4 — Compute weighted overall overlap

Weights reflect how predictive each facet is of actual auction overlap:

| Facet | Weight | Why |
|---|---:|---|
| seniorities | 1.0 | High-value LinkedIn signal, frequently used |
| jobFunctions | 1.0 | Same |
| industries | 0.8 | Often used but coarser |
| titles | 1.5 | Specific titles are strong overlap signal |
| staffCountRanges | 0.8 | Important but often broad |
| locations | 0.5 | Usually overlapping (same country) — less differentiating |
| audienceMatchingSegments | 1.5 | Shared matched audience is direct overlap |
| dynamicSegments | 1.0 | Same |

Overall score = weighted average of per-facet Jaccards, ignoring `neutral` facets. Express as 0-100.

### Step 5 — Compute auction-overlap dollars

```
overlap_dollars = min(daily_budget_A, daily_budget_B) × (overall_score / 100)
```

This represents the daily budget that's at risk in the shared auction. If two campaigns at $50/day each have 80% overlap, ~$40/day on each side is effectively bidding against the other.

### Step 6 — Generate recommendation per pair

Based on overall_score:

* **80-100% overlap → Consolidate.** These are functionally the same campaign with different creatives. Combine into one with rotating creative.
* **60-80% overlap → Exclude or differentiate.** Differentiate via either exclusion (each campaign excludes the other's matched audiences) or facet differentiation (one targets enterprise sizes, the other mid-market; one targets EMEA, the other US).
* **40-60% overlap → Light touch.** Worth knowing about but usually fine to leave. Re-check if CPMs are rising.
* **< 40% → No action.** Different campaigns.

### Step 7 — Build the report

```
# LinkedIn Targeting Overlap Finder

**N active campaigns analyzed. M overlapping pairs detected (above 60% threshold).**

**Total auction-overlap dollars (estimate): $X/day.**

## Top overlapping pairs (sorted by overlap dollars)

### [Campaign A] ↔ [Campaign B]
- **Overall overlap: N%** | Daily budgets: $X / $Y | Auction-overlap dollars: $Z/day
- Per-facet Jaccard:
  - Seniorities: N% (both target [labels])
  - Job functions: N% (both target [labels])
  - Industries: N%
  - Matched audiences: N%
  - ...
- **Recommendation:** [Consolidate / Differentiate / etc.]
- **Specific action:** [Concrete next step]

[Repeat for each significant pair]

## Account-wide overlap density

- N% of active-campaign pairs overlap by ≥60%
- Estimated auction-overlap dollars across the account: $X/day = ~$Y/month
- Most-overlapping campaign: [name] — appears in N high-overlap pairs

## Summary
[one-line headline]
```

## Watch for these failure modes

* **Don't penalize broad targeting unfairly.** A campaign with empty job-function targeting and another with empty job-function targeting BOTH target everyone — they overlap on that facet, but it's not "100% overlap on functions." Use the `neutral` skip logic.
* **Don't flag overlap as a problem when objectives differ.** A Brand Awareness campaign and a Lead Gen campaign at the same target are *complementary*, not overlapping. They serve different funnel stages and won't usually bid in the same auction. Include `objectiveType` in the report and skip pair-level flagging when objectives differ — but still surface the audience-share for awareness.
* **Don't recommend consolidation across campaign groups.** Different campaign groups often exist for budget reporting reasons. Consolidating across groups breaks reporting. Flag the overlap, but recommend exclusion rather than merge.
* **Match-segment overlap is a feature of HubSpot/audience-sync pipelines.** If two campaigns both use a customer-uploaded list AND a lookalike of that list, the actual member overlap is by design. Flag, but recommend exclude-the-customer-list-from-the-lookalike-campaign, not merge.

## Handoff

* **`linkedin-audience-health-check`** detects shared-URN overlap. This skill picks up where that one stops.
* **`linkedin-auto-optimize`** uses this skill's findings as part of the account-level health score (when implemented as orchestrator).
