# Meta (Facebook) MCP Tool Reference — VERIFIED against the live BlueAlpha connector

> **Verified June 2026 on a live production account.** The BlueAlpha MCP exposes Meta under the
> **`facebook_ads_*`** namespace (NOT `meta_ads_*`). All Meta skills in this plugin use these
> exact tools. Meta data also appears as `platform="meta"` in `creative_fatigue_*`,
> `channel="meta"` in `incrementality_*`, and as a channel in `meridian_*` (MMM).

## Object hierarchy & IDs

Meta hierarchy is **ad account -> campaign -> ad set -> ad**. Ad account IDs are `act_<numeric>`
(e.g. `act_1380466552164808`). Campaign / ad set / ad IDs are bare numeric strings. Meta's
"ad set" == TikTok's "ad group".

## Tools (exact)

| Tool | Purpose | Key args |
|---|---|---|
| `facebook_ads_list_facebook_ad_accounts()` | List every Meta ad account the user can manage (incl. Business Manager / client access) | none |
| `facebook_ads_list_facebook_campaigns(ad_account_id)` | List campaigns (config: name, objective, status, daily_budget...) | `ad_account_id="act_<num>"` |
| `facebook_ads_list_facebook_ad_sets(campaign_id)` | List ad sets in a campaign | `campaign_id` (numeric) |
| `facebook_ads_list_facebook_ads(ad_set_id)` | List ads in an ad set | `ad_set_id` (numeric) |
| `facebook_ads_get_facebook_insights(object_id, level, breakdowns, date_preset OR time_range, action_attribution_windows, time_increment)` | THE performance read for any entity | see below |
| `facebook_ads_compare_facebook_insights(object_id, current_since, current_until, previous_since, previous_until, breakdowns, level, action_attribution_windows)` | Period-over-period deltas in one call | digests / fatigue trend |

### `facebook_ads_get_facebook_insights` — the workhorse
- `object_id` (required): `act_<num>` for an account; bare numeric for a campaign / ad set / ad.
- `level`: `"account" | "campaign" | "adset" | "ad"`. At `level="campaign"` on an account
  object_id you get one row per campaign; `level="ad"` returns per-ad rows (ad_id/ad_name).
- `breakdowns`: e.g. `["publisher_platform","platform_position"]`, `["age","gender"]`,
  `["country"]`, `["impression_device"]`. Each breakdown multiplies rate-limit cost.
- `date_preset` (default `last_30d`): `today | yesterday | last_7d | last_14d | last_30d |
  last_90d | this_month | lifetime`. Ignored if `time_range` is set.
- `time_range`: `{"since":"YYYY-MM-DD","until":"YYYY-MM-DD"}` (custom window; period-over-period
  and fatigue prior/recent windows).
- `action_attribution_windows`: e.g. `["1d_view","7d_click"]` (Meta default reporting).
- `time_increment`: `1` daily, `7` weekly, `"monthly"` — time-series / slope analysis.
- There is **no `fields` argument** — the tool returns a fixed metric set per row.

### Returned shape & parsing (critical)
- Top-level per row (strings — cast to float): `spend, impressions, clicks, ctr, cpm, cpc,
  reach, frequency`, plus breakdown keys and `campaign_name`/`adset_name`/`ad_name`.
- **Conversions are NOT top-level.** They live in `actions[]`, the object where
  `action_type == "purchase"` (or `offsite_conversion.fct_purchase` /
  `offsite_conversion.fb_pixel_purchase` / `onsite_web_app_purchase` / `lead` depending on
  setup/objective). Revenue is in `action_values[]` for the same `action_type`.
  **Resolve the objective-correct action_type before computing CPA/ROAS — do not sum all actions.**
- CPA = spend / purchases. ROAS = purchase_value / spend. `frequency` = impressions / reach.

### IMPORTANT — large responses
`get_facebook_insights` rows carry a large `actions`/`action_values` array each, so account-
wide pulls (esp. `level="ad"`, or any `breakdowns`) routinely **exceed the chat token limit and
are saved to a file**. When that happens, process the file with jq/python — ideally in a
**subagent (Agent tool)** — and return only the ranked/aggregated slice. Do not read the raw
file into context. To keep payloads small: scope `object_id` to a specific campaign / ad set,
use a shorter `date_preset`, or read per-campaign then drill down.

## What is NOT exposed (verified)
- No Advantage+/ASC config flags on the campaign list (objective + budget only). `meta-advantage-plus-audit`
  can compute the economics but cannot auto-detect ASC / Advantage+ Audience / Advantage+
  Creative from the read tools — needs config fields exposed or a manual check.
- No pixel/CAPI config (EMQ, AEM 8-event order, dedup, SKAN). `meta-capi-signal-health` does a
  data-symptom read and leaves the config layer as an Events Manager checklist.
- No write/execution tools — analysis only; execution routes through the BlueAlpha pipeline.
