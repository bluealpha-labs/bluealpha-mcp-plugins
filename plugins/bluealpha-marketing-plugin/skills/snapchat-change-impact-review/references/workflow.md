# Snapchat Change Impact Review: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Change history" section. Run tools with
> `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

What changed in a Snapchat Ads account, and whether each change helped, hurt or can't be judged yet. Snapchat-specific:
the connector reads each entity's change history, with who made each change and its before and after values.

**Read this first.** Snap keeps no account-wide change log and no date filter. `get_snapchat_change_history` reads one
entity at a time, newest first. So this skill reads the entities that spent, says which ones it checked, and never
calls the others unchanged.

## Phase 1: Scope

1. **The account:** `get_snapchat_ad_account` for its timezone and currency.
2. **The window:** the last 30 days, or the date the user names. Each change needs 7 days before it, so stats reach
   back 7 days further.
3. **The campaigns that spent in the window,** including any paused during it (a pause is a change):
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={ad_account_id, breakdown: "campaign",
     granularity: "TOTAL", start_date: <window start>, end_date: <yesterday>, include_names: true})
   ```
4. **Their ad squads and ads,** per campaign (`get_snapchat_ad_squads` and `get_snapchat_ads` with `campaign_id`).
   Note each ad squad's `optimization_goal`, `bid_strategy`, `bid`, budget and `delivery_status`, and each
   campaign's `pacing_level`.

## Phase 2: Read the change history

1. **Campaigns and ad squads, always.** These calls are small; batch them:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_change_history", arguments: {entity_id: <campaign id>,
       entity_type: "campaign", limit: 50}},
     {tool_id: "snapchat_ads.get_snapchat_change_history", arguments: {entity_id: <ad squad id>,
       entity_type: "ad_squad", limit: 50}}
   ])
   ```
2. **Ads and creatives, where needed.** Read them for an ad squad whose results moved while its own history doesn't
   explain it, or for every ad when there are fewer than about 30. Use `entity_type: "ad"`, then `"creative"` for
   their creatives.
3. **Keep the entries in the window,** and the 7 days before it. When `complete` is false and the oldest entry returned
   is still inside the window, say the history for that entity is cut off.
4. **Put each entry on the account's calendar.** `event_at` is UTC, so convert it to the account's timezone before
   choosing the change day.
5. **Classify each entry.** `CREATED` entries are new entities. `UPDATED` entries carry `update_value_records`: a
   `before_value` and `after_value` per field, with money in currency units. History writes bid strategies in
   lowercase (`auto_bid`, `target_cost`), and an `AUTO_BID` bid as the text "auto bid":

| Change | Fields | What to judge it on |
|---|---|---|
| Budget | `daily_budget`, `lifetime_budget`, `lifetime_spend_cap` | Did spend follow, and what happened to cost per result |
| Bid | `bid`, `bid_strategy` | Cost per result and the number of results |
| Targeting | `targeting` | CPM, swipe rate and cost per result |
| Goal | `optimization_goal` | Only the new goal's metric, after the change: the windows don't measure the same thing |
| Status | `status` | Spend and results across the account (did they move elsewhere?) |
| Schedule | `start_time`, `end_time` | Delivery days |
| Creative | an ad's `creative_id`, or a creative's own fields | The ad's swipe rate and results |

   Report any other field with its before and after values. Changes to one entity on the same day are one event;
   people edit in bursts, such as a bid strategy change followed by a bid tweak. An edit undone the same day (paused,
   then turned back on) is no change. Note who made each one (`email`) and the app it was made through (`app_name`).

## Phase 3: Before and after

For each event, measure the entity it changed: the campaign for a campaign budget, the ad squad for its bid,
targeting or goal, and the ad for a creative swap.

- **Windows:** the 7 full days before the change day, and the 7 full days after it. Leave the change day out; it
  mixes both settings.
- **Two TOTAL reads per event,** which are exact and small:
  ```
  execute(calls=[
    {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "ad_squad", entity_id: <id>,
      granularity: "TOTAL", start_date: <before start>, end_date: <before end>,
      fields: ["spend", "impressions", "swipes", <result metric>]}},
    {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, start_date: <after start>,
      end_date: <after end>}}
  ])
  ```
- **For each window:** spend per day, CPM, swipe rate (swipes ÷ impressions), results and cost per result, using the
  result metric of the ad squad's `optimization_goal`. For a campaign, add results only across ad squads with the
  same goal; otherwise compare them one by one.
- **Did the shift start on the change day?** When a verdict is close, read a DAY series across both windows. A trend
  that began before the change isn't the change.
- **Data that isn't final:** when the after window runs past the response's `notes` on finalized or processed data,
  say the after numbers can still move.

## Phase 4: Separate the change from everything else

1. **A control.** Find an ad squad in the account, ideally with the same goal, that had no change in either window.
   Read its two windows the same way. The change's effect is the entity's shift minus the control's shift. With no
   unchanged sibling, say so: auction, seasonality and the change can't be separated, so confidence is low.
2. **Overlaps.** When another event on the same entity, its campaign or its ads (an ad turned on, paused or swapped)
   falls inside either window, judge them together as one confounded event: 7 days before the first change against
   7 days after the last. Never split the credit between them.
3. **Launch.** When the before window starts within 7 days of the entity's `CREATED` entry, the baseline is its first
   days of delivery and hasn't settled. Say so; it lowers confidence in any verdict.
4. **Outside events.** Name any sale, launch, holiday or tracking change inside either window that the user mentions,
   or that shows as a single-day spike.
5. **Verdict per event:**

| Verdict | When |
|---|---|
| **Helped** | Cost per result improved by more than 15% beyond the control's shift, at the same or higher volume |
| **Hurt** | Cost per result worsened by more than 15% beyond the control's shift, or results fell with spend held |
| **No clear effect** | Within 15%, or it moved the same as the control |
| **Too recent** | Fewer than 7 full days after the change; show the days so far, labelled early |
| **Confounded** | It overlaps another change; judged together |
| **Too small** | Fewer than 30 results in either window |

   A bid strategy or goal change resets how Snap delivers; treat its first week as early, not final.

## Phase 5: Act

"Act" produces a change list. Applying it follows "Applying changes" in the tool reference.

- **Revert a hurtful budget, bid or bid strategy change** to its before value, one change at a time. First read the
  entity again: if its value is no longer the change's after value, someone has changed it since. Don't revert;
  judge the newer change when it settles.
  - In a Smart Budgets campaign (`pacing_level: CAMPAIGN`), revert the campaign's budget.
  - Pass bid strategies in uppercase, whatever the history wrote. Back to `AUTO_BID`: pass
    `bid_strategy: "AUTO_BID"` without a `bid`. Back to `TARGET_COST` or `LOWEST_COST_WITH_MAX_BID`: pass the
    strategy and its before `bid`.
  - A hurtful change that turned something on can be undone by pausing it.
- **Never revert** targeting, goal, schedule, a creative, or a pause (that would set something ACTIVE). Give the
  exact before values from the history, so the user can restore them in Ads Manager.
- **A change that helped:** keep it. To go further with a budget, step by up to 20% at a time; the update tools warn
  above that.
- **Too recent or confounded:** give the date to re-run this skill.

## Output

1. **Coverage:** the window, the entities checked, and any history cut off.
2. **Timeline:** date (account timezone), entity, field, before and after, who, verdict.
3. **Each judged event:** before and after (spend a day, CPM, swipe rate, results, cost per result), the control's
   shift, the verdict and its confidence.
4. **Next steps:** reverts (applied only on request), exact values to restore in Ads Manager, and re-check dates.

## Important notes

- **Only the entities read are covered.** Say which ones; never say "nothing else changed".
- **Before and after is correlation.** For a decision that moves a lot of money, recommend a holdout
  (`snapchat-incrementality-test`).
- **The change day is excluded,** and `event_at` is UTC: a late-evening change in the account's timezone can fall on
  the next UTC day.
- **Changes made through an app** (`app_name`) include edits made by other tools and by this connector; report them
  like any other.
