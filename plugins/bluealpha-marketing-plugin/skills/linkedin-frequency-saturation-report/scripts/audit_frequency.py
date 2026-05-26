#!/usr/bin/env python3
"""LinkedIn Frequency Saturation Report."""
import json
import statistics
import sys


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


def parse_campaign_id(urn):
    return urn.replace("urn:li:sponsoredCampaign:", "")


FACETS = {
    "matched_audiences": "urn:li:adTargetingFacet:audienceMatchingSegments",
    "dynamic_segments": "urn:li:adTargetingFacet:dynamicSegments",
}


def audience_profile(campaign):
    tc = campaign.get("targetingCriteria", {})
    matched = []
    dynamic = []
    for clause in tc.get("include", {}).get("and", []):
        or_ = clause.get("or", {})
        for facet_urn, values in or_.items():
            if facet_urn == FACETS["matched_audiences"]:
                matched.extend(values)
            elif facet_urn == FACETS["dynamic_segments"]:
                dynamic.extend(values)
    return {
        "matched_count": len(set(matched)),
        "dynamic_count": len(set(dynamic)),
        "attribute_only": not (matched or dynamic),
    }


def get_cap(campaign):
    opt_pref = campaign.get("optimizationPreference") or {}
    fop = opt_pref.get("frequencyOptimizationPreference")
    if not fop:
        return None
    return {
        "frequency": fop.get("frequency"),
        "duration": fop.get("timeSpan", {}).get("duration"),
        "unit": fop.get("timeSpan", {}).get("unit"),
        "type": fop.get("optimizationType"),
    }


def recommend_cap(audience_type, objective):
    table = {
        ("matched", "BRAND_AWARENESS"): "4-5 per 7 days",
        ("matched", "ENGAGEMENT"): "3-4 per 7 days",
        ("matched", "WEBSITE_VISIT"): "3-4 per 7 days",
        ("matched", "WEBSITE_CONVERSION"): "3-4 per 7 days",
        ("matched", "LEAD_GENERATION"): "2-3 per 7 days",
        ("attribute", "BRAND_AWARENESS"): "5-7 per 7 days",
        ("attribute", "ENGAGEMENT"): "3-5 per 7 days",
        ("attribute", "WEBSITE_VISIT"): "3-5 per 7 days",
        ("attribute", "WEBSITE_CONVERSION"): "3-5 per 7 days",
        ("attribute", "LEAD_GENERATION"): "3-4 per 7 days",
        ("retargeting", "WEBSITE_VISIT"): "5-7 per 7 days (intentionally higher)",
        ("retargeting", "WEBSITE_CONVERSION"): "5-7 per 7 days (intentionally higher)",
    }
    return table.get((audience_type, objective), "3-5 per 7 days")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    campaigns_resp = load(sys.argv[1])
    analytics_resp = load(sys.argv[2])

    analytics = {}
    for row in analytics_resp.get("elements", []):
        cid = parse_campaign_id(row["pivotValues"][0])
        analytics[cid] = {
            "impressions": int(row.get("impressions", 0)),
            "cost": float(row.get("costInLocalCurrency", 0)),
        }

    audits = []
    for c in campaigns_resp.get("elements", []):
        if c.get("status") != "ACTIVE":
            continue
        cid = str(c.get("id"))
        a = analytics.get(cid, {"impressions": 0, "cost": 0})
        prof = audience_profile(c)
        cap = get_cap(c)
        # Classify audience type
        if prof["dynamic_count"] > 0 and prof["matched_count"] == 0:
            atype = "retargeting"  # dynamic segments are usually behavioral
        elif prof["matched_count"] > 0:
            atype = "matched"
        else:
            atype = "attribute"
        # impressions per dollar
        ipd = (a["impressions"] / a["cost"]) if a["cost"] > 0 else 0
        audits.append({
            "campaign": c,
            "cid": cid,
            "name": c.get("name", "?"),
            "objective": c.get("objectiveType", "?"),
            "daily_budget": float((c.get("dailyBudget") or {}).get("amount", 0) or 0),
            "audience_profile": prof,
            "audience_type": atype,
            "cap": cap,
            "impressions": a["impressions"],
            "cost": a["cost"],
            "impressions_per_dollar": ipd,
        })

    # Account median impressions per dollar
    ipds = [a["impressions_per_dollar"] for a in audits if a["impressions_per_dollar"] > 0]
    median_ipd = statistics.median(ipds) if ipds else 0

    # Apply rules
    for a in audits:
        issues = []
        cap = a["cap"]
        atype = a["audience_type"]
        objective = a["objective"]

        if cap is None and atype == "matched":
            issues.append({
                "severity": "🔴",
                "type": "No frequency cap on matched-audience campaign",
                "detail": f"Targeting {a['audience_profile']['matched_count']} matched audience(s) with no cap.",
                "rec": f"Set a cap of {recommend_cap('matched', objective)}.",
            })
        elif cap is None and atype == "attribute" and a["daily_budget"] >= 50:
            issues.append({
                "severity": "🟡",
                "type": "No frequency cap on high-spend attribute campaign",
                "detail": f"Attribute-only targeting, daily budget {fmt_money(a['daily_budget'])}, no cap set.",
                "rec": f"Consider a soft cap of {recommend_cap('attribute', objective)}.",
            })
        elif cap is not None:
            # Normalize cap to "per 7 days" for comparison
            freq = cap.get("frequency")
            duration = cap.get("duration") or 7
            unit = cap.get("unit", "DAY")
            # Convert to per-week
            if unit == "DAY":
                per_week = freq / duration * 7
            elif unit == "HOUR":
                per_week = freq / duration * (24 * 7)
            else:
                per_week = freq
            if per_week < 3:
                issues.append({
                    "severity": "🟠",
                    "type": "Cap may be too tight",
                    "detail": f"Cap is {freq}/{duration} {unit.lower()}(s) = ~{per_week:.1f}/week.",
                    "rec": f"Consider relaxing to {recommend_cap(atype, objective)} unless intentionally restricting reach.",
                })
            elif per_week > 10 and atype == "matched":
                issues.append({
                    "severity": "🟠",
                    "type": "Cap may be too loose",
                    "detail": f"Cap is {freq}/{duration} {unit.lower()}(s) = ~{per_week:.1f}/week on a matched audience.",
                    "rec": f"Consider tightening to {recommend_cap('matched', objective)} to avoid burnout.",
                })

        # Impression intensity
        if median_ipd > 0 and a["impressions_per_dollar"] > 5 * median_ipd:
            issues.append({
                "severity": "🟡",
                "type": "High impression intensity",
                "detail": (
                    f"{a['impressions_per_dollar']:.0f} impressions per dollar — "
                    f"{a['impressions_per_dollar']/median_ipd:.1f}x the account median ({median_ipd:.0f}/$). "
                    "Could indicate low bid + saturated audience."
                ),
                "rec": "Verify campaign isn't repeatedly serving to a tiny pool. Consider raising bid or expanding audience.",
            })
        a["issues"] = issues

    audits.sort(key=lambda a: a["daily_budget"], reverse=True)

    # ===== Output =====
    out = []
    out.append("# LinkedIn Frequency Saturation Report")
    out.append("")
    with_issues = [a for a in audits if a["issues"]]
    out.append(
        f"**{len(audits)} active campaigns analyzed. {len(with_issues)} with frequency-configuration issues.**"
    )
    out.append("")
    out.append(
        "> ⚠️ The LinkedIn MCP doesn't expose `approximateUniqueImpressions`, so this skill is a "
        "configuration audit + impression-intensity proxy — not a direct frequency measurement. "
        "Confirm specific findings via the reach/frequency tab in Campaign Manager."
    )
    out.append("")

    # 🔴 / 🟠 / 🟡 per campaign
    out.append("## Findings (sorted by daily budget)")
    out.append("")
    for a in audits:
        cap_str = "no cap" if a["cap"] is None else (
            f"{a['cap']['frequency']}/{a['cap']['duration']} {a['cap']['unit'].lower()}(s)"
        )
        out.append(
            f"### {a['name']} (objective: {a['objective']}, daily budget: {fmt_money(a['daily_budget'])})"
        )
        out.append(
            f"- Audience type: {a['audience_type']} "
            f"(matched: {a['audience_profile']['matched_count']}, "
            f"dynamic: {a['audience_profile']['dynamic_count']}). "
            f"Cap: {cap_str}. 30d impressions: {a['impressions']:,}, "
            f"impressions/dollar: {a['impressions_per_dollar']:.0f}."
        )
        if not a["issues"]:
            out.append("- ✅ Frequency configuration looks reasonable.")
        else:
            for i in a["issues"]:
                out.append(f"- {i['severity']} **{i['type']}:** {i['detail']}")
                out.append(f"  - **Recommendation:** {i['rec']}")
        out.append("")

    # Headline
    out.append("---")
    out.append("")
    total = sum(len(a["issues"]) for a in audits)
    red = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🔴")
    orange = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🟠")
    yellow = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🟡")
    if total == 0:
        out.append("**Headline:** Frequency configuration looks healthy across active campaigns.")
    else:
        out.append(
            f"**Headline:** {red} no-cap matched-audience issue(s), {orange} mis-calibrated "
            f"cap(s), {yellow} other concerns. Set caps where missing first."
        )

    print("\n".join(out))


if __name__ == "__main__":
    main()
