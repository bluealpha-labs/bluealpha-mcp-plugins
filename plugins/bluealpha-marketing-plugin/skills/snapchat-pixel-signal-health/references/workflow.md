# Snapchat Pixel Signal Health: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Signal and attribution" section. Run tools
> with `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

Whether Snapchat's reported conversions can be trusted before any skill acts on them. The Snapchat counterpart of
`meta-capi-signal-health`.

**Read this first.** Snapchat counts conversions from the Snap Pixel (web), the Conversions API (server), and, for
apps, the Snap App ID with a mobile measurement partner (MMP). It credits them with 28-day swipe and 1-day view
attribution by default. The tools show the pixel, the app setup and the numbers. Events Manager's diagnostics aren't
read, so they become a checklist in Phase 4.

## Phase 1: The setup Snapchat shows

1. **Pixels:**
   ```
   execute(tool_id="snapchat_ads.get_snapchat_pixels", arguments={ad_account_id})
   ```
   Note each pixel's `status`, and who owns it (an `ad_account_id`, or only an `organization_id`). Where present, note
   `automatic_pii_collection` and `automatic_event_opt_in`. Older pixels don't return them, so their absence doesn't
   mean off.
2. **What each live ad squad optimizes on:** its `optimization_goal`, and `event_sources`, the pixel or app that
   reports its event (`MOBILE_APP` with the Snap App ID for apps). Flag an ad squad whose event source isn't one of
   the account's `ACTIVE` pixels or its app.
3. **App campaigns:**
   - the campaign's `measurement_spec` holds the store app ids, and `mobile_app_properties` holds the Snap App ID
     (`mobile_app_id`), `skad_network_status` and `app_optimization_type`;
   - each ad squad's `skadnetwork_properties.status` says whether it's enrolled in SKAdNetwork.
   An iOS app campaign that isn't enrolled is a question for the user: intended, or a gap?

## Phase 2: Symptoms in the numbers

1. **The daily trend,** per live campaign, on each ad squad's goal metric, for the last 30 days:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={ad_account_id, level: "campaign",
     entity_id: <id>, granularity: "DAY", start_date: <30 days ago>, end_date: <yesterday>,
     fields: ["spend", "swipes", <result metric>, "conversion_purchases_value"]})
   ```
   - **A cliff:** results fall to near zero while spend holds. The event stopped reaching Snap: a site release, a tag
     manager change or an app SDK update. Find the day.
   - **Spend with no results** on a pixel or app goal: the event isn't firing, or fires under another name.
   - **A jump** with flat spend: double counting (pixel and Conversions API without deduplication) or a newly mapped
     event.
   - DAY series skip days with no delivery; a missing day isn't a cliff.
2. **Values.** `conversion_purchases_value` at 0 while purchases come in means no value is sent: ROAS is unavailable,
   and Snap can't optimize for value.
3. **How much comes from view-through.** Read the same 14 days, ending before `conversion_data_processed_end_time`,
   under four settings:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <id>,
       granularity: "TOTAL", start_date: <start>, end_date: <end>, fields: ["spend", <result metric>]}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, swipe_up_attribution_window: "28_DAY",
       view_attribution_window: "none"}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, swipe_up_attribution_window: "7_DAY",
       view_attribution_window: "none"}},
     {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, swipe_up_attribution_window: "1_DAY",
       view_attribution_window: "none"}}
   ])
   ```
   - **View-through share** = 1 − (28-day swipe, no view) ÷ (the default).
   - When most results come from view-through, Snapchat's cost per result is far better than any click-based count
     will show. Say so plainly, and route budget decisions through the MMM or a holdout (`snapchat-incrementality-test`).
   - The swipe-only figures are closer to what most analytics tools count; use them when comparing with the client's
     numbers.
4. **By operating system,** for accounts on both iOS and Android: results and spend by `os`. An iOS cost per result
   far worse than Android's points at the iOS signal gap (App Tracking Transparency, SKAdNetwork). Skip it for
   single-OS accounts.
5. **Volume:** results a week for each optimizing ad squad, on its goal. Thin volume makes Snap's optimization
   unstable; hand that to `snapchat-auto-optimize` (consolidation).

## Phase 3: Cross-check against the client's own numbers

- `search` for the client's warehouse or platform history ("platform history by day") and the MMM ("MMM channel ROI").
  Otherwise, ask for the backend count (orders, sign-ups, the MMP's purchases) for the same days.
- **Snap well above the backend:** double counting, or view-through credit. Compare the backend with the swipe-only
  figures before calling it double counting.
- **Snap well below:** events missing, or not matched to Snapchat users (Phase 4, items 1, 2, 4 and 5).

## Phase 4: The Events Manager checklist

What the tools can't read. Mark each item confirmed, needs a check, or broken:
1. **Snap Pixel** on every key page, firing the events the ad squads optimize on. Events Manager shows the events
   received.
2. **Conversions API** sending the money events from the server, with the right `action_source` (`WEB`,
   `MOBILE_APP` or `OFFLINE`).
3. **Deduplication:** the same id on the pixel's `client_dedup_id` and the Conversions API's `event_id` (for
   purchases, the `transaction_id` can serve). Snap deduplicates within 48 hours. Without it, pixel and server events
   count twice.
4. **Match keys:** hashed email (`em`) and phone (`ph`), `client_ip_address`, `client_user_agent`, Snap's click id
   (`sc_click_id`) and cookie (`sc_cookie1`), and `madid` for apps. More keys mean more conversions matched to
   Snapchat users.
5. **Event Quality Score,** per event and source in Events Manager. A low score on the money event means conversions
   are under-counted.
6. **Value and currency** (`value`, `currency`) on purchase events.
7. **Apps:**
   - a Snap App ID linked to the store app ids;
   - the MMP chosen to receive Snap's postbacks;
   - SKAdNetwork conversion values mapped to Snap events in the MMP;
   - iOS ad squads opted in to SKAdNetwork where intended.

## Phase 5: Verdict

- **Trust verdict:** trusted, trusted with caveats, or not trusted, and why.
- **Critical:** spend with no results on the optimized event, a results cliff, or double counting. Every cost per
  result is wrong until fixed.
- **High:**
  - deduplication not confirmed;
  - no purchase values;
  - results mostly from view-through with no MMM or test behind the budget.
- **Medium:**
  - few match keys;
  - iOS app spend without SKAdNetwork where the user expects it.

**Applying.** Analysis only. Measurement is fixed in Events Manager, the site, the app or the MMP; the skills don't
change it.

## Output

1. **Trust verdict,** in one line.
2. **Setup:** pixels, event sources per ad squad, app and SKAdNetwork status.
3. **Symptoms:** trend findings with dates, values, view-through share, OS gap, volume.
4. **Cross-check** against the client's numbers, or what to ask for.
5. **Checklist,** each item marked.
6. **Fix list,** Critical first.
7. **Gating note:** until Critical items are fixed, every Snapchat cost per result in the other skills is unreliable.

## Important notes

- **This skill gates the others.** Run it first whenever conversion numbers are in doubt.
- **Signal quality isn't read.** Snap's signal readiness is held back (see the reference), so Event Quality Score is
  a checklist item, never a number this skill reports.
- **View-through isn't wrong, but it isn't proof.** A high share is a reason to test, not to cut.
- **Say what was verified in data** and what needs an Events Manager check.
