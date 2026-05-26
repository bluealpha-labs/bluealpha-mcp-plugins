---
name: linkedin-audience-health-check
description: "Audit LinkedIn matched-audience and segment health across an ad account: identify campaigns on AUDIENCE_COUNT_HOLD, map which audiences are shared across campaigns (auction overlap risk), flag single-audience dependencies, surface declining/stale audiences via impression decay, and produce a manual-validation checklist for what the API can't see (audience sizes, sync recency, list freshness). Use this skill whenever the user says 'check my LinkedIn audiences', 'audience health check', 'matched audience audit', 'why is my campaign on hold', 'audience count hold', 'why isn't my campaign delivering', 'are my audiences too small', 'audience overlap on LinkedIn', 'audience hygiene', 'are any of my LinkedIn audiences stale', or anything about validating matched-audience configuration. Use BEFORE running auto-optimize — audience problems are upstream of pacing and bidding issues."
---

# LinkedIn Audience Health Check

You produce a structural audit of an account's matched audiences and segment configuration — finding count holds, overlap risk, single-points-of-failure, and stale audiences — and output a prioritized fix list plus a manual-validation checklist for what the API can't see.

This skill exists because LinkedIn's matched audiences are the leading cause of campaign delivery failure. AUDIENCE_COUNT_HOLD blocks delivery silently; matched audiences decay as members leave roles; multiple campaigns sharing one audience cannibalize each other in the auction. The LinkedIn UI doesn't surface any of this in one place — this skill does.

## What the skill produces

A structured health report with:

1. **🛑 Urgent: campaigns currently delivery-blocked** — every campaign with `AUDIENCE_COUNT_HOLD` (or `CAMPAIGN_AUDIENCE_COUNT_HOLD`) in its servingStatuses, with the audience URNs it depends on and an estimate of paused daily budget.
2. **Audience usage map** — every matched-audience URN in use, which campaigns use it, and whether each is a single point of failure or a shared-overlap risk.
3. **Stale/declining audiences** — campaigns where impressions have collapsed over the trailing 14 days vs. the prior 14 days despite ACTIVE status. Likely an audience-decay signal.
4. **Dynamic-segment vs matched-audience split** — distinguish LinkedIn-managed interest/behavioral segments (`dynamicSegments`) from customer-uploaded matched audiences (`audienceMatchingSegments`). The first decays differently than the second.
5. **Manual validation checklist** — the things the API can't tell you. Audience sizes, sync recency, list-source health (e.g., HubSpot sync errors). The skill flags *which* audiences to check, not what their current state is.

## API constraint (important — read first)

The LinkedIn Ads MCP does **not** expose a `/dmpSegments` or audience-listing endpoint. That means this skill cannot:

* Look up the size of an audience by URN
* Show the audience name (only the URN)
* Tell you when an audience was last refreshed
* See match rate or list-source metadata

The skill works around this by deriving everything inferable from campaign targeting criteria + serving statuses + impression-trend signals. For the things it can't see, it produces a checklist the user can run in Campaign Manager.

If/when the MCP adds the `/dmpSegments` endpoint, the skill should be upgraded to look up actual audience sizes and sync dates. Until then, the manual checklist is the bridge.

## Prerequisites

* **LinkedIn Ads MCP** — `linkedin_ads_list_linkedin_campaigns`, `linkedin_ads_get_linkedin_ad_analytics` (campaign pivot).
* Bash/Python for parsing campaign targeting JSON.

## Inputs

1. **Account ID.** If unknown, list accounts first and ask.
2. **Optional date window.** Default for the stale-audience trend: trailing 28 days split into two 14-day halves. Allow override.
3. **Scope:** active campaigns only by default; offer to include paused if the user wants a full hygiene pass.

## Process

### Step 1 — Pull campaigns and analytics

```
linkedin_ads_list_linkedin_campaigns(account_id=...)
linkedin_ads_get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<28d ago>, end=<14d ago>, fields=pivotValues,impressions,clicks,landingPageClicks,costInLocalCurrency)
linkedin_ads_get_linkedin_ad_analytics(account_id, pivot=CAMPAIGN, start=<14d ago>, end=<today>, fields=pivotValues,impressions,clicks,landingPageClicks,costInLocalCurrency)
```

The two analytics windows let you compare period-over-period to detect impression decay (stale-audience signal).

### Step 2 — Parse targeting criteria per campaign

For each campaign in the list, extract these from `targetingCriteria.include.and[].or`:

* `urn:li:adTargetingFacet:audienceMatchingSegments` → list of `urn:li:adSegment:N` (matched audiences — customer-uploaded lists, retargeting from website, lookalikes)
* `urn:li:adTargetingFacet:dynamicSegments` → list of `urn:li:adSegment:N` (LinkedIn-managed behavioral/interest segments — these decay differently and aren't user-controlled)
* `urn:li:adTargetingFacet:staffCountRanges` → company-size targeting
* `urn:li:adTargetingFacet:seniorities`, `:jobFunctions`, `:titles`, `:industries`, `:employers` → attribute targeting

Also extract:

* `servingStatuses` — look for `CAMPAIGN_AUDIENCE_COUNT_HOLD`, `AUDIENCE_COUNT_HOLD`, `BILLING_HOLD`, `CAMPAIGN_GROUP_STATUS_HOLD`, `STOPPED`, `RUNNABLE`
* `dailyBudget.amount` — for impact estimation on count-hold campaigns
* `status` — `ACTIVE`, `PAUSED`, `PENDING_DELETION`

### Step 3 — Build the audience usage map

For each unique audience URN, build a list of campaigns that use it, then assign a risk classification using this scoring hierarchy (highest wins):

* **🛑 In a delivery-blocked campaign** (score 5) — Audience belongs to a campaign with `AUDIENCE_COUNT_HOLD` in its serving statuses. Most urgent.
* **🔥 Compound risk: shared AND sole-audience** (score 4) — Audience is used by 2+ active campaigns AND is the *only* matched audience for at least one of them. This is the worst case: auction overlap (multiple campaigns bidding for the same members) compounded by single-point-of-failure (if the audience decays, the SPoF campaign stops cold). Surface the campaign name in the risk text so the reader knows which campaign carries the SPoF.
* **⚠️ Shared by 2+ active campaigns** (score 3) — Auction overlap risk. Multiple campaigns competing in the auction for the same members.
* **⚠️ Single-point-of-failure** (score 2) — Audience is the sole matched audience for exactly one active campaign. If it decays, that campaign loses all delivery.
* **ℹ️ Only paused-campaign uses** (score 1) — Candidate for removal from the account if not part of a planned relaunch.
* **✓ Normal** (score 0) — Used by one active campaign which has other audiences, or by zero campaigns.

Then for each audience URN:

* Sort by risk score descending. Lead with the highest-risk audiences.
* Cap the output at ~25 audiences. If there are more, summarize the tail in one line.

**Why compound risk gets its own class instead of just being "shared + SPoF":** A shared audience that's *also* the sole source for one of its campaigns has a multiplicative failure mode — if it decays, you lose delivery on the SPoF campaign immediately AND lose impression share on the shared campaign (since the audience pool shrinks). Reporting these together masks the urgency.

### Step 4 — Identify count-hold campaigns

For each campaign with `CAMPAIGN_AUDIENCE_COUNT_HOLD` or `AUDIENCE_COUNT_HOLD` in `servingStatuses`:

* List the audience URNs it depends on (matched + dynamic combined)
* Note its `dailyBudget` — that's the daily delivery currently blocked
* Estimate "days held" if possible (compare changeAuditStamps.lastModified — if it's been weeks since the campaign was modified, it's likely been held that whole time)
* Sort by daily budget × estimated days held — that's the dollar impact

This is the **most urgent** section of the report. Lead with it.

### Step 5 — Detect impression decay

For each campaign that ran in both halves of the comparison window:

```
prior_impr = impressions in [14d ago, 28d ago]
recent_impr = impressions in [today, 14d ago]
decay_ratio = recent_impr / prior_impr
```

Flag campaigns with:

* `decay_ratio < 0.5` AND `prior_impr > 1000` → impressions collapsed by 50%+ on a campaign that was previously delivering. Most common cause: matched audience shrinking (members leaving roles), audience match rate degrading, or list TTL expiry. If the campaign uses a single matched audience, attribute the decay to that audience.
* `recent_impr == 0` AND `prior_impr > 100` AND campaign status is ACTIVE → campaign has fully stopped delivering. Likely a count-hold the API hasn't surfaced yet, or audience match rate hit zero.

Don't flag campaigns where decay is explained by budget changes (compare cost too). If both impressions AND cost dropped proportionally, that's a budget adjustment, not an audience issue.

### Step 6 — Produce the report

Output sections in this order:

#### A. 🛑 Urgent: delivery-blocked campaigns

For each count-hold campaign:

```
- **[Campaign name]** (id: [N]) — Daily budget: $X. Held since: ~[date]. Estimated lost delivery: ~$Y.
  - Depends on matched audience: urn:li:adSegment:[ID] (and N other audiences)
  - Action: Open the audience in Campaign Manager → check size. If <300 forecast, replace, expand, or remove from targeting.
```

If no count-holds, say so explicitly — "No campaigns currently delivery-blocked by audience count holds." Don't omit this section.

#### B. Audience usage map

For each unique matched audience URN (active or paused campaigns):

```
- urn:li:adSegment:[ID]
  - Used by: [Campaign A (ACTIVE), Campaign B (PAUSED)]
  - Type: matched audience (or dynamic segment)
  - Risk: single-point-of-failure / shared-with-N-campaigns / stale (no active users)
```

Sort by risk: count-hold-blocking → shared-with-multiple-active → single-point-of-failure → normal → stale.

Cap at 20 audiences for readability. If there are more, summarize the long tail.

#### C. Stale / declining audiences

For each campaign with decay flagged:

```
- **[Campaign name]** — Prior 14 days: X impressions. Recent 14 days: Y impressions. Decay: Z%.
  - Likely cause: [matched audience N appears single-source — audience size or match rate has dropped]
  - Action: Refresh the matched audience list in Campaign Manager. Check HubSpot sync (or whatever list source). If list is fresh, the issue is match rate — try uploading hashed-email versions in addition to the raw list.
```

#### D. Dynamic segment vs matched audience split

A summary table:

```
- Matched audiences in use: X unique URNs across Y campaigns
- Dynamic segments in use: A unique URNs across B campaigns
- Campaigns using only attribute targeting (no audience layer): C
```

This sets context for the next skill in sequence (overlap-finder) which works differently for each type.

#### E. Manual validation checklist

A bulleted list of things the user needs to check in Campaign Manager that the API can't reach:

```
- For each matched audience URN flagged above: open Audiences → confirm size > 300 → confirm Last Sync within 30 days → confirm match rate > 30%
- For each audience sourced from HubSpot: verify the sync is enabled and the source list hasn't been modified recently
- For each audience > 90 days old: consider rebuilding from the current source list
- For Lookalike audiences: confirm the seed audience is still > 300 and has fresh signal
```

### Step 7 — End with one-line summary

A single line of the form:

> "[N] campaigns delivery-blocked, [M] audiences carry single-point-of-failure risk, [K] campaigns showing audience decay. Estimated unblocked-able delivery: $X/day."

This is the user's elevator-pitch read of the account's audience health.

## Watch for these failure modes

* **Don't recommend "expand the audience" without checking match rate.** A 300-member audience that LinkedIn matched to 5K members is healthier than a 50K-member audience matched to 800. The skill can't see match rate (API constraint), so the manual checklist must prompt the user to verify.
* **Don't treat all `AUDIENCE_COUNT_HOLD` campaigns as fixable by expanding audiences.** Sometimes the hold is because the audience EXISTS but LinkedIn hasn't sync'd / matched it yet. Look at `changeAuditStamps.lastModified` — recent campaign updates often trigger temporary holds while LinkedIn re-evaluates.
* **Don't equate `urn:li:adSegment:N` shared across campaigns with overlap.** Shared use is fine if the campaigns target different objectives (one Brand Awareness + one Lead Gen). It's only auction-overlap if both are bidding for the same impression event. Cross-check the campaign objectives before flagging.
* **Dynamic segments aren't matched audiences.** `dynamicSegments` are LinkedIn-managed (e.g., "Senior Tech Decision Makers" cohorts). They don't have count-hold issues the same way and the user can't refresh them. Always separate the two in the report.
* **Don't recommend deleting unused audiences from a paused-campaign report.** The user may be testing or seasonally rotating campaigns. Flag for review, don't recommend deletion.

## What this skill HANDS OFF to other skills

* **linkedin-targeting-overlap-finder** picks up the audience-sharing flags from Section B to look at attribute-level overlap too.
* **linkedin-auto-optimize** treats Section A (count-holds) as a blocking issue — don't run the rest of auto-optimize until those are resolved.
* **linkedin-frequency-saturation-report** uses Section C (decaying campaigns) as supporting context — sometimes "decay" is actually frequency saturation in a shrinking audience.

## When to run it

Manual one-shot, or scheduled weekly. For a healthy account, scheduling weekly catches count-holds within a week of onset rather than waiting for someone to notice budget isn't pacing. Pair with the Cowork schedule tool.
