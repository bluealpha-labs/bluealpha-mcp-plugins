# Snapchat Lead Gen Auditor: Detailed Workflow

> **Tool bindings are verified.** Use the exact tool ids, arguments and units in
> `snapchat-auto-optimize/references/snapchat-mcp-tools.md`, including its "Catalogs, dynamic ads and lead ads"
> section. Run tools with `search`, then `execute`, passing `user_message` every time, and batch independent reads
> into one `execute(calls=[...])`.

Lead form setup and lead flow for Snapchat Lead Generation ads. The Snapchat counterpart of
`linkedin-lead-form-quality-auditor`.

**Read this first.** The tools return the forms and where their leads are sent, never the leads. Lead quality is a
manual check, listed in Phase 5.

## Phase 1: The lead gen surface

1. **The forms:**
   ```
   execute(tool_id="snapchat_ads.get_snapchat_lead_gen_forms", arguments={ad_account_id})
   ```
   With none, say the account has no lead forms and stop. When `complete` is false, say the list was cut off.
2. **The lead ads.** For each live campaign (`status: "ACTIVE"`), read its ad squads, ads and their creatives. A lead
   ad's creative has `type: "LEAD_GENERATION"` and names its form in `lead_generation_form_id`. Build the map of form
   to ads, and note each lead ad squad's `optimization_goal`.
3. **Where each form's leads go,** for every form a live ad uses and every `ACTIVE` form, batched:
   ```
   execute(calls=[
     {tool_id: "snapchat_ads.get_snapchat_lead_gen_webhooks", arguments: {ad_account_id,
       lead_generation_form_id: <id>}}
   ])
   ```
   Snap allows one webhook per form. Show only the webhook URL's host; a URL can carry a token.

## Phase 2: Lead flow

| Finding | What it means |
|---|---|
| A live ad's form has no webhook | Leads wait in Ads Manager until someone downloads them. Ask how they reach the CRM; slow follow-up loses leads |
| The webhook host is a test or catch-all service | Leads go somewhere nobody works them; confirm it's intended |
| An `ACTIVE` form no live ad uses | Tidy-up |
| One form used by ads in different campaigns | Leads arrive mixed; fine if intended, but campaign-level lead quality can't be told apart in the CRM |

## Phase 3: Ads and cost per lead

For each live campaign with lead ads, two 14-day windows:
```
execute(calls=[
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {ad_account_id, level: "campaign", entity_id: <id>,
    breakdown: "ad", granularity: "TOTAL", start_date: <28 days ago>, end_date: <15 days ago>,
    fields: ["spend", "impressions", "swipes", "native_leads"], include_names: true}},
  {tool_id: "snapchat_ads.get_snapchat_stats", arguments: {<same>, start_date: <14 days ago>,
    end_date: <yesterday>}}
])
```
For each lead ad:
- **Cost per lead** = spend ÷ `native_leads`, for ads with at least 5 leads in the window; fewer is too noisy to rank.
- **Leads per swipe** = `native_leads` ÷ swipes. On a lead ad, a swipe opens the form, so this approximates the form's
  completion rate. Compare it across forms: a low one points at the form, a low swipe rate at the creative.
- **Classify:**

| Class | When |
|---|---|
| **Spend without leads** | Spend over 3 times the account's cost per lead (or over 50 in the account's currency when there's none yet) and 0 leads. Check the ad's `review_status`, the form's `status`, and the ad squad's goal |
| **Declining** | Recent leads under half the earlier window's, with at least 10 earlier |
| **Too new** | Created in the last 7 days; don't judge it |
| **Low delivery** | Under about 1,000 impressions in the window; a delivery problem, not a form problem |
| **Healthy** | Leads coming in, no decline |

- **Goal match.** A lead ad in an ad squad whose `optimization_goal` isn't `LEAD_FORM_SUBMISSIONS` is bought for
  another result (often swipes). Judge it on that goal's metric, and say that switching the goal is the usual fix.

## Phase 4: Form friction

For each form a live ad uses:
- **Questions:** count `form_fields` and list their types. Every question beyond the contact details costs
  completions. Where cost per lead is high or leads per swipe is low, name the questions that could go.
- **Volume or intent:** `strategy_type` (for example `MORE_VOLUME`). Read it next to cost per lead and the lead
  quality the user reports: a volume setting with poor leads, or an intent setting with too few, is the trade-off
  to revisit.
- **Trust and follow-through:** a `privacy_policy_url` on the advertiser's own domain; `legal_disclosures` where the
  industry needs them; a `default_end_page` with a call to action and URL, so the person has somewhere to go next.

## Phase 5: Manual checks

What the tools can't see, for the user to check:
- **Lead quality:** sample recent leads in Ads Manager or the CRM for fake details, duplicates and odd timing.
- **The CRM link:** send a test lead through the webhook and confirm it lands in the CRM.
- **Downstream results:** from the CRM, how many leads become qualified leads and customers, by campaign. Cost per
  lead alone rewards cheap, poor leads.

**Applying.** Analysis only. Pausing ads, editing forms and setting up webhooks are recommendations for Ads Manager;
this skill doesn't make them.

## Output

1. **Summary:** lead ads live, forms in use, leads and cost per lead over the last 14 days.
2. **Lead flow:** each form, the ads using it, and its webhook host, or "none".
3. **Ads:** spend, swipes, leads, cost per lead, leads per swipe, class.
4. **Form friction:** questions, setting, end page and policy findings per form.
5. **Manual checklist.**

## Important notes

- **Leads are never read,** so lead quality is always the manual check, never a guess.
- **`native_leads` counts form submissions,** not good leads.
- **Paused campaigns collect no leads,** so only live campaigns are judged.
- **Never call a missing webhook a broken setup** without asking: some teams download leads on purpose.
