# Snapchat Geo Expansion: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Splits" section. Run tools with
> `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

Geo tiers and expansion candidates for a Snapchat Ads account. The Snapchat counterpart of `geo-expansion-scout`,
`tiktok-geo-expansion` and `meta-geo-expansion`.

**Read this first.** Snapchat reports spend, impressions and swipes by country, region and DMA. Whether it reports
results by geo depends on the account: on an app advertiser, every geo row's installs and purchases came back 0. So
this skill first checks whether results by geo are real, and otherwise gets them from the client's own data.

## Phase 1: Current geo delivery

1. **Read the live ad squads' `targeting.geos`** (`get_snapchat_ad_squads` for each live campaign) to see where
   they're allowed to deliver: whole countries, or `INCLUDE`/`EXCLUDE` lists of regions and metros.
2. **Pull the geo split for each live campaign.** Use `region` and `dma` for a one-country account, and `country`
   for a multi-country one:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <id>,
       granularity: "TOTAL", start_date: <30 days ago>, end_date: <yesterday>, report_dimension: "region",
       fields: ["spend", "impressions", "swipes", <result metric>]}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, report_dimension: "dma"}}
   ])
   ```
   Keep the window to 31 days at DAY, or one TOTAL, and after any geo targeting change (check
   `get_snapchat_change_history` for the ad squads).
3. **Name the DMAs.** The `dma` values are metro ids:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_targeting_geos", arguments={level: "metro", country_code: "us"})
   ```
   For other countries, use their two-letter `code2`.

## Phase 2: Results by geo (decide the measure)

- **Snapchat reports them** (rows carry results that add up to roughly the campaign's): use cost per result per geo.
- **Every row's result is 0 while the campaign has results:** Snapchat isn't reporting them. In order:
  1. `search` for the client's warehouse or platform history by geo ("platform history by region"), or the MMM's
     geo-level contribution ("MMM geo contribution"), and use the results by geo it returns;
  2. ask the user for results by state or DMA from their own analytics or app attribution partner;
  3. otherwise, tier on cost per swipe and swipe rate, labelled clearly as a proxy, not results.

## Phase 3: Tier current markets

Use each geo's cost per result (or the proxy) against the account's median, and its share of spend:

| Tier | Efficiency | Volume | Move |
|---|---|---|---|
| **Star** | Better than the median | High | Protect; give it more when the budget allows |
| **Volume** | Near the median | High | Hold |
| **Opportunity** | Better than the median | Low | Test more budget here |
| **Drain** | Worse than 1.5× the median | Meaningful spend | Reduce or exclude, after checking the creative isn't the cause |

Ignore geos with too little spend to judge, under about 1% of the campaign's. Report `unknown` on its own.

## Phase 4: Expansion candidates

- **Inside the current country:** Opportunity regions and DMAs, and Star DMAs that a national ad squad underserves.
  The usual way to act is a separate ad squad targeting the Stars and Opportunities with its own budget, or excluding
  the Drains.
- **New countries:** list Snapchat's countries (`get_snapchat_targeting_geos` with `level: "country"`). Shortlist
  only where the business can sell, and the language and currency fit. Never recommend a market the user can't
  serve.
- **For each candidate,** give its exact targeting id (metro `id`, region `id`, country `code2`), so the change can
  be made without searching.

## Phase 5: MMM and incrementality check

`search` for "MMM channel ROI". If a model covers Snapchat with geo detail, check that the Stars agree. Before a
large expansion, or before cutting a big Drain, recommend a geo holdout (`snapchat-incrementality-test`):
platform-attributed geo results can mislead.

**Applying.** Geo targeting changes and new ad squads are recommendations for Ads Manager; the skills don't make
them. Moving budget between existing geo-split ad squads can be applied on request with Snapchat write access,
following "Applying changes" in the tool reference.

## Output

1. Measure used: results from Snapchat, from the client's data, or the swipe proxy, and why.
2. Geo table: region or DMA name, spend, swipes, results (or "not reported"), efficiency, tier.
3. Expansion candidates, with targeting ids and the reasoning.
4. Drains to fix, with what to check first (creative, bid, audience).
5. Test recommendation, if expansion or a cut is large.

## Important notes

- **Never read "not reported" as zero results.** It is the most likely mistake in this skill.
- **DMA codes are metro ids,** so name them before showing them.
- **National campaigns spread spend by population.** A Star needs efficiency as well as volume.
- **Geo windows and targeting changes:** keep the window after the last geo or targeting change.
