#!/usr/bin/env python3
"""
LinkedIn Full Monty orchestrator.

Runs all sub-skill analyzer scripts against a shared data set and composes a unified report.

Expected directory layout (sub-skills are siblings of this skill):
  ../linkedin-auto-optimize/scripts/account_health.py
  ../linkedin-audience-health-check/scripts/audit_audiences.py
  ../linkedin-creative-fatigue-watchdog/scripts/score_creative_fatigue.py
  ../linkedin-targeting-overlap-finder/scripts/find_overlap.py
  ../linkedin-bid-strategy-audit/scripts/audit_bids.py
  ../linkedin-frequency-saturation-report/scripts/audit_frequency.py
  ../linkedin-lead-form-quality-auditor/scripts/audit_lead_forms.py
  ../linkedin-performance-digest/scripts/build_digest.py
  ../linkedin-demographic-deep-dive/scripts/analyze_demographics.py

Inputs (positional, paths to JSON files):
  1. campaigns.json
  2. creatives.json
  3. analytics_campaign_30d.json
  4. analytics_campaign_14d_prior.json
  5. analytics_campaign_14d_recent.json
  6. analytics_campaign_7d.json
  7. analytics_creative_14d_prior.json
  8. analytics_creative_14d_recent.json
  9. demo_seniority.json
  10. demo_function.json
  11. demo_size.json
  12. demo_industry.json
  13. taxonomy.json (for demographic deep dive)
"""
import os
import re
import subprocess
import sys


def find_skills_root(this_path):
    """Walk up from this script's path to find the skills/ directory."""
    here = os.path.dirname(os.path.abspath(this_path))
    # Walk up until we find a sibling that's a skill dir
    while here and here != "/":
        if os.path.basename(here) == "linkedin-full-monty":
            return os.path.dirname(here)
        here = os.path.dirname(here)
    return None


def run_script(script_path, args):
    """Run a sub-skill script and capture its stdout."""
    if not os.path.exists(script_path):
        return f"[skipped — script not found: {script_path}]"
    try:
        result = subprocess.run(
            ["python3", script_path] + args,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"[error running {os.path.basename(script_path)}: {result.stderr[:500]}]"
        return result.stdout
    except Exception as e:
        return f"[exception running {os.path.basename(script_path)}: {e}]"


def extract_headline(section_text):
    """Pull the headline/summary line from a sub-skill output, if present."""
    # Try the canonical patterns first, in priority order
    for pattern in [
        r"\*\*Headline:?\*\*\s*(.+?)(?:\n|$)",
        r"\*\*Summary:?\*\*\s*(.+?)(?:\n|$)",
    ]:
        m = re.search(pattern, section_text)
        if m:
            text = m.group(1).strip()
            # Strip trailing markdown noise
            return re.sub(r"\s+", " ", text)[:240]
    # Fallback: first non-header, non-list, non-table line over 30 chars
    for line in section_text.split("\n"):
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith("---")
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith(">")
            and not stripped.startswith("*")
            and len(stripped) > 30
        ):
            return stripped[:240]
    return "(no headline extracted)"


def main():
    if len(sys.argv) < 14:
        print(__doc__)
        sys.exit(1)

    (
        campaigns, creatives,
        analytics_30d, analytics_14d_prior, analytics_14d_recent, analytics_7d,
        creative_prior, creative_recent,
        demo_seniority, demo_function, demo_size, demo_industry, taxonomy,
    ) = sys.argv[1:14]

    skills_root = find_skills_root(__file__)
    if not skills_root:
        print("ERROR: couldn't find skills/ directory")
        sys.exit(1)

    # Run each sub-skill
    sections = {}
    sections["auto_optimize"] = run_script(
        os.path.join(skills_root, "linkedin-auto-optimize/scripts/account_health.py"),
        [campaigns, creatives, analytics_30d, analytics_7d],
    )
    sections["audience_health"] = run_script(
        os.path.join(skills_root, "linkedin-audience-health-check/scripts/audit_audiences.py"),
        [campaigns, analytics_14d_prior, analytics_14d_recent],
    )
    sections["overlap"] = run_script(
        os.path.join(skills_root, "linkedin-targeting-overlap-finder/scripts/find_overlap.py"),
        [campaigns],
    )
    sections["frequency"] = run_script(
        os.path.join(skills_root, "linkedin-frequency-saturation-report/scripts/audit_frequency.py"),
        [campaigns, analytics_30d],
    )
    sections["fatigue"] = run_script(
        os.path.join(skills_root, "linkedin-creative-fatigue-watchdog/scripts/score_creative_fatigue.py"),
        [creatives, campaigns, creative_prior, creative_recent],
    )
    sections["lead_forms"] = run_script(
        os.path.join(skills_root, "linkedin-lead-form-quality-auditor/scripts/audit_lead_forms.py"),
        [creatives, campaigns, creative_prior, creative_recent],
    )
    sections["demographics"] = run_script(
        os.path.join(skills_root, "linkedin-demographic-deep-dive/scripts/analyze_demographics.py"),
        [demo_seniority, demo_function, demo_size, demo_industry, campaigns, taxonomy],
    )
    sections["bids"] = run_script(
        os.path.join(skills_root, "linkedin-bid-strategy-audit/scripts/audit_bids.py"),
        [campaigns],
    )
    sections["digest"] = run_script(
        os.path.join(skills_root, "linkedin-performance-digest/scripts/build_digest.py"),
        [campaigns, analytics_14d_prior, analytics_14d_recent, creative_recent],
    )

    # Extract headlines for the priorities synthesis
    headlines = {k: extract_headline(v) for k, v in sections.items()}

    # ===== Compose output =====
    out = []
    out.append("# LinkedIn Full Monty — Complete Account Audit")
    out.append("")
    out.append("This is the full BlueAlpha LinkedIn audit suite composed into a single report.")
    out.append("")

    out.append("## Executive headline")
    out.append("")
    # Compose a meta-headline by reading the sub-headlines
    out.append(f"- **Structure (auto-optimize):** {headlines['auto_optimize']}")
    out.append(f"- **Audience health:** {headlines['audience_health']}")
    out.append(f"- **Auction overlap:** {headlines['overlap']}")
    out.append(f"- **Frequency:** {headlines['frequency']}")
    out.append(f"- **Creative fatigue:** {headlines['fatigue']}")
    out.append(f"- **Lead forms:** {headlines['lead_forms']}")
    out.append(f"- **Targeting drift (demographics):** {headlines['demographics']}")
    out.append(f"- **Bid configuration:** {headlines['bids']}")
    out.append(f"- **This-period performance:** {headlines['digest']}")
    out.append("")

    out.append("## 🚨 Top 5 priority actions")
    out.append("")
    out.append("*Cross-skill prioritized — synthesize manually from the section headlines above. "
               "Anchor each action to a section.*")
    out.append("")
    out.append("> The orchestrator script identifies the per-section findings. Synthesize the top "
               "5 across all sections by reading the section outputs below and ranking by estimated "
               "dollar impact. Highest-leverage actions usually come from auto-optimize (structural "
               "blockers), audience-health (count holds), and demographic-deep-dive (targeting "
               "drift dollars).")
    out.append("")

    # Append each section
    section_order = [
        ("Structure & Health (auto-optimize)", "auto_optimize"),
        ("Audiences — Health", "audience_health"),
        ("Audiences — Auction Overlap", "overlap"),
        ("Audiences — Frequency Saturation", "frequency"),
        ("Creatives — Fatigue Watchdog", "fatigue"),
        ("Creatives — Lead Form Quality", "lead_forms"),
        ("Targeting & Segments — Demographic Deep Dive", "demographics"),
        ("Bid & Configuration Audit", "bids"),
        ("Performance Digest (period-over-period)", "digest"),
    ]
    for title, key in section_order:
        out.append("---")
        out.append("")
        out.append(f"# {title}")
        out.append("")
        # Sub-skill outputs already contain their own H1 — strip it so we don't double up
        text = sections[key]
        # Remove the first H1 line from the embedded section (we have our own)
        lines = text.split("\n")
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines.pop(0)
        out.append("\n".join(lines))
        out.append("")

    # Recommended cadence
    out.append("---")
    out.append("")
    out.append("# Recommended cadence going forward")
    out.append("")
    out.append("Schedule via the Cowork schedule tool. Suggested cadence:")
    out.append("")
    out.append("- **Weekly (Monday morning):** `linkedin-auto-optimize`, `linkedin-performance-digest`")
    out.append("- **Bi-weekly:** `linkedin-creative-fatigue-watchdog`, `linkedin-audience-health-check`")
    out.append("- **Monthly:** `linkedin-targeting-overlap-finder`, `linkedin-frequency-saturation-report`, `linkedin-bid-strategy-audit`")
    out.append("- **Quarterly:** `linkedin-demographic-deep-dive`, `linkedin-lead-form-quality-auditor`, `linkedin-full-monty` (this skill)")

    print("\n".join(out))


if __name__ == "__main__":
    main()
