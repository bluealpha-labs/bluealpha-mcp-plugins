---
name: linkedin-demographic-deep-dive
description: "Analyze LinkedIn Ads spend, clicks, and engagement by member demographics (seniority, job function, company size, industry) to surface which segments are actually working, where the targeting is drifting, and which segments to add or exclude. Use this skill whenever the user says 'demographic analysis on LinkedIn', 'who's clicking my LinkedIn ads', 'job function breakdown', 'LinkedIn seniority report', 'analyze my LinkedIn audience', 'who am I actually reaching on LinkedIn', 'company size breakdown', 'LinkedIn industry mix', or anything about understanding LinkedIn ad delivery by member attributes. Also trigger when prepping a LinkedIn quarterly review, evaluating whether LinkedIn targeting is hitting the intended ICP, or looking for waste to cut. Do NOT use this skill for cross-platform analysis or MMM reconciliation — it's LinkedIn-only and reads native LinkedIn member demographic reporting, which no other platform exposes."
---

# LinkedIn Demographic Deep-Dive

You produce a strategic read of *who* is actually being reached, clicked by, and engaged on a LinkedIn ad account, broken down across LinkedIn's four most informative member-attribute pivots: **seniority, job function, company size, and industry**. The deliverable is a narrative interpretation plus targeting actions — not a metric dump.

This skill exists because LinkedIn's demographic reporting is the platform's killer feature — no other ad platform exposes click-by-job-title or spend-by-seniority data this cleanly — and most marketers never look at it. The result is six-figure spend with no idea whether the wrong job functions are quietly burning a third of the budget.

## What the skill produces

A four-section read of the account:

1. **Who you're paying to reach** — spend distribution across each pivot, with intended-vs-actual comparison against the campaign targeting criteria. Surfaces drift.
2. **Who's actually engaging** — CTR, landing-page-click rate, and (if conversion tracking is live) cost-per-conversion by segment. Surfaces the segments that punch above their spend share.
3. **Where you're wasting** — segments getting meaningful spend with poor engagement. Concrete exclusion candidates.
4. **Where to expand** — segments with strong engagement that the current targeting isn't deliberately reaching. Concrete include candidates.

Plus a one-line headline and a top-3 targeting-action list.

## Prerequisites

* **LinkedIn Ads MCP** — specifically `linkedin_ads_get_linkedin_ad_analytics` (the single-pivot finder) and `linkedin_ads_list_linkedin_campaigns` (to parse intended targeting). Confirm both are connected before starting.
* **`references/linkedin_taxonomy.json`** — the URN-to-label mapping shipped with this skill. Bash/Python is used to resolve URNs and crunch the four pivot responses.

If the LinkedIn Ads MCP isn't connected, say so and stop.

## Inputs you need from the user

1. **Account ID.** If unknown, run `linkedin_ads_list_linkedin_ad_accounts` first and ask which to use.
2. **Date range.** Default to the trailing 90 days. Offer a 30-day quick read or a 365-day strategic read as alternatives via AskUserQuestion.
3. **Optional scope.** All campaigns by default, but the user may want to scope to a single campaign or campaign group. If the account has both active and paused campaigns, ask whether to include paused (default: active only).

## Process

### Step 1 — Get the four pivots

Call `linkedin_ads_get_linkedin_ad_analytics` once per pivot. Always pass `fields` explicitly — the default field set omits `pivotValues`, which means you can't map metrics to segments.

The four required calls (substitute account_id and date range):

```
pivot=MEMBER_SENIORITY
pivot=MEMBER_JOB_FUNCTION
pivot=MEMBER_COMPANY_SIZE
pivot=MEMBER_INDUSTRY
```

**Required `fields` parameter** for every call:

```
pivotValues,clicks,impressions,costInLocalCurrency,externalWebsiteConversions,oneClickLeads,likes,comments,shares,follows,videoViews,videoCompletions,landingPageClicks,reactions
```

`time_granularity=ALL` — you don't need daily breakdowns for the strategic read. If the user asks for a trend (e.g., "is the seniority mix shifting"), re-run with `MONTHLY`.

### Step 2 — Pull intended targeting

Call `linkedin_ads_list_linkedin_campaigns` for the account. For each campaign, extract `targetingCriteria.include` and `targetingCriteria.exclude` — specifically the `seniorities`, `jobFunctions`, `industries`, and `staffCountRanges` facets.

Aggregate across active campaigns to build the **intended targeting set**: which seniorities, functions, industries, and sizes the account *means* to reach. This is the ground truth against which to compare actual delivery.

Note any campaign-level mismatches (e.g., one campaign targets VPs only while another targets Manager+, so the account-aggregate intended set is "Manager through VP").

### Step 3 — Resolve URNs

Load `references/linkedin_taxonomy.json`. For each pivot value:

* Seniority: strip `urn:li:seniority:` prefix, look up in `taxonomy.seniority`.
* Function: strip `urn:li:function:` prefix, look up in `taxonomy.function`.
* Industry: strip `urn:li:industry:` prefix, look up in `taxonomy.industry`. **If not found, keep the raw URN and flag for taxonomy update at the end of the output.** Don't silently drop unknown industries.
* Company size: the value is already an enum (`SIZE_1001_TO_5000`); look up in `taxonomy.company_size`.

### Step 4 — Compute the metrics

For each segment within each pivot:

* **Spend share** = segment cost / total cost across pivot
* **Impression share** = segment impressions / total impressions
* **CTR** = clicks / impressions
* **CPC** = cost / clicks (skip if clicks=0)
* **Landing page click rate** = landingPageClicks / clicks (skip if clicks=0) — this filters out junk clicks that never made it to the site
* **Engagement rate** = (likes + comments + shares + reactions + follows) / impressions
* **CPLPC** = cost / landingPageClicks (skip if landingPageClicks=0) — the most honest "cost to acquire a real visitor" on LinkedIn
* **Cost per conversion** = cost / (externalWebsiteConversions + oneClickLeads), if conversions > 0

**Compute a benchmark for each metric** at the account level (total cost / total clicks, etc.) so you can flag segments that are 1.5x worse or 1.5x better than the account average.

### Step 5 — The honest-engagement check

**LinkedIn click counts include accidental and reflex clicks.** A high CTR with a low landing-page-click rate is usually noise, not signal. Always pair CTR with landing-page-click rate before calling a segment "engaged."

Two pivots specifically to scrutinize:

* **Junior seniorities (Entry, Senior IC)** — often show high CTR because they're newer to the platform and click more reflexively. Check landing-page-click rate before recommending you target them.
* **Very small company sizes (Self-employed, 2-10)** — same pattern. High curiosity clicks, low intent.

If landing-page-click rate is <30% of clicks for a segment, treat its CTR as noise.

### Step 6 — Handle the no-conversions case

Many LinkedIn accounts (including the BlueAlpha account at time of this skill's creation) have zero conversions tracked because the Insight Tag isn't installed or events aren't firing. When `externalWebsiteConversions` and `oneClickLeads` are both 0 across all segments:

1. Note this explicitly at the top of the output as a caveat: "No conversion data available — analysis uses engagement metrics (landing page clicks, CTR, video completion) as the performance proxy."
2. Switch the "performance" axis to **landing-page-click rate** and **CPLPC**, not cost-per-conversion.
3. Recommend installing the Insight Tag as the first targeting action — without it, the optimizer is flying blind.

### Step 7 — Detect cross-pivot patterns BEFORE writing single-pivot findings

Single-pivot findings can hide the most important story. Two patterns to check for explicitly before the narrative:

**SMB / Founder cluster.** When Owner/Partner seniorities AND small-company sizes (SIZE_1, SIZE_2_TO_10, SIZE_11_TO_50) BOTH show LP-click rates above 1.3× the account average, treat them as the same population — founders and solo-marketers at small businesses. Surface this as a single finding and frame as a *decision point*: lean in (add deliberate includes + more budget) or cut (exclude SMB sizes across all campaigns). For most enterprise-B2B paid LinkedIn programs, this is the single highest-leverage targeting decision. Do not write up Owner and SIZE_2_TO_10 as two separate sleeper findings — that obscures the shared population.

**Enterprise cluster.** When Director/VP/CXO seniorities AND large-company sizes (1,001+) both engage above the benchmark, that's a confirmation signal that the intended ICP is being reached effectively, not a fix to make.

**Industry × function correlation** (only run if user explicitly asks for it — requires a multi-pivot call via `get_linkedin_ad_statistics` with `pivots=MEMBER_INDUSTRY,MEMBER_JOB_FUNCTION`). Useful for accounts with deliberate industry-include targeting; otherwise the long tail makes the call noisy and the spend impact small.

### Step 8 — Find the four narrative beats per pivot

After cross-pivot detection, for each pivot identify:

1. **Top spender, intended.** The segment getting the most spend that's in the intended targeting. Is the optimizer concentrating spend where it should? (E.g., for a Marketing-targeted account, you'd expect function:15 to dominate. If it's only 35% of spend with a long tail of unintended functions, the targeting isn't tight.)
2. **Top spender, unintended.** The segment getting the most spend that *isn't* in the intended targeting. This is a high-leverage cut candidate.
3. **Best performer, intended.** The intended segment with the best landing-page-click rate or cost-per-conversion. Lean into this with audience expansion or bid increase.
4. **Sleeper performer, unintended.** A segment outside the intended set with strong engagement and meaningful spend. Candidate to add to the include set.

### Step 9 — Write the strategic read

**Rank actions by dollar impact, not by worst engagement.** Score each candidate action by an explicit dollar number:

- **Insight Tag install** (if conversions are zero) → score = total account spend, because everything's at risk without measurement
- **Cross-pivot cluster decision** (e.g., SMB cluster) → score = total spend inside the cluster
- **Single-segment exclude** → score = `cost × (1 - lpc_rate / account_lpc_rate)` — the recoverable dollars
- **Single-segment add** (sleeper) → score = `cost × (lpc_rate / account_lpc_rate - 1)` — the unrealized lift

Sort all candidates by score, take the top 3, present in dollar-impact order. If a cross-pivot cluster is detected, don't also list its constituent sleepers individually — that double-counts the same population. The script's de-duplication logic handles this; do the same when writing the narrative manually.

After the Top 3 actions block, write four sections, each ~80-150 words:

**1. Who you're paying to reach.** Top 3 segments by spend share for each pivot, with a one-line intended-vs-actual comparison. Flag the biggest drift.

**2. Who's actually engaging.** Top 3 segments by landing-page-click rate (or cost-per-conversion if available). Highlight any segments outside the intended set that are punching above their weight.

**3. Where you're wasting (ranked by dollar opportunity).** Sort by recoverable dollars (`cost × shortfall`), not by worst rate. A $279 segment at 0% LP-click rate is less impactful than a $497 segment at 5% LP-click rate.

**4. Where to expand (ranked by dollar-weighted lift).** Sort by `cost × uplift_ratio`. A $3,000 sleeper at 13% is more important than a $400 sleeper at 22%.

### Step 9 — Present a clean table

After the narrative, render a compact table per pivot showing the top 8-12 segments with these columns:

| Segment | Spend | Spend % | Clicks | LP Clicks | CTR | LPC Rate | CPLPC | In Targeting? |

Use the In Targeting column to mark `✓ intended`, `— unintended`, or `✗ excluded`. This is the at-a-glance view that supports the prose.

For the industry pivot specifically, cap the table at the top 12 by spend. The long tail isn't actionable.

### Step 10 — Flag taxonomy gaps

If any URNs didn't resolve in Step 3, list them at the bottom under "Taxonomy gaps to investigate." This is how `references/linkedin_taxonomy.json` improves over time.

## Watch for these failure modes

* **Don't conflate CTR with intent.** A 2% CTR with a 15% landing-page-click rate is worse than a 0.8% CTR with a 75% landing-page-click rate. Use the latter as the primary signal.
* **Don't recommend expansion based on tiny sample sizes.** Any segment with <100 impressions in the window should be marked "insufficient volume" rather than included in the read.
* **Don't treat MEMBER_INDUSTRY's long tail as signal.** Below the top ~12 industries, the data is mostly noise unless the user is running an industry-targeted campaign.
* **Don't ignore the targeting criteria.** A segment that's getting spend *despite* being in the campaign's exclude list often signals a config bug worth flagging.
* **Don't recommend Insight Tag install as a passing comment.** When conversions are zero, that's the #1 action, not a footnote.
* **Don't use the raw URN in user-facing output.** Always resolve to label. If unknown, write "Industry (urn:li:industry:NNNN — taxonomy gap)" so the gap is visible but the segment is still readable.

## A note on company-size targeting

LinkedIn's company-size pivot is one of the most actionable: it tells you whether your spend is hitting enterprise, mid-market, or SMB. Almost every B2B account has an opinion about which company size is the ICP, and almost every account has spend leaking outside that band. Always call this out specifically — it's the easiest targeting fix on LinkedIn and the one most marketers overlook.

For an account targeting "1,001+", any meaningful spend in SIZE_2_TO_10 or SIZE_11_TO_50 is waste. For an account targeting "51-1,000", spend in SIZE_10001_OR_MORE is waste. Be specific about the dollar amount.
