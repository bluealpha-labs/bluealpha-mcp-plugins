---
name: linkedin-lead-form-quality-auditor
description: "Audit LinkedIn Lead Gen Form campaigns and creatives — surface forms with declining volume, creatives that consume spend without producing leads, dormant forms in active campaigns, and CTR-to-lead conversion gaps. Outputs a manual-validation checklist for the lead-quality dimensions the LinkedIn MCP doesn't expose (form field count, completion patterns, lead-source domains). Use when the user says 'check my LinkedIn lead forms', 'lead gen quality on LinkedIn', 'why am I not getting leads from LinkedIn', 'audit my LinkedIn lead gen', or 'review my LinkedIn lead form performance'."
---

# LinkedIn Lead Form Quality Auditor

You audit LinkedIn Lead Gen Form campaigns at the creative + analytics level — what the LinkedIn MCP exposes — and produce a checklist for the lead-quality dimensions that require manual inspection in Campaign Manager.

## What this skill CAN see (via the MCP)

* Which campaigns are `objectiveType=LEAD_GENERATION`
* Which creatives have `leadgenCallToAction` (Lead Gen Form attached) and the form URN (`urn:li:adForm:N`)
* `oneClickLeads` count per campaign and per creative over a date window
* Spend per creative

## What this skill CANNOT see (API constraint)

* Form field count or specific fields
* Completion rate (mid-form drop-off)
* Lead-level submission data (names, emails, source signals)
* Lead-quality dimensions (junk email patterns, suspicious time-of-day distribution)
* Form view count separate from form opens

For these dimensions, the skill produces a manual checklist for Campaign Manager.

## What the skill produces

1. **🔴 Spend without leads** — creatives with Lead Gen Forms attached that have meaningful spend (>$50) and zero `oneClickLeads`. Either the form is broken or the creative isn't compelling enough.
2. **🟠 Declining lead volume** — Lead Gen creatives where recent-14d lead count is <50% of prior-14d, with min-volume guardrails.
3. **🟡 Dormant Lead Gen creatives in active campaigns** — Lead Gen creatives in `isServing=true` state but zero recent impressions. Likely audience-count-hold downstream.
4. **Cost-per-lead leaderboard** — best and worst creatives by cost/lead, where there's enough volume to assess.
5. **Form usage map** — every Lead Gen form URN in use and which creatives reference it. Forms used by 0 active creatives are candidates for archiving.
6. **Manual validation checklist** — what to check in Campaign Manager.

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`, `list_linkedin_creatives`, `get_linkedin_ad_analytics` (CREATIVE pivot).
* Bash/Python.

## Process

### Step 1 — Pull data

```
list_linkedin_campaigns(account_id) — filter to objectiveType=LEAD_GENERATION OR campaigns containing creatives with leadgenCallToAction
list_linkedin_creatives(account_id) — filter to creatives with leadgenCallToAction set
get_linkedin_ad_analytics(account_id, pivot=CREATIVE, two 14-day windows, fields include oneClickLeads)
```

### Step 2 — Identify the Lead Gen surface

A Lead Gen creative is any creative with `leadgenCallToAction.destination` set to `urn:li:adForm:N`. Build:

* List of Lead Gen creatives with their form URNs
* Map: form_urn → list of creatives using it
* Map: creative_id → recent + prior analytics

### Step 3 — Classify each Lead Gen creative

For each Lead Gen creative in ACTIVE campaigns:

* **🔴 Spend without leads** — recent cost > $50 AND recent oneClickLeads == 0
* **🟠 Declining leads** — recent leads < 0.5 × prior leads AND prior leads >= 5
* **🟡 Dormant Lead Gen creative** — `isServing=true` but recent impressions == 0
* **✓ Healthy** — has leads, no decline

### Step 4 — Cost-per-lead analysis

For creatives with ≥3 recent leads, compute `cost_per_lead = recent_cost / recent_leads`. Rank best and worst. Don't compute CPL for creatives with <3 leads — too noisy.

### Step 5 — Form usage hygiene

For each form URN:
* If used by 0 currently-active creatives → candidate for archive
* If used by 2+ active creatives in different campaigns → flag for shared-form review (sometimes intentional, sometimes a config copy that wasn't updated)

### Step 6 — Build the report

```
# LinkedIn Lead Form Quality Audit

**N Lead Gen creatives in active campaigns. M Lead Gen Form URNs in use.**

## 🔴 Spend without leads
[list]

## 🟠 Declining lead volume
[list]

## 🟡 Dormant Lead Gen creatives
[list]

## Cost-per-lead leaderboard
- Best: [creative] — $X/lead on Y leads
- Worst: [creative] — $X/lead on Y leads

## Lead Gen Form usage map
[form_urn → creatives, flagged for unused or shared]

## Manual validation checklist (Campaign Manager)
- For forms with high spend per lead: review form fields. Forms with > 6 fields complete at ~50% lower rate. Trim to 4-5 essential fields.
- For forms with no leads: check the form's review status in Campaign Manager — rejected forms silently fail.
- Pull a CSV of recent leads and sample-check email domains. > 30% personal-domain emails (gmail, yahoo) suggests audience is too broad or junk traffic.
- Check lead submission time-of-day distribution. Heavy weekend/late-night submissions are a junk signal.
- Confirm form leads are syncing to your CRM. Broken sync silently destroys downstream attribution.

## Summary
[one-line headline]
```

## Watch for these failure modes

* **Don't flag Lead Gen Form campaigns that just launched.** Forms need 7+ days to accumulate enough leads to assess. Skip creatives with `createdAt < 7 days ago`.
* **Lead Gen Form creatives can also have a landing page CTA** — but `oneClickLeads` only counts native form submissions, not landing-page form fills. If a Lead Gen creative is driving traffic-page conversions, those won't show in this skill's metrics.
* **The `oneClickLeads` metric counts form *submissions*, not high-quality leads.** A spike in oneClickLeads doesn't always mean a spike in good leads. The manual checklist covers the quality dimension.
* **Forms in PAUSED campaigns don't accumulate leads.** Filter to ACTIVE campaigns only.
* **Don't recommend "rewrite the form" for low-volume creatives.** If the creative has < 100 impressions in the recent window, low lead count is a delivery problem, not a form problem.
