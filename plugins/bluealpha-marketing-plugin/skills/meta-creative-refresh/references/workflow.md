# Meta Creative Refresh — Detailed Workflow

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



Turn a fatigue read into a production-ready Meta creative brief. Equivalent to
`tiktok-creative-refresh` / `brand-refresh-pipeline`. This skill produces a brief; it does not
launch anything.

## Phase 1: Confirm refresh is needed

Don't brief new creative against an audience problem. Run (or read the output of)
`meta-creative-fatigue-watchdog` first. Refresh is warranted when Critical/High fatigue is
creative-driven (falling thumb-stop / link-CTR / relevance at stable frequency), or when ad
sets have <3 active ads. If the only fired signal is frequency at stable CTR, the fix is
audience rotation, not new creative — route back to `meta-audience-intelligence`.

## Phase 2: Audit the winners (what to clone)

Pull the top performers over a stable 30-90d window:
```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="ad",
  fields=["spend","impressions","frequency","ctr","cpm","inline_link_clicks",
          "video_p25_watched_actions","video_p100_watched_actions",
          "video_thruplay_watched_actions","actions","action_values","purchase_roas",
          "quality_ranking","engagement_rate_ranking","conversion_rate_ranking"],
  time_range={last_90d}, include_names=True, sort=["spend_descending"], limit=50)
```
Pull each top ad's creative object (format, aspect ratio, length, hook, primary text, CTA).
Profile the **winning DNA**: which formats convert (Reels 9:16 vs feed 4:5 vs carousel vs
static), which hooks earn the thumb-stop (first 3 seconds), which angles/CTAs convert, optimal
length. If `meta-placement-performance` data exists, note which winners are placement-specific
(a Reels winner is not automatically a Feed winner).

## Phase 3: Generate the brief (5 concepts)

For each of 5 concepts, specify: concept name + angle; format & aspect ratio (prioritize the
winning DNA; cover 9:16 for Reels/Stories and 4:5/1:1 for feed); hook (the first 3 seconds —
the single most important element on Meta); messaging beats; on-screen text / captions
(sound-off is the default — design for it); CTA; and the fatigue insight it addresses (new
hook for a tired opener, new angle for a saturated message, new format to reach an
under-served placement).

Include 1-2 "different swing" concepts (new angle/format, not just a reskin) so the test can
actually find a new winner rather than incrementally decaying.

## Phase 4: Test & rollout plan

- **Launch structure:** add new ads into existing winning ad sets (preserve learning) rather
  than spinning up new ad sets — avoids re-entering the learning phase and fragmenting volume.
- **Don't pause winners on day one.** Run new alongside fatigued; shift budget as new ads earn
  delivery. Pull the Critical fatigued ads on the schedule the watchdog set.
- **Read window:** give new creative ~50 conversions / a few days before judging; Meta needs
  signal. Compare thumb-stop and link-CTR first (lead indicators), CPA/ROAS second.
- **Compliance:** flag `special_ad_categories` constraints (housing/employment/credit/social
  issues) and any Advantage+ Creative enhancements you do/don't want applied to brand assets.

## Output

1. **Refresh rationale** — what's fatiguing and why new creative (not audience) is the fix.
2. **Winning-DNA profile** — formats/hooks/angles/CTAs that convert today.
3. **5-concept brief** — production-ready, each tied to a fatigue insight.
4. **Launch + measurement plan** — into winning ad sets, read window, pause schedule.
5. **Compliance notes.**

## Important Notes

- **The hook is everything on Meta.** Sound-off, fast-scroll feed — the first 3 seconds and
  on-screen text decide the thumb-stop. Brief the hook hardest.
- **Design for placement.** 9:16 for Reels/Stories, 4:5 for feed; a single 16:9 asset wastes
  the highest-volume placements. Coordinate with `meta-placement-performance`.
- **Preserve learning** — new ads into existing ad sets, not new ad sets.
- **A brief is not a launch.** Production and launch route through the BlueAlpha pipeline.
