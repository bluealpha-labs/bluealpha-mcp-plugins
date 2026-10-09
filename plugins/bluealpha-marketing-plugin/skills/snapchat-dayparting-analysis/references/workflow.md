# Snapchat Dayparting Analysis: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Hourly stats" section. Run tools with
> `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

When a Snapchat account's ads deliver results most cheaply, by hour of day and day of week, and whether an ad schedule
would help. Snapchat-specific: the connector reads hourly stats with results, credited to the hour of the impression.

**Read this first.**
- **Snap already chooses when to show ads.** Its delivery bids for the ad squad's goal through the day, so most
  hourly differences are the auction at work, not waste. A schedule earns its place only when a block of hours is
  consistently and clearly worse.
- **A schedule needs a lifetime budget.** Snap accepts a schedule (`ad_scheduling_config`) only on an ad squad with
  a lifetime budget, not a daily one. Recommending a schedule for a daily-budget ad squad means recommending that
  switch too.
- **Hours don't line up exactly.** Stats come in the account's timezone; a schedule runs in each viewer's local time.
  An audience spread across timezones blurs the hourly pattern by the difference.
- **Analysis only.** A schedule is a recommendation for Ads Manager; this skill changes nothing.

## Phase 1: Scope

1. **The account:** `get_snapchat_ad_account` for its timezone and currency.
2. **The live ad squads:** campaigns with `status: "ACTIVE"`, then their ad squads (`get_snapchat_ad_squads` with
   `campaign_id`), kept if `delivery_status` is `["VALID"]`. Note each one's `optimization_goal`, `daily_budget` or
   `lifetime_budget`, and `ad_scheduling_config`. An ad squad without `ad_scheduling_config` runs at all hours; one
   with it already has a schedule, so report its days and hours.
3. **The window:** the last 28 days, ending 2 days before today. Results credited at impression time keep arriving
   after the impression, and the last days are the least complete.
   - **Keep it stable.** Read each ad squad's change history (`get_snapchat_change_history`,
     `entity_type: "ad_squad"`). A bid strategy, bid or targeting change inside the window changes how Snap delivers
     through the day, so start the window after it, or end it the day before it. A window that ends before a change
     describes the setup before it; say so.
   - **Whole weeks.** Keep the window to 7, 14, 21 or 28 days, so each weekday appears equally. Under 14 stable
     days, say it's too soon and stop.
4. **Which ad squads to profile:** their results in the window, in one read per campaign:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={ad_account_id, level: "campaign",
     entity_id: <id>, breakdown: "ad_squad", granularity: "TOTAL", start_date: <window start>,
     end_date: <window end>, action_report_time: "impression", include_names: true,
     fields: ["spend", "impressions", "swipes", <result metric>]})
   ```
   Profile each ad squad with at least 200 results in the window. Ad squads with the same goal in one campaign can be
   profiled together at the campaign level. Name the ones too small to profile.

## Phase 2: Read the hours

For each ad squad to profile, the hourly rows and a TOTAL for the same window, batched (`level: "campaign"` with the
campaign's id when its ad squads are profiled together):
```
execute(calls=[
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "ad_squad", entity_id: <id>,
    granularity: "HOUR", start_date: <window start>, end_date: <window end>, action_report_time: "impression",
    fields: ["spend", "impressions", "swipes", <result metric>]}},
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, granularity: "TOTAL"}}
])
```
- **`action_report_time: "impression"`** credits each result to the hour of the impression that led to it, which is
  what a schedule controls. At the default, `conversion`, a purchase at 2 a.m. from an ad seen at 9 p.m. lands in
  the 2 a.m. row.
- **Large responses:** 28 days is up to 672 rows per ad squad, and the response may be saved to a file. Process it
  with a script, as the reference's "Large responses" section says.
- **Check the sum.** Add each field across all the hourly rows and compare with the TOTAL. They match exactly when
  the rows are complete. If they don't, say so and stop: hours are missing.

## Phase 3: The profile

1. **Hour of day.** Put each row in the hour of its `start_time` (account time) and add the counts across days:
   spend, impressions, swipes and results. Per hour: spend share, results, cost per result, swipe rate, CPM, and an
   index = the hour's cost per result ÷ the window's. Never add reach.
2. **Blocks.** Single hours are thin. Group them into four six-hour blocks, 00-05, 06-11, 12-17 and 18-23 (account
   time), with the same measures.
3. **Both halves.** Split the window in two and compute each block's index in each half. A pattern that flips
   between halves is noise or a change, not the time of day.
4. **Day of week.** Put each row on the date of its `start_time`, with the same measures. Act on it only with 28
   days (each weekday four times); with less, show it labeled as early.
5. **Budget capping.** Add the hourly spend by date. An ad squad whose daily spend equals its daily budget day after
   day is capped by budget: Snap spends all of it, wherever the hours fall.
6. **The timezone mix,** for a country spanning timezones: the spend by region over the window
   (`report_dimension: "region"`, `granularity: "TOTAL"`, `fields: ["spend"]`), grouped by each region's main
   timezone. Say how much spend sits in each and how many hours each is from the account's timezone.

## Phase 4: Verdicts

For each block, and each day of the week when the window is 28 days, checking "too thin" first:

| Verdict | When |
|---|---|
| **Schedule candidate** | Index over 1.25 with at least 30 results, and over 1.15 in both halves |
| **Watch** | Index over 1.15, but under the bar or not in both halves |
| **No change** | Index 1.15 or under |
| **Too thin** | Fewer than 30 results |

Judge on cost per result, never on swipe rate alone: the hours with the cheapest swipes aren't always the hours with
the cheapest results.

## Phase 5: Recommendation

- **No schedule candidates:** no schedule. The profile still shows where the spend goes and when results are
  cheapest. Name any Watch blocks, share the profile with creative and reporting, and re-run this skill in a month.
- **Schedule candidates:** the days and hours to keep, for the user to set in Ads Manager ("Run ads on a schedule",
  under "Budget & Schedule"). With it:
  - **The hours, in viewer time.** Snap applies a schedule in each viewer's local time. When most spend sits in one
    timezone, give the hours in that timezone. When it's split across timezones more than an hour apart, cut only
    blocks whose neighboring hours are also weak, since the edges blur.
  - **What it requires:** a lifetime budget instead of a daily one (Snap paces it across the scheduled hours), flight
    dates the schedule doesn't conflict with, and at least an hour on every day selected.
  - **What to expect:** cutting hours from a budget-capped ad squad doesn't save money. Snap spends the same budget
    in the remaining hours, at their prices, and those prices can rise. The gain is at most the gap between the cut
    block's cost per result and the rest.
  - **How to judge it:** after two weeks, re-run this skill, and compare the ad squad's cost per result with the two
    weeks before the change (two TOTAL reads). The budget switch lands with the schedule, so the read covers both.

## Output

1. **Coverage:** the window and why it was chosen, the ad squads profiled and those too small, and the sum check.
2. **Hour of day:** 24 rows (spend share, results, cost per result, index, swipe rate), then the four blocks, overall
   and in each half.
3. **Day of week,** or "needs 28 days".
4. **The timezone mix,** and whether the ad squad is capped by budget.
5. **The verdict per ad squad,** and any schedule with what it requires.

## Important notes

- **Impression time, not conversion time.** The profile shows when ads are shown, which is what a schedule changes.
- **Snapchat attributes to itself** (28-day swipe, 1-day view by default). When most results are view-through, an
  hour's results partly reflect who saw an ad, not only who acted on it. Compare hours with each other, not with
  other channels.
- **The hour isn't always the cause.** A block can look weak because of the creative or the audience Snap reaches at
  that time. Hand-offs: angles for a weak block → `snapchat-creative-refresh`; budget → `snapchat-auto-optimize`.
- **Cadence:** monthly, or after a big change to bids, targeting or creative.
