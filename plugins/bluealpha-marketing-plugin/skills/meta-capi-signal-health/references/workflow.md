# Meta CAPI & Signal Health — Detailed Workflow

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



Every Meta CPA/ROAS number is only as good as the conversion signal feeding it. Post-iOS14,
that signal is a stack: browser **pixel** + server-side **Conversions API (CAPI)**, joined by
**deduplication**, scored by **Event Match Quality (EMQ)**, constrained on web by **Aggregated
Event Measurement (AEM)**'s 8 prioritized events, and on iOS app by **SKAN**. If this stack is
broken, no amount of optimization fixes the account — and the platform numbers other skills
read are fiction. Run this FIRST when conversion trust is in question. No TikTok/Google
analogue (this is Meta's specific post-ATT measurement architecture).

This skill is part live-data, part configuration audit. Configuration items that the MCP can't
read are surfaced as a manual checklist for Events Manager.

## Phase 1: Symptom read from the data (facebook_ads_*)

Pull conversions and cost-per-result trends to spot signal breakage:
```
facebook_ads_get_facebook_insights(object_id=<act_id>, level="account",
  fields=["spend","impressions","actions","action_values","cost_per_action_type"],
  breakdowns=["publisher_platform"], time_range={last_30d_vs_prior})
```
Signal-breakage tells:
- **Conversions cliff** at a date with flat spend → pixel/CAPI break or AEM/domain change.
- **iOS conversions implausibly low** vs Android/desktop → SKAN/AEM coverage gap (expected to
  a degree; quantify it).
- **Reported conversions far below backend truth** → dedup or CAPI coverage problem (compare to
  the client's actual order count if available).
- **Cost-per-result volatile / missing** for the priority event → event not firing or not
  prioritized in AEM.

## Phase 2: The configuration checklist (manual — Events Manager / pipeline)

The MCP generally cannot read pixel/CAPI config; produce this as a validation checklist and
ask the user to confirm (or pull via the BlueAlpha pipeline if exposed):

1. **CAPI live & deduplicated** — is server-side CAPI sending the key events? Is every event
   sent by both pixel and CAPI sharing an `event_id` + matching `event_name` so Meta
   deduplicates? (No dedup = double-counting; no CAPI = under-counting post-iOS.)
2. **Event Match Quality (EMQ)** — score per key event (target ≥ ~6.0/"Good"+). Low EMQ = Meta
   can't match conversions to users = under-reported, worse optimization. Improve by sending
   more/cleaner customer parameters (email, phone, fbc/fbp, IP, UA) hashed via CAPI.
3. **Aggregated Event Measurement (AEM)** — is the domain verified? Are the **8 events
   prioritized** with the real money event (purchase) at the top? Only the top-priority event
   counts for an iOS web conversion; misordered priorities silently lose conversions.
4. **Attribution setting** — confirm the ad-set `attribution_spec` (default 7-day click /
   1-day view). Note it on every downstream CPA/ROAS read; a 1-day-click setting will look
   "worse" but isn't necessarily.
5. **iOS / SKAN** — for app campaigns, is SKAN configured (conversion schema/values)? Expect
   reporting delay and modeling; never read iOS app CPA at face value.
6. **Domain & data sharing** — domain verification present, no recent pixel/domain migration,
   data-sharing/consent settings intact.

## Phase 3: Diagnose & prioritize

Rank issues by conversion impact:
- **Critical:** CAPI absent or undeduplicated; AEM priority event wrong; domain unverified —
  these corrupt every number and every optimization decision.
- **High:** EMQ "Poor/OK" on the money event; large unexplained iOS gap.
- **Medium:** attribution-window mismatch with how the business thinks about conversions;
  minor parameter coverage gaps.

## Phase 4: Output

1. **Signal health verdict** — can Meta's reported conversions be trusted right now? (Y/N + why)
2. **Data symptoms** — conversion trends/cliffs, iOS gap quantified, dedup/coverage flags.
3. **Configuration checklist** — CAPI/dedup, EMQ, AEM 8-event order, attribution, SKAN, domain,
   each marked confirmed / needs-check / broken.
4. **Prioritized fix list** — Critical/High/Medium with the conversion impact of each.
5. **Gating note for other skills** — until Critical items are fixed, every platform CPA/ROAS
   read (auto-optimize, performance-digest, audience, advantage-plus) is unreliable; lean on
   MMM/incrementality and re-run those skills after the signal is fixed.

## Important Notes

- **This skill gates the others.** Broken signal means broken CPA/ROAS means broken
  optimization. When trust is in doubt, run this before acting on any Meta efficiency number.
- **EMQ is the quiet killer.** An account can look "fine" while low EMQ under-reports
  conversions and starves the optimizer of the matches it needs.
- **CAPI without deduplication is worse than no CAPI** — it double-counts and corrupts CPA.
  Always verify shared `event_id`.
- **The iOS gap is real and partly unfixable** — quantify it, model around it, and use
  incrementality (`meta-incrementality-test`) / MMM for iOS-heavy accounts rather than chasing
  platform parity.
- **Much of this is config the API won't expose** — be explicit about what was data-verified vs
  what needs an Events Manager check, and route deeper diagnosis through the BlueAlpha pipeline.
