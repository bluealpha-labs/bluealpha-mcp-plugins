#!/usr/bin/env python3
"""
LinkedIn Targeting Overlap Finder.

Compute per-facet Jaccard similarity between every pair of ACTIVE campaigns and surface
pairs whose overall weighted overlap exceeds the threshold.

Inputs:
  1. campaigns.json — list_linkedin_campaigns response
  2. (optional) taxonomy.json — for resolving URNs to human-readable labels
"""
import json
import sys
from itertools import combinations


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


FACET_KEYS = {
    "seniorities": "urn:li:adTargetingFacet:seniorities",
    "jobFunctions": "urn:li:adTargetingFacet:jobFunctions",
    "industries": "urn:li:adTargetingFacet:industries",
    "titles": "urn:li:adTargetingFacet:titles",
    "locations": "urn:li:adTargetingFacet:locations",
    "staffCountRanges": "urn:li:adTargetingFacet:staffCountRanges",
    "audienceMatchingSegments": "urn:li:adTargetingFacet:audienceMatchingSegments",
    "dynamicSegments": "urn:li:adTargetingFacet:dynamicSegments",
}

# Weights for the overall overlap score
FACET_WEIGHTS = {
    "seniorities": 1.0,
    "jobFunctions": 1.0,
    "industries": 0.8,
    "titles": 1.5,
    "locations": 0.5,
    "staffCountRanges": 0.8,
    "audienceMatchingSegments": 1.5,
    "dynamicSegments": 1.0,
}


def extract_targeting(campaign):
    facets = {k: set() for k in FACET_KEYS}
    tc = campaign.get("targetingCriteria", {})
    for clause in tc.get("include", {}).get("and", []):
        or_ = clause.get("or", {})
        for facet_urn, values in or_.items():
            for facet_key, urn_prefix in FACET_KEYS.items():
                if facet_urn == urn_prefix:
                    facets[facet_key].update(values)
    return facets


def jaccard(a, b):
    if not a and not b:
        return None  # neutral — both empty
    if not a or not b:
        return 0.0  # one restricts, the other doesn't — different population
    return len(a & b) / len(a | b)


def overlap_score(facets_a, facets_b):
    """Return overall weighted score (0-100) plus per-facet Jaccard map."""
    per_facet = {}
    weighted_sum = 0.0
    weight_sum = 0.0
    for facet, weight in FACET_WEIGHTS.items():
        j = jaccard(facets_a[facet], facets_b[facet])
        per_facet[facet] = j
        if j is not None:
            weighted_sum += j * weight
            weight_sum += weight
    overall = (weighted_sum / weight_sum * 100) if weight_sum > 0 else 0
    return overall, per_facet


def label_set(s, kind):
    """Render a set of URNs as a compact label string."""
    if not s:
        return "(empty — all match)"
    if len(s) <= 5:
        return ", ".join(sorted(s))
    return f"{len(s)} values"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    campaigns_resp = load(sys.argv[1])

    # Active only
    actives = []
    for c in campaigns_resp.get("elements", []):
        if c.get("status") != "ACTIVE":
            continue
        actives.append({
            "id": str(c.get("id")),
            "name": c.get("name", "?"),
            "objective": c.get("objectiveType", "?"),
            "facets": extract_targeting(c),
            "daily_budget": float((c.get("dailyBudget") or {}).get("amount", 0) or 0),
        })

    # Pairwise
    pairs = []
    for a, b in combinations(actives, 2):
        overall, per_facet = overlap_score(a["facets"], b["facets"])
        overlap_dollars = min(a["daily_budget"], b["daily_budget"]) * (overall / 100)
        pairs.append({
            "a": a,
            "b": b,
            "overall": overall,
            "per_facet": per_facet,
            "overlap_dollars": overlap_dollars,
        })
    pairs.sort(key=lambda p: p["overlap_dollars"], reverse=True)

    threshold = 60
    flagged = [p for p in pairs if p["overall"] >= threshold]

    # ===== Output =====
    out = []
    out.append("# LinkedIn Targeting Overlap Finder")
    out.append("")
    out.append(
        f"**{len(actives)} active campaigns analyzed. {len(flagged)} overlapping pairs detected "
        f"(above {threshold}% threshold).**"
    )
    total_overlap = sum(p["overlap_dollars"] for p in flagged)
    out.append("")
    out.append(f"**Total auction-overlap dollars (estimate): {fmt_money(total_overlap)}/day "
               f"(~{fmt_money(total_overlap * 30)}/month).**")
    out.append("")

    # Top pairs
    out.append("## Top overlapping pairs (sorted by overlap dollars)")
    out.append("")
    if not flagged:
        out.append("No campaign pairs overlap above the threshold. ✅")
    for p in flagged[:8]:
        a, b = p["a"], p["b"]
        out.append(f"### {a['name']} ↔ {b['name']}")
        out.append("")
        out.append(
            f"- **Overall overlap: {p['overall']:.0f}%** | "
            f"Objectives: {a['objective']} / {b['objective']} | "
            f"Daily budgets: {fmt_money(a['daily_budget'])} / {fmt_money(b['daily_budget'])} | "
            f"Auction-overlap dollars: **{fmt_money(p['overlap_dollars'])}/day**"
        )
        out.append("- Per-facet Jaccard:")
        for facet, j in p["per_facet"].items():
            if j is None:
                # neutral facet — only show if both are empty (common, skip noise)
                continue
            shared = a["facets"][facet] & b["facets"][facet]
            label = f"{j*100:.0f}%"
            if j > 0 and shared:
                label += f" ({len(shared)} shared)"
            elif j == 0 and (a["facets"][facet] or b["facets"][facet]):
                label += " (only one campaign restricts)"
            out.append(f"  - {facet}: {label}")

        # Recommendation
        same_objective = a["objective"] == b["objective"]
        if p["overall"] >= 80:
            if same_objective:
                rec = ("Consolidate into one campaign with rotating creative formats. These are "
                       "functionally the same campaign.")
            else:
                rec = ("Different objectives but very high targeting overlap. Add cross-exclusions "
                       "so each excludes the other's matched audiences. Or pause one if you can't "
                       "justify both objectives on the same audience.")
        elif p["overall"] >= 60:
            if same_objective:
                rec = ("Differentiate or exclude. Either narrow the targeting on one (different "
                       "industries, seniorities, or sizes) or add cross-exclusions on matched "
                       "audiences.")
            else:
                rec = ("Different funnel stages but overlapping audience. Acceptable if intentional "
                       "(awareness → lead gen), but worth confirming you want both running.")
        else:
            rec = "Light overlap — no action."
        out.append(f"- **Recommendation:** {rec}")
        out.append("")

    # Account-wide
    out.append("## Account-wide overlap density")
    out.append("")
    n_pairs = len(pairs)
    pct_overlap = (len(flagged) / n_pairs * 100) if n_pairs else 0
    out.append(f"- {pct_overlap:.0f}% of active-campaign pairs overlap by ≥60% ({len(flagged)} of {n_pairs} pairs)")
    out.append(f"- Estimated auction-overlap dollars across the account: "
               f"{fmt_money(total_overlap)}/day ≈ {fmt_money(total_overlap * 30)}/month")

    # Most-overlapping campaign — count appearances in flagged pairs
    appearance = {}
    for p in flagged:
        appearance[p["a"]["id"]] = appearance.get(p["a"]["id"], 0) + 1
        appearance[p["b"]["id"]] = appearance.get(p["b"]["id"], 0) + 1
    if appearance:
        worst_id = max(appearance, key=appearance.get)
        worst = next((a for a in actives if a["id"] == worst_id), None)
        if worst:
            out.append(f"- Most-overlapping campaign: **{worst['name']}** — appears in "
                       f"{appearance[worst_id]} high-overlap pair(s)")
    out.append("")

    # Headline
    out.append("---")
    out.append("")
    if not flagged:
        out.append("**Headline:** No significant overlap detected — campaigns are sufficiently differentiated.")
    else:
        out.append(
            f"**Headline:** {len(flagged)} overlapping pair(s) wasting ~{fmt_money(total_overlap)}/day "
            f"in auction competition. Top fix: address the {flagged[0]['a']['name']} ↔ "
            f"{flagged[0]['b']['name']} overlap ({fmt_money(flagged[0]['overlap_dollars'])}/day at stake)."
        )

    print("\n".join(out))


if __name__ == "__main__":
    main()
