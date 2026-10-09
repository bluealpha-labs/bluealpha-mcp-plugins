# Snapchat Ad Review Auditor: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Ad review and media" section. Run tools
> with `search`, then `execute`, passing `user_message` every time, and batch independent reads into one
> `execute(calls=[...])`.

Which Snapchat ads Snap has rejected or is still reviewing, why, and what to fix; and which live creatives and media
miss Snap's specs. Snapchat-specific: the connector reads Snap's review status and reasons on every ad and creative.

**Read this first.**
- **A rejected ad doesn't deliver,** and an ad squad with no approved ad can't deliver at all.
- **Snap's reasons are the fix list.** `review_status_reasons` says what to change, in Snap's words. Quote them.
- **Analysis only.** Fixes happen in Ads Manager: edit and resubmit, or build a new creative. This skill changes
  nothing.

## Phase 1: Read

1. **The account:** `get_snapchat_ad_account` for its timezone and `regulations`.
2. **The live structure:** campaigns with `status: "ACTIVE"`, then per campaign its ad squads and ads
   (`get_snapchat_ad_squads` and `get_snapchat_ads` with `campaign_id`). Note each live ad squad's
   `targeting.regulated_content`.
3. **The rest of the account's ads,** for rejections outside the live campaigns:
   ```
   execute(tool_id="snapchat_ads.get_snapchat_ads", arguments={ad_account_id, limit: 1000})
   ```
   A long-running account can hold hundreds of ads, so process the response by script, as the reference's "Large
   responses" section says. When `complete` is false, the list is partial; say so.
4. **Creatives and media** for every ad in a live ad squad, and every rejected or pending ad, batched:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_creatives", arguments: {ad_account_id, creative_ids: [<ids>]}},
     {tool_id: "snapchat_ads.get_snapchat_media", arguments: {ad_account_id, media_ids: [<top_snap_media_id>s]}}
   ])
   ```
   The media ids come from the creatives, so this is two steps when the creatives aren't read yet.

## Phase 2: Review status

Sort every ad that isn't `APPROVED`, and every ad whose `delivery_status` includes `INVALID_CREATIVE_PROFILE_DELETED`:

| Tier | What | Why it matters |
|---|---|---|
| **Blocking** | An active ad squad in a live campaign with no approved, active ad | It can't deliver |
| **Fix now** | A rejected ad that's active in a live ad squad | One fewer ad in rotation, and its creative may fail elsewhere |
| **Stuck** | Pending for over 24 hours since the later of the ad's and its creative's `updated_at` (a creative edit can send its ads back to review) | Snap reviews most ads within 8 hours and asks to allow about 24 |
| **Clean up** | Any of these in an ad squad or campaign that's off, including approved ads whose Public Profile was deleted | No delivery now; fix it before turning it back on |

For each rejected ad:
- **Snap's reasons, verbatim.** Group ads with the same reason: one fix often covers many.
- **Its creative,** with the creative's own `review_status_details` when set, and every other ad that uses the same
  creative. Editing the creative changes it on all of them.
- **The fix,** as the reason states it.

**Housing, credit and employment (HEC).** Two of Snap's rejection reasons are about the account and the targeting,
not the creative:
- **The vertical isn't declared** ("needs to be reflected in Ads Manager"). Check the account's
  `regulations.restricted_delivery_signals`: Snap requires it to be true for HEC ads, and once true it can't be
  turned off. On an approved credit advertiser, the account's flag and the live ad squads'
  `targeting.regulated_content` are both true. In Ads Manager, it's the account's Housing, Credit and Employment
  setting and the campaign's checkbox, as Snap's reason says.
- **Targeting too specific.** Snap's reason says ads for products such as loans or credit may not be targeted on
  gender, age or a specific location. Broaden the ad squad's targeting as it says, then resubmit. A whole-country,
  18-and-over audience was approved on a credit advertiser.

## Phase 3: Live creatives and media against Snap's specs

Snap's specs for a single image or video ad (Snap Business Help, checked October 2026):
- **Shape and size:** 9:16, at 1080×1920. Images at least 720×1280.
- **Video:** .mp4 or .mov, H.264, 3 seconds to 30 minutes, up to 1 GB. Under 3 seconds, Snap loops it to 3.
- **Image:** .jpg or .png, up to 5 MB. Snap shows it as a 5-second video.
- **Headline:** up to 34 characters. **Brand name:** up to 32, the paying advertiser, and not the same as the headline.
- **Audio:** 2 balanced channels, about -16 LUFS, PCM or AAC, at least 192 kbps.

On live creatives and their media:

| Check | Field | Flag when | Tier |
|---|---|---|---|
| Creative packaged | creative `packaging_status` | anything but `SUCCESS` | Check in Ads Manager: every delivering creative read was `SUCCESS` |
| Public Profile | the ad's `delivery_status` | it includes `INVALID_CREATIVE_PROFILE_DELETED` | Blocking |
| Media ready | `media_status` | anything but `READY` | Blocking |
| Shape | `width_px` ÷ `height_px` in `video_metadata` or `image_metadata` | not 9:16 (0.5625) | Fix: re-export at 9:16 |
| Size | `width_px`, `height_px` | under 1080×1920 | Improve |
| Video length | `duration_in_seconds` | under 3 | Improve: it plays on a loop |
| File size | `file_size_in_bytes` | a video over 1 GB, or an image over 5 MB | Fix |
| Text length | `headline`, `brand_name` | a headline over 34 characters, or a brand name over 32 | Fix |
| Brand | `brand_name`, `headline`, `profile_properties` | the brand name equals the headline, or there's neither a brand name nor a Public Profile | Fix |

A creative without a `brand_name` but with a Public Profile (`profile_properties.profile_id`) is fine: Snap shows the
profile's name instead.

## Phase 4: What the tools can't see

A short checklist for the user:
- **The content:** text and logos clear of Snapchat's interface (Snap's safe zones), and any claims or disclosures
  the product category needs.
- **Audio:** the loudness fields come back empty, so check the audio spec above at export.
- **The brand name** names the paying advertiser.
- **The destination:** the app store page or website matches what the ad promises.

## Output

1. **Review summary:** ads by review status, in the live campaigns and across the account, and whether the account
   list is complete.
2. **Blocking and fix now:** each ad, its ad squad, Snap's reasons verbatim, the fix, and the other ads that share
   its creative.
3. **Stuck reviews,** with how long each has been pending.
4. **Clean up:** counts by reason, not every ad.
5. **Spec findings** for the live creatives and media.
6. **The manual checklist.**

## Important notes

- **Edits send ads back to review.** Changing a brand name, headline or web view URL can trigger a new review, and an
  ad doesn't deliver while it's in review. Keep at least one approved ad running in each live ad squad while the
  others are fixed.
- **A rejection that looks wrong** can be contested with Snap, through the link in Snap's help on rejected ads.
- **Hand-offs:** active ads not delivering for other reasons → `snapchat-auto-optimize`; replacing a rejected
  creative → `snapchat-creative-refresh`.
- **Cadence:** after new ads go up, and again a day later if any are still pending.
