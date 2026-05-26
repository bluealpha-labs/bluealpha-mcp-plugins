---
name: linkedin-auto-optimize
description: "Run a full LinkedIn ad account health cycle: pacing on lifetime budgets, structural issues (billing/group holds, no-creative campaigns, dormant campaigns), delivery vs budget gaps, and a prioritized action list across audiences, creatives, and structure. Combines lightweight versions of audience-health, creative-fatigue, and bid-sanity checks into a single account-level dashboard. Use when the user says 'optimize my LinkedIn account', 'LinkedIn health check', 'audit my LinkedIn ads', 'why is my LinkedIn spend low', 'why isn't my LinkedIn delivering', 'LinkedIn account review', 'is anything broken on LinkedIn', or 'weekly LinkedIn check-in'. Use as the FIRST skill in any LinkedIn troubleshooting session — it surfaces what's structurally broken before you dig into specific layers."
---

# LinkedIn Auto-Optimize (Account Health Cycle)

You produce a single-page account-health read of a LinkedIn ad account, surfacing the structural and pacing issues that block delivery, and routing to deeper-dive skills for specifics.

This skill exists because most LinkedIn delivery problems are structural — a billing hold, a campaign with no creatives, a lifetime-budget campaign that's already overspent, an audience-count-hold quietly blocking 80% of intended delivery. Marketers tend to debug from the creative layer downward (CTR, copy, audience). The right debug order is the opposite: structure → audiences → creatives. This skill enforces that order.

Auto-optimize is the **first** skill to run in any LinkedIn troubleshooting session. The deeper-dive skills assume the account is structurally healthy; if it isn't, their outputs are misleading.

## What the skill produces

A single-page health report with these sections:

1. **🚨 Blocker issues** — anything that's preventing delivery RIGHT NOW. Billing holds, no-creative campaigns, group-status holds, count holds. Sorted by daily budget at stake.
2. **🟠 Pacing issues** — lifetime-budget campaigns that are burning too fast or too slow, daily budgets sitting well under their cap (under-delivery), or above their cap (overpacing risk).
3. **🟡 Structure hygiene** — campaigns in PENDING_DELETION still appearing in reports, dormant ACTIVE campaigns (no impressions for 7+ days), campaigns with creatives in REJECTED review state.
4. **Routing list** — which deeper-dive skill to run for each finding (audience-health, creative-fatigue, demographic-deep-dive, frequency-saturation, etc.).
5. **Account health score** — 0-100 single number derived from the issue count weighted by severity. Includes a one-line headline summary.

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`, `list_linkedin_creatives`, `get_linkedin_ad_analytics` (CAMPAIGN pivot, recent window).
* Bash/Python.

## Inputs

1. **Account ID.** If unknown, list accounts first and confirm.
2. **Date window** for pacing analysis. Default: trailing 30 days for delivery, current lifetime-budget windows for pacing.

## Process

### Step 1 — Pull all relevant data

```
list_linkedin_campaigns(account_id)
list_linkedin_creatives(account_id)
get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<30d ago>, end=<today>, fields=pivotValues,impressions,clicks,landingPageClicks,costInLocalCurrency)
get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<7d ago>, end=<today>, fields=pivotValues,impressions,clicks,costInLocalCurrency)
```

### Step 2 — Classify every campaign

For each campaign, derive its current health state by combining `status`, `servingStatuses`, recent-window analytics, and creative presence:

```
- LIVE-OK: status=ACTIVE, no holds in servingStatuses, has ≥1 isServing creative, has impressions in last 7d
- LIVE-DORMANT: status=ACTIVE, no holds, has creatives, but zero impressions in last 7d
- BLOCKED-BILLING: BILLING_HOLD in any serving status
- BLOCKED-GROUP: CAMPAIGN_GROUP_STATUS_HOLD in any serving status
- BLOCKED-AUDIENCE: AUDIENCE_COUNT_HOLD or CAMPAIGN_AUDIENCE_COUNT_HOLD
- BLOCKED-NO-CREATIVES: status=ACTIVE but zero serving creatives (all paused/rejected/removed)
- BLOCKED-REJECTED: status=ACTIVE but all creatives in REJECTED review status
- PAUSED: status=PAUSED (informational only — not a blocker)
- PENDING-DELETION: status=PENDING_DELETION (cleanup candidate)
```

Multiple blockers can apply; record all of them.

### Step 3 — Pacing analysis

For each LIVE campaign, compute:

* **Delivery rate** = `recent_7d_cost / (daily_budget × 7)`. Healthy = 0.85-1.15. Below 0.85 = under-pacing (delivery problem). Above 1.15 = over-pacing (budget issue, though LinkedIn rarely lets this happen).
* **For LIFETIME-pacing campaigns**: if you can see `runSchedule.start` and the campaign uses lifetime budget, compute days remaining and project end-spend. Flag campaigns that will overspend or substantially underspend their lifetime budget at current pace.

Flag under-pacing campaigns specifically — they're the silent failure mode. A campaign budgeted at $150/day but pacing $40/day is leaving 73% of intended delivery on the table.

### Step 4 — Structural hygiene

Flag:

* **Dormant ACTIVE campaigns** — `status=ACTIVE` but zero impressions in the last 7 days, with creatives that exist. Either count-hold (handled in audience-health) or some other delivery block.
* **Campaigns with no serving creatives** — `status=ACTIVE` but every creative under it is `isServing=false` or `intendedStatus=PAUSED`. Surface the campaign and tell the user to either add creatives or pause the campaign.
* **Pending-deletion campaigns still in serving lists** — `status=PENDING_DELETION` but appearing in recent analytics. Likely served briefly then was canceled. Cleanup candidate.
* **Campaigns with rejected creatives** — Look at the creative-level `review.status` field. Any creatives in REVIEW_FAILED or REJECTED block delivery.

### Step 5 — Build the prioritized action list

Rank issues by severity × dollar impact:

* **Severity 5 (Blocker)**: Billing hold, group hold, audience count hold, no-creative — daily budget × 1.0 weighting
* **Severity 4 (Under-delivery)**: Live but pacing <50% of daily budget — daily budget × delivery shortfall
* **Severity 3 (Pacing risk)**: Lifetime campaign projected to underspend by ≥20% — projected dollar loss
* **Severity 2 (Hygiene)**: Dormant ACTIVE, pending-deletion drift, rejected creatives — daily budget × 0.3
* **Severity 1 (Informational)**: Paused campaigns, campaigns with empty creative names — minor

### Step 6 — Compute account health score

```
score = max(0, 100 - sum(severity × 2 for each issue))
```

Cap at 0 floor, 100 ceiling. Round to nearest 5. Then map to a label:

* 85-100 — Healthy
* 70-84 — Minor issues
* 50-69 — Several issues, needs attention
* 30-49 — Multiple blockers
* 0-29 — Account is largely broken; immediate intervention needed

### Step 7 — Produce the report

In order:

```
# LinkedIn Auto-Optimize — [Account name]

**Health score: [N]/100 — [label]**

**Total daily budget on active campaigns:** $X
**Estimated daily budget actually delivering:** $Y ([Y/X]% utilization)
**Number of campaigns: [active], [paused], [pending deletion]**

## 🚨 Blockers (resolve first)
[list, sorted by daily budget at stake]

## 🟠 Pacing issues
[list]

## 🟡 Structure hygiene
[list]

## Routing — next skills to run
- If you have blockers in the count-hold category → run `linkedin-audience-health-check` for the full audit
- If you have creative-rejection blockers → check each rejected creative's reason in Campaign Manager
- If you have pacing issues with high spend on a campaign → run `linkedin-creative-fatigue-watchdog` next
- If overall delivery looks healthy but you want to find waste → run `linkedin-demographic-deep-dive`

## Headline
[one-line summary of the account's state]
```

## What this skill is NOT

This is not the place to do deep audience overlap detection, creative refresh recommendations, demographic drift analysis, or MMM-style ROI reconciliation. Those have dedicated skills. Auto-optimize is the pre-flight checklist that tells you whether the deeper analyses are worth running.

If everything is structurally fine — score ≥ 85 — surface that explicitly. "No structural issues — proceed to demographic deep dive and creative refresh review for performance optimization."

## When to run it

* As the **first** check when someone says "is something wrong with my LinkedIn ads?"
* Weekly, automated via the Cowork schedule tool — perfect Monday-morning health check.
* After making structural changes (adding campaigns, changing audiences, refreshing creatives) — confirm nothing was broken inadvertently.
