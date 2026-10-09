# Snapchat Ads MCP Tool Reference: VERIFIED against the live BlueAlpha connector

> **Verified October 2026** against the Snapchat MCP's source and live read-only calls on a real advertiser account.
> Every Snapchat skill in this plugin uses these exact tool ids and arguments. Don't add an argument that isn't listed
> here: the tools reject unknown arguments.

## How the tools are called

- **Find, then run:** the BlueAlpha connector finds tools with `search` and runs them with `execute(tool_id, arguments)`.
  Snapchat tool ids are `snapchat_ads.<tool>`, for example `snapchat_ads.get_snapchat_stats`.
- **`user_message`:** pass it on every call, with the user's latest request, verbatim.
- **Batch reads, never writes:** batch independent reads into one `execute(calls=[{tool_id, arguments}, ...])`.
  Write tools can't be batched; run each one alone.
- **Other engines:** for MMM, creative fatigue, incrementality and warehouse history, never guess an id. `search` by
  intent ("MMM channel ROI", "creative fatigue scores", "geo holdout test", "platform history") and use the ids it
  returns. If a search returns nothing for Snapchat, say so and continue with the Snapchat tools alone.

## Large responses

Account-wide listings on a long-running account are big. Ad squads carry full targeting, and old accounts keep many
ad squads that say ACTIVE but no longer deliver. A batch of them can exceed the chat's limit and be saved to a file.
- **When that happens:** process the file with a script (jq or Python), ideally in a subagent, and keep only the
  counts and the live entities. Don't read the raw file into context.
- **To keep payloads small:** list campaigns with `status: "ACTIVE"` first, then read ad squads and ads by
  `campaign_id` for the live campaigns only.

## Object hierarchy and ids

Organization -> ad account -> campaign -> ad squad (Snapchat's ad set) -> ad. An ad shows a creative, and a creative
shows media. Ad account, campaign, ad squad, ad, creative and media ids are UUIDs; the audience segment ids in an ad
squad's targeting are numeric strings.

## Read tools (exact)

| Tool id | Purpose | Arguments (`*` required) |
|---|---|---|
| `snapchat_ads.list_snapchat_ad_accounts` | Every ad account the connected Snapchat user can access, with currency, timezone, roles and organization | none |
| `snapchat_ads.get_snapchat_ad_account` | One account: status, currency, timezone, billing type, lifetime spend cap | `ad_account_id*` |
| `snapchat_ads.get_snapchat_campaigns` | Campaigns: `objective_v2_properties`, status, `delivery_status`, `pacing_level`, budgets | `ad_account_id*`, `campaign_ids`, `status` (`ACTIVE`/`PAUSED`), `limit` (100) |
| `snapchat_ads.get_snapchat_ad_squads` | Ad squads: `optimization_goal`, `bid_strategy`, `bid`, budgets, targeting, `targeting_reach_status`, `delivery_status` | `ad_account_id*`, `campaign_id`, `ad_squad_ids`, `limit` (100) |
| `snapchat_ads.get_snapchat_ads` | Ads: status, `review_status`, `review_status_reasons`, `creative_id`, `render_type`, `delivery_status` | `ad_account_id*`, `campaign_id`, `ad_squad_id`, `ad_ids`, `limit` (100) |
| `snapchat_ads.get_snapchat_creatives` | Creatives: type, headline, brand name, call to action, `top_snap_media_id`, attachment (such as the web view URL) | `ad_account_id*`, `creative_ids`, `limit` (100) |
| `snapchat_ads.get_snapchat_media` | Media (videos, images, lenses, playables): type, `media_status` (`READY` or `PENDING_UPLOAD`), video or image details, usages | `ad_account_id*`, `media_ids`, `type` (`VIDEO`/`IMAGE`/`LENS_PACKAGE`), `limit` (100) |
| `snapchat_ads.get_snapchat_stats` | All performance; see below | see below |
| `snapchat_ads.get_snapchat_change_history` | One entity's changes: who, when, before and after | `entity_id*`, `entity_type*` (`campaign`/`ad_squad`/`ad`/`creative`), `limit` (50) |
| `snapchat_ads.get_snapchat_pixels` | The account's Snap Pixel and its status | `ad_account_id*` |
| `snapchat_ads.get_snapchat_targeting_geos` | Countries, or one country's regions, metros (DMAs) or ZIP codes | `level` (`country`/`region`/`metro`/`postal_code`), `country_code`, `limit` (1000) |
| `snapchat_ads.get_snapchat_interest_categories` | Snap Lifestyle Categories for one country | `country_code*`, `is_hec`, `limit` (1000) |

Every list returns `count` and `complete`, plus `status_counts` when its entities have a status. When `complete`
is false the listing stopped at `limit` or a page cap: say so, and don't call missing entities absent.

Never call `snapchat_ads.get_snapchat_signal_quality`, even though the pixel tool's description points to it. It's held
back until Snap approves showing signal readiness.

### `snapchat_ads.get_snapchat_stats`: the workhorse

| Argument | Values |
|---|---|
| `ad_account_id*` | the account |
| `level` | `ad_account` (default), `campaign`, `ad_squad`, `ad`; with `entity_id` for anything below the account |
| `granularity` | `DAY` (default, up to 366 days a call), `HOUR` (up to 31), `TOTAL` (one figure for the range), `LIFETIME` (no dates) |
| `start_date`, `end_date` | inclusive days in the account's timezone, `YYYY-MM-DD` |
| `breakdown` | `campaign` (on an account), `ad_squad` (on a campaign), `ad` (on anything above an ad) |
| `report_dimension` | `country`, `region`, `dma`, `country,os`, `gender`, `age`, `age,gender`, `os`, `os,country`, `make`, `lifestyle_category` |
| `fields` or `field_preset` | Snap metric names, or a preset: `delivery` (default: impressions, swipes, spend, video_views, screen_time_millis), `video`, `conversions` |
| `swipe_up_attribution_window` | `1_DAY`, `7_DAY`, `28_DAY` (default) |
| `view_attribution_window` | `none`, `1_HOUR`, `3_HOUR`, `6_HOUR`, `1_DAY` (default), `7_DAY` |
| `action_report_time` | `conversion` (default) or `impression` |
| `include_names` | adds each entity's name to breakdown rows |
| `omit_empty` | true by default: drops rows with no delivery |

Rules the tool enforces, and the ones it leaves to you:
- **A whole ad account reports spend only.** For anything else, use `breakdown="campaign"`.
- **Use `TOTAL` for one figure over a range.** Never add up DAY rows. For daily totals across entities, call DAY with
  no breakdown.
- **Reach comes only from `TOTAL`.** `uniques` and `frequency` (and `attachment_*`) are returned only that way. Never
  add them across rows.
- **`report_dimension` has limits.** It isn't served at HOUR, and only within one window: 31 days at DAY (30 when
  the range crosses a daylight-saving change where clocks go back), or a TOTAL. Snap's `35+` age bucket overlaps
  35-44, 45-54 and 55+; never add it to them.
- **Some data isn't final yet.** Delivery after `finalized_data_end_time`, and conversions after
  `conversion_data_processed_end_time`, can still change. The response's `notes` says so; pass that on to the user.

## Units

- **Money** (`spend`, `*_value`, budgets, bids) is in the account's currency units, already converted.
- **`swipe_up_percent` is a fraction, not a percent:** 0.0045 means 0.45%. Verified: swipes ÷ impressions gives the
  same 0.0045. Multiply by 100 to show a percent.
- **Time:** `*_millis` fields come back as hours (`screen_time_hours`, `view_time_hours`), and per-view averages as
  seconds (`avg_view_time_seconds`).
- **`frequency`** = impressions ÷ uniques (verified: 4,228,398 ÷ 2,483,104 = 1.70).
- **`conversion_purchases_value` can be 0** when the advertiser sends no values. Then ROAS is unavailable; never
  report a ROAS of 0.

## What's live: `delivery_status`, not `status`

`status: ACTIVE` only means not paused. Delivery is in `delivery_status`:
- **`["VALID"]`** is delivering;
- **`INVALID_*` codes** (for example `INVALID_END_TIME`, `INVALID_NOT_EFFECTIVE_ACTIVE`,
  `INVALID_NO_CREATIVE_EFFECTIVE_ACTIVE`) name why it isn't.

Report the codes as Snap gives them. Ads also carry `review_status` (`APPROVED`, or a pending or rejected state with
`review_status_reasons`).

## Result metric by optimization goal

Judge every ad squad on the metric its `optimization_goal` optimizes. Never add different events together, and never
compare cost per install with cost per purchase. All names below were accepted by Snap in a live call.

| `optimization_goal` | Result metric |
|---|---|
| `APP_INSTALLS` | `total_installs` (also `ios_installs`, `android_installs`) |
| `APP_SIGNUP`, `PIXEL_SIGNUP` | `conversion_sign_ups` |
| `APP_PURCHASE`, `PIXEL_PURCHASE`, `APP_REENGAGE_PURCHASE` | `conversion_purchases`; value `conversion_purchases_value` |
| `APP_ADD_TO_CART`, `PIXEL_ADD_TO_CART` | `conversion_add_cart` |
| `APP_REENGAGE_OPEN` | `conversion_app_opens` |
| `PIXEL_PAGE_VIEW` | `conversion_page_views` |
| `LANDING_PAGE_VIEW` | `landing_page_views` |
| `LEAD_FORM_SUBMISSIONS` | `native_leads` |
| `SWIPES` | `swipes` |
| `VIDEO_VIEWS` | `video_views` (2 seconds); `video_views_15s` for depth |
| `STORY_OPENS` | `story_opens` |
| `IMPRESSIONS` | `impressions` |
| `USES` | no single verified metric: report impressions and swipes, and say so |

Campaign objectives are in `objective_v2_properties` (for example `objective_v2_type: APP_PROMOTION`, `promotion_type:
APP_INSTALL`). `pacing_level: CAMPAIGN` means Smart Budgets: Snap sets the ad squad budgets from the campaign's.

## Not exposed

- **Frequency caps:** ad squads come back without their frequency-cap settings. Judge frequency from the `frequency`
  metric.
- **Audiences, catalogs and lead forms:** the connector doesn't read them. An ad squad's targeting shows its segment
  ids, and a lead ad's creative its `lead_generation_form_id`.
- **No account-wide change log:** `get_snapchat_change_history` takes one entity at a time, and history starts on
  16 July 2019.
- **Signal quality:** held back, as above.

## Applying changes (every Snapchat skill that offers it follows this)

Skills are analysis-first. "Act" always produces a change list: each change, its reason, its expected effect and its
risk. Applying it is a separate step.

**When:**
- Only when the user asks to apply.
- Only when `search` returns the Snapchat write tools (results with `read_only: false`), which means write access is
  on. Without them, say: "Write access is off for your workspace. Email access@bluealpha.ai to turn it on, then
  disconnect and reconnect BlueAlpha MCP so your assistant picks it up."

**What a skill may change, and the only fields it passes:**

| Change | Tool id | Arguments |
|---|---|---|
| Pause a campaign | `snapchat_ads.update_snapchat_campaign` | `ad_account_id`, `campaign_id`, `status: "PAUSED"` |
| Campaign budget | `snapchat_ads.update_snapchat_campaign` | `daily_budget` or `lifetime_spend_cap` |
| Smart Budgets target cost | `snapchat_ads.update_snapchat_campaign` | `shared_target_cost` |
| Rename a campaign | `snapchat_ads.update_snapchat_campaign` | `name` |
| Pause an ad squad | `snapchat_ads.update_snapchat_ad_squad` | `ad_account_id`, `ad_squad_id`, `status: "PAUSED"` |
| Ad squad budget | `snapchat_ads.update_snapchat_ad_squad` | the budget it already uses: `daily_budget` or `lifetime_budget` |
| Bid or bid strategy | `snapchat_ads.update_snapchat_ad_squad` | `bid`, `bid_strategy` (`AUTO_BID`, `LOWEST_COST_WITH_MAX_BID`, `TARGET_COST`) |
| Rename an ad squad | `snapchat_ads.update_snapchat_ad_squad` | `name` |
| Pause an ad | `snapchat_ads.update_snapchat_ad` | `ad_account_id`, `ad_id`, `status: "PAUSED"` |
| Rename an ad | `snapchat_ads.update_snapchat_ad` | `name` |

**Never:**
- delete, create, or set anything `ACTIVE` (that starts spend);
- change targeting, ad schedules, creatives or media.

The user does those in Ads Manager, or with the tools directly.

**How:**
1. **One change per `execute` call.** Before each, show the entity, the field, its value now and after, and why.
   Then wait for the user's yes.
2. **Snap's rules, checked before asking:**
   - In a Smart Budgets campaign (`pacing_level: CAMPAIGN`), change the campaign's budget, not an ad squad's.
   - Never pass a `bid` with `AUTO_BID`: Snap rejects it.
   - Budgets have minimums: $20 a day for a campaign and $5 a day for an ad squad in USD accounts, or the equivalent.
3. **Report the tool's `outcome` exactly.** It's one of `applied`, `applied_unverified`,
   `applied_with_unexpected_changes`, `partially_applied`, `not_applied` (Snap didn't make the change), `conflict`
   (the entity changed since it was read), `rejected` or `outcome_unknown`.
   - Stop on anything but `applied`, and never retry. An `outcome_unknown` means check in Ads Manager before
     anything else.
   - Show every warning the tool returns (budget changes over 20%, 30% and 50%; bid strategy changes) and never
     argue past one.
4. **Prove:** name when to re-run the skill and which metric should move.
