#!/usr/bin/env python3
"""
LinkedIn Audience Health Check auditor.

Inputs (positional args, all JSON files):
  1. campaigns.json — list_linkedin_campaigns response
  2. analytics_prior.json — analytics for the prior 14-day window (pivot=CAMPAIGN)
  3. analytics_recent.json — analytics for the most-recent 14-day window (pivot=CAMPAIGN)
"""
import json
import sys
from collections import defaultdict
from datetime import datetime


def load(path):
    with open(path) as f:
        return json.load(f)


def fmt_dollars(amount):
    return f"${amount:,.0f}"


def parse_campaign_id(pivot_value):
    return pivot_value.replace("urn:li:sponsoredCampaign:", "")


def extract_targeting(campaign):
    """Pull audience URNs and other targeting facets out of targetingCriteria."""
    facets = {
        "matched_audiences": [],
        "dynamic_segments": [],
        "seniorities": [],
        "job_functions": [],
        "industries": [],
        "titles": [],
        "employers": [],
        "staff_count_includes": [],
        "staff_count_excludes": [],
    }
    tc = campaign.get("targetingCriteria", {})
    for clause in tc.get("include", {}).get("and", []):
        or_ = clause.get("or", {})
        for facet_urn, values in or_.items():
            if facet_urn == "urn:li:adTargetingFacet:audienceMatchingSegments":
                facets["matched_audiences"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:dynamicSegments":
                facets["dynamic_segments"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:seniorities":
                facets["seniorities"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:jobFunctions":
                facets["job_functions"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:industries":
                facets["industries"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:titles":
                facets["titles"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:employers":
                facets["employers"].extend(values)
            elif facet_urn == "urn:li:adTargetingFacet:staffCountRanges":
                facets["staff_count_includes"].extend(values)
    exclude_or = tc.get("exclude", {}).get("or", {})
    for facet_urn, values in exclude_or.items():
        if facet_urn == "urn:li:adTargetingFacet:staffCountRanges":
            facets["staff_count_excludes"].extend(values)
    return facets


def analyze(campaigns_resp, prior_resp, recent_resp):
    # Index analytics by campaign id
    def idx(resp):
        out = {}
        for row in resp.get("elements", []):
            cid = parse_campaign_id(row["pivotValues"][0])
            out[cid] = {
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "lp_clicks": int(row.get("landingPageClicks", 0)),
                "cost": float(row.get("costInLocalCurrency", 0)),
            }
        return out

    prior = idx(prior_resp)
    recent = idx(recent_resp)

    # Decorate every campaign with parsed targeting and analytics
    campaigns = []
    for c in campaigns_resp.get("elements", []):
        cid = str(c.get("id"))
        targeting = extract_targeting(c)
        db = c.get("dailyBudget") or {}
        campaigns.append({
            "id": cid,
            "name": c.get("name", "(unnamed)"),
            "status": c.get("status"),
            "serving_statuses": c.get("servingStatuses", []),
            "daily_budget": float(db.get("amount", 0)) if db else 0,
            "last_modified": c.get("changeAuditStamps", {}).get("lastModified", {}).get("time", 0),
            "objective": c.get("objectiveType"),
            "targeting": targeting,
            "prior": prior.get(cid, {"impressions": 0, "clicks": 0, "lp_clicks": 0, "cost": 0}),
            "recent": recent.get(cid, {"impressions": 0, "clicks": 0, "lp_clicks": 0, "cost": 0}),
        })

    # Build audience usage map (matched audiences only — dynamic segments tracked separately)
    matched_use = defaultdict(list)
    dynamic_use = defaultdict(list)
    for c in campaigns:
        for urn in c["targeting"]["matched_audiences"]:
            matched_use[urn].append(c)
        for urn in c["targeting"]["dynamic_segments"]:
            dynamic_use[urn].append(c)

    return campaigns, matched_use, dynamic_use


def section_count_holds(campaigns):
    held = [
        c for c in campaigns
        if any(
            s in {"CAMPAIGN_AUDIENCE_COUNT_HOLD", "AUDIENCE_COUNT_HOLD"}
            for s in c["serving_statuses"]
        )
    ]
    held.sort(key=lambda c: c["daily_budget"], reverse=True)
    return held


def section_decay(campaigns, decay_threshold=0.5, min_prior_impressions=1000):
    decayed = []
    for c in campaigns:
        # Only flag decay for campaigns that should be delivering. Paused / pending-deletion
        # campaigns having zero recent impressions is expected, not a stale-audience signal.
        if c["status"] != "ACTIVE":
            continue
        prior_i = c["prior"]["impressions"]
        recent_i = c["recent"]["impressions"]
        if prior_i < min_prior_impressions:
            continue
        # Skip campaigns where cost dropped proportionally (likely budget change, not audience decay)
        prior_cost = c["prior"]["cost"]
        recent_cost = c["recent"]["cost"]
        if prior_cost > 0 and (recent_cost / prior_cost) < 0.8 and abs((recent_cost / prior_cost) - (recent_i / max(prior_i, 1))) < 0.15:
            continue
        ratio = recent_i / prior_i if prior_i else 0
        if ratio < decay_threshold:
            decayed.append({
                "campaign": c,
                "prior_impr": prior_i,
                "recent_impr": recent_i,
                "decay_pct": (1 - ratio) * 100,
            })
    decayed.sort(key=lambda d: d["prior_impr"], reverse=True)
    return decayed


def render():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    campaigns_resp = load(sys.argv[1])
    prior_resp = load(sys.argv[2])
    recent_resp = load(sys.argv[3])

    campaigns, matched_use, dynamic_use = analyze(campaigns_resp, prior_resp, recent_resp)

    out = []
    out.append("# LinkedIn Audience Health Check")
    out.append("")

    active_campaigns = [c for c in campaigns if c["status"] == "ACTIVE"]
    paused_campaigns = [c for c in campaigns if c["status"] == "PAUSED"]
    out.append(
        f"**Scope:** {len(active_campaigns)} active campaigns, {len(paused_campaigns)} paused, "
        f"{len(campaigns)} total. **Comparison window:** trailing 14 days vs prior 14 days."
    )
    out.append("")

    # ===== Section A: count holds =====
    out.append("## 🛑 Section A — Delivery-blocked campaigns")
    out.append("")
    held = section_count_holds(campaigns)
    if not held:
        out.append("No campaigns currently delivery-blocked by `AUDIENCE_COUNT_HOLD`. ✅")
    else:
        total_held_daily = sum(c["daily_budget"] for c in held if c["status"] != "PENDING_DELETION")
        out.append(
            f"**{len(held)} campaign(s) blocked by audience count holds. "
            f"Estimated paused daily delivery: {fmt_dollars(total_held_daily)}/day.**"
        )
        out.append("")
        for c in held:
            audiences = c["targeting"]["matched_audiences"]
            dyn = c["targeting"]["dynamic_segments"]
            audience_str = f"{len(audiences)} matched audience(s)" + (f" + {len(dyn)} dynamic segment(s)" if dyn else "")
            if not audiences and not dyn:
                audience_str = "no audience layer — likely attribute-targeting count hold (audience definition too narrow)"
            out.append(
                f"- **{c['name']}** (id: `{c['id']}`, status: {c['status']}) — Daily budget: "
                f"{fmt_dollars(c['daily_budget'])}. Depends on: {audience_str}."
            )
            if audiences:
                for a in audiences[:5]:
                    sharing = len([cc for cc in matched_use[a] if cc["status"] == "ACTIVE"])
                    out.append(f"  - `{a}` — shared with {sharing - 1 if sharing > 0 else 0} other active campaign(s)")
            out.append(
                "  - **Action:** Open the campaign in Campaign Manager → Audiences → verify each "
                "matched audience has forecast size ≥ 300. If not, expand the source list, replace "
                "with a lookalike, or remove the failing audience from targeting."
            )
        out.append("")

    # ===== Section B: audience usage map =====
    out.append("## Section B — Audience usage map")
    out.append("")
    if not matched_use and not dynamic_use:
        out.append("No matched audiences or dynamic segments in use — all campaigns rely on attribute targeting only.")
    else:
        out.append(f"**Matched audiences in use:** {len(matched_use)} unique URNs across "
                   f"{sum(len(set(c['id'] for c in cs)) for cs in matched_use.values())} campaign-uses.")
        out.append(f"**Dynamic segments in use:** {len(dynamic_use)} unique URNs across "
                   f"{sum(len(set(c['id'] for c in cs)) for cs in dynamic_use.values())} campaign-uses.")
        out.append("")
        out.append("### Matched audiences (customer-uploaded — risk surface)")
        out.append("")

        # Build risk-sorted list. Risk scoring (highest wins):
        #   5 — 🛑 inside a delivery-blocked campaign (already broken)
        #   4 — 🔥 compound: shared between active campaigns AND sole audience for at least one of them
        #   3 — ⚠️ shared by 2+ active campaigns (auction overlap)
        #   2 — ⚠️ single-point-of-failure for an active campaign
        #   1 — ℹ️ only paused-campaign uses (candidate for removal)
        #   0 — ✓ normal
        scored = []
        for urn, used_by in matched_use.items():
            active_uses = [c for c in used_by if c["status"] == "ACTIVE"]
            paused_uses = [c for c in used_by if c["status"] == "PAUSED"]
            held_uses = [c for c in active_uses if any(
                s in {"CAMPAIGN_AUDIENCE_COUNT_HOLD", "AUDIENCE_COUNT_HOLD"} for s in c["serving_statuses"]
            )]
            sole_audience_campaigns = [
                c for c in active_uses
                if len(c["targeting"]["matched_audiences"]) == 1
            ]

            if held_uses:
                risk = "🛑 in a delivery-blocked campaign"
                risk_score = 5
            elif len(active_uses) >= 2 and sole_audience_campaigns:
                spof_names = ", ".join(c["name"] for c in sole_audience_campaigns)
                risk = (
                    f"🔥 shared by {len(active_uses)} active campaigns AND sole audience for "
                    f"{len(sole_audience_campaigns)} of them ({spof_names}) — worst-case audience risk"
                )
                risk_score = 4
            elif len(active_uses) >= 2:
                risk = f"⚠️ shared by {len(active_uses)} active campaigns — auction overlap risk"
                risk_score = 3
            elif sole_audience_campaigns:
                spof_names = ", ".join(c["name"] for c in sole_audience_campaigns)
                risk = f"⚠️ single-point-of-failure for {spof_names}"
                risk_score = 2
            elif len(active_uses) == 0 and paused_uses:
                risk = "ℹ️ only used by paused campaigns — candidate for removal if not in rotation"
                risk_score = 1
            else:
                risk = "✓ normal"
                risk_score = 0

            scored.append({
                "urn": urn,
                "active_uses": active_uses,
                "paused_uses": paused_uses,
                "risk": risk,
                "risk_score": risk_score,
            })

        scored.sort(key=lambda s: s["risk_score"], reverse=True)
        for s in scored[:25]:
            campaign_list = ", ".join(
                f"{c['name']} ({c['status'][:3]})" for c in s["active_uses"] + s["paused_uses"]
            )
            out.append(f"- `{s['urn']}` — {s['risk']}")
            out.append(f"  - Used by: {campaign_list}")

    out.append("")

    # ===== Section C: stale / declining =====
    out.append("## Section C — Stale / declining audiences (impression decay)")
    out.append("")
    decayed = section_decay(campaigns)
    if not decayed:
        out.append("No campaigns showing >50% impression decay over the trailing 14 days. ✅")
    else:
        for d in decayed:
            c = d["campaign"]
            matched = c["targeting"]["matched_audiences"]
            audience_note = (
                f"Single matched audience: `{matched[0]}` — likely the decay source."
                if len(matched) == 1
                else f"{len(matched)} matched audiences — can't attribute decay to one."
                if matched
                else "No matched audience — decay is from attribute targeting (audience definition aging out)."
            )
            out.append(
                f"- **{c['name']}** (id: `{c['id']}`) — Prior 14d: {d['prior_impr']:,} impressions. "
                f"Recent 14d: {d['recent_impr']:,}. **Decay: {d['decay_pct']:.0f}%.**"
            )
            out.append(f"  - {audience_note}")
            out.append(
                "  - **Action:** Refresh the matched audience source list. If sourced from HubSpot, "
                "check sync status. If list is fresh, the issue is match rate — try a re-upload with "
                "hashed-email columns added."
            )
    out.append("")

    # ===== Section D: type breakdown =====
    out.append("## Section D — Targeting layer breakdown")
    out.append("")
    only_matched = [c for c in active_campaigns if c["targeting"]["matched_audiences"] and not c["targeting"]["dynamic_segments"]]
    only_dynamic = [c for c in active_campaigns if c["targeting"]["dynamic_segments"] and not c["targeting"]["matched_audiences"]]
    both = [c for c in active_campaigns if c["targeting"]["matched_audiences"] and c["targeting"]["dynamic_segments"]]
    neither = [c for c in active_campaigns if not c["targeting"]["matched_audiences"] and not c["targeting"]["dynamic_segments"]]
    out.append(f"- Matched audiences only: {len(only_matched)} active campaigns")
    out.append(f"- Dynamic segments only: {len(only_dynamic)} active campaigns")
    out.append(f"- Both layers: {len(both)} active campaigns")
    out.append(f"- Pure attribute targeting (no audience layer): {len(neither)} active campaigns")
    out.append("")

    # ===== Section E: manual checklist =====
    out.append("## Section E — Manual validation checklist")
    out.append("")
    out.append("The LinkedIn MCP can't see audience sizes, sync recency, or match rates. Check these in Campaign Manager:")
    out.append("")
    flagged_audiences = set()
    for s in scored if matched_use else []:
        if s["risk_score"] >= 2:
            flagged_audiences.add(s["urn"])
    for d in decayed:
        for urn in d["campaign"]["targeting"]["matched_audiences"]:
            flagged_audiences.add(urn)
    if flagged_audiences:
        out.append("**Audiences to verify (high-priority — flagged in sections above):**")
        for urn in sorted(flagged_audiences):
            out.append(f"- `{urn}` — confirm forecast size ≥ 300, last sync ≤ 30 days, match rate ≥ 30%")
    else:
        out.append("- For any matched audience > 90 days old: rebuild from current source list.")
    out.append("")
    out.append("**Account-wide hygiene checks:**")
    out.append("- For each HubSpot-sourced audience: verify the HubSpot list sync is enabled and recent.")
    out.append("- For each website-retargeting audience: confirm the Insight Tag is firing on the relevant pages.")
    out.append("- For each Lookalike audience: confirm the seed audience is still ≥ 300 and has fresh signal.")
    out.append("- Remove matched audiences only used by paused campaigns if you're not planning to relaunch.")
    out.append("")

    # ===== Headline summary =====
    total_held_daily = sum(c["daily_budget"] for c in held if c["status"] != "PENDING_DELETION") if held else 0
    compound_count = sum(1 for s in scored if s["risk_score"] == 4) if matched_use else 0
    spof_count = sum(1 for s in scored if s["risk_score"] == 2) if matched_use else 0
    shared_count = sum(1 for s in scored if s["risk_score"] == 3) if matched_use else 0
    out.append("---")
    out.append("")
    risk_summary_parts = []
    if compound_count:
        risk_summary_parts.append(f"🔥 {compound_count} compound-risk audience(s) (shared + SPoF)")
    if shared_count:
        risk_summary_parts.append(f"{shared_count} shared-across-campaigns audience(s)")
    if spof_count:
        risk_summary_parts.append(f"{spof_count} single-point-of-failure audience(s)")
    risk_summary = ". ".join(risk_summary_parts) + "." if risk_summary_parts else "No compound or single-source audience risks detected."
    out.append(
        f"**Summary:** {len(held)} campaign(s) delivery-blocked "
        f"(~{fmt_dollars(total_held_daily)}/day unblocked-able). "
        f"{risk_summary} "
        f"{len(decayed)} campaign(s) showing >50% impression decay."
    )

    print("\n".join(out))


if __name__ == "__main__":
    render()
