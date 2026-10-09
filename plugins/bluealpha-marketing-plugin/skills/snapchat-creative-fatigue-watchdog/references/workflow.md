# Snapchat Creative Fatigue Watchdog: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`. Run tools with `search`, then `execute`, passing
> `user_message` every time, and batch independent reads into one `execute(calls=[...])`.

Ad-level fatigue and waste for a Snapchat Ads account, the Snapchat counterpart of
`tiktok-creative-fatigue-watchdog` and `meta-creative-fatigue-watchdog`. The output is a refresh queue.

## Phase 0: BlueAlpha's fatigue engine, if it covers Snapchat

BlueAlpha's creative-fatigue engine scores ads from the client's warehouse data. `search` for "creative fatigue
alerts" and read the platforms its results accept.
- **If Snapchat is one of them:** pull the alert summary and the alert rows for the latest detection date, with the
  arguments the search result's schema gives. Use its categories and its severity ladder (`monitor` <
  `early_warning` < `warning` < `critical`) as the spine of the report. The steps below add detail and catch what
  sits under its alerting floor.
- **If the engine isn't available, or doesn't list Snapchat:** say so in one line and use the steps below alone,
  with the same severity ladder.

## Phase 1: Inventory

1. **Live campaigns, and their delivering ads:**
   ```
   execute(tool_id="snapchat_ads.get_snapchat_campaigns", arguments={ad_account_id, status: "ACTIVE"})
   execute(tool_id="snapchat_ads.get_snapchat_ads", arguments={ad_account_id, campaign_id: <live id>, limit: 100})
   ```
   Keep ads whose `delivery_status` is `["VALID"]`. Note each ad's `ad_squad_id`, `creative_id` and `created_at`;
   ads under 7 days old are too new to judge.

2. **What each ad shows.** Read the live ads' creatives, then their top snap media:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_creatives", arguments={ad_account_id, creative_ids: [...]})
   execute(tool_id="snapchat_ads.get_snapchat_media", arguments={ad_account_id, media_ids: [<top_snap_media_id>, ...]})
   ```
   You need the media `type` (`IMAGE` or `VIDEO`) and `duration_in_seconds`. Images and videos are judged on
   different signals.

3. **Each ad squad's result metric,** from its `optimization_goal` (the table in the tool reference).

4. **What changed in the ad squads** between and during the windows:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_change_history", arguments={entity_id: <ad squad id>,
     entity_type: "ad_squad", limit: 10})
   ```
   A bid, bid strategy, budget or targeting change inside the windows moves every ad's numbers at once. It isn't
   creative fatigue, so call it out next to the results.

## Phase 2: Two windows per ad

Compare the recent window with the one before it. Use 7 days and 7 days for busy accounts, or 14 and 14 when ads
get under about 50,000 impressions a week.

```
execute(calls=[
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <live id>,
    granularity: "TOTAL", start_date: <recent start>, end_date: <yesterday>, breakdown: "ad", include_names: true,
    fields: ["spend", "impressions", "swipes", "video_views", "video_views_15s", "quartile_1", "quartile_2",
             "quartile_3", "view_completion", "avg_view_time_millis", <result metric>]}},
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same, for the prior window>}},
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <live id>,
    granularity: "TOTAL", start_date: <recent start>, end_date: <yesterday>, breakdown: "ad",
    fields: ["impressions", "uniques", "frequency"]}}
])
```

`avg_view_time_millis` comes back as `avg_view_time_seconds`.

**Per ad, per window.** Skip the rates for an ad with 0 impressions in a window. A paused ad can still show
conversions there, from earlier swipes credited later under the 28-day window; that isn't delivery.


| Signal | How | Applies to |
|---|---|---|
| Swipe rate | swipes ÷ impressions | every ad |
| Avg view time | `avg_view_time_seconds` | every ad |
| 2-second view rate | `video_views` ÷ impressions | video |
| 15-second view rate | `video_views_15s` ÷ `video_views` | video |
| Completion rate | `view_completion` ÷ `video_views` (and the quartiles, for where people drop) | video |
| CPM | spend ÷ impressions × 1,000 | every ad |
| Cost per result | spend ÷ the ad squad's result metric | every ad with results |
| Frequency | per ad, recent window (TOTAL only) | every ad |

Pull a DAY series only for the 3-5 top spenders that look fatigued, to see whether the decline is steady or a one-day
dip. Narrow it to their ad squad and keep the fields few: `level: "ad_squad"`, `entity_id: <ad squad id>`,
`breakdown: "ad"`, `granularity: "DAY"`, `fields: ["spend", "impressions", "swipes"]`.

## Phase 3: Severity

Starting thresholds. Tighten or loosen them with the account's own history, and say which you used.

| Severity | Rule |
|---|---|
| `critical` | Swipe rate down 40% or more, or down 25% with frequency over 2.5 in the recent window, with cost per result up 20% or more |
| `warning` | Swipe rate down 25% or more, with CPM or cost per result up 20% or more |
| `early_warning` | Swipe rate down 15% or more; or, for video, completion or 15-second view rate down 20% or more |
| `monitor` | Smaller declines, or too little volume to judge (under 50,000 impressions in a window) |

Also flag:
- **Weak from launch:** an ad 7-21 days old whose swipe rate has been under half its ad squad's median from the start.
  That's a creative problem, not fatigue.
- **High-spend waste:** a top-5 spender whose cost per result is over 1.5× its ad squad's median.
- **Top performers to protect:** the best cost per result with a stable swipe rate. Don't pause them, and copy
  their DNA (`snapchat-creative-refresh`).

When the engine (Phase 0) and these signals disagree, show both and the reason, such as a different window or the
engine's alerting floor.

## Phase 4: Output

1. **Refresh queue:** critical first. For each: the ad, its creative and format (image, or a video of N seconds), the
   signals that moved and by how much, spend at risk per week, and the suggested action.
2. **Weak from launch.**
3. **High-spend waste.**
4. **Protect list.**
5. **Ad squads that would be left thin:** fewer than 3 delivering ads after the suggested pauses. These go to
   `snapchat-creative-refresh` for new concepts.

**Applying pauses (optional).** If the user asks and has Snapchat write access, a fatigued ad can be paused, following
"Applying changes" in the tool reference:
- one ad at a time, shown and confirmed first;
- never the last delivering ad in its ad squad, and say so when that blocks a pause.

## Important notes

- **Images and videos fatigue differently.** Images report 0 video views, so judge them on swipe rate, avg view time
  and cost per result.
- **Fatigue is relative to the ad's own past,** not to other ads. A low swipe rate that never fell is "weak from
  launch".
- **Account-wide moves aren't fatigue.** When most ads' swipe rate or CPM moves the same way at once, look for an
  ad squad change (step 4 of Phase 1), seasonality or the auction, before blaming creative.
- **Frequency is per ad and per window.** It comes from TOTAL reads; never add or average it across ads.
- **Don't judge the last day or two on results:** conversions are still being processed (Snap's `notes`).
- **Recheck in 7 days** after a refresh or pause: the ad squad's cost per result should hold or improve.
