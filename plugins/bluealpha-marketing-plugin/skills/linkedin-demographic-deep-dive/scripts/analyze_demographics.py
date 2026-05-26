#!/usr/bin/env python3
"""
LinkedIn Demographic Deep-Dive analyzer (v2).

Takes raw pivot responses from the LinkedIn analytics API plus a list of campaign
targeting criteria, and produces a structured narrative read with metrics, drift
flags, cross-pivot patterns, and dollar-weighted targeting actions.

Inputs (positional args, all JSON files):
  1. seniority_pivot.json
  2. function_pivot.json
  3. company_size_pivot.json
  4. industry_pivot.json
  5. campaigns.json
  6. taxonomy.json
"""
import json
import sys


# ----------------------------- IO helpers -----------------------------

def load(path):
    with open(path) as f:
        return json.load(f)


def fmt_dollars(amount):
    return f"${amount:,.0f}"


# ----------------------------- Resolve URNs -----------------------------

def resolve_urn(value, pivot_type, taxonomy):
    if pivot_type == "seniority":
        code = value.replace("urn:li:seniority:", "")
        return taxonomy["seniority"].get(code, f"Unknown seniority {code}"), code
    if pivot_type == "function":
        code = value.replace("urn:li:function:", "")
        return taxonomy["function"].get(code, f"Unknown function {code}"), code
    if pivot_type == "industry":
        code = value.replace("urn:li:industry:", "")
        label = taxonomy["industry"].get(code, f"urn:li:industry:{code} (taxonomy gap)")
        return label, code
    if pivot_type == "company_size":
        return taxonomy["company_size"].get(value, value), value
    return value, value


# ----------------------------- Metrics -----------------------------

def compute_segment_metrics(rows, pivot_type, taxonomy):
    out = []
    for row in rows:
        urn = row["pivotValues"][0]
        label, code = resolve_urn(urn, pivot_type, taxonomy)
        cost = float(row.get("costInLocalCurrency", 0))
        impressions = int(row.get("impressions", 0))
        clicks = int(row.get("clicks", 0))
        lp_clicks = int(row.get("landingPageClicks", 0))
        conversions = int(row.get("externalWebsiteConversions", 0)) + int(row.get("oneClickLeads", 0))
        engagements = (
            int(row.get("likes", 0))
            + int(row.get("comments", 0))
            + int(row.get("shares", 0))
            + int(row.get("reactions", 0))
            + int(row.get("follows", 0))
        )
        out.append({
            "label": label,
            "code": code,
            "cost": cost,
            "impressions": impressions,
            "clicks": clicks,
            "lp_clicks": lp_clicks,
            "conversions": conversions,
            "engagements": engagements,
            "ctr": (clicks / impressions * 100) if impressions else 0,
            "lpc_rate": (lp_clicks / clicks * 100) if clicks else 0,
            "cpc": (cost / clicks) if clicks else None,
            "cplpc": (cost / lp_clicks) if lp_clicks else None,
            "engagement_rate": (engagements / impressions * 100) if impressions else 0,
        })
    return out


# ----------------------------- Intent parsing -----------------------------

def parse_intended_targeting(campaigns):
    intended = {
        "seniorities": set(),
        "functions": set(),
        "industries": set(),
        "size_excludes": set(),
    }
    for c in campaigns.get("elements", []):
        if c.get("status") != "ACTIVE":
            continue
        tc = c.get("targetingCriteria", {})
        include_and = tc.get("include", {}).get("and", [])
        for clause in include_and:
            or_ = clause.get("or", {})
            for facet_urn, values in or_.items():
                if facet_urn == "urn:li:adTargetingFacet:seniorities":
                    for v in values:
                        intended["seniorities"].add(v.replace("urn:li:seniority:", ""))
                elif facet_urn == "urn:li:adTargetingFacet:jobFunctions":
                    for v in values:
                        intended["functions"].add(v.replace("urn:li:function:", ""))
                elif facet_urn == "urn:li:adTargetingFacet:industries":
                    for v in values:
                        intended["industries"].add(v.replace("urn:li:industry:", ""))
        exclude_or = tc.get("exclude", {}).get("or", {})
        for facet_urn, values in exclude_or.items():
            if facet_urn == "urn:li:adTargetingFacet:staffCountRanges":
                for v in values:
                    intended["size_excludes"].add(
                        v.replace("urn:li:staffCountRange:", "").replace("(", "").replace(")", "")
                    )
    return intended


def annotate_intent(segments, intended_codes, pivot_type, intended_excludes=None):
    size_map = {"1,1": "SIZE_1", "2,10": "SIZE_2_TO_10", "10001,2147483647": "SIZE_10001_OR_MORE"}
    for s in segments:
        code = s["code"]
        if pivot_type == "company_size":
            excluded_sizes = {size_map.get(e) for e in intended_excludes or []}
            s["intent"] = "✗ excluded" if code in excluded_sizes else "✓ allowed"
        else:
            if not intended_codes:
                s["intent"] = "(no constraint)"
            elif code in intended_codes:
                s["intent"] = "✓ intended"
            else:
                s["intent"] = "— unintended"
    return segments


# ----------------------------- Findings -----------------------------

def detect_smb_cluster(seniority, size, account_lpc_rate):
    """Detect whether Owner/Partner seniorities and SMB sizes form a coherent high-engagement cluster."""
    smb_size_codes = {"SIZE_1", "SIZE_2_TO_10", "SIZE_11_TO_50"}
    smb_seniority_codes = {"9", "10"}  # Partner, Owner

    smb_size_segs = [s for s in size if s["code"] in smb_size_codes and s["clicks"] >= 30]
    smb_sen_segs = [s for s in seniority if s["code"] in smb_seniority_codes and s["clicks"] >= 30]

    smb_size_high = [s for s in smb_size_segs if s["lpc_rate"] > account_lpc_rate * 1.3]
    smb_sen_high = [s for s in smb_sen_segs if s["lpc_rate"] > account_lpc_rate * 1.3]

    if smb_size_high and smb_sen_high:
        size_spend = sum(s["cost"] for s in smb_size_segs)
        sen_spend = sum(s["cost"] for s in smb_sen_segs)
        return {
            "detected": True,
            "smb_size_spend": size_spend,
            "smb_sen_spend": sen_spend,
            "smb_size_avg_lpc": sum(s["lp_clicks"] for s in smb_size_segs)
            / max(sum(s["clicks"] for s in smb_size_segs), 1) * 100,
            "smb_sen_avg_lpc": sum(s["lp_clicks"] for s in smb_sen_segs)
            / max(sum(s["clicks"] for s in smb_sen_segs), 1) * 100,
            "size_high_labels": [s["label"] for s in smb_size_high],
            "sen_high_labels": [s["label"] for s in smb_sen_high],
        }
    return {"detected": False}


def detect_enterprise_cluster(seniority, size, account_lpc_rate):
    """Detect whether CXO/Director + large company sizes form a coherent high-engagement cluster."""
    enterprise_size_codes = {"SIZE_1001_TO_5000", "SIZE_5001_TO_10000", "SIZE_10001_OR_MORE"}
    enterprise_sen_codes = {"6", "7", "8"}  # Director, VP, CXO

    ent_size_segs = [s for s in size if s["code"] in enterprise_size_codes and s["clicks"] >= 30]
    ent_sen_segs = [s for s in seniority if s["code"] in enterprise_sen_codes and s["clicks"] >= 30]

    ent_size_high = [s for s in ent_size_segs if s["lpc_rate"] > account_lpc_rate * 1.2]
    ent_sen_high = [s for s in ent_sen_segs if s["lpc_rate"] > account_lpc_rate * 1.2]

    if ent_size_high and ent_sen_high:
        return {
            "detected": True,
            "size_high_labels": [s["label"] for s in ent_size_high],
            "sen_high_labels": [s["label"] for s in ent_sen_high],
        }
    return {"detected": False}


def rank_waste_by_dollars(segments, account_lpc_rate, min_cost=200, perf_threshold=0.6):
    """Rank underperforming segments by the dollar opportunity to cut."""
    waste = []
    for s in segments:
        if s["cost"] < min_cost:
            continue
        if s["clicks"] < 30:
            continue
        if s["lpc_rate"] < account_lpc_rate * perf_threshold:
            # underperformance ratio: how much worse vs account
            shortfall = max(0, account_lpc_rate - s["lpc_rate"]) / account_lpc_rate
            score = s["cost"] * shortfall
            reason = (
                f"LP-click rate {s['lpc_rate']:.1f}% vs account {account_lpc_rate:.1f}% "
                f"({shortfall*100:.0f}% below benchmark)"
            )
            waste.append((s, reason, score))
    waste.sort(key=lambda x: x[2], reverse=True)
    return waste


def rank_sleepers_by_dollars(segments, account_lpc_rate, intent_required=False):
    """Unintended segments with strong engagement and meaningful spend — rank by dollar opportunity."""
    sleepers = []
    for s in segments:
        if s["clicks"] < 30 or s["cost"] < 200:
            continue
        if intent_required and "unintended" not in s["intent"]:
            continue
        if s["lpc_rate"] > account_lpc_rate * 1.3:
            uplift = (s["lpc_rate"] - account_lpc_rate) / account_lpc_rate
            score = s["cost"] * uplift
            sleepers.append((s, score))
    sleepers.sort(key=lambda x: x[1], reverse=True)
    return sleepers


# ----------------------------- Rendering -----------------------------

def render_pivot_table(name, segments, top_n=12, min_impr=100):
    filtered = [s for s in segments if s["impressions"] >= min_impr]
    filtered.sort(key=lambda s: s["cost"], reverse=True)
    top = filtered[:top_n]
    total_cost = sum(s["cost"] for s in segments)

    lines = [
        f"\n### {name}",
        "",
        "| Segment | Spend | Spend % | Clicks | LP Clicks | CTR | LPC Rate | CPLPC | Intent |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for s in top:
        share = (s["cost"] / total_cost * 100) if total_cost else 0
        cplpc = f"${s['cplpc']:.2f}" if s["cplpc"] else "—"
        lines.append(
            f"| {s['label']} "
            f"| {fmt_dollars(s['cost'])} "
            f"| {share:.1f}% "
            f"| {s['clicks']:,} "
            f"| {s['lp_clicks']:,} "
            f"| {s['ctr']:.2f}% "
            f"| {s['lpc_rate']:.1f}% "
            f"| {cplpc} "
            f"| {s['intent']} |"
        )
    return "\n".join(lines)


# ----------------------------- Main -----------------------------

def main():
    if len(sys.argv) != 7:
        print(__doc__)
        sys.exit(1)
    seniority_data = load(sys.argv[1])
    function_data = load(sys.argv[2])
    size_data = load(sys.argv[3])
    industry_data = load(sys.argv[4])
    campaigns = load(sys.argv[5])
    taxonomy = load(sys.argv[6])

    intended = parse_intended_targeting(campaigns)

    seniority = compute_segment_metrics(seniority_data["elements"], "seniority", taxonomy)
    function = compute_segment_metrics(function_data["elements"], "function", taxonomy)
    size = compute_segment_metrics(size_data["elements"], "company_size", taxonomy)
    industry = compute_segment_metrics(industry_data["elements"], "industry", taxonomy)

    annotate_intent(seniority, intended["seniorities"], "seniority")
    annotate_intent(function, intended["functions"], "function")
    annotate_intent(industry, intended["industries"], "industry")
    annotate_intent(size, None, "company_size", intended_excludes=intended["size_excludes"])

    # Account-wide benchmarks (use function pivot — it's a complete partition of clicks)
    total_cost = sum(s["cost"] for s in function)
    total_clicks = sum(s["clicks"] for s in function)
    total_lp = sum(s["lp_clicks"] for s in function)
    total_impr = sum(s["impressions"] for s in function)
    account_lpc_rate = (total_lp / total_clicks * 100) if total_clicks else 0
    account_ctr = (total_clicks / total_impr * 100) if total_impr else 0
    account_cplpc = (total_cost / total_lp) if total_lp else 0
    total_conv = sum(s["conversions"] for s in function)
    has_conversions = total_conv > 0

    # Cross-pivot pattern detection
    smb = detect_smb_cluster(seniority, size, account_lpc_rate)
    enterprise = detect_enterprise_cluster(seniority, size, account_lpc_rate)

    # ============== OUTPUT ==============
    out = []
    out.append("# LinkedIn Demographic Deep-Dive — BlueAlpha (Account 515970088)")
    out.append("")
    out.append("**Window:** Trailing 90 days (Feb 22 – May 22, 2026)  ")
    out.append(
        f"**Total spend:** {fmt_dollars(total_cost)} · "
        f"**Clicks:** {total_clicks:,} · "
        f"**LP clicks:** {total_lp:,}  "
    )
    out.append(
        f"**Account CTR:** {account_ctr:.2f}% · "
        f"**LP-click rate:** {account_lpc_rate:.1f}% · "
        f"**CPLPC:** {fmt_dollars(account_cplpc)}"
    )
    out.append("")
    if not has_conversions:
        out.append(
            "> ⚠️ **No conversion data tracked.** The LinkedIn Insight Tag isn't recording "
            "externalWebsiteConversions or oneClickLeads. Analysis uses landing-page-click "
            "rate as the performance proxy. **Installing the Insight Tag should be the #1 "
            "action — without it, the LinkedIn optimizer is flying blind.**"
        )
        out.append("")

    # ============== CROSS-PIVOT PATTERNS (lead with these) ==============
    if smb["detected"] or enterprise["detected"]:
        out.append("---")
        out.append("")
        out.append("## Cross-pivot patterns")
        out.append("")

    if smb["detected"]:
        smb_total = smb["smb_size_spend"]
        smb_share = smb_total / total_cost * 100
        out.append(
            f"**🔵 SMB / Founder cluster.** Owner/Partner seniorities ({fmt_dollars(smb['smb_sen_spend'])} "
            f"at {smb['smb_sen_avg_lpc']:.1f}% LP-click rate) AND small companies ({', '.join(smb['size_high_labels'])}, "
            f"{fmt_dollars(smb_total)} = {smb_share:.0f}% of spend at {smb['smb_size_avg_lpc']:.1f}% LP-click rate) both "
            f"engage ~2x the account average ({account_lpc_rate:.1f}%). These are almost certainly the same population — "
            f"founders and solo-marketers at small businesses. **Decision point: lean in (add as deliberate include) "
            f"or exclude (if ICP is enterprise-only).** This is the single highest-leverage targeting decision on the "
            f"account."
        )
        out.append("")

    if enterprise["detected"]:
        out.append(
            f"**🟣 Enterprise cluster.** {', '.join(enterprise['sen_high_labels'])} seniorities and "
            f"{', '.join(enterprise['size_high_labels'])} companies both engage above the account benchmark. "
            f"The intended ICP is being reached effectively — this is a confirmation signal, not a fix."
        )
        out.append("")

    # ============== TOP 3 ACTIONS (dollar-prioritized) ==============
    out.append("---")
    out.append("")
    out.append("## Top 3 actions (ranked by dollar impact)")
    out.append("")

    # Collect all candidate actions with a dollar-impact score so we can rank them.
    # Each entry: (score, action_type, text)
    candidates = []

    # Insight Tag — anchored to total spend at risk (everything if untracked)
    if not has_conversions:
        candidates.append((
            total_cost,  # the entire account is "at risk" without measurement
            "insight_tag",
            "**Install the LinkedIn Insight Tag and define conversion events.** Zero conversions "
            f"tracked across {fmt_dollars(total_cost)} of spend — the optimizer is bidding on clicks, "
            "not outcomes. Unlocks every other optimization on this account."
        ))

    # Cross-pivot SMB cluster — score by spend in the cluster
    if smb["detected"]:
        candidates.append((
            smb["smb_size_spend"],
            "smb_cluster",
            f"**Make a deliberate decision about the SMB / Founder cluster.** "
            f"{fmt_dollars(smb['smb_size_spend'])} ({smb['smb_size_spend']/total_cost*100:.0f}% of spend) "
            f"is going to small companies (2-10, 11-50) that engage at ~{smb['smb_size_avg_lpc']:.0f}% "
            f"LP-click rate vs {account_lpc_rate:.1f}% account average. Either embrace (include "
            f"explicitly + budget more) or cut (exclude SIZE_1 / 2-10 / 11-50 across all campaigns)."
        ))

    # Biggest dollar-saving exclude across all pivots
    all_waste = []
    for pivot_name, segs in [
        ("function", function),
        ("seniority", seniority),
        ("company size", size),
        ("industry", industry),
    ]:
        for s, reason, score in rank_waste_by_dollars(segs, account_lpc_rate):
            all_waste.append((pivot_name, s, reason, score))
    all_waste.sort(key=lambda x: x[3], reverse=True)

    if all_waste:
        pivot_name, s, reason, score = all_waste[0]
        candidates.append((
            score,
            "exclude",
            f"**Exclude {s['label']} from {pivot_name} targeting.** {fmt_dollars(s['cost'])} spent — "
            f"{reason}. Estimated waste recovered: {fmt_dollars(score)}."
        ))

    # Biggest dollar-weighted sleeper to add
    all_sleepers = []
    for pivot_name, segs in [
        ("function", function),
        ("seniority", seniority),
        ("industry", industry),
    ]:
        for s, score in rank_sleepers_by_dollars(segs, account_lpc_rate, intent_required=True):
            all_sleepers.append((pivot_name, s, score))
    all_sleepers.sort(key=lambda x: x[2], reverse=True)
    if all_sleepers:
        pivot_name, s, score = all_sleepers[0]
        # de-duplicate: if SMB cluster is detected, don't also recommend Owner/SMB sleepers
        if not (smb["detected"] and (s["code"] in {"10", "9"} or pivot_name == "company size")):
            candidates.append((
                score,
                "expand",
                f"**Add {s['label']} as a deliberate {pivot_name} include.** "
                f"{fmt_dollars(s['cost'])} of unintended spend with {s['lpc_rate']:.1f}% LP-click rate "
                f"(vs {account_lpc_rate:.1f}% account). Biggest dollar-weighted expansion opportunity."
            ))

    # Rank by dollar impact and keep the top 3
    candidates.sort(key=lambda c: c[0], reverse=True)
    for i, (_, _, text) in enumerate(candidates[:3], 1):
        out.append(f"{i}. {text}")
    out.append("")

    # ============== Narrative sections ==============
    out.append("---")
    out.append("")
    out.append("## 1. Who you're paying to reach")
    out.append("")

    # Function
    func_sorted = sorted(function, key=lambda s: s["cost"], reverse=True)
    func_total = sum(s["cost"] for s in function)
    top_func = func_sorted[0]
    unintended_func_spend = sum(s["cost"] for s in function if "unintended" in s["intent"])
    out.append(
        f"**Job function** — Marketing (intended) gets {top_func['cost']/func_total*100:.0f}% of spend "
        f"({fmt_dollars(top_func['cost'])}). But {unintended_func_spend/func_total*100:.0f}% "
        f"({fmt_dollars(unintended_func_spend)}) goes to unintended functions — chiefly Business Development, "
        f"Operations, Media & Communication. Some is reasonable LinkedIn overlap; some is waste."
    )
    out.append("")

    # Seniority
    sen_total = sum(s["cost"] for s in seniority)
    sen_intended_spend = sum(s["cost"] for s in seniority if "intended" in s["intent"])
    sen_unintended = [s for s in seniority if "unintended" in s["intent"] and s["cost"] > 200]
    unintended_str = ", ".join(f"{s['label']} ({fmt_dollars(s['cost'])})" for s in sen_unintended[:3])
    out.append(
        f"**Seniority** — Intended bracket is Manager → CXO. {sen_intended_spend/sen_total*100:.0f}% of "
        f"spend lands inside that band. Notable unintended leakage: {unintended_str if unintended_str else 'minimal'}."
    )
    out.append("")

    # Company size
    size_total = sum(s["cost"] for s in size)
    size_sorted = sorted(size, key=lambda s: s["cost"], reverse=True)
    size_top = size_sorted[:3]
    size_str = ", ".join(f"{s['label']} ({s['cost']/size_total*100:.0f}%)" for s in size_top)
    smb_spend = sum(
        s["cost"]
        for s in size
        if s["code"] in {"SIZE_1", "SIZE_2_TO_10", "SIZE_11_TO_50"}
    )
    out.append(
        f"**Company size** — Top three: {size_str}. {fmt_dollars(smb_spend)} ({smb_spend/size_total*100:.0f}%) "
        f"goes to companies under 50 employees. Two campaigns already exclude SIZE_1, SIZE_2_TO_10, and "
        f"SIZE_10001_OR_MORE — that exclusion isn't applied across the rest of the account."
    )
    out.append("")

    # Industry
    ind_total = sum(s["cost"] for s in industry)
    ind_sorted = sorted(industry, key=lambda s: s["cost"], reverse=True)
    ind_top_5 = ind_sorted[:5]
    ind_str = ", ".join(f"{s['label']} ({fmt_dollars(s['cost'])})" for s in ind_top_5)
    out.append(
        f"**Industry** — Top 5: {ind_str}. No industry-include constraint set, so this distribution is "
        f"LinkedIn's optimizer choosing. Tech/SaaS/Financial Services concentrated with a long tail."
    )
    out.append("")

    # ===== Section 2 =====
    out.append("## 2. Who's actually engaging")
    out.append("")
    out.append("Using **landing-page-click rate** as the performance proxy (conversions aren't tracked).")
    out.append("")

    def best_performers(segments, min_clicks=30):
        return sorted(
            [s for s in segments if s["clicks"] >= min_clicks],
            key=lambda s: s["lpc_rate"],
            reverse=True,
        )[:3]

    out.append(f"**Best seniorities by LP-click rate:**")
    for s in best_performers(seniority):
        out.append(
            f"- {s['label']} — {s['lpc_rate']:.1f}% LP-click rate, "
            f"{fmt_dollars(s['cplpc']) if s['cplpc'] else '—'} CPLPC, {s['intent']}"
        )
    out.append("")

    out.append(f"**Best functions by LP-click rate:**")
    for s in best_performers(function):
        out.append(
            f"- {s['label']} — {s['lpc_rate']:.1f}% LP-click rate, "
            f"{fmt_dollars(s['cplpc']) if s['cplpc'] else '—'} CPLPC, {s['intent']}"
        )
    out.append("")

    out.append(f"**Best company sizes by LP-click rate:**")
    for s in best_performers(size):
        out.append(
            f"- {s['label']} — {s['lpc_rate']:.1f}% LP-click rate, "
            f"{fmt_dollars(s['cplpc']) if s['cplpc'] else '—'} CPLPC, {s['intent']}"
        )
    out.append("")

    out.append(f"**Best industries (min 50 clicks):**")
    ind_perf = sorted(
        [s for s in industry if s["clicks"] >= 50],
        key=lambda s: s["lpc_rate"],
        reverse=True,
    )[:3]
    for s in ind_perf:
        out.append(
            f"- {s['label']} — {s['lpc_rate']:.1f}% LP-click rate, "
            f"{fmt_dollars(s['cplpc']) if s['cplpc'] else '—'} CPLPC"
        )
    out.append("")

    # ===== Section 3: waste (ranked by dollar opportunity) =====
    out.append("## 3. Where you're wasting (ranked by dollar opportunity)")
    out.append("")
    if all_waste:
        for pivot_name, s, reason, score in all_waste[:6]:
            out.append(
                f"- **{s['label']}** ({pivot_name}) — {fmt_dollars(s['cost'])} spent. "
                f"{reason}. **Estimated waste: {fmt_dollars(score)}.** "
                f"**Recommendation: exclude or de-prioritize.**"
            )
    else:
        out.append("No segments above the $200-spend threshold are dramatically underperforming.")
    out.append("")

    # ===== Section 4: expansion =====
    out.append("## 4. Where to expand (ranked by dollar-weighted lift)")
    out.append("")
    expanders = []
    for pivot_name, segs in [
        ("function", function),
        ("seniority", seniority),
        ("company size", size),
        ("industry", industry),
    ]:
        for s, score in rank_sleepers_by_dollars(segs, account_lpc_rate):
            expanders.append((pivot_name, s, score))
    expanders.sort(key=lambda x: x[2], reverse=True)
    if expanders:
        for pivot_name, s, score in expanders[:6]:
            out.append(
                f"- **{s['label']}** ({pivot_name}) — {s['lpc_rate']:.1f}% LP-click rate "
                f"(vs account {account_lpc_rate:.1f}%) on {fmt_dollars(s['cost'])} spend, "
                f"{s['intent']}. **Recommendation: add as deliberate include.**"
            )
    else:
        out.append("No unintended segments are dramatically outperforming the account average.")
    out.append("")

    # ===== Detail tables =====
    out.append("---")
    out.append("")
    out.append("## Detail tables")

    out.append(render_pivot_table("Seniority", seniority, top_n=10))
    out.append(render_pivot_table("Job Function", function, top_n=12))
    out.append(render_pivot_table("Company Size", size, top_n=9))
    out.append(render_pivot_table("Industry (top 12 by spend)", industry, top_n=12))

    # Taxonomy gaps
    gaps = [s["label"] for s in industry if "taxonomy gap" in s["label"]]
    if gaps:
        out.append("")
        out.append("## Taxonomy gaps to investigate")
        out.append("")
        for g in gaps[:20]:
            out.append(f"- {g}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
