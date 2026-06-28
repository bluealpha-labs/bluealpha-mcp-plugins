# Meta Ads skills (added in v0.6.0)

Twelve Meta (Facebook/Instagram) skills, mirroring the TikTok suite plus three Meta-specific
additions. Analysis-only; execution routes through the BlueAlpha pipeline.

## Mirror of the TikTok suite
- `meta-auto-optimize` — structure, CBO/ABO, learning-phase & fragmentation, pacing, budget reallocation
- `meta-creative-fatigue-watchdog` — frequency/thumb-stop/CTR/relevance decay; uses the live `creative_fatigue_*` engine
- `meta-performance-digest` — weekly/monthly narrative read
- `meta-audience-intelligence` — demo/geo/device + prospecting-vs-retargeting + Advantage+ Audience
- `meta-creative-refresh` — winning-DNA audit → 5-concept brief
- `meta-content-to-campaign` — content asset → build-ready campaign spec
- `meta-geo-expansion` — geo tiering + expansion candidates + drain cleanup
- `meta-incrementality-test` — geo holdout / Conversion Lift design; uses the live `incrementality_*` tools
- `meta-full-monty` — orchestrator over all of the above

## Meta-specific additions (no TikTok/Google analogue)
- `meta-advantage-plus-audit` — ASC / Advantage+ Audience / CBO / Advantage+ Creative; ASC existing-customer harvesting check
- `meta-placement-performance` — publisher_platform × platform_position; Audience Network waste audit
- `meta-capi-signal-health` — CAPI/dedup, Event Match Quality, AEM 8-event, attribution, SKAN/iOS — gates trust in every CPA/ROAS

## Tool bindings — VERIFIED (v0.6.1)

The Meta read tools on the BlueAlpha connector are the **`facebook_ads_*`** family (not
`meta_ads_*`). All 12 skills are bound to them and were run live on a real production account:
`facebook_ads_list_facebook_ad_accounts`, `facebook_ads_list_facebook_campaigns`,
`facebook_ads_list_facebook_ad_sets`, `facebook_ads_list_facebook_ads`,
`facebook_ads_get_facebook_insights` (object_id + level + breakdowns + date_preset|time_range;
conversions in `actions[]`), and `facebook_ads_compare_facebook_insights`. Account-wide /
breakdown / ad-level pulls are large and return via file — crunch in a subagent. Full
reference: `skills/meta-auto-optimize/references/meta-mcp-tools.md`.

Two skills are partially gated by the connector (not by the skill): `meta-advantage-plus-audit`
(ASC/Advantage+ flags aren't on the campaign-list payload) and `meta-capi-signal-health`
(pixel/CAPI config isn't exposed — it does a data-symptom read + Events Manager checklist).

