---
name: linkedin-bid-strategy-audit
description: "Audit LinkedIn campaign bid strategies — cost type (CPM/CPC/CPV/CPL), optimization target, unit cost, creative selection mode, and pacing strategy — against each campaign's objective. Flag mismatches (e.g., CPC on Brand Awareness, CPM on Lead Gen with high unit cost), suspicious unit costs (way above LinkedIn's recommended range or below the bid floor), and missing optimization targets that leave the optimizer flying blind. Output: per-campaign findings + recommended changes. Use when the user says 'audit my LinkedIn bids', 'should I use CPC or CPM on LinkedIn', 'why is my CPM so high', 'is my bid strategy right', 'LinkedIn bid sanity check', or 'check my optimization settings'. Pair with auto-optimize for a complete pre-flight."
---

# LinkedIn Bid Strategy Audit

You score every active LinkedIn campaign's bid configuration against its objective and surface specific misconfigurations with recommended fixes.

LinkedIn has more bid types and optimization knobs than any other ad platform. Manual CPC vs Maximum Delivery vs Target Cost vs Enhanced CPC, paired with five cost types (CPM, CPC, CPV, CPL, CPS) and four optimization targets, multiplied across six campaign objectives — and a meaningful fraction of accounts have at least one campaign on the wrong combination. This skill catches it.

## What the skill produces

Per-campaign findings, sorted by daily-budget impact:

* **🔴 Mismatch** — bid type incompatible with the campaign's objective (e.g., CPC bid on a Brand Awareness campaign that should be CPM)
* **🟠 Suspicious unit cost** — bid amount outside LinkedIn's typical range for the objective, or far above/below the campaign's actual delivery cost
* **🟡 Optimization target missing or wrong** — `NONE` optimization on a campaign that has clear conversion goals; or `ENHANCED_CONVERSION` on a campaign that doesn't have conversion tracking
* **🟡 Creative selection mode** — `ROUND_ROBIN` is rarely better than `OPTIMIZED` for accounts running multiple creatives; flag for review
* **🟡 Pacing strategy** — `LIFETIME` vs `STANDARD` review; flag mismatches with run schedule

Plus a per-objective best-practice cheatsheet so the recommendations are actionable.

## Best-practice rules per objective

| Campaign objective | Cost type | Optimization target | Notes |
|---|---|---|---|
| `BRAND_AWARENESS` | CPM | MAX_REACH (broad reach) or MAX_FREQUENCY (concentrated) | Never use CPC — you're paying for impressions, not clicks. Target cost optional. |
| `ENGAGEMENT` | CPM or CPC | MAX_REACH if CPM, else NONE | CPM with MAX_REACH usually outperforms CPC for engagement metrics. |
| `WEBSITE_VISIT` (Traffic) | CPC | NONE (manual CPC) or AUTOMATED_BID | Manual CPC works if you have a target click value; otherwise use AUTOMATED_BID |
| `WEBSITE_CONVERSION` | CPC | ENHANCED_CONVERSION | Required: install Insight Tag + conversion events. Otherwise this collapses to CPC manual. |
| `LEAD_GENERATION` | CPM with CAP_COST_AND_MAXIMIZE_LEADS, or CPL once you have data | CAP_COST_AND_MAXIMIZE_LEADS (with bid cap) or NONE | Avoid: high-CPM manual bids without lead optimization. |
| `VIDEO_VIEW` | CPV | MAX_VIDEO_VIEWS | Pay per view, not per impression. |

## Suspicious unit-cost ranges (US accounts, May 2026)

These are heuristic floors/ceilings for "is this bid reasonable":

| Cost type / objective | Reasonable low | Reasonable high | Notes |
|---|---|---|---|
| CPM Brand Awareness | $20 | $80 | Below $20 likely under bid floor; above $80 suspicious unless ultra-targeted |
| CPM Engagement | $20 | $80 | Same |
| CPC Traffic | $4 | $25 | B2B traffic often $8-15; under $4 won't win auctions; above $25 = audience too narrow |
| CPC Conversion | $5 | $30 | Higher tolerable because conversions matter |
| CPC Engagement | $3 | $15 | Engagement clicks are cheap on LinkedIn |
| CPM Lead Gen (with CAP_COST) | $20 | $100 | The unit_cost is a CAP, not an actual CPM — but capping above $100 is rare |

Flag unit costs outside these ranges as 🟠 "suspicious" and prompt the user to verify intent.

## Prerequisites

* **LinkedIn Ads MCP** — `list_linkedin_campaigns`.
* Bash/Python.

## Inputs

1. **Account ID.**
2. **Scope** — default ACTIVE campaigns. Optionally include PAUSED if user is preparing to unpause.

## Process

### Step 1 — Pull campaigns

```
list_linkedin_campaigns(account_id)
```

### Step 2 — For each campaign, extract bid config

```
- objectiveType
- costType (CPM/CPC/CPV/CPL/CPS)
- unitCost.amount (the bid in account currency)
- optimizationTargetType (MAX_REACH/MAX_FREQUENCY/ENHANCED_CONVERSION/CAP_COST_AND_MAXIMIZE_LEADS/NONE)
- creativeSelection (OPTIMIZED/ROUND_ROBIN)
- pacingStrategy (LIFETIME/STANDARD)
- dailyBudget
- runSchedule.start (to check if campaign is recent enough for a lifetime budget review)
```

### Step 3 — Apply rules

Walk through each campaign and check it against:

1. **Cost type compatible with objective.** Use the table above.
2. **Unit cost in reasonable range.** Use the heuristic ranges. Flag both above and below.
3. **Optimization target appropriate.** Specifically:
   - WEBSITE_CONVERSION should have ENHANCED_CONVERSION optimization (assuming Insight Tag installed). If not, flag.
   - LEAD_GENERATION should have CAP_COST_AND_MAXIMIZE_LEADS or NONE — never ENHANCED_CONVERSION (which is for web conversions, not native leads).
   - BRAND_AWARENESS/ENGAGEMENT should have MAX_REACH or MAX_FREQUENCY — not NONE.
   - WEBSITE_VISIT can be NONE (manual CPC) — that's fine.
4. **Creative selection.** OPTIMIZED is almost always preferred unless deliberately A/B testing. Flag ROUND_ROBIN with > 2 creatives as a candidate to switch.
5. **Pacing strategy.** LIFETIME on a campaign with no end date is risky — it can over-spend early or starve later. Flag if `runSchedule.end` is missing on a LIFETIME-pacing campaign.

### Step 4 — Render the report

```
# LinkedIn Bid Strategy Audit

**N active campaigns analyzed. K with bid configuration issues.**

## Findings (sorted by daily budget at stake)

### [Campaign name] (objective: X, daily budget: $Y)
- Current: cost_type=X, unit_cost=$N, optimization=X, creative_selection=X, pacing=X
- **🔴 Mismatch:** [specific issue]
  - **Recommendation:** [specific change]
- **🟠 Suspicious bid:** [specific issue]
- **🟡 Optimization concern:** [specific issue]

[Repeat per campaign with issues]

## Best-practice cheatsheet
[the bid table above, in compact form]

## Summary
[one-line headline]
```

## Watch for these failure modes

* **Don't flag a high CPC bid as suspicious if delivery is also high.** Some B2B niches genuinely require $25+ CPC. The flag is for cases where the bid is high AND delivery is starved — usually a bid floor mismatch.
* **Don't recommend ENHANCED_CONVERSION without confirming Insight Tag is installed.** If the account has zero tracked conversions (confirm via analytics), ENHANCED_CONVERSION will silently fail. Recommend Insight Tag install first.
* **The `unitCost` semantics differ by cost type and optimization combo.** For CAP_COST_AND_MAXIMIZE_LEADS, the unit cost is a CAP, not a target. The skill should know this and not flag a $350 CAP unit cost as "way over the CPM range" — it's a ceiling, not a bid.
* **Some campaigns have an opaque `objectiveType=UNKNOWN`.** Older campaigns and certain campaign types don't expose a clean objective. When `UNKNOWN`, skip rule-checking and flag for manual review.

## Headline framing

The skill ends with a one-line read of bid-strategy health:

> "X campaigns with bid configuration issues — N mismatches, M suspicious bids, K optimization concerns. Highest-impact fix: [specific campaign change]."
