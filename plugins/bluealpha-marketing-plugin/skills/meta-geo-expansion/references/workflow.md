# Meta Geo Expansion — Detailed Workflow

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



Map current geo performance, surface expansion candidates, and clean up bleeding markets.
Equivalent to `tiktok-geo-expansion` / `geo-expansion-scout`.

Read-only. Recommendations route through the BlueAlpha pipeline.

## Phase 1: Current geo performance

```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="campaign" or "account",
  fields=["spend","impressions","reach","frequency","ctr","cpm",
          "actions","action_values","purchase_roas","cost_per_action_type"],
  breakdowns=["country"], time_range={last_30d_or_90d}, include_names=True)
```
For domestic sub-geo detail use `breakdowns=["region"]`. Resolve the objective-correct
conversion `action_type` for CPA/ROAS. Note: geo breakdowns split conversions across windows —
treat low-volume geos as directional.

## Phase 2: Tier current markets

| Tier | Criteria | Action |
|---|---|---|
| **Star** | CPA <= median (ROAS >= target) AND volume | Scale; consider a dedicated ad set/campaign |
| **Opportunity** | Efficient but under-served (low spend share, low frequency) | Increase budget / break into its own ad set |
| **Volume** | High spend, median efficiency | Maintain; watch frequency & saturation |
| **Drain** | CPA > 1.5x median, no improvement | Exclude or pause; reclaim the budget |

Flag **Drain markets bleeding >$1K/week** as urgent — geo exclusions are low-risk, high-confidence wins.

## Phase 3: Expansion candidates

Identify markets you're not in (or barely in) that resemble your Stars:
- **Lookalike geos:** countries/regions demographically and economically similar to Star markets.
- **CPM headroom:** Meta CPMs vary widely by country; cheaper auctions can deliver efficient
  volume if the offer/LP/shipping/currency support it.
- **Spillover signal:** geos already converting organically or via existing broad targeting at
  low spend — proof of latent demand.
- **Operational fit:** only recommend geos the business can actually service (shipping,
  language, payments, support, legal). A cheap CPM in an unserviceable market is a trap.

For each candidate produce a mini-spec: market, why (the Star it resembles + the signal),
suggested objective/structure, starting budget, localized creative needs (language, currency,
9:16 + 4:5), and the success threshold to keep scaling.

## Phase 4: MMM / incrementality check

If an MMM exists, sanity-check that geo-level platform efficiency isn't just retargeting
harvesting demand in mature markets. A new-market entry is a clean **geo holdout candidate** —
recommend validating major expansions with `meta-incrementality-test` rather than trusting
platform CPA in a market with no baseline.

## Output

1. **Geo tier map** — Star / Opportunity / Volume / Drain with metrics.
2. **Drain cleanup list** — geos to exclude/pause + reclaimed budget.
3. **Top 5 expansion candidates** — each with a mini-spec and success threshold.
4. **Measurement note** — which expansions warrant a geo holdout.

## Important Notes

- **Cheap CPM is necessary but not sufficient.** Operational fit and offer relevance decide
  whether a low-cost geo converts.
- **Geo exclusions are auto-approve-tier** when a market clearly bleeds; expansions are
  needs-discussion (budget + ops commitment).
- **New markets distort platform CPA early** (no pixel history, modeled conversions). Use a
  holdout or MMM to read true incrementality, not week-1 platform numbers.
- **Localize creative** — a US 16:9 asset dropped into a new market underperforms; brief
  language + format per market.
