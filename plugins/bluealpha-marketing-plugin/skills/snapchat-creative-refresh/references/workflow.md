# Snapchat Creative Refresh: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`. Run tools with `search`, then `execute`, passing
> `user_message` every time, and batch independent reads into one `execute(calls=[...])`.

Turns a Snapchat account's winning ads into a brief for the next ones. The Snapchat counterpart of
`tiktok-creative-refresh` and `meta-creative-refresh`. Analysis only: making and uploading the ads is the user's
step, in Ads Manager or with the Snapchat write tools.

## Phase 1: Confirm a refresh is needed

Use `snapchat-creative-fatigue-watchdog`'s output if it ran. Otherwise check quickly. A refresh is due when:
- an ad squad has fewer than 3 delivering ads (`delivery_status: ["VALID"]`);
- its top spenders' swipe rate fell 25% or more against the prior window;
- or every delivering ad shares one format or one message.

If none apply, say so and stop: a refresh against healthy creative burns budget on tests.

## Phase 2: Audit the winners

1. **Pull 30-90 days per ad** for the live campaigns:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_stats", arguments={ad_account_id, level: "campaign",
     entity_id: <live id>, granularity: "TOTAL", start_date: <30-90 days ago>, end_date: <yesterday>,
     breakdown: "ad", include_names: true,
     fields: ["spend", "impressions", "swipes", "video_views", "video_views_15s", "view_completion",
              "avg_view_time_millis", <result metric>]})
   ```
   Paused ads count too: past winners are evidence.

2. **Rank within each ad squad** by cost per result on its goal's metric. Only rank ads with enough spend to judge,
   for example at least 3 times the ad squad's median cost per result. Take the top 3-5 and the bottom 3.

3. **Read what they show.** Batch the creatives, then their top snap media:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_ads", arguments={ad_account_id, ad_ids: [...]})
   execute(tool_id="snapchat_ads.get_snapchat_creatives", arguments={ad_account_id, creative_ids: [...]})
   execute(tool_id="snapchat_ads.get_snapchat_media", arguments={ad_account_id, media_ids: [...]})
   ```
   Fields that matter:

   | From the creative | From the media |
   |---|---|
   | `type`, `headline`, `brand_name`, `call_to_action`, `forced_view_eligibility`, `shareable`, `ad_product`, attachment (such as the app or web view) | `type` (`IMAGE`/`VIDEO`), `duration_in_seconds`, `image_metadata` or `video_metadata` (width and height), `file_size_in_bytes` |

   Ad names often carry the concept (for example "UGC", "Static", a hook name); use them, but say they're names.

4. **Profile the winning DNA against the losers:**
   - image or video, and the length that wins;
   - the headline and value proposition that wins;
   - the call to action;
   - six-second forced view or none;
   - full 1080×1920 or lower-resolution files;
   - user-made (UGC-style) or produced, from names and media.

   For video, read where people drop with the quartile counts. A big fall from 2-second views to the first quartile
   is a weak opening.

## Phase 3: The brief (five concepts)

Ground every concept in this account's winners. Snap's own published guidance (Snap's "golden rules", 2018) is the
frame:
- top snaps of five seconds or less, where the first two seconds matter most;
- a clear action;
- one message per ad;
- purposeful sound ("almost 60%" of Snapchatters had sound on).

Where the account's winners disagree, such as longer videos that win, say so and follow the account's evidence.

For each concept:
- name and angle;
- format: image or video, its length, full-screen 9:16 at 1080×1920;
- the first two seconds, or for an image what reads in one glance;
- the single message, and the headline (34 characters at most);
- sound, for video;
- the call to action;
- forced view (six seconds) or not;
- the fatigue it answers: a new opening for a tired one, a new angle for a worn message, or a new format.

Make 1-2 of the five a real departure, a new angle or format, not a reskin. That's how a test finds a new winner
instead of a slower decline.

Other Snapchat formats to consider when they fit:
- story ads, for several snaps of one message;
- collection ads, if there's a catalog (`snapchat-dynamic-ads-audit`);
- AR lenses, which are a bigger production.

## Phase 4: Test and rollout

- Put new ads into the ad squad that needs them, 2-4 at a time, next to its current best ad as the control.
- Judge after 7 days, and at least 50 results or 100,000 impressions per new ad, whichever comes later, on cost per
  result and swipe rate.
- Promote a winner by keeping it delivering, and pause the losers. Pausing needs write access and follows
  "Applying changes" in the tool reference.
- Re-run `snapchat-creative-fatigue-watchdog` in 14 days.

## Output

1. Refresh verdict: needed or not, and why.
2. Winning DNA: a table of the top and bottom ads with their attributes and economics.
3. Five-concept brief.
4. Test plan: which ad squad, how many at a time, success criteria, and when to read.

## Important notes

- **Evidence over taste.** Every concept cites the winner it builds on or the gap it fills.
- **Snap's guidance is dated (2018).** Use it as a frame, not a rule, and let the account's results decide.
- **Don't refresh on one bad day.** Conversions for the last day or two aren't final (Snap's `notes`).
- **Creative changes go back to review.** Editing a live creative pauses its ads until Snap approves it again, so
  new concepts go into new ads.
