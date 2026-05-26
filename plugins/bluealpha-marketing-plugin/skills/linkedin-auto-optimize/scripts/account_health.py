#!/usr/bin/env python3
"""
LinkedIn Auto-Optimize account health cycle.

Inputs (positional):
  1. campaigns.json — list_linkedin_campaigns
  2. creatives.json — list_linkedin_creatives
  3. analytics_30d.json — pivot=CAMPAIGN, trailing 30 days
  4. analytics_7d.json — pivot=CAMPAIGN, trailing 7 days
"""
import json
import sys
from collections import defaultdict


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


def parse_campaign_id(urn):
    return urn.replace("urn:li:sponsoredCampaign:", "")


def index_analytics(resp):
    out = {}
    for row in resp.get("elements", []):
        cid = parse_campaign_id(row["pivotValues"][0])
        out[cid] = {
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "cost": float(row.get("costInLocalCurrency", 0)),
        }
    return out


def classify_campaign(c, recent_7d_analytics, serving_creative_count):
    """Return (state, all_blockers) where blockers is a list of specific blocker labels."""
    blockers = []
    status = c.get("status")
    serving_statuses = c.get("servingStatuses", [])

    if "BILLING_HOLD" in serving_statuses:
        blockers.append("BLOCKED-BILLING")
    if "CAMPAIGN_GROUP_STATUS_HOLD" in serving_statuses:
        blockers.append("BLOCKED-GROUP")
    if "AUDIENCE_COUNT_HOLD" in serving_statuses or "CAMPAIGN_AUDIENCE_COUNT_HOLD" in serving_statuses:
        blockers.append("BLOCKED-AUDIENCE")
    if status == "ACTIVE" and serving_creative_count == 0:
        blockers.append("BLOCKED-NO-CREATIVES")

    if status == "PENDING_DELETION":
        return "PENDING-DELETION", blockers
    if status == "PAUSED":
        return "PAUSED", blockers
    if blockers:
        return "BLOCKED", blockers
    if status == "ACTIVE":
        recent = recent_7d_analytics.get(str(c.get("id")), {})
        if recent.get("impressions", 0) == 0:
            return "LIVE-DORMANT", blockers
        return "LIVE-OK", blockers
    return "UNKNOWN", blockers


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    campaigns_resp = load(sys.argv[1])
    creatives_resp = load(sys.argv[2])
    analytics_30d_resp = load(sys.argv[3])
    analytics_7d_resp = load(sys.argv[4])

    analytics_30d = index_analytics(analytics_30d_resp)
    analytics_7d = index_analytics(analytics_7d_resp)

    # Count serving creatives per campaign
    serving_count = defaultdict(int)
    rejected_count = defaultdict(int)
    for creative in creatives_resp.get("elements", []):
        cid = parse_campaign_id(creative.get("campaign", ""))
        if creative.get("isServing"):
            serving_count[cid] += 1
        review_status = (creative.get("review") or {}).get("status")
        if review_status in ("REJECTED", "REVIEW_FAILED"):
            rejected_count[cid] += 1

    # Classify every campaign
    campaigns = []
    for c in campaigns_resp.get("elements", []):
        cid = str(c.get("id"))
        state, blockers = classify_campaign(c, analytics_7d, serving_count[cid])
        db = c.get("dailyBudget") or {}
        daily_budget = float(db.get("amount", 0)) if db else 0
        recent_7d = analytics_7d.get(cid, {})
        recent_30d = analytics_30d.get(cid, {})
        recent_7d_cost = recent_7d.get("cost", 0)
        # Pacing: 7-day cost / (daily_budget * 7)
        pacing_rate = (recent_7d_cost / (daily_budget * 7)) if daily_budget > 0 else None
        campaigns.append({
            "id": cid,
            "name": c.get("name", "(unnamed)"),
            "status": c.get("status"),
            "state": state,
            "blockers": blockers,
            "serving_statuses": c.get("servingStatuses", []),
            "daily_budget": daily_budget,
            "pacing_strategy": c.get("pacingStrategy"),
            "objective": c.get("objectiveType"),
            "recent_7d_cost": recent_7d_cost,
            "recent_30d_cost": recent_30d.get("cost", 0),
            "recent_7d_impressions": recent_7d.get("impressions", 0),
            "pacing_rate": pacing_rate,
            "rejected_creatives": rejected_count[cid],
            "serving_creatives": serving_count[cid],
        })

    # Compute account-level numbers
    active = [c for c in campaigns if c["status"] == "ACTIVE"]
    paused = [c for c in campaigns if c["status"] == "PAUSED"]
    pending_del = [c for c in campaigns if c["status"] == "PENDING_DELETION"]
    blocked = [c for c in campaigns if c["state"] == "BLOCKED"]
    dormant = [c for c in campaigns if c["state"] == "LIVE-DORMANT"]
    live_ok = [c for c in campaigns if c["state"] == "LIVE-OK"]

    total_daily_active = sum(c["daily_budget"] for c in active)
    delivering_daily = sum(c["daily_budget"] for c in live_ok)
    utilization = (delivering_daily / total_daily_active * 100) if total_daily_active > 0 else 0

    # Severity-weighted issues
    # The key insight: a blocker on a PAUSED campaign isn't blocking current delivery.
    # It's a cleanup task — surface it, but don't crater the health score over it.
    issues = []
    for c in campaigns:
        # Blockers on ACTIVE campaigns are severity 5 (real delivery problem).
        # Blockers on PAUSED or PENDING_DELETION campaigns are severity 2 (cleanup, not blocking delivery).
        for b in c["blockers"]:
            if c["status"] == "ACTIVE":
                issues.append({"campaign": c, "blocker": b, "severity": 5})
            elif c["status"] == "PAUSED":
                issues.append({"campaign": c, "blocker": b, "severity": 2, "context": "on paused campaign"})
            # PENDING_DELETION blockers are noise — don't surface
        if c["state"] == "LIVE-OK" and c["pacing_rate"] is not None and c["pacing_rate"] < 0.5:
            issues.append({"campaign": c, "blocker": "UNDER-PACING", "severity": 4})
        if c["state"] == "LIVE-DORMANT" and c["status"] == "ACTIVE":
            issues.append({"campaign": c, "blocker": "DORMANT-ACTIVE", "severity": 3})
        if c["rejected_creatives"] > 0 and c["status"] == "ACTIVE":
            issues.append({"campaign": c, "blocker": "REJECTED-CREATIVES", "severity": 4})
        if c["status"] == "PENDING_DELETION" and c["recent_30d_cost"] > 0:
            issues.append({"campaign": c, "blocker": "PENDING-DEL-STILL-SERVING", "severity": 2})

    # Health score
    score = 100 - sum(i["severity"] * 2 for i in issues)
    score = max(0, min(100, score))
    score = (score // 5) * 5
    if score >= 85:
        score_label = "Healthy"
    elif score >= 70:
        score_label = "Minor issues"
    elif score >= 50:
        score_label = "Several issues, needs attention"
    elif score >= 30:
        score_label = "Multiple blockers"
    else:
        score_label = "Account is largely broken; immediate intervention needed"

    # ===== Output =====
    out = []
    out.append("# LinkedIn Auto-Optimize")
    out.append("")
    out.append(f"**Health score: {score}/100 — {score_label}**")
    out.append("")
    out.append(
        f"**Total daily budget on active campaigns:** {fmt_money(total_daily_active)}/day  "
    )
    out.append(
        f"**Estimated daily budget actually delivering:** {fmt_money(delivering_daily)}/day "
        f"({utilization:.0f}% utilization)  "
    )
    out.append(
        f"**Campaigns:** {len(active)} active ({len(live_ok)} delivering, {len(dormant)} dormant, "
        f"{len(blocked)} blocked), {len(paused)} paused, {len(pending_del)} pending deletion"
    )
    out.append("")

    # 🚨 Blockers
    out.append("## 🚨 Blockers (resolve first)")
    out.append("")
    blocker_issues = [i for i in issues if i["severity"] == 5]
    if blocker_issues:
        # Group by campaign, sort by daily budget
        seen = set()
        for i in sorted(blocker_issues, key=lambda i: -i["campaign"]["daily_budget"]):
            cid = i["campaign"]["id"]
            if cid in seen:
                continue
            seen.add(cid)
            c = i["campaign"]
            all_blockers = ", ".join(c["blockers"])
            out.append(
                f"- **{c['name']}** (id: `{c['id']}`, status: {c['status']}, "
                f"daily budget: {fmt_money(c['daily_budget'])}) — blockers: {all_blockers}"
            )
            if "BLOCKED-AUDIENCE" in c["blockers"]:
                out.append("  - **Next:** Run `linkedin-audience-health-check` to identify the failing audience.")
            if "BLOCKED-BILLING" in c["blockers"]:
                out.append("  - **Next:** Check billing in Campaign Manager → Account settings.")
            if "BLOCKED-NO-CREATIVES" in c["blockers"]:
                out.append("  - **Next:** Add ≥1 active creative or pause this campaign.")
            if "BLOCKED-GROUP" in c["blockers"]:
                out.append("  - **Next:** Resolve the campaign group status (often a group-level pause or budget issue).")
    else:
        out.append("No structural blockers detected. ✅")
    out.append("")

    # 🟠 Pacing
    out.append("## 🟠 Pacing issues")
    out.append("")
    pacing_issues = [i for i in issues if i["blocker"] == "UNDER-PACING"]
    if pacing_issues:
        for i in pacing_issues:
            c = i["campaign"]
            out.append(
                f"- **{c['name']}** — Daily budget: {fmt_money(c['daily_budget'])}, "
                f"actual 7-day pace: {fmt_money(c['recent_7d_cost']/7)}/day "
                f"({c['pacing_rate']*100:.0f}% utilization)."
            )
            out.append(
                "  - **Next:** Check audience size (count-hold edge case), bid floor, "
                "or creative serving status. If healthy, consider increasing bids."
            )
    else:
        out.append("No under-pacing campaigns detected. ✅")
    out.append("")

    # 🟡 Hygiene
    out.append("## 🟡 Structure hygiene")
    out.append("")
    hygiene_issues = [i for i in issues if i["severity"] in (2, 3)]
    paused_blocker_issues = [i for i in hygiene_issues if "context" in i and i["context"] == "on paused campaign"]
    other_hygiene = [i for i in hygiene_issues if i not in paused_blocker_issues]

    if paused_blocker_issues:
        # Group paused-campaign blockers by campaign
        seen = set()
        out.append("**Paused-campaign issues** (will block delivery if you unpause without fixing):")
        for i in sorted(paused_blocker_issues, key=lambda i: -i["campaign"]["daily_budget"]):
            cid = i["campaign"]["id"]
            if cid in seen:
                continue
            seen.add(cid)
            c = i["campaign"]
            all_blockers = ", ".join(c["blockers"])
            out.append(
                f"- **{c['name']}** (daily budget if resumed: {fmt_money(c['daily_budget'])}) — "
                f"blockers waiting: {all_blockers}"
            )
        out.append("")

    if other_hygiene:
        for i in other_hygiene:
            c = i["campaign"]
            if i["blocker"] == "DORMANT-ACTIVE":
                out.append(
                    f"- **{c['name']}** — Status ACTIVE but zero impressions in last 7 days. "
                    f"Daily budget: {fmt_money(c['daily_budget'])}."
                )
                out.append("  - **Next:** Either resolve the underlying delivery issue or pause.")
            elif i["blocker"] == "PENDING-DEL-STILL-SERVING":
                out.append(
                    f"- **{c['name']}** — Status PENDING_DELETION but had "
                    f"{fmt_money(c['recent_30d_cost'])} spend in last 30d. Cleanup."
                )

    if not paused_blocker_issues and not other_hygiene:
        out.append("No structure hygiene issues detected. ✅")
    out.append("")

    # Routing
    out.append("## Routing — what to do next")
    out.append("")
    if score >= 85:
        out.append("- Account is healthy. Move to deeper analysis:")
        out.append("  - `linkedin-demographic-deep-dive` to find targeting waste at the seniority/function/industry/size layer")
        out.append("  - `linkedin-creative-fatigue-watchdog` to score per-creative engagement decay")
        out.append("  - `linkedin-targeting-overlap-finder` if multiple campaigns share audiences")
    else:
        if any(i["blocker"] == "BLOCKED-AUDIENCE" for i in issues):
            out.append("- Run **`linkedin-audience-health-check`** for the full count-hold audit and audience risk surface.")
        if any(i["blocker"] == "UNDER-PACING" for i in issues):
            out.append("- Investigate the under-pacing campaigns — usually audience-count edge or bid-floor issues.")
        if any(i["blocker"] == "REJECTED-CREATIVES" for i in issues):
            out.append("- Resolve rejected creatives in Campaign Manager before proceeding to other optimization.")
        out.append("- After resolving blockers, re-run this skill to confirm health score recovers, then proceed to demographic / creative analysis.")
    out.append("")

    # Headline — branch on whether there are ACTIVE blockers vs cleanup-only issues
    out.append("---")
    out.append("")
    active_blocker_count = sum(1 for i in issues if i["severity"] == 5)
    pacing_issue_count = sum(1 for i in issues if i["blocker"] == "UNDER-PACING")
    paused_blocker_count = sum(1 for i in issues if i.get("context") == "on paused campaign")

    if score >= 85:
        out.append("**Headline:** Account is structurally healthy — proceed to performance optimization.")
    elif active_blocker_count > 0:
        out.append(
            f"**Headline:** {active_blocker_count} active campaign(s) blocked from delivering. "
            f"Fix structure first, then optimize performance."
        )
    elif pacing_issue_count > 0:
        out.append(
            f"**Headline:** Active campaigns are delivering, but {pacing_issue_count} campaign(s) "
            f"under-pacing significantly. {paused_blocker_count} paused-campaign cleanup task(s) "
            f"queued. Investigate pacing first."
        )
    else:
        out.append(
            f"**Headline:** Active delivery is healthy. {paused_blocker_count} paused-campaign "
            f"cleanup task(s) to resolve before any unpause. Otherwise account is in good shape."
        )

    print("\n".join(out))


if __name__ == "__main__":
    main()
