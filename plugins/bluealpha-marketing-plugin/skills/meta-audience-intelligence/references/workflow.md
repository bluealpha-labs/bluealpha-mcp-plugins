# Meta Audience Intelligence — Detailed Workflow

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



Find which Meta audiences actually work, where targeting is drifting, and which segments to
add or exclude. Equivalent to `tiktok-audience-intelligence` / `audience-intelligence`.

Read-only. Recommendations route through the BlueAlpha pipeline.

## The Meta audience reality (read this first)

Meta does **not** report conversion performance per interest inside an ad set — once an ad set
runs, you cannot see which of its stacked interests drove results. So "audience intelligence"
on Meta means three things, in priority order:

1. **Delivery breakdowns** Meta *does* report: `age`, `gender`, `country`/`region`,
   `impression_device`/`platform`. These tell you who Meta actually served and converted.
2. **Audience-construct comparison** at the ad-set level: prospecting vs retargeting,
   lookalike vs custom vs broad/Advantage+ Audience — because each ad set *is* an audience.
3. **Advantage+ Audience evaluation**: is auto-expansion helping or leaking to broad?

## Phase 1: Demographic & device breakdowns (what Meta will tell you)

```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="account" or "campaign",
  fields=["spend","impressions","reach","frequency","ctr","cpm",
          "actions","action_values","purchase_roas","cost_per_action_type"],
  breakdowns=["age","gender"], time_range={last_30d})
```
Repeat with `breakdowns=["impression_device"]` and `breakdowns=["publisher_platform"]`
(placement detail belongs to `meta-placement-performance`; here use it only as an audience
proxy). Resolve the objective-correct conversion `action_type` for CPA/ROAS.

Note: breakdowns generally cannot be combined arbitrarily and split conversions across
attribution windows; treat thinly-populated cells as directional. `dma`/`region` availability
varies — confirm against the connector.

## Phase 2: Audience-construct read (ad set as audience)

Pull ad sets and classify each by its targeting construct:
```
facebook_ads_list_facebook_ad_sets(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=500)
facebook_ads_get_facebook_insights(object_id=<act_id>, level="adset",
  fields=[...same metrics...], time_range={last_30d}, include_names=True)
```
Classify from `targeting`: **Prospecting** (broad / interest / lookalike) vs **Retargeting**
(custom audiences: site/CRM/engagers) vs **Advantage+ Audience** (auto-expand on). Capture
audience type: `lookalike` (and %), `custom`, `broad/Advantage+`.

Compare economics by construct: retargeting almost always shows the best platform CPA/ROAS but
is the **least incremental** (it harvests demand) — flag this explicitly and route scaling
decisions to MMM/incrementality, not platform ROAS.

## Phase 3: Tier the segments

| Tier | Criteria | Action |
|---|---|---|
| **Gold** | CPA <= account median (or ROAS >= target) AND meaningful volume AND incremental construct (prospecting/broad/LAL) | Scale; build more lookalikes off the converters |
| **Silver** | Efficient but small, or efficient-but-low-incrementality (retargeting) | Maintain; cap retargeting budget so it doesn't crowd prospecting |
| **Bronze** | Above-median CPA, improving or thin data | Watch / give learning time |
| **Cut** | CPA > 1.5x median, no improvement, or a demo cell bleeding spend | Exclude the demo / pause the ad set |

## Phase 4: Advantage+ Audience evaluation

For ad sets with auto-expansion on, compare in-defined-audience vs expanded delivery where
visible, and the ad set's CPA vs comparable original-audience ad sets. Recommend keep (broad
DR, expansion efficient), constrain (winning tight audience being diluted), or test
(head-to-head original vs Advantage+ Audience). Deeper Advantage+ work → `meta-advantage-plus-audit`.

## Phase 5: Output

1. **Demographic tier map** — age/gender/device/geo winners and bleeders, with exclusion
   recommendations and $ wasted on Cut cells.
2. **Audience-construct read** — prospecting vs retargeting vs Advantage+ economics, with the
   incrementality caveat on retargeting.
3. **Lookalike/segment expansion shortlist** — new LALs to build off Gold converters, custom
   audiences to add, demos to exclude.
4. **MMM validation** (if available): does the MMM agree the scaled construct is incremental?
5. **Handoffs:** Advantage+ depth → `meta-advantage-plus-audit`; placements →
   `meta-placement-performance`; validate a Gold segment before scaling →
   `meta-incrementality-test`.

## Important Notes

- **You cannot see per-interest performance on Meta** — don't pretend to. Work the breakdowns
  Meta reports plus the ad-set-as-audience construct.
- **Retargeting ROAS is a trap.** It looks best and is least incremental. Never recommend
  shifting budget into retargeting on platform ROAS alone.
- **Demographic exclusions are the highest-confidence, lowest-risk win** here — a clearly
  bleeding age/gender cell is auto-approve-tier.
- **Thin breakdown cells are directional**, not decisive. Require volume before cutting.
