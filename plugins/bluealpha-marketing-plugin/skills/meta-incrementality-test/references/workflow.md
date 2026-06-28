# Meta Incrementality Test — Detailed Workflow

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



Design, launch-spec, and read incrementality tests for Meta. Meta's 7-day-click / 1-day-view
attribution plus modeled conversions systematically over-credit Meta; this skill establishes
the causal truth. Equivalent to `tiktok-incrementality-test` / `incrementality-test-runner`.

Design & monitoring only. Launch routes through the BlueAlpha pipeline.

## Phase 0: Existing tests (LIVE tooling)

BlueAlpha has live incrementality tooling — check for prior/running tests first:
```
incrementality_list_incrementality_tests()
incrementality_get_incrementality_test(<id>)
incrementality_get_incrementality_test_timeseries(<id>)
incrementality_get_incrementality_test_validation(<id>)
```
If a Meta test is already running, skip to Phase 4 (read & validate). If complete, fold the
measured lift into the recommendation and (if relevant) stage it as an MMM prior.

## Phase 1: Decide whether a test is warranted

Run a Meta incrementality test when any holds:
- MMM and platform ROAS disagree by >20% on Meta.
- Meta is >15% of paid spend and has never been incrementality-tested.
- A large retargeting line shows great platform ROAS (likely demand harvesting — prime
  suspect for low incrementality).
- A major scale decision or new-market entry is pending and you want causal proof first.

If none hold, document why no test this cycle and lean on the MMM.

## Phase 2: Choose the design

| Design | When | Notes |
|---|---|---|
| **Geo holdout (GeoLift-style)** | Default for web/omni; you control budget by geo | Hold out matched control regions, run in test regions, measure the difference-in-differences on the business KPI (not platform conversions) |
| **Meta Conversion Lift (native)** | User-level RCT inside Meta; good for a single-channel read | Ghost-ads/holdout managed by Meta; cleaner randomization but Meta-owned measurement — still cross-check against the business KPI |
| **Budget-scale / on-off** | Quick directional read when geo split isn't feasible | Weaker; confounded by seasonality — use only as a fallback |

Prefer **geo holdout** when the business can split geographically; it measures the real
outcome and isn't Meta-graded. Use Conversion Lift when geo isn't feasible.

## Phase 3: Spec the test

- **Hypothesis:** "Meta drives ≥ X incremental [KPI] at ≤ $Y iCPA." State the decision the
  result will drive.
- **Regions:** select test vs control with matched pre-period KPI trends (use
  `meridian_*`/geo data to match on baseline). Capture region identifiers for monitoring.
- **Power & duration:** size from baseline KPI volume, variance, and expected lift; typically
  ≥ 4 weeks and enough conversions for significance. Under-powered tests are worse than none.
- **Spend plan:** hold control at $0 incremental (or a fixed baseline); keep test spend stable
  to avoid confounding with a learning reset.
- **Integrity guardrails:** no other major Meta changes during the window (creative, budget
  >20%, audience), watch for cross-geo leakage (people travel / delivery spillover), confirm
  the conversion event is firing consistently (`meta-capi-signal-health`).

## Phase 4: Monitor & read

During the test, monitor integrity (entity status, pacing, geo leakage, CPM/CPC volatility,
conversion sparsity) via the live `incrementality_*` timeseries/validation tools. On
completion:
- Compute lift on the **business KPI**, with confidence interval, vs the control.
- Derive **incremental CPA/ROAS** and compare to **platform-reported** CPA/ROAS — the gap is
  the over-credit factor. (BlueAlpha proof points: beehiiv platform over-reported 345%; Cann
  found zero lift on a channel and saved $480K; Klover cut Meta iOS 50% with no lost
  conversions.)
- **Feed the result back:** stage the measured lift as an MMM prior and route the budget
  decision through `meta-auto-optimize` / the MMM budget tools.

## Output

1. **Test recommendation** — hypothesis + the decision it drives.
2. **Design** — geo holdout vs Conversion Lift vs budget-scale, with rationale.
3. **Test/control regions, duration, required power, spend plan.**
4. **Integrity guardrails.**
5. **On read:** incremental lift + CI, iCPA/iROAS vs platform, over-credit factor, and the
   budget action + MMM-prior handoff.

## Important Notes

- **Measure the business KPI, not Meta's conversion count.** A lift test graded on the
  platform's own modeled conversions defeats the purpose.
- **Retargeting is the usual culprit.** Great platform ROAS + low incrementality = you're
  paying to reach people who'd convert anyway. Test it before defending its budget.
- **Don't change anything else mid-test.** Creative/budget/audience edits confound the read
  and can reset learning.
- **One clean test reframes the whole account.** The incremental-vs-platform gap, once
  measured, should recalibrate every platform-ROAS-based decision downstream.
