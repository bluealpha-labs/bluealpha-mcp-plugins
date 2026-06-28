# Meta Full Monty — Orchestrator Workflow

> **Verified tool bindings (June 2026, tested live on a production account).** Meta is exposed on the BlueAlpha
> connector as `facebook_ads_*` (not `meta_ads_*`). Resolve the account with
> `facebook_ads_list_facebook_ad_accounts()` -> `act_<id>`. Pull config with
> `facebook_ads_list_facebook_campaigns(ad_account_id)` / `facebook_ads_list_facebook_ad_sets(campaign_id)`
> / `facebook_ads_list_facebook_ads(ad_set_id)`. Pull ALL performance with
> `facebook_ads_get_facebook_insights(object_id, level, breakdowns, date_preset|time_range)` —
> `object_id` is `act_<id>` (account) or a bare campaign/adset/ad id; `level` in
> account|campaign|adset|ad; there is NO `fields` arg. Conversions live in the `actions[]`
> array (action_type "purchase"/"lead"); revenue in `action_values[]` — never sum all actions.
> Account-wide or breakdown pulls are large and save to a file: crunch via jq/python in a
> subagent and return only the ranked slice. Full reference: meta-auto-optimize/references/meta-mcp-tools.md. Inline code blocks below are illustrative; the only valid args are those in the verified reference (e.g. get_facebook_insights takes object_id/level/breakdowns/date_preset|time_range, NOT fields/effective_status/limit).



The complete BlueAlpha Meta account workup. Runs the constituent Meta skills in dependency
order, composes the outputs into one leadership-ready report, and produces a prioritized,
risk-tiered action plan. Equivalent to `tiktok-full-monty` / `full-monty` /
`linkedin-full-monty`.

Heavy skill: expect 20-30 tool calls and a multi-page output. Use the single-purpose Meta
skills for routine weekly work. For: onboarding, QBRs, pre-renewal, "what's really going on".

## Sequence (dependency order)

```
1. meta-capi-signal-health        (FIRST — can we trust the numbers at all?)
2. meta-performance-digest        (the headline numbers)
3. meta-auto-optimize             (structure, pacing, budget, learning/fragmentation)
4. meta-advantage-plus-audit      (where automation helps vs leaks)
5. meta-creative-fatigue-watchdog (creative health — uses live creative_fatigue_* engine)
6. meta-placement-performance     (Reels/Feed/Stories/Audience Network)
7. meta-audience-intelligence     (who converts; Advantage+ Audience)
8. meta-geo-expansion             (where to grow / what to cut)
9. meta-creative-refresh          (only if fatigue is High/Critical)
10. meta-incrementality-test      (design — do not execute)
11. (optional) meta-content-to-campaign (if a launch is upcoming)
```

The orchestrator composes, deduplicates, and prioritizes — it does not re-do work.

## Phase 1: Setup

1. Resolve ad account (`facebook_ads_list_facebook_ad_accounts`). Confirm with the user.
2. Period: full-monty default trailing 30d vs prior 30d; quarterly 90/90; onboarding 90d no
   comparison.
3. MMM availability: `meridian_list_models()` — capture a Meta-inclusive model_id for
   cross-checks throughout.
4. Scaffold the executive summary (account, period, spend, conversions, CPA/ROAS, key movement).

## Phase 2: Signal health GATE (run first)

Invoke `meta-capi-signal-health`. This is the gate: if CAPI/AEM/EMQ is broken, every platform
CPA/ROAS in the rest of the report is unreliable. Capture the verdict and **carry a trust
caveat through every efficiency section**. If signal is Critical-broken, lead the executive
summary with it — fixing measurement outranks every tactical optimization.

## Phase 3: Performance Digest

Invoke `meta-performance-digest`. Capture top-line + deltas, top spend drivers, top efficiency
movers, creative/placement pulse, MMM cross-check. Decision branch: a campaign CPA blowout
>50% becomes a deep-dive target downstream.

## Phase 4: Account Audit

Invoke `meta-auto-optimize`. Capture structural scorecard, underspend diagnosis (incl.
learning-phase census + fragmentation), budget reallocation, settings audit, risk-tiered
actions. Decision branch: underspend >20% of budget → executive-summary headline.

## Phase 5: Advantage+ Audit

Invoke `meta-advantage-plus-audit`. Capture ASC verdict (existing-vs-new split!), Advantage+
Audience / CBO / Creative verdicts. Decision branch: if ASC ROAS is glowing but mostly
existing-customer harvesting, flag in the executive summary and force an incrementality test in
Phase 10.

## Phase 6: Creative Health

Invoke `meta-creative-fatigue-watchdog` (uses the live `creative_fatigue_*` engine + raw
read). Capture tier counts, refresh queue, at-risk weekly spend, audience-vs-creative root
cause. Decision branch: Critical+High >25% of weekly spend → trigger Phase 9 (refresh brief).

## Phase 7: Placements

Invoke `meta-placement-performance`. Capture placement economics, Audience Network verdict,
Advantage+ Placements vs manual, creative-fit gaps. Decision branch: a bleeding Audience
Network >$1K/wk → urgent auto-approve cut.

## Phase 8: Audience

Invoke `meta-audience-intelligence`. Capture demographic tier map, prospecting-vs-retargeting
economics (with the incrementality caveat), lookalike/exclusion shortlist, MMM validation.

## Phase 9: Geo

Invoke `meta-geo-expansion`. Capture geo tier map, Drain cleanup, top expansion candidates.
Decision branch: >2 Drain geos bleeding >$1K/wk each → urgent.

## Phase 10: Creative Refresh (conditional)

Only if Phase 6 flagged High/Critical creative-driven fatigue. Produce the 5-concept brief +
launch/measurement plan. Otherwise note the recommendation and skip.

## Phase 11: Incrementality Design (conditional)

Run `meta-incrementality-test` *design* (not execution) when any holds: MMM vs platform
disagree >20%; Meta >15% of paid spend and never tested; ASC/retargeting showing
suspiciously-good ROAS (Phase 5/8); a major scale or new-market decision pending (Phase 8/9).
Check `incrementality_list_incrementality_tests(channel="meta")` for prior tests first. If no
trigger applies, document why.

## Phase 12: Content-to-Campaign (optional)

Only if the user has a launch. Ask explicitly; if yes, run `meta-content-to-campaign` and
append the spec.

## Phase 13: Compose the master report

```
META ACCOUNT REVIEW — FULL MONTY
Client: <name>   Period: <range>   Ad account: act_<id>

EXECUTIVE SUMMARY (1 page)
- Headline (one sentence)
- Signal trust verdict (can we believe these numbers?)
- Spend / Conversions / CPA / ROAS (Δ%)
- Top 3 wins · Top 3 issues
- Total addressable improvement $/wk (underspend + AN waste + Cut audiences + Drain geos + fatigued creative + Advantage+ leakage)
- Top 5 actions ranked by impact

S1 SIGNAL & MEASUREMENT (capi-signal-health) — the trust layer
S2 WHAT HAPPENED (performance-digest)
S3 ACCOUNT HEALTH (auto-optimize: structure/pacing/budget/learning)
S4 AUTOMATION (advantage-plus-audit: ASC/Advantage+ Audience/CBO/Creative)
S5 CREATIVE (fatigue + conditional refresh brief)
S6 PLACEMENTS (placement-performance + Audience Network verdict)
S7 AUDIENCE (audience-intelligence)
S8 GEOGRAPHY (geo-expansion)
S9 MEASUREMENT/INCREMENTALITY (test design + MMM cross-checks)
S10 LAUNCH PIPELINE (optional content-to-campaign)
APPENDIX — per-campaign & per-ad-set tables, full action plan with risk tiers + impact
```

## Phase 14: Action plan synthesis

Reconcile across skills into one deduplicated, prioritized, risk-tiered list:
- **Dedup** overlapping recommendations (e.g. fatigue + placement both flag the same ad).
- **Prioritize** by quantified $-impact.
- **Risk-tier:** Auto-approve (pause clear failures, exclude bleeding Audience Network/geos/demos,
  fix AEM priority) / Recommend (budget shifts <20%, cost-cap loosening, consolidation) /
  Needs discussion (CBO↔ABO, ASC changes, Advantage+ toggles, objective changes, incrementality
  launches, geo expansion).
- Present as the final page with checkboxes.

## Phase 15: Next-cycle cadence

- **Weekly:** performance-digest + creative-fatigue-watchdog
- **Bi-weekly:** auto-optimize
- **Monthly:** advantage-plus-audit + placement-performance + audience-intelligence + geo-expansion
- **Quarterly:** this full monty
- **As-needed:** content-to-campaign (per launch), incrementality-test (per test), capi-signal-health (any time trust drops)
Offer the `schedule` skill for the recurring digest + watchdog.

## Important Notes

- **Signal health is the gate, not a section.** If the numbers can't be trusted, say so at the
  top and caveat everything downstream. This is the difference between a real Meta audit and a
  pretty platform screenshot.
- **The MMM/incrementality cross-check is the BlueAlpha differentiator.** A full-monty without
  it is a structured platform read. Route efficiency calls through the model where possible.
- **Action plan is the deliverable.** A 20-page report without a prioritized, risk-tiered action
  list is a vanity exercise.
- **Don't auto-execute.** Everything recommends; execution routes through the BlueAlpha pipeline
  with per-action approval.
- **Respect cost.** 20-30+ tool calls. Use the single skills for routine work; this is for the
  moments that warrant the whole picture.
