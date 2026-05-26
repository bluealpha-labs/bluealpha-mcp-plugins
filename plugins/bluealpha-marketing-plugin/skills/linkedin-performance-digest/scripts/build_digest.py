#!/usr/bin/env python3
"""LinkedIn Performance Digest — generates a narrative period-over-period report."""
import json
import sys


def load(p):
    with open(p) as f:
        return json.load(f)


def fmt_money(x):
    return f"${x:,.0f}"


def fmt_pct(x):
    return f"{x*100:+.0f}%"


def parse_campaign_id(urn):
    return urn.replace("urn:li:sponsoredCampaign:", "")


def parse_creative_id(urn):
    return urn.replace("urn:li:sponsoredCreative:", "")


def aggregate(rows):
    tot = {"impressions": 0, "clicks": 0, "lp_clicks": 0, "cost": 0, "leads": 0, "conversions": 0}
    for r in rows:
        tot["impressions"] += int(r.get("impressions", 0))
        tot["clicks"] += int(r.get("clicks", 0))
        tot["lp_clicks"] += int(r.get("landingPageClicks", 0))
        tot["cost"] += float(r.get("costInLocalCurrency", 0))
        tot["leads"] += int(r.get("oneClickLeads", 0))
        tot["conversions"] += int(r.get("externalWebsiteConversions", 0))
    return tot


def pct(new, old):
    if old == 0:
        return None
    return (new - old) / old


def fmt_delta(new, old, fmt):
    pct_change = pct(new, old)
    if pct_change is None:
        return f"{fmt(new)} (prior: {fmt(old)})"
    return f"{fmt(new)} ({fmt_pct(pct_change)} vs prior {fmt(old)})"


def index_by_campaign(rows):
    out = {}
    for r in rows:
        cid = parse_campaign_id(r["pivotValues"][0])
        out[cid] = aggregate([r])
    return out


def index_by_creative(rows):
    out = {}
    for r in rows:
        cid = parse_creative_id(r["pivotValues"][0])
        out[cid] = aggregate([r])
    return out


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    campaigns_resp = load(sys.argv[1])
    campaign_prior = load(sys.argv[2])
    campaign_recent = load(sys.argv[3])
    creative_recent = load(sys.argv[4])

    campaign_name = {str(c.get("id")): c.get("name", "?") for c in campaigns_resp.get("elements", [])}
    campaign_status = {str(c.get("id")): c.get("status") for c in campaigns_resp.get("elements", [])}

    prior = aggregate(campaign_prior.get("elements", []))
    recent = aggregate(campaign_recent.get("elements", []))

    by_campaign_prior = index_by_campaign(campaign_prior.get("elements", []))
    by_campaign_recent = index_by_campaign(campaign_recent.get("elements", []))
    by_creative_recent = index_by_creative(creative_recent.get("elements", []))

    # Per-campaign deltas
    deltas = []
    all_cids = set(by_campaign_prior) | set(by_campaign_recent)
    for cid in all_cids:
        p = by_campaign_prior.get(cid, {})
        r = by_campaign_recent.get(cid, {})
        deltas.append({
            "id": cid,
            "name": campaign_name.get(cid, f"id:{cid}"),
            "prior_cost": p.get("cost", 0),
            "recent_cost": r.get("cost", 0),
            "delta_cost": r.get("cost", 0) - p.get("cost", 0),
            "prior_clicks": p.get("clicks", 0),
            "recent_clicks": r.get("clicks", 0),
            "prior_lp": p.get("lp_clicks", 0),
            "recent_lp": r.get("lp_clicks", 0),
            "delta_lp": r.get("lp_clicks", 0) - p.get("lp_clicks", 0),
            "prior_leads": p.get("leads", 0),
            "recent_leads": r.get("leads", 0),
            "delta_leads": r.get("leads", 0) - p.get("leads", 0),
        })

    # Sort by absolute cost delta — biggest movers
    deltas.sort(key=lambda d: abs(d["delta_cost"]), reverse=True)

    # Top creatives by recent spend
    creatives_sorted = sorted(by_creative_recent.items(), key=lambda kv: kv[1].get("cost", 0), reverse=True)[:3]

    # Account-level metrics
    cpc_prior = (prior["cost"] / prior["clicks"]) if prior["clicks"] else 0
    cpc_recent = (recent["cost"] / recent["clicks"]) if recent["clicks"] else 0
    cplpc_prior = (prior["cost"] / prior["lp_clicks"]) if prior["lp_clicks"] else 0
    cplpc_recent = (recent["cost"] / recent["lp_clicks"]) if recent["lp_clicks"] else 0

    # ===== Output =====
    out = []
    out.append("# LinkedIn Performance Digest — BlueAlpha")
    out.append("")
    out.append("")

    # Headline — pick the most narratively useful summary
    cost_change = pct(recent["cost"], prior["cost"])
    leads_change = pct(recent["leads"], prior["leads"]) if prior["leads"] else None

    # Build the headline
    if cost_change is None:
        headline = "First-period report — no prior comparison available."
    elif abs(cost_change) < 0.05 and (leads_change is None or abs(leads_change or 0) < 0.1):
        headline = (
            f"Quiet period — spend essentially flat ({fmt_pct(cost_change)}). "
            f"No new audience or creative dynamics worth flagging."
        )
    else:
        cost_phrase = f"Spend {fmt_pct(cost_change)}"
        if leads_change is not None:
            lead_phrase = f"leads {fmt_pct(leads_change)}"
        else:
            lp_change = pct(recent["lp_clicks"], prior["lp_clicks"])
            lead_phrase = f"landing-page clicks {fmt_pct(lp_change) if lp_change is not None else 'flat'}"
        top_mover = deltas[0] if deltas else None
        if top_mover and abs(top_mover["delta_cost"]) > 50:
            direction = "drove the increase" if top_mover["delta_cost"] > 0 else "drove the decline"
            mover_pct = pct(top_mover["recent_cost"], top_mover["prior_cost"])
            if mover_pct is None:
                # New campaign — no prior baseline
                detail = f"new in window, {fmt_money(top_mover['recent_cost'])} spent"
            else:
                detail = f"{fmt_pct(mover_pct)} in that campaign, +{fmt_money(top_mover['delta_cost'])}"
            headline = (
                f"{cost_phrase}; {lead_phrase}; **{top_mover['name']}** {direction} "
                f"({detail})."
            )
        else:
            headline = f"{cost_phrase}; {lead_phrase}."

    out.append(f"**Headline.** {headline}")
    out.append("")

    # What happened
    out.append("## What happened")
    out.append("")
    out.append(
        f"Over the trailing window, the account spent **{fmt_delta(recent['cost'], prior['cost'], fmt_money)}** "
        f"across {recent['impressions']:,} impressions "
        f"(vs {prior['impressions']:,} prior). Clicks totaled "
        f"{fmt_delta(recent['clicks'], prior['clicks'], lambda x: f'{x:,}')}, with "
        f"{fmt_delta(recent['lp_clicks'], prior['lp_clicks'], lambda x: f'{x:,}')} reaching landing pages. "
    )
    extras = []
    if recent['leads'] > 0 or prior['leads'] > 0:
        extras.append(f"Lead Gen submissions: {fmt_delta(recent['leads'], prior['leads'], lambda x: str(x))}")
    if recent['conversions'] > 0 or prior['conversions'] > 0:
        extras.append(f"Website conversions: {fmt_delta(recent['conversions'], prior['conversions'], lambda x: str(x))}")
    if extras:
        out.append(". ".join(extras) + ".")
    out.append(
        f"CPC moved to {fmt_money(cpc_recent)} from {fmt_money(cpc_prior)} "
        f"({fmt_pct(pct(cpc_recent, cpc_prior)) if pct(cpc_recent, cpc_prior) is not None else '—'}), "
        f"cost per landing-page click moved to {fmt_money(cplpc_recent)} from {fmt_money(cplpc_prior)}."
    )
    out.append("")

    # What drove it
    out.append("## What drove it")
    out.append("")
    movers = [d for d in deltas[:3] if abs(d["delta_cost"]) > 50]
    if not movers:
        out.append("No single campaign moved spend by more than $50 — performance was distributed evenly.")
    else:
        for d in movers:
            direction_word = "added" if d["delta_cost"] > 0 else "shed"
            out.append(
                f"- **{d['name']}** {direction_word} {fmt_money(abs(d['delta_cost']))} "
                f"in spend ({fmt_money(d['prior_cost'])} → {fmt_money(d['recent_cost'])}); "
                f"landing-page clicks went from {d['prior_lp']} to {d['recent_lp']}"
                + (f", leads from {d['prior_leads']} to {d['recent_leads']}." if (d['recent_leads'] or d['prior_leads']) else ".")
            )

        # Top creatives by recent spend
        if creatives_sorted:
            out.append("")
            out.append("Top creatives by recent spend:")
            for crid, metrics in creatives_sorted:
                out.append(
                    f"- `{crid}` — {fmt_money(metrics['cost'])} on {metrics['impressions']:,} impressions, "
                    f"{metrics['clicks']} clicks, {metrics['lp_clicks']} LP clicks, "
                    f"{metrics['leads']} leads."
                )
    out.append("")

    # What to watch
    out.append("## What to watch")
    out.append("")
    watch_items = []
    # Detect any campaign with major decay — only flag ACTIVE campaigns (paused ones dropping to $0 is expected)
    for d in deltas:
        if d["prior_cost"] > 100 and d["recent_cost"] < d["prior_cost"] * 0.5:
            if campaign_status.get(d["id"]) == "ACTIVE":
                watch_items.append(
                    f"- **{d['name']}** — spend dropped from {fmt_money(d['prior_cost'])} to "
                    f"{fmt_money(d['recent_cost'])} on an ACTIVE campaign. Likely an audience-count or pacing issue worth checking."
                )
    # CPC creep
    if pct(cpc_recent, cpc_prior) and pct(cpc_recent, cpc_prior) > 0.15:
        watch_items.append(
            f"- CPC climbed {fmt_pct(pct(cpc_recent, cpc_prior))} period-over-period. "
            f"Check for auction-overlap (run `linkedin-targeting-overlap-finder`) or creative fatigue."
        )
    # CPLPC creep
    if pct(cplpc_recent, cplpc_prior) and pct(cplpc_recent, cplpc_prior) > 0.20:
        watch_items.append(
            f"- Cost per landing-page click climbed {fmt_pct(pct(cplpc_recent, cplpc_prior))}. "
            f"Either traffic-quality is degrading or landing page is converting fewer clicks."
        )
    if not watch_items:
        watch_items.append("- No leading indicators of trouble. Continue monitoring.")
    out.extend(watch_items)
    out.append("")

    # Slack one-liner
    out.append("---")
    out.append("")
    one_liner = (
        f"*LinkedIn — spend {fmt_money(recent['cost'])} ({fmt_pct(cost_change) if cost_change is not None else 'no prior'}), "
        f"{recent['lp_clicks']:,} LP clicks "
        f"({fmt_pct(pct(recent['lp_clicks'], prior['lp_clicks'])) if pct(recent['lp_clicks'], prior['lp_clicks']) is not None else '—'}), "
        f"{recent['leads']} leads"
    )
    if movers:
        one_liner += f". Top mover: {movers[0]['name']}*"
    else:
        one_liner += "*"
    out.append(one_liner)

    print("\n".join(out))


if __name__ == "__main__":
    main()
