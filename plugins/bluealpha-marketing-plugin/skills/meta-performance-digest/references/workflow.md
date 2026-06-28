# Meta Performance Digest — Detailed Workflow

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



A weekly or monthly Meta performance read in the BlueAlpha three-act narrative: **what
happened, what drove it, what to watch.** Leadership-ready prose, not a spreadsheet. Equivalent
to `tiktok-performance-digest` / `linkedin-performance-digest`.

Read-only. Output is a narrative + a compact metrics table. No execution.

## Phase 1: Set the period & pull top-line

1. Resolve ad account (`facebook_ads_list_facebook_ad_accounts`).
2. Period: weekly digest = trailing 7d vs prior 7d; monthly = trailing 30d vs prior 30d. Use
   `time_range` for clean period-over-period (avoid `date_preset` drift across the comparison).
3. **Account-level both periods:**
   ```
   facebook_ads_get_facebook_insights(object_id=<act_id>, level="account",
     fields=["spend","impressions","reach","frequency","clicks","ctr","cpm","cpc",
             "actions","action_values","purchase_roas","cost_per_action_type"],
     time_range={since,until})
   ```
   Resolve the objective-correct conversion `action_type` for CPA/ROAS before computing deltas.

## Phase 2: Attribute the movement (what drove it)

Don't just report deltas — explain them.

1. **Campaign-level** both periods (`level="campaign"`, `include_names=True`, sort by spend).
   Identify the top 3 spend drivers and the top 3 efficiency movers (CPA/ROAS improved or
   blew out). A digest that says "CPA rose 18%" is weak; "CPA rose 18%, 70% of it from the
   Prospecting-Broad campaign whose frequency hit 3.4 and CPM rose 22%" is the product.
2. **Creative pulse** (`level="ad"`, top by spend): note any winner that's aging or any new
   ad that's outperforming. Pull frequency + relevance rankings for the headline ads.
3. **Placement pulse** (one call with `breakdowns=["publisher_platform","platform_position"]`):
   a one-line read on where efficiency concentrated (e.g. "Reels carried volume, Feed carried
   efficiency"). Deep dives belong to `meta-placement-performance`.
4. **MMM cross-check (live, if a Meta-inclusive model exists):**
   ```
   meridian_list_models()
   meridian_get_reconciled_overview(model=<kpi>, last_n_weeks=<1 or 4>)
   ```
   If platform ROAS and MMM disagree materially, say so in one sentence — the digest should
   never present platform numbers as ground truth without the caveat.

## Phase 3: What to watch

Forward-looking early signals for next period: frequency creeping toward 3.0, ad sets near or
in `LEARNING_LIMITED`, creative aging past 21d, a cost cap throttling delivery, a placement
quietly degrading, budget pacing off. 3-5 bullets, each tied to a specific entity.

## Output

```
META PERFORMANCE DIGEST — <Client>     <period>     act_<id>

THE HEADLINE
<one sentence: the period in a line>

WHAT HAPPENED
Spend $X (Δ%) · Conversions X (Δ%) · CPA $X (Δ%) · ROAS X (Δ%) · CTR/CPM/Frequency deltas

WHAT DROVE IT
- <driver 1 with the entity + mechanism>
- <driver 2> ; <driver 3>
- MMM note (if available)

WHAT TO WATCH
- <forward signal 1 tied to an entity> ... (3-5)

APPENDIX: campaign table (spend, conv, CPA, ROAS, CTR, CPM, freq, Δ vs prior)
```

## Important Notes

- **Narrative over numbers.** Leadership reads the headline and the three acts. Make the
  causal link explicit; the table is the appendix.
- **Always period-over-period.** A number without a delta is noise.
- **Caveat platform ROAS.** Meta's 7d-click/1d-view over-credits; one MMM sentence keeps the
  digest honest. For trust questions, route to `meta-capi-signal-health`.
- **Schedule it.** Offer to wire a Monday-morning weekly via the `schedule` skill.
- **Keep it tight.** A digest is one page. Anything that needs a deep dive names the skill
  that does it (`meta-auto-optimize`, `meta-creative-fatigue-watchdog`, etc.).
