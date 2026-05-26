#!/usr/bin/env python3
"""LinkedIn Lead Form Quality Auditor."""
import json
import sys
from collections import defaultdict


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


def parse_creative_id(urn):
    return urn.replace("urn:li:sponsoredCreative:", "")


def parse_campaign_id(urn):
    return urn.replace("urn:li:sponsoredCampaign:", "")


def index_analytics(resp):
    out = {}
    for row in resp.get("elements", []):
        cid = parse_creative_id(row["pivotValues"][0])
        out[cid] = {
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "lp_clicks": int(row.get("landingPageClicks", 0)),
            "cost": float(row.get("costInLocalCurrency", 0)),
            "leads": int(row.get("oneClickLeads", 0)),
        }
    return out


def creative_label(c):
    name = c.get("name", "").strip()
    if name:
        return name
    return f"id:{parse_creative_id(c.get('id', ''))}"


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    creatives_resp = load(sys.argv[1])
    campaigns_resp = load(sys.argv[2])
    prior_resp = load(sys.argv[3])
    recent_resp = load(sys.argv[4])

    # Campaign status map
    campaign_status = {}
    campaign_name = {}
    for c in campaigns_resp.get("elements", []):
        cid = str(c.get("id"))
        campaign_status[cid] = c.get("status")
        campaign_name[cid] = c.get("name", f"id:{cid}")

    prior = index_analytics(prior_resp)
    recent = index_analytics(recent_resp)

    # Filter to Lead Gen creatives in ACTIVE campaigns
    leadgen_creatives = []
    form_usage = defaultdict(list)  # form_urn -> [creatives]
    for c in creatives_resp.get("elements", []):
        lgcta = c.get("leadgenCallToAction") or {}
        form_urn = lgcta.get("destination")
        if not form_urn:
            continue
        campaign_id = parse_campaign_id(c.get("campaign", ""))
        if campaign_status.get(campaign_id) != "ACTIVE":
            continue
        cid = parse_creative_id(c.get("id", ""))
        record = {
            "id": cid,
            "name": creative_label(c),
            "campaign_id": campaign_id,
            "campaign_name": campaign_name.get(campaign_id, "?"),
            "form_urn": form_urn,
            "is_serving": c.get("isServing", False),
            "intended_status": c.get("intendedStatus"),
            "created_at": c.get("createdAt", 0),
            "prior": prior.get(cid, {}),
            "recent": recent.get(cid, {}),
        }
        leadgen_creatives.append(record)
        form_usage[form_urn].append(record)

    if not leadgen_creatives:
        print("# LinkedIn Lead Form Quality Audit\n\nNo Lead Gen creatives found in active campaigns. ✅")
        return

    # Classify
    spend_no_leads = []
    declining = []
    dormant = []
    healthy = []
    too_new = []

    for c in leadgen_creatives:
        if c["intended_status"] not in ("ACTIVE",) and not c["is_serving"]:
            continue
        rec = c["recent"]
        pri = c["prior"]
        # 7-day age guardrail
        # (Note: this is approximate — we'd need actual timestamps to do this right)
        if rec.get("impressions", 0) == 0 and pri.get("impressions", 0) == 0:
            continue
        if rec.get("impressions", 0) == 0 and pri.get("impressions", 0) > 0:
            dormant.append(c)
            continue
        if rec.get("cost", 0) > 50 and rec.get("leads", 0) == 0:
            spend_no_leads.append(c)
            continue
        if rec.get("leads", 0) > 0 and pri.get("leads", 0) >= 5 and rec.get("leads", 0) < 0.5 * pri.get("leads", 0):
            declining.append(c)
            continue
        healthy.append(c)

    # Cost-per-lead leaderboard (creatives with >= 3 leads in recent)
    cpl_candidates = [c for c in leadgen_creatives if c["recent"].get("leads", 0) >= 3]
    for c in cpl_candidates:
        c["cpl"] = c["recent"]["cost"] / c["recent"]["leads"]
    cpl_candidates.sort(key=lambda c: c["cpl"])

    # ===== Output =====
    out = []
    out.append("# LinkedIn Lead Form Quality Audit")
    out.append("")
    out.append(
        f"**{len(leadgen_creatives)} Lead Gen creatives in active campaigns. "
        f"{len(form_usage)} unique Lead Gen Form URNs in use.**"
    )
    out.append("")

    # 🔴 Spend without leads
    out.append("## 🔴 Spend without leads")
    out.append("")
    if spend_no_leads:
        for c in spend_no_leads:
            out.append(
                f"- **{c['name']}** (campaign: {c['campaign_name']}, form: `{c['form_urn']}`)"
            )
            out.append(
                f"  - Recent 14d: {fmt_money(c['recent']['cost'])} spent, "
                f"{c['recent']['impressions']:,} impressions, {c['recent']['clicks']} clicks, "
                f"**0 leads**."
            )
            out.append(
                "  - **Action:** Open the form in Campaign Manager and verify it's active and "
                "approved. If approved, test the form submission flow manually. If the form is "
                "fine, the creative or audience is the issue."
            )
    else:
        out.append("No Lead Gen creatives with significant spend and zero leads. ✅")
    out.append("")

    # 🟠 Declining
    out.append("## 🟠 Declining lead volume")
    out.append("")
    if declining:
        for c in declining:
            decay = (c["prior"]["leads"] - c["recent"]["leads"]) / c["prior"]["leads"] * 100
            out.append(
                f"- **{c['name']}** — Prior 14d: {c['prior']['leads']} leads. "
                f"Recent 14d: {c['recent']['leads']} leads. **Decay: {decay:.0f}%.**"
            )
    else:
        out.append("No Lead Gen creatives with >50% lead-volume decline. ✅")
    out.append("")

    # 🟡 Dormant
    out.append("## 🟡 Dormant Lead Gen creatives")
    out.append("")
    if dormant:
        for c in dormant:
            out.append(
                f"- **{c['name']}** (campaign: {c['campaign_name']}) — "
                f"{c['prior']['impressions']:,} prior-14d impressions, 0 recent. "
                f"Likely audience-count-hold or campaign group hold."
            )
    else:
        out.append("No dormant Lead Gen creatives. ✅")
    out.append("")

    # CPL leaderboard
    out.append("## Cost-per-lead leaderboard")
    out.append("")
    if cpl_candidates:
        best = cpl_candidates[0]
        worst = cpl_candidates[-1]
        out.append(f"- **Best:** {best['name']} — ${best['cpl']:.0f}/lead on {best['recent']['leads']} leads")
        out.append(f"- **Worst:** {worst['name']} — ${worst['cpl']:.0f}/lead on {worst['recent']['leads']} leads")
    else:
        out.append("Insufficient lead volume across creatives to compute reliable CPL (need ≥3 leads per creative).")
    out.append("")

    # Form usage map
    out.append("## Lead Gen Form usage map")
    out.append("")
    if form_usage:
        for form_urn, creatives in sorted(form_usage.items(), key=lambda x: len(x[1]), reverse=True):
            campaign_set = set(c["campaign_name"] for c in creatives)
            tag = ""
            if len(campaign_set) > 1:
                tag = " — ⚠️ used across multiple campaigns, verify intentional"
            elif all(c["intended_status"] != "ACTIVE" and not c["is_serving"] for c in creatives):
                tag = " — ℹ️ no active creatives using this form, archive candidate"
            out.append(f"- `{form_urn}` — {len(creatives)} creative(s) across {len(campaign_set)} campaign(s){tag}")
    out.append("")

    # Manual checklist
    out.append("## Manual validation checklist (Campaign Manager)")
    out.append("")
    out.append("- For forms with high CPL or zero leads: review form fields. Forms with > 6 fields complete ~50% lower than 4-field forms.")
    out.append("- For forms with no leads: confirm form review status is APPROVED. Rejected forms silently fail.")
    out.append("- Pull a sample of recent leads. >30% personal-email-domain submissions (gmail, yahoo) suggests broad audience or junk.")
    out.append("- Verify CRM/HubSpot sync on Lead Gen Forms is enabled and recent.")
    out.append("- Confirm Lead Gen Form leads are routed to the right list in HubSpot.")
    out.append("")

    # Headline
    out.append("---")
    out.append("")
    total_issues = len(spend_no_leads) + len(declining) + len(dormant)
    if total_issues == 0:
        out.append("**Headline:** Lead Gen surface is healthy. Confirm via manual quality checks in Campaign Manager.")
    else:
        out.append(
            f"**Headline:** {len(spend_no_leads)} creative(s) spending without leads, "
            f"{len(declining)} declining, {len(dormant)} dormant. Priority: investigate the "
            f"'spend without leads' creatives first — usually a broken form or rejected status."
        )

    print("\n".join(out))


if __name__ == "__main__":
    main()
