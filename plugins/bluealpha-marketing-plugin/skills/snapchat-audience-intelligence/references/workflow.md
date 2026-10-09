# Snapchat Audience Intelligence: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Splits" section. Run tools with
> `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

Who converts on Snapchat, and how each ad squad's targeting reaches them. The Snapchat counterpart of
`tiktok-audience-intelligence` and `meta-audience-intelligence`.

## What Snapchat tells you (read this first)

- **Results by age, gender and OS:** yes. Results by interest, region, DMA or device make: no. Those splits are
  delivery only (spend, impressions, swipes).
- **Interest rows overlap,** so they show affinity, not shares.
- **Snap's `35+` bucket overlaps 35-44, 45-54 and 55+:** drop it.
- **Splits only cover one window:** 31 days at DAY, or a TOTAL; never at HOUR. A window that crosses a targeting
  change mixes both settings.
- **Audience segments come as ids only,** in each ad squad's `targeting.segments`. Their names, types and sizes
  are in Ads Manager (Audiences); the connector doesn't read segments.

## Phase 1: Demographics and device

1. For each live campaign (`get_snapchat_campaigns` with `status: "ACTIVE"`, kept if `delivery_status` is
   `["VALID"]`), pull 30 days by age and gender, and by OS:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <id>,
       granularity: "TOTAL", start_date: <30 days ago>, end_date: <yesterday>, report_dimension: "age,gender",
       fields: ["spend", "impressions", "swipes", <result metric>]}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, report_dimension: "os"}}
   ])
   ```
2. **Per bucket:** spend share, results share, cost per result, swipe rate. Drop `35+`, and report `unknown` as its
   own row.
3. **Check against the targeting.** Read the live ad squads' `targeting.demographics` and `targeting.devices`. Spend
   in a bucket the targeting now excludes means a targeting change inside the window; confirm it with
   `snapchat_ads.get_snapchat_change_history` (`entity_type: "ad_squad"`). If so, narrow the window to after the change.

## Phase 2: Interest affinity

Pull `report_dimension: "lifestyle_category"` over the same window, with `fields: ["spend", "impressions",
"swipes"]`.

For each interest:
- its **affinity index** = the interest's swipe rate ÷ the campaign's swipe rate;
- its CPM.

Rank by affinity, with a floor of 1% of the campaign's impressions so tiny rows don't lead. Never add the rows. The
high-affinity interests are creative angles and targeting ideas, not proven converters: Snap doesn't report their
results.

## Phase 3: Targeting map, per live ad squad

From `get_snapchat_ad_squads`, for each live ad squad:
- **Segments:** the segment ids it includes and excludes, from `targeting.segments`. Ask the user which ids are
  customer lists, lookalikes or pixel and app audiences, or have them check in Ads Manager (Audiences).
- **Prospecting or retargeting:** no included segments, or only lookalikes, makes it prospecting; customer, pixel
  or app audiences make it retargeting.
- **Exclusions:** prospecting should exclude existing customers or purchasers. Say which segment ids are
  excluded, and ask whether they cover them.
- **Targeting expansion:** `enable_targeting_expansion` and `auto_expansion_options`. Broad prospecting with
  expansion on is normal; a narrow retargeting ad squad with expansion on leaks into prospecting.
- **Demographics, devices, geos** against where results come from (Phase 1).

## Phase 4: Tiers and recommendations

**Tier the age, gender and OS buckets, within each goal:**

| Tier | Rule |
|---|---|
| **Scale** | Cost per result at or under the median, with real volume |
| **Hold** | Near the median |
| **Cut or test** | Over 1.5× the median, with enough spend to judge |

**Recommendations, each with its evidence:**
- age or device targeting to tighten or open;
- exclusions to add;
- prospecting and retargeting split fixes;
- interest angles to test in creative (hand to `snapchat-creative-refresh`).

**Applying.** Targeting and audience changes are recommendations for Ads Manager; the skills don't make them. A
budget move between ad squads can be applied on request with Snapchat write access, following "Applying changes" in
the tool reference.

## Output

1. Demographic and device table: spend, results, cost per result, swipe rate, tier.
2. Interest affinity: top and bottom 10, labeled as delivery only.
3. Targeting map: each live ad squad, prospecting or retargeting, the segment ids it includes and excludes,
   expansion.
4. Prioritized recommendations.

## Important notes

- **Results only by age, gender and OS.** Never present interest, geo or device-make rows as converting or not.
- **Snapchat attributes to itself** (28-day swipe, 1-day view by default). Compare buckets with each other, not with
  other channels.
- **Watch the window** for targeting changes, and drop the `35+` bucket.
- **Hand-offs:** creative angles → `snapchat-creative-refresh`; geo → `snapchat-geo-expansion`; "is the audience
  incremental?" → `snapchat-incrementality-test`.
