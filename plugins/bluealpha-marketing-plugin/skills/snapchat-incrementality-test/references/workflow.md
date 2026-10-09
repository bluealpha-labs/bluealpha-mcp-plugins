# Snapchat Incrementality Test: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Splits" section. Run tools with
> `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

Designs and monitors a geo-holdout test of Snapchat's incremental impact. The Snapchat counterpart of
`incrementality-test-runner`, `tiktok-incrementality-test` and `meta-incrementality-test`. Analysis only: starting
the holdout is a targeting change the user makes.

## Phase 0: Existing tests

`search` for "incrementality tests". If BlueAlpha's incrementality engine is available, list the client's tests,
read any that cover Snapchat (its results, timeseries and validation, with the arguments the search result gives),
and build on them. If it isn't available, say so in one line and continue: this workflow designs the test itself.

## Phase 1: Is a test warranted?

A test earns its cost when at least one is true:
- **Snapchat is a meaningful share of paid spend,** and its platform-reported results drive budget decisions.
- **The MMM is unsure about Snapchat** (a wide interval), or disagrees with the platform (`search` "MMM channel
  ROI").
- **A big budget decision is coming:** scale Snapchat up, cut it, or enter a new market (`snapchat-geo-expansion`).
- **Attribution is in doubt.** Examples: iOS app results under SKAdNetwork, or view-through credit (the default
  1-day view window) carrying many results.

If none are true, say so and recommend the cheaper read (`snapchat-performance-digest` plus the MMM).

## Phase 2: Choose the design

1. **Unit: DMAs.** Snapchat targets metros by id, and reports delivery by DMA under the same ids (verified). That
   makes DMA holdouts both possible and checkable.
2. **Outcome: the client's own results by DMA.** Snapchat may not report results by geo; it doesn't for app
   conversions. So the outcome comes from:
   - BlueAlpha's engine, if available;
   - or the client's warehouse, analytics or app attribution partner, by DMA, for at least 8 weeks of history.

   Without outcomes by DMA, the test can't be read. Say so and stop.
3. **Matched groups.** Pair DMAs on pre-period outcome level and trend, and on Snapchat spend (the DMA split's
   `spend` and `impressions`, last 30 days). Hold out about 10-20% of the outcome volume. Keep the biggest one or two
   DMAs out of the holdout unless they're matched with each other.
4. **Duration and power.**
   - From the daily outcome volume and its day-to-day variation in the matched groups, estimate the smallest lift
     the test could detect.
   - Choose a length (usually 3-6 weeks, plus a cool-down for lagged conversions) that can detect the lift worth
     acting on.
   - If it can't within 8 weeks, say the test isn't viable at this spend.
5. **Alternative:** Snap's own lift studies, run with Snap's team, when the client has a Snap representative and the
   budget for them.

## Phase 3: The test spec

1. **Groups:** the test and control DMA lists, by name and metro `id`
   (`get_snapchat_targeting_geos` with `level: "metro"`).
2. **The change to make:** in each live ad squad, add the holdout metros to `targeting.geos` with `operation:
   "EXCLUDE"`. An update to `targeting.geos` replaces the whole list, so keep the existing country include in it.
   This is a targeting change: it sends the ads back to review and briefly pauses delivery. So it's made by the user
   in Ads Manager, or with `update_snapchat_ad_squad` directly; this skill doesn't apply it. Note any Smart Budgets
   campaign: excluding geos shifts its budget to the rest.
3. **Pre-period check:** confirm the groups tracked each other over the 8 weeks before.
4. **Primary metric and decision rule:** for example, "incremental purchases per $1,000 of Snapchat spend; scale if
   the lower bound is above X".
5. **Dates:** start, end, cool-down, read date.

## Phase 4: Monitor and read

1. **Leakage check, weekly:** pull `report_dimension: "dma"` with `fields: ["spend", "impressions"]` for the test
   window. The holdout DMAs should show next to no delivery. Any real spend there is leakage: fix it before reading.
2. **No other changes during the test:** check `get_snapchat_change_history` on the test ad squads. Budget, bid or
   targeting changes mid-test weaken the read. Log them if they happen.
3. **Read:** compare test and control outcomes against the pre-period relationship, with the engine's validation if
   it's available. Report the lift with its interval, and the incremental cost per result against Snapchat's
   platform-reported one.

## Output

1. Verdict on whether to test, with the reason.
2. The design: unit, outcome source, groups, holdout share, duration, detectable lift.
3. The spec: DMA lists with metro ids, the exclusion to make, dates, decision rule.
4. The monitoring plan, with the weekly leakage check.
5. The read, when the test is done.

## Important notes

- **No outcomes by DMA, no test.** Snapchat's geo split shows delivery, and may not show results.
- **Starting the holdout is the user's step.** It's a targeting change, outside what the Snapchat skills apply.
- **Hold everything else still** during the test, and log what changes.
- **Hand-offs:** expansion decisions → `snapchat-geo-expansion`; budget after the read → `snapchat-auto-optimize`.
