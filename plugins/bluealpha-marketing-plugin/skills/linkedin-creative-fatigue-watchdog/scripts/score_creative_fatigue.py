#!/usr/bin/env python3
"""
LinkedIn Creative Fatigue Watchdog.

Inputs (positional, all JSON files):
  1. creatives.json — list_linkedin_creatives response
  2. campaigns.json — list_linkedin_campaigns response (for objective lookup)
  3. analytics_prior.json — pivot=CREATIVE, prior 14 days
  4. analytics_recent.json — pivot=CREATIVE, recent 14 days
"""
import json
import statistics
import sys


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


def parse_creative_id(urn):
    return urn.replace("urn:li:sponsoredCreative:", "")


def parse_campaign_id(urn):
    return urn.replace("urn:li:sponsoredCampaign:", "")


# Engagement metric selection per campaign objective.
# Returns the primary metric value as a fraction (0-1).
def primary_metric(obj_type, m):
    """Compute the primary metric value for a creative given its campaign objective."""
    impressions = m.get("impressions", 0)
    clicks = m.get("clicks", 0)
    lp_clicks = m.get("lp_clicks", 0)
    video_views = m.get("video_views", 0)
    video_completions = m.get("video_completions", 0)
    engagements = m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0) + m.get("reactions", 0) + m.get("follows", 0)
    one_click_leads = m.get("one_click_leads", 0)
    conversions = m.get("conversions", 0)

    if obj_type in {"BRAND_AWARENESS", "ENGAGEMENT"}:
        # LinkedIn's `clicks` metric on these objectives already includes all social
        # engagement actions (reactions, comments, profile views, etc.). CTR is the
        # right fatigue signal here, NOT the narrower (likes + comments + shares) sum
        # — that's just one slice of engagement and is very noisy on small samples.
        return (clicks / impressions) if impressions else 0, "ctr"
    if obj_type == "WEBSITE_VISIT":
        # LP-click rate is the primary signal; CTR is secondary
        return (lp_clicks / clicks) if clicks else 0, "lp_click_rate"
    if obj_type == "WEBSITE_CONVERSION":
        if conversions > 0:
            return (conversions / clicks) if clicks else 0, "conversion_rate"
        return (lp_clicks / clicks) if clicks else 0, "lp_click_rate"
    if obj_type == "LEAD_GENERATION":
        if one_click_leads > 0:
            return (one_click_leads / clicks) if clicks else 0, "lead_rate"
        return (clicks / impressions) if impressions else 0, "ctr"
    if obj_type == "VIDEO_VIEW":
        return (video_views / impressions) if impressions else 0, "hook_rate"
    # default
    return (clicks / impressions) if impressions else 0, "ctr"


# Fatigue threshold per objective: how much decay constitutes "fatigued"
FATIGUE_THRESHOLD = {
    "BRAND_AWARENESS": 0.30,
    "ENGAGEMENT": 0.30,
    "WEBSITE_VISIT": 0.40,
    "WEBSITE_CONVERSION": 0.40,
    "LEAD_GENERATION": 0.40,
    "VIDEO_VIEW": 0.30,
}


def index_analytics(resp):
    out = {}
    for row in resp.get("elements", []):
        cid = parse_creative_id(row["pivotValues"][0])
        out[cid] = {
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "lp_clicks": int(row.get("landingPageClicks", 0)),
            "cost": float(row.get("costInLocalCurrency", 0)),
            "video_views": int(row.get("videoViews", 0)),
            "video_completions": int(row.get("videoCompletions", 0)),
            "likes": int(row.get("likes", 0)),
            "comments": int(row.get("comments", 0)),
            "shares": int(row.get("shares", 0)),
            "reactions": int(row.get("reactions", 0)),
            "follows": int(row.get("follows", 0)),
            "conversions": int(row.get("externalWebsiteConversions", 0)),
            "one_click_leads": int(row.get("oneClickLeads", 0)),
        }
    return out


def creative_label(creative):
    name = creative.get("name", "").strip()
    if name:
        return name
    # Fall back to content reference snippet
    content = creative.get("content", {})
    if "textAd" in content:
        return f"[text ad: {content['textAd'].get('headline', '?')[:40]}]"
    if "reference" in content:
        ref = content["reference"]
        return f"[post {ref.split(':')[-1][:14]}]"
    return f"[id:{parse_creative_id(creative.get('id', ''))}]"


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    creatives_resp = load(sys.argv[1])
    campaigns_resp = load(sys.argv[2])
    prior_resp = load(sys.argv[3])
    recent_resp = load(sys.argv[4])

    # Build campaign objective map
    campaign_obj = {}
    campaign_status = {}
    campaign_name = {}
    for c in campaigns_resp.get("elements", []):
        cid = str(c.get("id"))
        campaign_obj[cid] = c.get("objectiveType", "UNKNOWN")
        campaign_status[cid] = c.get("status")
        campaign_name[cid] = c.get("name", f"id:{cid}")

    prior = index_analytics(prior_resp)
    recent = index_analytics(recent_resp)

    # Build creative records — only those in ACTIVE campaigns
    creatives = []
    unnamed_count = 0
    for c in creatives_resp.get("elements", []):
        cid = parse_creative_id(c.get("id", ""))
        campaign_id = parse_campaign_id(c.get("campaign", ""))
        if campaign_status.get(campaign_id) != "ACTIVE":
            continue
        if c.get("intendedStatus") not in ("ACTIVE",) and not c.get("isServing"):
            continue
        if not c.get("name", "").strip():
            unnamed_count += 1
        creatives.append({
            "id": cid,
            "name": creative_label(c),
            "campaign_id": campaign_id,
            "campaign_name": campaign_name.get(campaign_id, "?"),
            "objective": campaign_obj.get(campaign_id, "UNKNOWN"),
            "intended_status": c.get("intendedStatus"),
            "is_serving": c.get("isServing", False),
            "prior": prior.get(cid, {}),
            "recent": recent.get(cid, {}),
        })

    # Compute metrics
    for c in creatives:
        obj = c["objective"]
        prior_metric, metric_name = primary_metric(obj, c["prior"])
        recent_metric, _ = primary_metric(obj, c["recent"])
        c["metric_name"] = metric_name
        c["prior_metric"] = prior_metric
        c["recent_metric"] = recent_metric
        c["prior_impressions"] = c["prior"].get("impressions", 0)
        c["recent_impressions"] = c["recent"].get("impressions", 0)
        c["recent_cost"] = c["recent"].get("cost", 0)
        c["prior_cost"] = c["prior"].get("cost", 0)
        c["sufficient_volume"] = c["prior_impressions"] >= 500 and c["recent_impressions"] >= 500

    # Campaign median benchmarks (from creatives with sufficient recent volume)
    campaign_median = {}
    by_campaign = {}
    for c in creatives:
        by_campaign.setdefault(c["campaign_id"], []).append(c)
    for cid, lst in by_campaign.items():
        vals = [c["recent_metric"] for c in lst if c["recent_impressions"] >= 500]
        campaign_median[cid] = statistics.median(vals) if vals else 0

    # Classify
    fatigued = []
    weak = []
    waste = []
    top = []
    for c in creatives:
        if not c["sufficient_volume"]:
            continue
        threshold = FATIGUE_THRESHOLD.get(c["objective"], 0.4)
        prior_m, recent_m = c["prior_metric"], c["recent_metric"]
        median = campaign_median.get(c["campaign_id"], 0)
        decay_pct = ((prior_m - recent_m) / prior_m * 100) if prior_m > 0 else 0
        c["decay_pct"] = decay_pct
        c["campaign_median"] = median

        # Fatigued
        if prior_m > 0 and recent_m < (1 - threshold) * prior_m:
            fatigued.append(c)

        # Weak-from-launch: never reached median (both windows below median, recent < 0.6 × median)
        if median > 0 and recent_m < 0.6 * median and prior_m < median and c["recent_cost"] > 50:
            weak.append(c)

        # Waste: recent metric < 0.5 × median, recent spend > $50
        if median > 0 and recent_m < 0.5 * median and c["recent_cost"] > 50:
            waste.append(c)

        # Top performer
        if median > 0 and recent_m > 1.5 * median and c["recent_cost"] > 50:
            top.append(c)

    fatigued.sort(key=lambda c: c["recent_cost"] * abs(c["decay_pct"]), reverse=True)
    weak.sort(key=lambda c: c["recent_cost"], reverse=True)
    waste.sort(key=lambda c: c["recent_cost"], reverse=True)
    top.sort(key=lambda c: c["recent_cost"], reverse=True)

    total_recent_spend = sum(c["recent_cost"] for c in creatives)
    fatigued_spend = sum(c["recent_cost"] for c in fatigued)
    waste_spend = sum(c["recent_cost"] for c in waste)

    out = []
    out.append("# LinkedIn Creative Fatigue Watchdog")
    out.append("")
    scored = [c for c in creatives if c["sufficient_volume"]]
    out.append(
        f"**Scope:** {len(creatives)} creatives in active campaigns, "
        f"{len(scored)} with sufficient volume (≥500 impressions in each window) to score. "
        f"Comparison: trailing 14 days vs prior 14 days. "
        f"Total recent spend: {fmt_money(total_recent_spend)}."
    )
    out.append("")

    def render_creative(c, kind):
        line = f"- **{c['name']}** — Campaign: {c['campaign_name']} (objective: {c['objective']})"
        if kind == "fatigued":
            line += (
                f"\n  - Prior 14d: {c['prior_metric']*100:.1f}% {c['metric_name']} on "
                f"{fmt_money(c['prior_cost'])}. Recent: {c['recent_metric']*100:.1f}% on "
                f"{fmt_money(c['recent_cost'])}. **Decay: {c['decay_pct']:.0f}%.**"
            )
        else:
            line += (
                f"\n  - Recent {c['metric_name']}: {c['recent_metric']*100:.1f}% "
                f"vs campaign median {c['campaign_median']*100:.1f}%. "
                f"Recent spend: {fmt_money(c['recent_cost'])}."
            )
        return line

    out.append("## 🔴 Fatigued creatives (refresh queue)")
    out.append("")
    if fatigued:
        for c in fatigued[:10]:
            out.append(render_creative(c, "fatigued"))
            out.append(
                "  - **Action:** Pause and replace. Build the new variant around the "
                "headline/hook of a top-performing creative in the same campaign."
            )
    else:
        out.append("No fatigued creatives detected over the trailing 14-day window. ✅")
    out.append("")

    out.append("## 🟠 Weak-from-launch creatives")
    out.append("")
    if weak:
        for c in weak[:10]:
            out.append(render_creative(c, "weak"))
            out.append(
                "  - **Action:** Pause. This creative never reached campaign median performance — "
                "the concept isn't working for this audience."
            )
    else:
        out.append("No weak-from-launch creatives detected. ✅")
    out.append("")

    out.append("## 🟡 High-spend low-engagement waste")
    out.append("")
    if waste:
        for c in waste[:10]:
            out.append(render_creative(c, "waste"))
            out.append(
                "  - **Action:** Reduce budget allocation or pause if no near-term plan to refresh."
            )
    else:
        out.append("No high-spend low-engagement creatives detected. ✅")
    out.append("")

    out.append("## 🟢 Top performers — consider doubling down")
    out.append("")
    if top:
        for c in top[:10]:
            out.append(render_creative(c, "top"))
            out.append(
                "  - **Action:** Increase budget allocation. Duplicate as the base for new variants."
            )
    else:
        out.append("No standout top performers (>1.5× campaign median) in the recent window.")
    out.append("")

    out.append("## Creative naming hygiene")
    out.append("")
    out.append(
        f"{unnamed_count} of {len(creatives)} active creatives have empty `name` fields. "
        f"Adding descriptive names (e.g., 'Hook A — Founder POV — May refresh') makes future "
        f"runs of this skill — and any cross-tool reporting — substantially more readable."
    )
    out.append("")

    # Headline summary
    out.append("---")
    out.append("")
    out.append(
        f"**Summary:** {len(fatigued)} fatigued, {len(weak)} weak-from-launch, "
        f"{len(waste)} waste-flagged, {len(top)} top performers. "
        f"Estimated recoverable spend (fatigued + waste): "
        f"~{fmt_money((fatigued_spend + waste_spend) * 2)}/month at current pacing."
    )

    print("\n".join(out))


if __name__ == "__main__":
    main()
