# Meta Content-to-Campaign — Detailed Workflow

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



Convert a content asset into a build-ready Meta campaign spec. Equivalent to
`tiktok-content-to-campaign` / `content-to-campaign`. Output is a spec; execution routes
through the BlueAlpha pipeline.

## Phase 1: Understand the asset & the goal

Gather: the content (URL or description), the business goal (sales / leads / traffic /
awareness / app), the offer, the landing destination, budget, and any brand/compliance
constraints. Map the goal to an ODAX objective:

| Goal | Objective | Ad-set optimization_goal | Notes |
|---|---|---|---|
| Purchases | `OUTCOME_SALES` | conversions (purchase) | needs pixel/CAPI + the purchase event — check `meta-capi-signal-health` |
| Leads | `OUTCOME_LEADS` | leads / conversions | instant forms vs site leads |
| Site visits | `OUTCOME_TRAFFIC` | landing_page_views (not link_clicks) | only when no conversion event exists |
| Reach/video | `OUTCOME_AWARENESS` | reach / ThruPlay | frequency cap matters |
| Engagement | `OUTCOME_ENGAGEMENT` | post engagement / video views | for organic-style boosting done right |
| App | `OUTCOME_APP_PROMOTION` | app installs / app events | SKAN/AEM constraints on iOS |

"Boost this post" almost always maps to a real `OUTCOME_*` objective with conversion
optimization — not the native Boost button, which optimizes for cheap engagement.

## Phase 2: Mine the account for what works

Don't spec in a vacuum. Pull recent winners to seed audiences, placements, and creative:
```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="adset",
  fields=["spend","actions","action_values","purchase_roas","cost_per_action_type","ctr","cpm"],
  time_range={last_90d}, include_names=True)
```
Identify the best-performing audience constructs and placements to reuse. Reference
`meta-audience-intelligence` and `meta-placement-performance` outputs if available.

## Phase 3: Spec the campaign

1. **Structure:** default to a lean build — 1 campaign, 1-3 ad sets. Use ABO for a controlled
   test (you want to read each audience), CBO only if you have several comparable audiences and
   enough volume to exit learning. Avoid fragmentation — too many ad sets starve the
   ~50-conversion threshold.
2. **Audiences:** 1 broad/Advantage+ prospecting + (if a list exists) 1 lookalike + retargeting
   only if there's existing demand to harvest. Don't over-segment a launch.
3. **Placements:** Advantage+ Placements by default for DR efficiency; manual only if a
   placement read justifies it. Ensure creative covers 9:16 and 4:5.
4. **Creative brief from the asset:** translate the content into 3-5 ads — hook (first 3s),
   format(s), on-screen text (sound-off), primary text, CTA. A blog → carousel of key points +
   a video summary; a webinar → clip-based video ads; a product launch → demo Reel + static
   benefit set.
5. **Budget & bid:** start with enough daily budget for the ad set to target ~50 conversions/wk
   at the expected CPA; `LOWEST_COST_WITHOUT_CAP` to gather signal, add a cost cap later once
   stable.
6. **Measurement:** define the success event and reporting window; pre-register an
   incrementality check if this is a major launch (`meta-incrementality-test`); set the read
   date after learning.

## Output

A build-ready spec: objective + optimization goal, campaign/ad-set structure (CBO/ABO rationale),
audiences, placements, 3-5 ad creative briefs, budget + bid strategy, KPIs + measurement plan,
and compliance notes. Hand to the BlueAlpha pipeline to build (paused).

## Important Notes

- **"Boost" is a trap.** Re-spec it as a proper conversion campaign or the spend optimizes for
  vanity engagement.
- **Objective + ad-set optimization_goal must agree.** A sales objective optimizing for
  landing-page views won't drive purchases.
- **Don't fragment a launch.** A lean structure exits learning; a sprawling one never does.
- **Confirm the signal exists** before specing a conversion objective — no purchase event
  feeding Meta means no conversion optimization (`meta-capi-signal-health`).
