---
name: linkedin-full-monty
description: "Run the complete BlueAlpha LinkedIn Ads audit suite — auto-optimize (structure), audience-health (count holds + overlap risk), targeting-overlap (auction competition), creative-fatigue (per-creative decay), demographic-deep-dive (segment-level waste), bid-strategy-audit, frequency-saturation, lead-form-quality, and performance-digest — and compose the findings into one comprehensive 'state of the account' report. Use when the user says 'full LinkedIn audit', 'LinkedIn full monty', 'complete LinkedIn account review', 'comprehensive LinkedIn audit', 'run everything on LinkedIn', or wants the full BlueAlpha LinkedIn workup on an account. This is the orchestrator — pair with the schedule tool to run quarterly."
---

# LinkedIn Full Monty (Complete Account Audit)

You run the entire BlueAlpha LinkedIn audit suite on an account and compose the findings into a single unified report. This is the comprehensive view used for client deliverables, quarterly business reviews, or first-pass diagnostics on a new account.

## What this skill produces

A single composed report with sections:

1. **Executive headline** — one-line summary of account state, derived from all sub-skill outputs.
2. **🚨 Priority actions (top 5)** — cross-skill action prioritization. The 5 highest-leverage moves across structure, audience, creative, bid, and targeting layers.
3. **Structure & health** — output from `linkedin-auto-optimize`.
4. **Audiences** — composed output from `linkedin-audience-health-check` + `linkedin-targeting-overlap-finder` + `linkedin-frequency-saturation-report`.
5. **Creatives** — composed output from `linkedin-creative-fatigue-watchdog` + `linkedin-lead-form-quality-auditor`.
6. **Targeting & segments** — composed output from `linkedin-demographic-deep-dive`.
7. **Bid & configuration** — output from `linkedin-bid-strategy-audit`.
8. **Performance digest** — output from `linkedin-performance-digest`.
9. **Recommended cadence** — which sub-skills to schedule weekly vs quarterly going forward.

## Why this exists

Each sub-skill is useful standalone. But for a quarterly business review or onboarding audit, leadership wants ONE document — not nine. The full monty composes them into a single narrative with a unified prioritization across all the layers.

The cross-skill prioritization is the value-add. Auto-optimize reports a count-held campaign. Audience-health reports it's caused by audience X. Targeting-overlap finds audience X is also shared with another campaign. The unified report says: "Audience X is causing $350/day blocked delivery AND $60/day of auction overlap — fix it first."

## Prerequisites

* All nine sub-skills installed and functional.
* LinkedIn Ads MCP connected.
* Bash/Python.

## Inputs

1. **Account ID.**
2. **Date windows.** Default:
   - 30 days for demographic / performance / digest baseline
   - 14d + 14d for fatigue / decay comparisons
   - 7d for pacing
3. **Report audience.** Leadership (default) or operator. Adjusts level of detail.

## Process

### Step 1 — Pull all data ONCE

Auto-optimize and the sub-skills mostly use the same underlying API calls. Run them once at the start of the orchestrator and pass the data into each sub-skill:

```
campaigns = list_linkedin_campaigns(account_id)
creatives = list_linkedin_creatives(account_id)
analytics_30d_campaign = get_linkedin_ad_analytics(pivot=CAMPAIGN, 30d window)
analytics_14d_prior_campaign = get_linkedin_ad_analytics(pivot=CAMPAIGN, prior 14d)
analytics_14d_recent_campaign = get_linkedin_ad_analytics(pivot=CAMPAIGN, recent 14d)
analytics_7d_campaign = get_linkedin_ad_analytics(pivot=CAMPAIGN, 7d)
analytics_14d_prior_creative = get_linkedin_ad_analytics(pivot=CREATIVE, prior 14d)
analytics_14d_recent_creative = get_linkedin_ad_analytics(pivot=CREATIVE, recent 14d)
analytics_90d_seniority = get_linkedin_ad_analytics(pivot=MEMBER_SENIORITY, 90d)
analytics_90d_function = get_linkedin_ad_analytics(pivot=MEMBER_JOB_FUNCTION, 90d)
analytics_90d_size = get_linkedin_ad_analytics(pivot=MEMBER_COMPANY_SIZE, 90d)
analytics_90d_industry = get_linkedin_ad_analytics(pivot=MEMBER_INDUSTRY, 90d)
```

Save each to a temporary JSON file.

### Step 2 — Run each sub-skill against the shared data

Invoke the underlying Python script for each sub-skill, passing the relevant JSON files:

```
python3 ../linkedin-auto-optimize/scripts/account_health.py [args] > section_auto_optimize.md
python3 ../linkedin-audience-health-check/scripts/audit_audiences.py [args] > section_audience_health.md
python3 ../linkedin-targeting-overlap-finder/scripts/find_overlap.py [args] > section_overlap.md
python3 ../linkedin-frequency-saturation-report/scripts/audit_frequency.py [args] > section_frequency.md
python3 ../linkedin-creative-fatigue-watchdog/scripts/score_creative_fatigue.py [args] > section_fatigue.md
python3 ../linkedin-lead-form-quality-auditor/scripts/audit_lead_forms.py [args] > section_lead_forms.md
python3 ../linkedin-demographic-deep-dive/scripts/analyze_demographics.py [args] > section_demographics.md
python3 ../linkedin-bid-strategy-audit/scripts/audit_bids.py [args] > section_bids.md
python3 ../linkedin-performance-digest/scripts/build_digest.py [args] > section_digest.md
```

The wrapper script `scripts/run_full_monty.py` orchestrates this — see the script for the exact arg shape.

### Step 3 — Cross-skill prioritization

Read all section outputs. Extract the headline findings:

* From auto-optimize: count holds, structural blockers, pacing issues
* From audience-health: high-risk audiences, single-points-of-failure
* From overlap-finder: campaign pairs in auction competition
* From fatigue-watchdog: refresh-queue creatives
* From demographic-deep-dive: targeting drift dollars
* From bid-audit: mismatches and suspicious bids
* From frequency-saturation: missing caps
* From lead-form-auditor: forms with no leads

Aggregate into a single **Top 5 actions** list ranked by estimated dollar impact (using each sub-skill's dollar estimate where present). Where two findings overlap (e.g., audience-health flags audience X AND overlap-finder flags the campaigns using X), merge into one action.

### Step 4 — Compose the final report

The report is the Top 5 actions + each section's output in sequence + a recommended cadence at the end.

The Top 5 should reference the section that produced it: "Action 1: Set frequency caps on 3 matched-audience campaigns. See Frequency Saturation section."

### Step 5 — Recommended cadence

End the report with a maintenance schedule:

* **Weekly**: auto-optimize, performance-digest
* **Bi-weekly**: creative-fatigue-watchdog, audience-health-check
* **Monthly**: targeting-overlap-finder, frequency-saturation-report, bid-strategy-audit
* **Quarterly**: demographic-deep-dive, lead-form-quality-auditor, **full-monty** (this skill)

Pair with the Cowork schedule tool to automate.

## Watch for these failure modes

* **Don't just paste nine sections.** The value-add is the cross-skill prioritization at the top. Without that, the report is just a stapled stack of audits.
* **Don't duplicate findings across sections.** Each finding appears in one place (its primary section). The Top 5 references it. Other sections cite it but don't re-explain.
* **Don't manufacture priorities.** If the account has only 1 finding, the Top 5 is a Top 1. Don't pad.
* **Caveats compose.** If the account has no Insight Tag, every conversion-dependent finding is footnoted. Don't re-state the caveat in every section — surface it once, in the executive header, and reference it.
* **Currency consistency.** Every dollar figure should be in the account's currency. State the currency at the top.

## Output length

A full monty report on a typical account is 4-8 pages of Markdown. If yours is shorter than 3 pages, you've under-analyzed; if longer than 10, you're padding.
