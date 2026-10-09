# Snapchat Dynamic Ads Audit: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Catalogs, dynamic ads and lead ads"
> section. Run tools with `search`, then `execute`, passing `user_message` every time, and batch independent reads
> into one `execute(calls=[...])`.

The pipeline behind Snapchat Dynamic Product Ads, from the feed to delivery. Snapchat-specific: the connector reads
catalogs, feeds, feed uploads, product sets, dynamic templates and collection ad tiles.

**Read this first.** Catalogs belong to the organization, not the ad account. The tools never list the products
themselves, how many products a set holds, or stats by product. The feed uploads' item counts and the dynamic ads'
delivery are the evidence.

## Phase 1: Catalogs

1. **The organization:** `list_snapchat_ad_accounts` returns each ad account's `organization_id`.
2. **Its catalogs:**
   ```
   execute(tool_id="snapchat_ads.get_snapchat_catalogs", arguments={organization_id})
   ```
   - **None:** say the organization has no catalogs, confirm that no live ad has `render_type: DYNAMIC`, and stop.
   - **For each catalog,** note its `vertical`, its `default_product_set_id` (the "All Products" set), and its
     `event_sources`: the pixels and Snap App IDs that report events for it.
3. **Event sources.** Compare them with the account's pixel (`get_snapchat_pixels`). A catalog with no event
   sources, or only ones the account doesn't use, can't match events to products. Retargeting by product then has
   nothing to work with.

## Phase 2: Feeds and uploads

1. **Each catalog's feeds and sets,** batched:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_product_feeds", arguments: {organization_id, catalog_id: <id>}},
     {tool_id: "snapchat_ads.get_snapchat_product_sets", arguments: {organization_id, catalog_id: <id>}}
   ])
   ```
   A catalog has one `PRIMARY` feed, and a primary feed at most one `SUPPLEMENTAL` feed (`parent_feed_id`). A feed's
   `schedule` is the file Snap fetches and how often. A feed without one takes one-off uploads only, so it goes stale
   unless someone uploads.
2. **Each feed's uploads:**
   ```
   execute(tool_id="snapchat_ads.get_snapchat_feed_uploads", arguments={organization_id, catalog_id: <id>,
     product_feed_id: <id>})
   ```
   Sort them by `created_at`. Take the newest, and the few before it for the trend. Each upload's `summary` holds its
   item counts and `issues_summary`: Snap's error and warning codes, with its recommendations.
3. **Flag:**

| Finding | What it means |
|---|---|
| Newest upload `ERRORED` | Every product failed; the catalog keeps the last good upload's products and prices |
| `COMPLETE` with errored items | Those products didn't update. Give the share of items errored, and the top error codes with Snap's recommendations |
| Warned items | Products that load but may not show well; list the top warning codes |
| `INITIALIZED`, `FETCHING` or `PROCESSING` for over a day | The upload is stuck; check the file URL and that Snap can reach it |
| No completed upload in twice the schedule's interval, or in 7 days for a feed without one | Stale prices and availability |
| Far more items deleted than usual | A broken export emptied part of the feed |

## Phase 3: Product sets

From Phase 2's reads: each set's `name`, `filter` and `status`. A catalog holds at most 50.
- **Status:** `LIVE` sets serve. `MATERIALIZING` means Snap is still building the set after it was created or its
  filter changed; one that stays that way for over a day is stuck. Report any other status as Snap gives it.
- **Read each filter** in plain words (for example "in stock, and brand is BlueAlpha"). The default set's filter is
  empty: every product.
- **Flag** sets no live ad squad uses (tidy-up), and live sets whose filter depends on a field that the latest upload
  reported errors for.
- **Set size isn't exposed.** A `LIVE` set that selects nothing shows up as a dynamic ad squad with a `VALID` delivery
  status and no impressions. Name that as the likely cause, and suggest checking the set's product count in Ads
  Manager.

## Phase 4: Dynamic delivery

1. **The live structure:** campaigns with `status: "ACTIVE"`, then their ad squads, ads and creatives (per campaign,
   as the reference's "Large responses" says). Then the account's templates and collection ad tiles:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_dynamic_templates", arguments: {ad_account_id}},
     {tool_id: "snapchat_ads.get_snapchat_creative_elements", arguments: {ad_account_id}},
     {tool_id: "snapchat_ads.get_snapchat_interaction_zones", arguments: {ad_account_id}}
   ])
   ```
   Snap's E3002 on these means the connected user's role can't read them; say so and continue.
2. **Map it:** catalog, then product set, then ad squads, then ads and their creatives' templates. The links are in
   the reference's "Catalogs, dynamic ads and lead ads" section.
3. **Flag:**
   - a dynamic ad squad whose product set is in none of the organization's catalogs (deleted or moved);
   - a dynamic creative whose product set isn't its ad squad's (Snap requires the same one);
   - a campaign whose catalog isn't the catalog of its ad squads' sets;
   - dynamic ads whose `delivery_status` isn't `["VALID"]`, with Snap's codes, and any `review_status_reasons`;
   - collection ads: an interaction zone's `render_type` must match its creative (`DYNAMIC` tiles show products from
     the ad's set, `STATIC` tiles are fixed). Check that each static tile's `interaction_type` (`WEB_VIEW`,
     `APP_INSTALL` or `DEEP_LINK`) and URL open what the ad promises;
   - templates no creative uses (tidy-up). A template's `text_fields` are the product fields it shows (for example
     `title` and `price`), so errors in those feed fields show up in the ad.

## Phase 5: Performance by product set

For each live dynamic campaign:
```
execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={ad_account_id, level: "campaign",
  entity_id: <id>, breakdown: "ad_squad", granularity: "TOTAL", start_date: <30 days ago>, end_date: <yesterday>,
  fields: ["spend", "impressions", "swipes", <result metric>], include_names: true})
```
- Use the result metric of each ad squad's `optimization_goal`. For purchase goals, also read
  `conversion_purchases_value`.
- Roll the ad squads up to their product set: add spend and results across ad squads with the same goal.
- **ROAS** = `conversion_purchases_value` ÷ spend. When the value is 0, ROAS is unavailable; never report 0.
- **Rank the sets** by cost per result and ROAS. Look first at a set far behind the others: its products' price,
  stock and images in the feed, then its filter.

## Output

1. **Pipeline status:** each catalog, its event sources, feeds, newest upload status and freshness.
2. **Feed issues:** error and warning codes with item counts and Snap's recommendations, most items first.
3. **Product sets:** status, each filter in plain words, the ad squads using it, and its results and ROAS.
4. **Delivery issues:** broken links between set, ad squad and creative; invalid or rejected dynamic ads.
5. **Fix list:** for each item, where it's fixed (the feed source, the catalog in Ads Manager, or the campaign).

## Important notes

- **Analysis only.** Feeds, sets, templates and catalogs are fixed at the feed source or in Ads Manager; the skills
  never change them.
- **No product-level data.** Never guess which products sold or how many a set holds.
- **Upload counts are per upload.** A `REPLACE` upload restates the whole catalog; an `UPSERT` changes only the
  products in its file.
- **Catalogs are per organization.** A catalog can serve several ad accounts in it; say which account's ads you
  measured.
