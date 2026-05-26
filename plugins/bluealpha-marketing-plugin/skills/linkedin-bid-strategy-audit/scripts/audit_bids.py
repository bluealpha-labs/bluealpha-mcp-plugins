#!/usr/bin/env python3
"""LinkedIn Bid Strategy Audit."""
import json
import sys


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


# Best-practice cost type per objective
BEST_COST_TYPE = {
    "BRAND_AWARENESS": {"CPM"},
    "ENGAGEMENT": {"CPM", "CPC"},
    "WEBSITE_VISIT": {"CPC"},
    "WEBSITE_CONVERSION": {"CPC"},
    "LEAD_GENERATION": {"CPM", "CPL", "CPC"},
    "VIDEO_VIEW": {"CPV"},
}

# Best-practice optimization target per objective
GOOD_OPT = {
    "BRAND_AWARENESS": {"MAX_REACH", "MAX_FREQUENCY"},
    "ENGAGEMENT": {"MAX_REACH", "MAX_FREQUENCY", "NONE"},
    "WEBSITE_VISIT": {"NONE", "ENHANCED_CONVERSION"},
    "WEBSITE_CONVERSION": {"ENHANCED_CONVERSION", "MAX_LEAD"},
    "LEAD_GENERATION": {"CAP_COST_AND_MAXIMIZE_LEADS", "MAX_LEAD", "NONE"},
    "VIDEO_VIEW": {"MAX_VIDEO_VIEWS"},
}

# Reasonable unit-cost ranges per (cost_type, objective)
RANGES = {
    ("CPM", "BRAND_AWARENESS"): (20, 80),
    ("CPM", "ENGAGEMENT"): (20, 80),
    ("CPC", "WEBSITE_VISIT"): (4, 25),
    ("CPC", "WEBSITE_CONVERSION"): (5, 30),
    ("CPC", "ENGAGEMENT"): (3, 15),
    ("CPC", "LEAD_GENERATION"): (5, 30),
}


def audit_campaign(c):
    issues = []
    obj = c.get("objectiveType", "UNKNOWN")
    cost_type = c.get("costType")
    # If costType is missing, we can't run the audit on this campaign — note it but don't flag
    if not cost_type:
        return {
            "campaign": c,
            "obj": obj,
            "cost_type": "—",
            "unit_cost": 0,
            "opt_target": "—",
            "creative_sel": "—",
            "pacing": "—",
            "issues": [{
                "severity": "ℹ️",
                "type": "Insufficient data",
                "detail": "Campaign payload missing costType — bid audit can't run on this campaign.",
                "rec": "Pull a full `list_linkedin_campaigns` response so bid configuration fields are present.",
            }],
        }
    unit_cost = float((c.get("unitCost") or {}).get("amount", 0) or 0)
    opt_target = c.get("optimizationTargetType", "NONE")
    if isinstance(opt_target, dict):
        # Some campaigns nest the optimization preference
        opt_target = opt_target.get("type", "NONE")
    creative_sel = c.get("creativeSelection", "?")
    pacing = c.get("pacingStrategy", "STANDARD")

    # Mismatch: cost type vs objective
    expected_costs = BEST_COST_TYPE.get(obj)
    if expected_costs and cost_type not in expected_costs:
        issues.append({
            "severity": "🔴",
            "type": "Cost type mismatch",
            "detail": f"Objective {obj} expects {' or '.join(sorted(expected_costs))}, found {cost_type}.",
            "rec": f"Change cost type to {sorted(expected_costs)[0]}.",
        })

    # Optimization target
    expected_opts = GOOD_OPT.get(obj, set())
    is_cap_cost = opt_target == "CAP_COST_AND_MAXIMIZE_LEADS"
    if expected_opts and opt_target not in expected_opts:
        issues.append({
            "severity": "🟡",
            "type": "Optimization target",
            "detail": f"Objective {obj} typically uses {' or '.join(sorted(expected_opts))}, found {opt_target}.",
            "rec": f"Consider switching optimization target to {sorted(expected_opts)[0]}.",
        })

    # Unit cost range — only check when NOT in CAP_COST mode (where unitCost is a ceiling, not a bid)
    if not is_cap_cost:
        rng = RANGES.get((cost_type, obj))
        if rng and unit_cost > 0:
            lo, hi = rng
            if unit_cost < lo:
                issues.append({
                    "severity": "🟠",
                    "type": "Bid below typical floor",
                    "detail": f"{cost_type} bid of ${unit_cost:.2f} is below the ${lo} typical floor for {obj}. Likely won't win auctions.",
                    "rec": f"Increase bid to at least ${lo}-{(lo+hi)//2}.",
                })
            elif unit_cost > hi:
                issues.append({
                    "severity": "🟠",
                    "type": "Bid above typical ceiling",
                    "detail": f"{cost_type} bid of ${unit_cost:.2f} is above the ${hi} typical ceiling for {obj}. Verify intent — likely overpaying.",
                    "rec": f"Consider lowering bid to ${(lo+hi)//2}-{hi}, or confirm audience is narrow enough to justify.",
                })

    # Creative selection
    if creative_sel == "ROUND_ROBIN":
        issues.append({
            "severity": "🟡",
            "type": "Creative selection",
            "detail": "Set to ROUND_ROBIN. LinkedIn's OPTIMIZED mode is usually preferable for multi-creative campaigns.",
            "rec": "Switch to OPTIMIZED unless deliberately A/B testing.",
        })

    return {
        "campaign": c,
        "obj": obj,
        "cost_type": cost_type,
        "unit_cost": unit_cost,
        "opt_target": opt_target,
        "creative_sel": creative_sel,
        "pacing": pacing,
        "issues": issues,
    }


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    resp = load(sys.argv[1])
    active = [c for c in resp.get("elements", []) if c.get("status") == "ACTIVE"]
    audits = [audit_campaign(c) for c in active]
    audits.sort(key=lambda a: float((a["campaign"].get("dailyBudget") or {}).get("amount", 0) or 0), reverse=True)

    out = []
    out.append("# LinkedIn Bid Strategy Audit")
    out.append("")
    with_issues = [a for a in audits if a["issues"]]
    out.append(f"**{len(audits)} active campaigns analyzed. {len(with_issues)} with bid configuration issues.**")
    out.append("")

    if not audits:
        out.append("No active campaigns.")
        print("\n".join(out))
        return

    out.append("## Findings (sorted by daily budget at stake)")
    out.append("")
    for a in audits:
        c = a["campaign"]
        budget = float((c.get("dailyBudget") or {}).get("amount", 0) or 0)
        out.append(f"### {c.get('name','?')} (objective: {a['obj']}, daily budget: {fmt_money(budget)})")
        out.append(
            f"- Current config: cost_type=`{a['cost_type']}`, unit_cost=${a['unit_cost']:.2f}, "
            f"optimization=`{a['opt_target']}`, creative_selection=`{a['creative_sel']}`, "
            f"pacing=`{a['pacing']}`"
        )
        if not a["issues"]:
            out.append("- ✅ No issues detected.")
        else:
            for issue in a["issues"]:
                out.append(f"- {issue['severity']} **{issue['type']}:** {issue['detail']}")
                out.append(f"  - **Recommendation:** {issue['rec']}")
        out.append("")

    # Headline
    total_red = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🔴")
    total_orange = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🟠")
    total_yellow = sum(1 for a in audits for i in a["issues"] if i["severity"] == "🟡")
    out.append("---")
    out.append("")
    if total_red + total_orange + total_yellow == 0:
        out.append("**Headline:** Bid configurations look healthy across the active set.")
    else:
        # Find highest-budget campaign with a 🔴 or 🟠 issue
        candidates = [a for a in audits if any(i["severity"] in ("🔴", "🟠") for i in a["issues"])]
        if candidates:
            top = candidates[0]
            out.append(
                f"**Headline:** {total_red} cost-type mismatch(es), {total_orange} suspicious "
                f"bid(s), {total_yellow} optimization concern(s). "
                f"Highest-impact fix: review **{top['campaign'].get('name', '?')}**."
            )
        else:
            out.append(
                f"**Headline:** {total_yellow} optimization concern(s) — mostly creative selection "
                f"and optimization-target tweaks. No critical mismatches."
            )

    print("\n".join(out))


if __name__ == "__main__":
    main()
