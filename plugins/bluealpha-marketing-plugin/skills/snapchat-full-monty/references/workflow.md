# Snapchat Full Monty: Orchestrator Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`. Run tools with `search`, then `execute`, passing
> `user_message` every time, and batch independent reads into one `execute(calls=[...])`.

The complete BlueAlpha Snapchat workup. Runs the Snapchat skills in dependency order, composes their findings into one
report, and produces one prioritized, risk-tiered action plan. The Snapchat counterpart of `meta-full-monty`,
`tiktok-full-monty`, `linkedin-full-monty` and `full-monty`.

A heavy skill: dozens of tool calls and a multi-page report. Use the single Snapchat skills for routine work; this one
is for onboarding, quarterly reviews, renewals and "what's really going on".

## Sequence (dependency order)

```
1. snapchat-pixel-signal-health      (first: can the numbers be trusted?)
2. snapchat-performance-digest       (the headline numbers)
3. snapchat-auto-optimize            (structure, delivery, pacing, budget, settings)
4. snapchat-change-impact-review     (what changed, and whether it helped)
5. snapchat-creative-fatigue-watchdog
6. snapchat-audience-intelligence
7. snapchat-geo-expansion
8. snapchat-ad-review-auditor        (rejected and stuck ads, creative off Snap's specs)
9. snapchat-dayparting-analysis      (results by hour of day and day of week)
10. snapchat-creative-refresh        (only if fatigue calls for it)
11. snapchat-incrementality-test     (design only, when a trigger applies)
```

The orchestrator composes, deduplicates and prioritizes; it doesn't redo work.
- **Read once:** the account, live campaigns, ad squads and ads are read in Phase 1 and reused by every phase.
- **Large responses:** process them by script, as the reference's "Large responses" section says.
- **One phase at a time,** in this conversation.

## Phase 1: Setup

1. **The account:** `list_snapchat_ad_accounts` if it isn't known, then `get_snapchat_ad_account` for the timezone
   and currency. Confirm the account with the user.
2. **The period:**
   - the last 30 days against the 30 before;
   - a quarterly review: 90 against 90;
   - onboarding: 90 days, with no comparison.
   Results for the last day or two may still be processing; carry the response's `notes` into the report.
3. **The live structure:** campaigns with `status: "ACTIVE"`, then ad squads and ads per campaign. Note each ad
   squad's `optimization_goal` and every `delivery_status`.
4. **Other engines:** `search` for "MMM channel ROI", "creative fatigue scores" and "geo holdout test". Note which
   exist for Snapchat; each phase uses them when they do.

## Phase 2: Signal health gate

Run `snapchat-pixel-signal-health`. Capture the trust verdict and the view-through share.
- **Not trusted:** lead the executive summary with it. Fixing measurement comes before any optimization.
- **Trusted with caveats:** carry the caveat into every cost-per-result section.

## Phase 3: Performance digest

Run `snapchat-performance-digest`. Capture the top line and its change, per goal, and what drove it. A campaign whose
cost per result rose by more than 50% becomes a target for Phases 4 and 5.

## Phase 4: Account audit

Run `snapchat-auto-optimize` as analysis only; its apply step waits for Phase 14. Capture:
- the scorecard and the ACTIVE-but-not-delivering list;
- underspend;
- the budget plan;
- the settings audit.

Underspend over 20% of budget goes in the executive summary.

## Phase 5: What changed

Run `snapchat-change-impact-review` over the period.
- **A change that hurt:** a revert candidate for the action plan.
- **Changes too recent to judge:** a re-check date.
- **Phase 4's budget moves:** hold any on an ad squad changed in the last 7 days until the change has settled.

## Phase 6: Creative health

Run `snapchat-creative-fatigue-watchdog`. Capture the refresh queue and the weekly spend on tired ads. Over 25% of
weekly spend on fatigued ads triggers Phase 10.

## Phase 7: Audience

Run `snapchat-audience-intelligence`. Capture:
- the demographic tiers;
- interest affinity;
- the targeting map, including exclusions.

## Phase 8: Geo

Run `snapchat-geo-expansion`. Capture the geo tiers, labeled as results or as the swipe proxy, and the expansion
candidates with their targeting ids.

## Phase 9: Ad review and timing

- **Run `snapchat-ad-review-auditor`.** A live ad squad with no approved ad goes in the executive summary, and
  Snap's rejection reasons become Ads Manager items in the action plan.
- **Run `snapchat-dayparting-analysis`** on the live ad squads with enough results. Capture the hourly profile
  and any schedule candidate; a schedule needs discussion.

## Phase 10: Creative refresh (conditional)

Only if Phase 6 triggered it: the concept brief from `snapchat-creative-refresh`. Otherwise note the recommendation
and skip.

## Phase 11: Incrementality design (conditional)

Design a test with `snapchat-incrementality-test` (design only; never launch one) when any of these holds:
- view-through gives over half the results (Phase 2);
- the MMM and Snapchat's numbers disagree by more than 20%;
- Snapchat is over 15% of paid spend and has never been tested;
- a large scale-up or cut is pending (Phases 4 and 8).

If none applies, say why.

## Phase 12: The master report

```
SNAPCHAT ACCOUNT REVIEW: FULL MONTY
Account: <name> (<id>)   Period: <range>   Timezone and currency

EXECUTIVE SUMMARY
- Headline, in one sentence
- Signal trust verdict, and the view-through share
- Spend, results per goal, cost per result (change)
- Top 3 wins, top 3 issues
- Money a week at stake (underspend, failing ad squads, tired creative, Drain geos)
- Top 5 actions by impact

S1 MEASUREMENT (pixel-signal-health)
S2 WHAT HAPPENED (performance-digest)
S3 ACCOUNT HEALTH (auto-optimize)
S4 WHAT CHANGED (change-impact-review)
S5 CREATIVE (creative-fatigue-watchdog, and the refresh brief if run)
S6 AUDIENCE (audience-intelligence)
S7 GEOGRAPHY (geo-expansion)
S8 AD REVIEW AND TIMING (ad-review-auditor, dayparting-analysis)
S9 INCREMENTALITY (test design and MMM cross-checks)
APPENDIX: per-campaign and per-ad-squad tables, and the full action plan
```

## Phase 13: One action plan

- **Deduplicate:** the same ad flagged by fatigue and by the audit is one item.
- **Prioritize** by money a week at stake.
- **Tier by risk,** as `snapchat-auto-optimize` does:
  - **Low:** pause clear failures, renames;
  - **Medium:** budget moves up to 20%, loosening a throttling bid, reverting a change that hurt;
  - **Needs discussion:** goal or objective changes, Smart Budgets, targeting, ad schedules, geo expansion, budget
    moves over 20%, test launches.
- **Mark each item** as one the skill can apply (pause, budget, bid, rename) or one for Ads Manager.

## Phase 14: Applying (on request)

Only when the user asks, after the report. Follow "Applying changes" in the tool reference exactly:
- one change per `execute`, in the plan's order, each shown and confirmed;
- read the entity again before each change, since the report's numbers may be hours old;
- report each outcome as given, and stop on anything but `applied`.

## Phase 15: Next cycle

- **Weekly:** `snapchat-performance-digest`, `snapchat-creative-fatigue-watchdog`.
- **Every two weeks:** `snapchat-auto-optimize` (weekly above $25K a month on Snapchat, monthly under $5K).
- **Monthly:** `snapchat-change-impact-review`, `snapchat-audience-intelligence`, `snapchat-geo-expansion`,
  `snapchat-dayparting-analysis`.
- **Quarterly:** this full monty.
- **As needed:** `snapchat-pixel-signal-health` (whenever tracking changes or trust drops), `snapchat-ad-review-auditor`
  (after new ads go up), `snapchat-creative-refresh`, `snapchat-incrementality-test`.

Offer the `schedule` skill for the weekly pair.

## Important notes

- **Signal health is the gate, not a section.** If the numbers can't be trusted, say so first and caveat everything
  after it.
- **The MMM and incrementality cross-check is the BlueAlpha difference.** Without it, this is a platform read.
- **The action plan is the deliverable.** A long report without a prioritized, risk-tiered list isn't done.
- **Nothing is applied unless the user asks,** and then one confirmed change at a time.
- **Respect cost.** Use the single skills for routine weeks.
