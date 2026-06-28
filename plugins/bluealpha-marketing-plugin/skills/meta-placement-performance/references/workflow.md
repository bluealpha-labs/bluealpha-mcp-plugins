# Meta Placement Performance — Detailed Workflow

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



Placement is a uniquely Meta lever: one ad set can serve Facebook Feed, Instagram Reels,
Stories, Explore, Marketplace, in-stream video, Messenger, and Audience Network — each a
different surface with different intent, CPM, and creative requirements. This skill finds
where spend actually converts and decides Advantage+ Placements vs manual control. No
TikTok/Google analogue.

Read-only. Recommendations route through the BlueAlpha pipeline.

## Phase 1: Pull the placement breakdown

```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="campaign" or "account",
  fields=["spend","impressions","reach","frequency","ctr","cpm",
          "actions","action_values","purchase_roas","cost_per_action_type",
          "video_thruplay_watched_actions"],
  breakdowns=["publisher_platform","platform_position"], time_range={last_30d}, include_names=True)
```
Add `breakdowns=["publisher_platform","platform_position","impression_device"]` for a device
cut where supported (some combinations are disallowed — fall back to fewer breakdowns).
Resolve the objective-correct conversion `action_type` for CPA/ROAS per placement.

## Phase 2: Map the placement economics

For each placement (publisher_platform × platform_position) compute spend share, CPM, CTR,
frequency, CPA/ROAS. Typical patterns to look for (verify, don't assume):

| Placement | Common pattern | Watch for |
|---|---|---|
| IG Reels / FB Reels | High volume, low CPM, strong for 9:16 video | high frequency, low link-CTR if creative isn't native vertical |
| FB Feed / IG Feed | Highest intent/conversion efficiency, higher CPM | the efficiency anchor |
| Stories | Cheap reach, good video | needs 9:16; weak with feed-shaped creative |
| Explore / Marketplace | Incremental reach | usually lower intent |
| In-stream video | Cheap impressions | low attention; verify it converts |
| **Audience Network** | Cheapest CPM, off-Meta apps | **classic waste sink** — low-quality clicks, accidental taps, MFA inventory; audit hard |
| Messenger | Niche | usually small |

## Phase 3: Decide placement strategy

1. **Advantage+ Placements (auto) vs manual:** Advantage+ Placements is the default and
   usually right for DR — it lets Meta find cheap conversions across surfaces. But it routinely
   over-allocates to **Audience Network** and low-intent in-stream. Decision: keep Advantage+
   Placements if every placement clears an acceptable CPA; move to manual / apply placement
   exclusions when a placement is clearly bleeding (high spend, CPA > 1.5x account median, no
   improvement).
2. **Audience Network audit (do this explicitly):** quantify AN spend share and its CPA. If AN
   is expensive per conversion or driving junk clicks (very high CTR + near-zero conversion =
   accidental taps / fraud signal), recommend excluding it. This is one of the most common,
   highest-confidence Meta savings.
3. **Creative-fit gaps:** flag placements receiving spend without the right asset ratio (e.g.,
   Reels/Stories served a 4:5 feed asset letterboxed). The fix is creative, not exclusion —
   route to `meta-creative-refresh` to brief 9:16.
4. **Frequency by placement:** a placement at frequency >3 while others are fresh signals
   uneven delivery / saturation on that surface.

## Phase 4: Output

1. **Placement economics table** — spend share, CPM, CTR, frequency, CPA/ROAS per
   publisher_platform × platform_position.
2. **Winners / bleeders** — scale the efficient placements; exclude or fix the drains.
3. **Audience Network verdict** — keep / exclude, with the $ reclaimed.
4. **Advantage+ Placements vs manual recommendation** — with rationale.
5. **Creative-fit gaps** — placements needing native ratios → `meta-creative-refresh`.

## Important Notes

- **Audience Network is the usual culprit.** Always audit it explicitly; excluding a bleeding
  AN is auto-approve-tier savings.
- **Don't exclude a placement that's just under-served by creative.** A Reels placement losing
  on a feed asset is a creative gap, not a bad placement — fix the asset first.
- **Advantage+ Placements is efficient but greedy.** It will chase the cheapest impressions
  (often AN/in-stream); keep it only if every surface clears CPA.
- **Manual placement splitting fragments learning.** Don't split every placement into its own
  ad set — exclude the drains within Advantage+ Placements rather than over-segmenting.
- **Placement reads inform creative.** Coordinate with `meta-creative-refresh` (ratios) and
  `meta-creative-fatigue-watchdog` (placement-specific decay).
