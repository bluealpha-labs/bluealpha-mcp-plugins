---
name: linkedin-frequency-saturation-report
description: "Audit LinkedIn campaigns for frequency-cap configuration and saturation risk. Identify campaigns running without frequency caps, campaigns with caps that are too tight (starving delivery) or too loose (saturating small audiences), and campaigns at risk of audience burnout based on impression intensity and audience composition. Output a per-campaign recommendation. Use when the user says 'LinkedIn frequency cap', 'is my LinkedIn audience saturated', 'how often am I showing my ads', 'frequency too high', 'audience burnout on LinkedIn', or 'should I tighten my LinkedIn frequency cap'."
---

# LinkedIn Frequency Saturation Report

You audit every active LinkedIn campaign's frequency-cap configuration and flag saturation risk. The skill works around a real API limitation: the LinkedIn MCP doesn't expose `approximateUniqueImpressions` or reach metrics, so direct frequency measurement isn't possible. Instead, the skill works as a configuration audit + indirect signal from impression intensity and audience composition.

## API constraint

* LinkedIn's MCP doesn't return `reach` or `approximateUniqueImpressions` in analytics responses.
* The skill therefore can't compute true frequency = impressions / unique users.
* Workaround: combine the campaign's `frequencyOptimizationPreference` setting (the cap), its impression volume, and its audience composition (matched audience = small + finite, attribute targeting = larger + open) to assess saturation risk.

If LinkedIn's MCP exposes reach in a future update, upgrade the skill to compute true frequency.

## What the skill produces

1. **🔴 No cap on matched-audience campaign** — running without a frequency cap against a finite matched audience is the highest saturation risk.
2. **🟠 Cap too tight** — campaigns with frequency caps below 3/week may be starving delivery. Common on lead gen.
3. **🟠 Cap too loose** — caps above 10/week on small matched audiences are likely over-serving.
4. **🟡 Impression intensity** — campaigns with >5x impressions per dollar above the account median (proxy for audience saturation), without an obvious explanation.
5. **Account-wide cap policy** — does the account have a consistent frequency policy, or is it ad-hoc per campaign?

## Recommended caps per scenario

| Audience type | Objective | Recommended cap |
|---|---|---|
| Matched audience (uploaded list, small) | Brand Awareness | 4-5 / 7 days |
| Matched audience (small) | Engagement / Traffic | 3-4 / 7 days |
| Matched audience (small) | Lead Gen | 2-3 / 7 days |
| Attribute targeting (large pool) | Brand Awareness | 5-7 / 7 days |
| Attribute targeting (large pool) | Engagement / Traffic | 3-5 / 7 days |
| Lookalike (large pool) | Lead Gen | 3-4 / 7 days |
| Website retargeting (recent visitors) | All | 5-7 / 7 days (intentionally higher) |

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`, `get_linkedin_ad_analytics` (campaign pivot, recent window).
* Bash/Python.

## Process

### Step 1 — Pull campaigns + analytics

```
list_linkedin_campaigns(account_id)
get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<30d ago>, end=<today>, fields=pivotValues,impressions,clicks,costInLocalCurrency)
```

### Step 2 — Parse frequency settings per campaign

For each active campaign, extract:

* `optimizationPreference.frequencyOptimizationPreference.frequency` — the cap value
* `optimizationPreference.frequencyOptimizationPreference.timeSpan.duration` + `.unit` — the cap window (e.g., 5 per 7 DAY)
* If `frequencyOptimizationPreference` is absent → no cap set
* Audience composition: `matched_audience_count`, `dynamic_segment_count`, `attribute_only` (true if no audience layer set)

### Step 3 — Apply rules

For each campaign:

1. **No cap on matched-audience campaign** — `frequencyOptimizationPreference` missing AND `matched_audience_count > 0`. Severity 🔴. Recommend cap of 4-5/week (or per the table above).
2. **Cap is below 3 per 7 days** — likely starving delivery. Severity 🟠. Confirm intent with the user.
3. **Cap is above 10 per 7 days** — likely over-serving. Severity 🟠.
4. **No cap on attribute-only campaign with high spend** — less urgent but worth a soft cap. Severity 🟡.

### Step 4 — Compute impression intensity proxy

For each campaign, compute `impressions / dollar`. Compare to the account median. Campaigns >5x the median may be saturating their audiences (delivering to a small group repeatedly).

Caveat: high impressions/dollar can also mean low bid → high impression delivery at low quality, not necessarily saturation. Use as a soft signal, not a hard flag.

### Step 5 — Build the report

```
# LinkedIn Frequency Saturation Report

**N active campaigns analyzed. K with frequency configuration issues.**

## 🔴 No frequency cap on matched-audience campaigns
[list with recommendations]

## 🟠 Cap may be miscalibrated
[list]

## 🟡 Impression intensity signal
[list]

## Account-wide cap policy
[summary of cap consistency]

## Recommended caps (cheatsheet)
[the table above, in compact form]

## Summary
[one-line headline]
```

## Watch for these failure modes

* **Frequency cap interpretation is window-dependent.** A "5 per 7 days" cap is much tighter than "5 per 30 days." Always cite both the value and the window.
* **Retargeting campaigns intentionally have higher frequency.** A 7/week cap on website-retargeting isn't a problem — it's the point. Don't flag retargeting (`dynamicSegments` with behavioral cohorts) as "too loose" without context.
* **Without true reach data, every flag is heuristic.** State the limitation clearly: "Without reach data from LinkedIn, this is a configuration-level audit, not a direct frequency measurement. Confirm by checking the campaign's reach/frequency tab in Campaign Manager."
* **A campaign with no cap isn't always a problem.** If the campaign uses attribute targeting on a multi-million-person audience, frequency saturation is rare. Don't flag it as 🔴.

## When to run it

* Quarterly review of cap policy across the account.
* After launching new campaigns on matched audiences — confirm caps are set.
* When a campaign's CTR is decaying (run alongside creative-fatigue-watchdog — fatigue and saturation are different causes of the same symptom).
