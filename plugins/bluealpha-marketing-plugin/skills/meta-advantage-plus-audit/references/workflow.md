# Meta Advantage+ Audit — Detailed Workflow

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



Meta's Advantage+ suite is where the platform takes control — and where the most spend
silently leaks or silently scales. This skill grades each Advantage+ surface and decides
keep / constrain / test / roll-back. This is a Meta-specific skill with no TikTok/Google
analogue; it's the highest-leverage Meta audit after structure.

Read-only. Recommendations route through the BlueAlpha pipeline.

## The five Advantage+ surfaces

1. **Advantage+ Sales (ASC / "Advantage+ Shopping Campaigns")** — fully automated sales
   campaign: pooled audiences, auto-placements, auto-creative selection, one budget.
2. **Advantage+ App** — the app-install equivalent.
3. **Advantage+ Audience** — ad-set-level audience auto-expansion beyond your defined audience
   (your targeting becomes a "suggestion").
4. **Advantage Campaign Budget (CBO)** — Meta distributes one campaign budget across ad sets.
5. **Advantage+ Creative** — per-ad automatic enhancements (brightness, music, text, 3:4
   crops, image-to-video, etc.).

## Phase 1: Inventory what's on

```
facebook_ads_list_facebook_campaigns(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=200)
facebook_ads_list_facebook_ad_sets(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=500)
facebook_ads_list_facebook_ads(ad_account_id=<act_id>, effective_status=["ACTIVE"], limit=1000)
```
Flag per object: is this an ASC / Advantage+ App campaign? is Advantage Campaign Budget on?
is Advantage+ Audience on at ad-set level? are Advantage+ Creative enhancements on per ad?
Capture the **ASC existing-customer budget cap** (the % of ASC budget allowed to spend on
existing customers — the single most important ASC lever).

## Phase 2: ASC (Advantage+ Sales) deep read

1. **Share of account:** ASC spend as % of total sales spend, and ASC vs manual sales
   campaigns head-to-head on CPA/ROAS (pull `level="campaign"` insights, last 30-90d).
2. **Existing vs new customer split:** ASC reports a new-vs-existing breakdown. The classic
   ASC failure is **ASC harvesting existing customers and reporting inflated ROAS** while doing
   little prospecting. Check the existing-customer cap and the actual split. If ASC ROAS is
   "great" but 60%+ is existing customers, the headline ROAS is demand harvesting, not
   acquisition — flag hard and route to `meta-incrementality-test`.
3. **Creative pool health:** ASC needs many creatives; a thin pool (<6-8) caps its advantage.
4. **Cannibalization:** ASC + manual prospecting in the same account bid against each other.
   Check for audience overlap / rising CPMs concurrent with ASC scaling.

## Phase 3: Advantage+ Audience read

For ad sets with auto-expansion on: compare against comparable original-audience ad sets and,
where visible, in-audience vs expanded delivery. Keep when broad prospecting is efficient;
**constrain** when a tightly-validated winning audience is being diluted by expansion (you
stop being able to control or read the segment). Recommend a head-to-head test where unclear.
Cross-reference `meta-audience-intelligence`.

## Phase 4: Advantage Campaign Budget (CBO) read

Is one budget being distributed sensibly, or is one ad set eating 80-90% while good ad sets
starve? In small accounts CBO often starves sub-threshold ad sets and hides per-segment
economics — recommend ABO. In high-volume accounts with comparable ad sets, CBO is usually
right. Match the recommendation to volume, not dogma.

## Phase 5: Advantage+ Creative read

Per ad, are enhancements on, and is that appropriate? Great for DR scale and creative volume;
risky for brand-strict or regulated accounts (auto text/music/crops alter the asset and can
trip `special_ad_categories` compliance). Flag enhancements applied to brand-sensitive assets;
recommend selective enablement (keep crops/brightness, disable text/music overlays) where
brand control matters.

## Phase 6: The measurement caveat (every Advantage+ surface)

Advantage+ products are **black boxes that grade their own homework** — pooled audiences and
auto-placement make platform attribution especially generous, and you can't decompose what
drove results. Treat every "Advantage+ is crushing it" platform read as a hypothesis to
validate. For any Advantage+ surface taking material budget, recommend an incrementality test
(`meta-incrementality-test`) and an MMM cross-check before scaling further.

## Output

1. **Advantage+ inventory** — what's on, where, and at what spend share.
2. **ASC verdict** — vs manual, existing-vs-new split, existing-customer cap recommendation,
   creative-pool & cannibalization flags.
3. **Advantage+ Audience verdict** — keep / constrain / test, per ad set.
4. **CBO verdict** — CBO vs ABO per campaign, with the volume rationale.
5. **Advantage+ Creative verdict** — per-ad enablement recommendations + compliance flags.
6. **Measurement plan** — which surfaces need an incrementality test before scaling.

## Important Notes

- **ASC existing-customer harvesting is the #1 ASC trap.** A glowing ASC ROAS that's mostly
  existing customers is not acquisition. Check the split and the cap first.
- **Automation isn't good or bad — it's a fit question.** Match each surface to account volume,
  brand constraints, and whether you need to *read* the segment.
- **Advantage+ inflates platform attribution.** Never scale a black box on its own ROAS;
  validate with incrementality + MMM.
- **Thin creative pools cap Advantage+.** If you turn on automation, feed it volume
  (`meta-creative-refresh`).
