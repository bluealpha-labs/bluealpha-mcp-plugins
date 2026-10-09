# Snapchat Performance Digest: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`. Run tools with `search`, then `execute`, passing
> `user_message` every time, and batch independent reads into one `execute(calls=[...])`.

A one-page weekly or monthly read of a Snapchat Ads account in the BlueAlpha narrative format, the Snapchat
counterpart of `tiktok-performance-digest` and `meta-performance-digest`. Narrative first; the table is the appendix.

## Phase 1: Set the period and pull the top line

1. **Resolve the account** (`snapchat_ads.list_snapchat_ad_accounts`) and its timezone. Periods are calendar days in
   that timezone:
   - **weekly:** the last 7 full days, ending yesterday;
   - **monthly:** the last full calendar month.

   The comparison period is the one just before, of equal length.

2. **Learn what each live ad squad optimizes for.** List live campaigns, then their ad squads:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_campaigns", arguments={ad_account_id, status: "ACTIVE"})
   execute(tool_id="snapchat_ads.get_snapchat_ad_squads", arguments={ad_account_id, campaign_id: <id>})
   ```
   Collect the result metrics of their `optimization_goal`s from the table in the tool reference. For example,
   `conversion_purchases` and `conversion_purchases_value` for purchase goals, or `total_installs` for installs.

3. **Pull both periods per campaign in one batch:**
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, granularity: "TOTAL",
       start_date: <this period start>, end_date: <this period end>, breakdown: "campaign", include_names: true,
       fields: ["spend", "impressions", "swipes", <result metrics>]}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, granularity: "TOTAL",
       start_date: <prior start>, end_date: <prior end>, breakdown: "campaign", include_names: true,
       fields: ["spend", "impressions", "swipes", <result metrics>]}}
   ])
   ```
   - Add one TOTAL read per live campaign with `fields: ["frequency", "uniques"]` for reach; reach can't be added
     across campaigns.
   - Keep the response's `notes`: they say which days aren't final yet.

4. **Compute for each campaign and each period:**
   - spend, impressions, swipe rate (swipes ÷ impressions), CPM (spend ÷ impressions × 1,000);
   - results, and cost per result on the goal's own metric;
   - ROAS, only when purchase value is above 0.

   Then the change between periods.

   **Account totals:**
   - **Spend** comes from Snap's own account-level read: the same TOTAL call with no `breakdown` returns spend only.
   - **Impressions, swipes and each goal's results** are the sum of the campaign rows. They're counts, and each
     campaign's are its own, so they add up.
   - **Reach never adds up,** and results of different goals never add into one "conversions" number.

## Phase 2: Attribute the movement

Find what explains the biggest changes, in order:

1. **Campaigns.** Rank by contribution to the change in spend and in results. The top 2-3 movers carry the story.
2. **Ad squads inside each mover.** Pull the same TOTAL reads with
   `level: "campaign", entity_id: <mover>, breakdown: "ad_squad"`, and find which ad squad moved.
3. **Creatives.** Pull `breakdown: "ad"` on the mover to see whether one ad's swipe rate or cost per result shifted.
4. **Changes.** For the 1-3 biggest movers, read `snapchat_ads.get_snapchat_change_history` (`entity_type`
   `campaign` or `ad_squad`) and name any budget, bid, status or targeting change dated inside or just before the
   period. That's usually the cause. `snapchat-change-impact-review` does this in depth.
5. **The market.** A CPM change on unchanged settings points to auction pressure or seasonality, not the account.
6. **The MMM, if there is one.** `search` for "MMM channel ROI". If a model covers Snapchat, add one sentence on its
   view. If there's no model, say the numbers are platform-attributed (28-day swipe, 1-day view by default).

## Phase 3: What to watch

3 to 5 forward signals, each tied to a named entity:
- results for the last days that are still being processed (from `notes`);
- frequency climbing toward about 2 a week on a campaign;
- an ad squad pacing over or under its budget;
- a top ad whose swipe rate is falling (hand off to `snapchat-creative-fatigue-watchdog`);
- an end date coming up.

## Output

```
SNAPCHAT PERFORMANCE DIGEST: <account>     <period>     vs <prior period>

THE HEADLINE
<one sentence: the period in a line>

WHAT HAPPENED
Spend $X (Δ%) · Results by goal: <installs X (Δ%) · purchases X (Δ%)> · Cost per result $X (Δ%) ·
Swipe rate X% (Δ) · CPM $X (Δ%) · Frequency X

WHAT DROVE IT
- <driver 1: the entity and the mechanism, such as "budget raised 20% on 3 Oct">
- <driver 2>; <driver 3>
- MMM note, or the platform-attribution caveat

WHAT TO WATCH
- <signal 1 tied to an entity> ... (3-5)

DATA NOTE
<Snap's notes on numbers still being processed, if any>

APPENDIX: campaign table (spend, results, cost per result, ROAS when available, swipe rate, CPM, frequency,
Δ vs prior)
```

If a driver calls for a budget move and the user asks to make it, it can be applied with Snapchat write access,
following "Applying changes" in the tool reference: one change at a time, shown and confirmed first.

## Important notes

- **Narrative over numbers.** Leadership reads the headline and the three acts, so make the cause explicit.
- **Always period over period.** A number without its change is noise.
- **Results are per goal.** Report installs, sign-ups and purchases separately; adding them hides the economics.
- **Don't add up reach.** Frequency and uniques come only from TOTAL reads, per campaign.
- **Say what isn't final.** Conversions for the last day or two can still change; Snap's `notes` says so.
- **Schedule it.** Offer a Monday-morning weekly run with the `schedule` skill.
- **Keep it to one page.** Deeper questions go to `snapchat-auto-optimize`, `snapchat-creative-fatigue-watchdog`,
  `snapchat-change-impact-review` or `snapchat-audience-intelligence`.
