---
name: linkedin-creative-fatigue-watchdog
description: "Detect LinkedIn ad creative fatigue and waste at the creative level. Score each active creative on engagement decay (prior 14d vs recent 14d) using metrics appropriate to its campaign objective (CTR + LP-click rate for Traffic, engagement rate for Brand/Engagement, hook + completion rate for Video, CTR for Lead Gen). Surface fatigued creatives, weak-from-launch creatives, and high-spend low-engagement waste. Output a prioritized refresh queue. Use whenever the user says 'creative fatigue', 'LinkedIn ads aren't working anymore', 'which creatives are tired', 'CTR is dropping', 'refresh my LinkedIn creative', 'audit my LinkedIn ads', or wants to know which creatives are bleeding spend on LinkedIn. Use BEFORE generating new creative briefs — fatigue scoring tells you whether refresh is needed."
---

# LinkedIn Creative Fatigue Watchdog

You score every active LinkedIn creative on whether it's fatigued, weak-from-launch, or wasting spend — and produce a prioritized refresh queue with concrete pause/refresh recommendations.

The hard part of this skill isn't pulling the data; it's **picking the right metric for each campaign objective**. LinkedIn's "clicks" mean different things depending on the campaign objective. Without that adjustment, the skill will incorrectly flag every Engagement-objective creative as broken (because they show zero landing-page clicks by design).

## Metric selection per objective (critical)

For each creative, pick the engagement metric based on the parent campaign's `objectiveType`:

| Campaign objective | Primary engagement metric | Fatigue threshold |
|---|---|---|
| `BRAND_AWARENESS` | `ctr = clicks / impressions` (LinkedIn's `clicks` on this objective includes all social action clicks — reactions, comments, profile views, etc.) | 30% decay |
| `ENGAGEMENT` | Same as Brand Awareness — `ctr` (clicks includes all engagement actions) | 30% decay |
| `WEBSITE_VISIT` | `lpc_rate = landingPageClicks / clicks` AND `ctr = clicks / impressions` | 40% decay in either |
| `WEBSITE_CONVERSION` | `cvr = externalWebsiteConversions / clicks` (if any), else `lpc_rate` | 40% decay |
| `LEAD_GENERATION` | `lead_rate = oneClickLeads / clicks` (if any), else `ctr` | 40% decay |
| `VIDEO_VIEW` | `hook_rate = videoViews / impressions` AND `completion_rate = videoCompletions / videoViews` | 30% decay |

**Important: don't use the narrow `(likes + comments + reactions + shares) / impressions` sum as the primary metric for Engagement / Brand Awareness campaigns.** That sum only captures *some* of what LinkedIn counts as social engagement on these objectives — it omits profile clicks, reaction-bar opens, expanded-text views, and other actions that DO count toward LinkedIn's `clicks` metric on Engagement campaigns. Using the sum as the primary metric produces false fatigue alerts on creatives that are engaging users in ways that aren't likes/comments specifically. CTR captures the full picture.

For video formats (single video creatives in any objective), ALSO check hook rate and completion rate as secondary signals — those are LinkedIn's most reliable video fatigue indicators.

**Never compare creative performance across campaign objectives.** A 2% CTR Engagement creative and a 2% CTR Traffic creative are not the same thing. Always benchmark within the campaign's objective.

## What the skill produces

1. **🔴 Fatigued creatives** — primary metric decayed beyond the threshold over the trailing 14 days vs prior 14 days. Sorted by `spend × decay_pct`.
2. **🟠 Weak-from-launch creatives** — creatives that never reached campaign-median performance, with meaningful spend. Sorted by spend.
3. **🟡 High-spend low-engagement waste** — creatives whose recent engagement is ≥ 50% below campaign median, regardless of trend. Sorted by recent spend.
4. **🟢 Top performers worth doubling down on** — creatives 50%+ above campaign median engagement, sorted by recent spend.
5. **Creative naming hygiene** — count of unnamed creatives (LinkedIn uses an empty `name` field by default). Naming improves all reporting.

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_creatives`, `list_linkedin_campaigns`, `get_linkedin_ad_analytics` (CREATIVE pivot, 2 windows).
* Bash/Python for analysis.

## Inputs

1. **Account ID.**
2. **Comparison window.** Default: trailing 28 days split into two 14-day halves. Allow override.
3. **Scope.** Default: creatives in ACTIVE campaigns only (where `isServing=true` or `intendedStatus=ACTIVE`).

## Process

### Step 1 — Pull creatives, campaigns, and two windows of analytics

```
list_linkedin_creatives(account_id)
list_linkedin_campaigns(account_id)
get_linkedin_ad_analytics(account_id, pivot=CREATIVE, start=<28d ago>, end=<14d ago>, fields=pivotValues,clicks,impressions,landingPageClicks,costInLocalCurrency,videoViews,videoCompletions,externalWebsiteConversions,oneClickLeads,likes,comments,shares,reactions,follows)
get_linkedin_ad_analytics(account_id, pivot=CREATIVE, start=<14d ago>, end=<today>, fields=pivotValues,clicks,impressions,landingPageClicks,costInLocalCurrency,videoViews,videoCompletions,externalWebsiteConversions,oneClickLeads,likes,comments,shares,reactions,follows)
```

### Step 2 — Join

* Build a map: creative URN → campaign URN → campaign objective.
* Build a map: creative URN → prior-window metrics.
* Build a map: creative URN → recent-window metrics.
* Filter to creatives where `isServing=true` OR (`intendedStatus=ACTIVE` AND campaign is ACTIVE).

### Step 3 — Compute primary metric per creative

Apply the metric-selection table above. Store both prior and recent values of the primary metric per creative.

**Min-volume guardrails.** Don't compute fatigue for creatives with < 500 impressions in either window — too noisy. Mark them as "insufficient volume."

### Step 4 — Compute campaign-median benchmarks

For each campaign, compute the median recent-window primary metric across all of its active creatives. This is the comparison anchor for "weak-from-launch" and "waste" classification.

### Step 5 — Classify each creative

For each creative with enough volume:

1. **Fatigued** — recent primary metric < (1 - threshold) × prior primary metric. Use the threshold from the objective table.
2. **Weak-from-launch** — recent primary metric < 0.6 × campaign median AND prior metric also < campaign median. Never performed.
3. **Waste** — recent primary metric < 0.5 × campaign median AND recent spend > $50. May or may not be decayed.
4. **Top performer** — recent primary metric > 1.5 × campaign median AND recent spend > $50.
5. **Normal** — none of the above.

A creative can be both "fatigued" and "waste" — it counts in both sections.

### Step 6 — Produce the report

In order:

#### A. Account summary
`X creatives in active campaigns, Y with sufficient volume to score. Total recent spend: $Z.`

#### B. 🔴 Fatigued creatives (refresh queue)
For each, in `spend × decay_pct` order:
```
- [Creative name or URN] (Campaign: [name], Objective: [type])
  - Prior 14d: X% engagement on $A spend. Recent 14d: Y% engagement on $B spend. Decay: Z%.
  - Recommendation: Pause and replace. Use [recommended new creative direction based on the campaign objective].
```

#### C. 🟠 Weak-from-launch creatives
Same shape, anchored on campaign-median comparison rather than decay.

#### D. 🟡 High-spend low-engagement waste
Same shape, sorted by recent spend.

#### E. 🟢 Top performers to double down on
Same shape, with recommendation to increase budget allocation or duplicate as a base for new variants.

#### F. Creative naming hygiene
`N of M creatives have empty names. Naming improves cross-skill reporting and helps when iterating.`

### Step 7 — Headline

Single-line summary:

> "X fatigued creative(s), Y weak-from-launch, Z waste-flagged. Estimated recoverable spend: $W/month at current pacing."

## Watch for these failure modes

* **Don't compare across campaign objectives.** Surfaced above — the most common mistake on LinkedIn creative analysis.
* **Don't flag creatives in their first 7 days.** New creatives often have a learning period; let them stabilize.
* **Don't recommend pausing the only active creative in a campaign.** That stops delivery. If a campaign has only one creative and it's flagged, recommend "add a fresh creative variant alongside" instead of "pause."
* **Don't treat 0 landing page clicks as creative failure on Engagement / Brand Awareness campaigns.** Those objectives don't optimize for site visits. The 0 is by design.
* **Video creatives need both hook AND completion rate.** A video with high hook rate but low completion rate is grabbing attention but failing to deliver — different fix than a low hook rate (failing to grab attention).

## When to run it

Weekly is the right cadence for LinkedIn. The eligible audience is small enough that fatigue can develop in 14-21 days. Pair with the Cowork schedule tool to run every Monday morning.
