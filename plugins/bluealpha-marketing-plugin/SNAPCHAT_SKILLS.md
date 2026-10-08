# Snapchat Ads skills (v0.7.0)

Twelve Snapchat skills: the TikTok and Meta suite, plus four built on tools only the Snapchat connector has.
Analysis-first. A skill can also apply pause, budget, bid and rename changes when the user asks and has Snapchat write
access, one confirmed change at a time.

## Mirror of the TikTok and Meta suites
- `snapchat-auto-optimize`: structure, delivery status, pacing, goal-matched budget reallocation, settings audit
- `snapchat-performance-digest`: weekly or monthly read
- `snapchat-creative-fatigue-watchdog`: swipe-rate, completion and frequency decay; the refresh queue
- `snapchat-audience-intelligence`: age, gender, geo, device and interest splits; audience segment health
- `snapchat-creative-refresh`: winning-creative audit, then a concept brief
- `snapchat-geo-expansion`: country, region and DMA tiers; expansion candidates
- `snapchat-incrementality-test`: geo holdout design and monitoring
- `snapchat-full-monty`: orchestrator over all of the above

## Snapchat-specific
- `snapchat-change-impact-review`: what changed (budgets, bids, statuses, creatives) right before performance moved
- `snapchat-dynamic-ads-audit`: catalogs, feeds, feed upload errors, product sets and dynamic ads
- `snapchat-lead-gen-auditor`: lead forms, webhooks, and ads spending without leads
- `snapchat-pixel-signal-health`: whether the conversion numbers can be trusted

## Tool bindings: VERIFIED (October 2026)

- **Tool ids:** Snapchat runs on the BlueAlpha connector as `snapchat_ads.*` tool ids, found with `search` and run with
  `execute`. Every skill is bound to the exact ids and arguments in
  `skills/snapchat-auto-optimize/references/snapchat-mcp-tools.md`, checked against the server's source and live
  read-only calls on a real advertiser account.
- **Facts that shape every skill:**
  - `delivery_status`, not `status`, says what's live.
  - Each ad squad is judged on the result metric of its `optimization_goal`.
  - `swipe_up_percent` is a fraction.
  - Reach metrics come only from TOTAL reads.
- **Applying changes:** limited to pausing, budgets, bids and renames, through the three update tools, each change
  shown and confirmed first. It never deletes, creates, or sets anything ACTIVE.
- **Not used:** `get_snapchat_signal_quality`, until Snap approves showing signal readiness. `snapchat-pixel-signal-health`
  reads the data symptoms instead and gives an Events Manager checklist.
