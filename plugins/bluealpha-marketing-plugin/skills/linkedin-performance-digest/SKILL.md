---
name: linkedin-performance-digest
description: "Generate a weekly or monthly LinkedIn Ads performance read in the BlueAlpha narrative format — what happened (period-over-period), what drove it (campaign + creative attribution), what to watch (early signals for next period). Leadership-ready prose, not a metric dump. Use when the user says 'LinkedIn weekly report', 'LinkedIn monthly digest', 'how did LinkedIn perform this week', 'LinkedIn performance summary', 'LinkedIn scorecard', 'what's the LinkedIn report saying', or wants the team-shareable view of LinkedIn ad performance. Pair with the schedule tool to run automatically every Monday morning."
---

# LinkedIn Performance Digest

You produce a narrative-style read of LinkedIn ad account performance over the last week or month, written for marketing leadership — not for the operator. The deliverable is prose with embedded numbers, not a dashboard.

## What the skill produces

A four-section report:

1. **Headline.** One sentence answering "how did LinkedIn perform?"
2. **What happened.** Period-over-period numbers: spend, impressions, clicks, landing page clicks, leads, conversions. Compare current period vs same-length prior period.
3. **What drove it.** The top 2-3 campaigns and 2-3 creatives that drove the biggest moves (positive or negative). Specific dollars and ratios.
4. **What to watch.** Early signals for next period — pacing issues, fatigue starting to show, audience holds emerging, creative refreshes due.

Plus a single line summary at the bottom for chat/Slack paste.

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`, `get_linkedin_ad_analytics` (CAMPAIGN + CREATIVE pivots, two windows).
* Bash/Python.

## Inputs

1. **Account ID.**
2. **Period.** Weekly (default) or monthly. The skill compares the last N days to the previous N days.
3. **Audience for the report** — internal team, leadership, client. Adjusts tone slightly. Default: leadership.

## Process

### Step 1 — Pull analytics for both windows

```
# Weekly
get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<14d ago>, end=<7d ago>, fields=...)
get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<7d ago>, end=<today>, fields=...)
# Same for CREATIVE pivot

# Monthly equivalent uses 30-day windows
```

Fields to pull: `clicks, impressions, costInLocalCurrency, landingPageClicks, oneClickLeads, externalWebsiteConversions, videoViews, videoCompletions`.

### Step 2 — Aggregate account-level totals per window

Sum per-window numbers. Compute period-over-period deltas:

* Spend Δ
* Impressions Δ
* Click Δ
* LP click Δ
* Lead Δ
* Conversion Δ
* CPC, CPM, CPLPC, CPL movement

### Step 3 — Find the drivers

For each metric that moved meaningfully (>10% change):

* Identify the top 2-3 campaigns by absolute change in that metric
* For creative-level drivers, identify the top 2-3 creatives by recent spend that also showed movement
* Compute their share of the total period-over-period delta

### Step 4 — Identify early signals for next period

* Campaigns approaching 50% pacing drop (worth flagging before they fully decay)
* Creatives with first signs of CTR decay
* New audience-count holds that just appeared
* Frequency caps being hit (if exposed)
* Calendar context — holidays, end-of-quarter spend pushes

### Step 5 — Write the narrative

In prose, not bullets. Roughly:

```
# LinkedIn Performance Digest — [Account Name], [Period: Week of MM/DD]

[**Headline** — one sentence with the verb-tense matching reality. "Spend up 12%; lead volume flat; HubSpot retargeting campaign drove the increase, but cost per lead climbed 24%."]

## What happened
[Prose paragraph: spend, impressions, clicks, LP clicks, leads/conversions, with period-over-period numbers in parentheses. Cite both absolute and percentage change. Compare against the prior period — not against a yearly average.]

## What drove it
[Prose paragraph identifying the 2-3 biggest drivers — campaign or creative. Each with a sentence: what changed, by how much, in dollars and ratio. Anchor to specific names.]

## What to watch
[Prose paragraph of next-period leading indicators. Things like: campaign X is on a fatigue trajectory; audience Y is reaching its match-rate ceiling; creative Z should be refreshed by next Friday.]

---
*[One-line summary suitable for Slack: "[Account] — spend $X (Δ %), leads N (Δ %), drivers: [brief]"]*
```

## Watch for these failure modes

* **Don't lead with metrics.** Lead with the headline — "Spend up but leads flat" is more useful than "Spend was $4,200." Numbers support the headline; they aren't the headline.
* **Don't compare against a long-term average.** Compare period-over-period with the same-length prior period. A long-term average is useful as additional context, not as the primary benchmark.
* **Don't write "everything is fine" if any of CPL, CPLPC, or CPC moved by >15%.** Even when totals look flat, the per-unit movement is the story.
* **Don't list every campaign.** Three campaigns max in "What drove it." If more than three campaigns moved meaningfully, surface the top three and add "plus N other smaller movers" — don't list them all.
* **Don't manufacture drama where the period was quiet.** A quiet week is fine to report as a quiet week. "Performance was steady — spend ±3%, leads ±5%. No new audience or creative dynamics worth flagging." That's a complete report.
* **Account currency matters.** Always cite the account's currency explicitly. LinkedIn accounts can be in USD, GBP, EUR, AUD, etc.

## When to run it

Weekly (Monday morning) for ongoing accounts. Monthly for accounts where weekly cadence is too tight (low spend, few campaigns). Schedule via the Cowork schedule tool — pair with auto-optimize (run that first, then digest).
