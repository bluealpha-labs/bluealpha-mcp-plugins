# BlueAlpha Marketing Plugin

A Claude-powered toolkit for performance marketers and analytics teams. Talk to Claude in plain English and get back account audits, keyword strategies, geo expansion plans, audience reviews, creative refresh ideas, full incrementality test designs, MMM-driven budget reallocations, saturation diagnostics, channel deep-dives, per-channel trust routing, attribution reconciliation, quarterly scenario plans, TikTok-native creative-fatigue, audience, and geo-holdout workflows, the complete LinkedIn Ads audit suite, and the full Meta (Facebook/Instagram) audit suite — all backed by your live Google Ads + Meta Ads + TikTok Ads + LinkedIn Ads data and BlueAlpha's Meridian marketing mix model.

No spreadsheets. No SQL. No agency lag.

## Who this is for

Performance marketers, growth leads, in-house Google Ads / Meta / TikTok / LinkedIn owners, and analytics teams who want a senior media strategist *and* a senior MMM analyst in their corner without paying senior-strategist hourly rates.

## What's inside

**Google Ads skills (10):**

- `auto-optimize` — full-account optimization cycle
- `audience-intelligence` — audience performance and targeting refinement
- `brand-refresh-pipeline` — creative fatigue detection and ad copy generation
- `competitive-conquest` — competitor research and conquest campaign specs
- `competitive-counterpunch` — auction-share defense planning
- `content-to-campaign` — turn content into paid campaign briefs
- `full-monty` — run everything end-to-end
- `geo-expansion-scout` — new market identification
- `incrementality-test-runner` — geo-holdout test design and monitoring
- `seo-paid-bridge` — organic/paid coverage gap analysis

**MMM skills (10):**

Foundational analysis:

- `mmm-budget-reallocator` — simulate a budget shift and project revenue lift with credible intervals
- `mmm-saturation-report` — flag saturated vs. headroom channels with per-channel runway
- `mmm-health-check` — overall trust grade (A/B/C/F) for the model: convergence, prior dominance, fit
- `mmm-performance-digest` — weekly/monthly MMM read in the BlueAlpha narrative format
- `mmm-launch-timing` — *"if I launch now, when do I see the impact?"* — adstock + saturation timing per channel
- `mmm-channel-deep-dive` — comprehensive single-channel read with cut/hold/scale/test verdict

Confidence, testing, and planning:

- `mmm-trust-router` — per-channel "Trust MMM / Validate first / Model insufficient" classifier
- `mmm-test-roadmap` — quarterly incrementality testing calendar from trust-router output
- `mmm-attribution-reconciler` — MMM channel ROI vs. platform-reported ROAS, with disagreement routing
- `mmm-scenario-planner` — 3-5 budget scenarios side-by-side with comparison matrix

**TikTok Ads skills (9):**

- `tiktok-auto-optimize` — full TikTok account optimization cycle
- `tiktok-audience-intelligence` — AUDIENCE-report driven demo/DMA/placement tiering
- `tiktok-content-to-campaign` — turn content into a TikTok campaign spec
- `tiktok-creative-fatigue-watchdog` — hook/hold/completion/CTR decay detection
- `tiktok-creative-refresh` — 5-concept creative brief production
- `tiktok-full-monty` — orchestrator that runs all 9 TikTok skills in sequence
- `tiktok-geo-expansion` — DMA-level market scouting and prioritization
- `tiktok-incrementality-test` — TikTok geo-holdout design and monitoring
- `tiktok-performance-digest` — weekly/monthly TikTok narrative read

**LinkedIn Ads skills (10, new in v0.5.0):**

Read what's happening:

- `linkedin-auto-optimize` — account health cycle (score, blockers, pacing, structure)
- `linkedin-performance-digest` — weekly/monthly LinkedIn narrative read
- `linkedin-demographic-deep-dive` — spend vs intended targeting by seniority / job function / company size / industry

Decide what to do with audiences and bids:

- `linkedin-audience-health-check` — count holds, compound-risk audiences, single-point-of-failure, decay
- `linkedin-targeting-overlap-finder` — Jaccard-based auction overlap detection between own campaigns
- `linkedin-frequency-saturation-report` — cap configuration audit + impression-intensity proxy
- `linkedin-bid-strategy-audit` — cost-type, optimization-target, creative-selection sanity check

Decide what to do with creatives:

- `linkedin-creative-fatigue-watchdog` — objective-aware CTR/engagement decay scoring
- `linkedin-lead-form-quality-auditor` — Lead Gen Form health, orphan-form cleanup, cost-per-lead

Run the whole audit:

- `linkedin-full-monty` — orchestrator that composes all nine sub-skills into one report

**Meta Ads skills (12, new in v0.6.0):**

Mirror of the TikTok suite:

- `meta-auto-optimize` — full-account optimization cycle (structure, CBO/ABO, learning-phase, pacing, budget)
- `meta-creative-fatigue-watchdog` — frequency / thumb-stop / CTR / relevance decay, via the live `creative_fatigue_*` engine
- `meta-creative-refresh` — winning-DNA audit → 5-concept brief
- `meta-audience-intelligence` — demo / geo / device + prospecting-vs-retargeting + Advantage+ Audience
- `meta-content-to-campaign` — content asset → build-ready Meta campaign spec
- `meta-geo-expansion` — geo tiering, expansion candidates, drain cleanup
- `meta-incrementality-test` — geo holdout / Conversion Lift design, via the live `incrementality_*` tools
- `meta-performance-digest` — weekly/monthly Meta narrative read
- `meta-full-monty` — orchestrator that runs the whole Meta suite in dependency order

Meta-specific (no TikTok/Google analogue):

- `meta-advantage-plus-audit` — ASC / Advantage+ Audience / CBO / Advantage+ Creative; existing-customer harvesting check
- `meta-placement-performance` — publisher_platform × platform_position; Audience Network waste audit
- `meta-capi-signal-health` — CAPI/dedup, Event Match Quality, AEM 8-event, attribution, SKAN/iOS — gates trust in every CPA/ROAS

## What you can ask it to do

Once installed, just talk to Claude. Some prompts to try:

**Google Ads:**

- *"Audit my Google Ads account and tell me what to fix first."*
- *"Find new geographic markets I should be testing."*
- *"My CTR is dropping — is it creative fatigue?"*
- *"Help me build a conquest campaign against Competitor X."*
- *"Design a geo holdout test to prove my brand campaign is incremental."*

**MMM — foundational:**

- *"If I move $50K/week from Meta to YouTube, what does the model say happens to revenue?"*
- *"Which of my channels are saturated and which still have headroom?"*
- *"Should I trust this MMM? Show me where the priors are doing the work."*
- *"If I turn TikTok on tomorrow, when will I see the lift?"*
- *"Give me the full read on Meta — ROI, saturation, decay, where it sits vs. the rest of the mix."*
- *"Give me the monthly MMM digest for the Net New Customers KPI."*

**MMM — confidence, testing, planning:**

- *"Which channels can I act on directly, and which need a test first?"*
- *"Build me a quarterly testing roadmap given a $200K test budget."*
- *"Reconcile what Google Ads is saying vs. what the MMM is saying — where do they disagree?"*
- *"Compare these three budget scenarios side by side and tell me which one to ship."*

**TikTok Ads:**

- *"Check TikTok creative fatigue on my account — which videos are tired?"*
- *"Give me the monthly TikTok performance digest."*
- *"Design a TikTok geo holdout test."*
- *"Build the full TikTok review and tell me what to fix."*
- *"Which TikTok DMAs and demos are converting? Where should I expand?"*

**LinkedIn Ads:**

- *"Run auto-optimize on my LinkedIn account and tell me what's blocking delivery."*
- *"Who is actually clicking my LinkedIn ads by job function and seniority?"*
- *"Find the LinkedIn campaigns on my account that are bidding against each other."*
- *"Why isn't my LinkedIn Lead Gen campaign delivering? Run the audience health check."*
- *"Should my LinkedIn campaigns be on OPTIMIZED or ROUND_ROBIN creative selection?"*
- *"Generate the weekly LinkedIn performance digest."*
- *"Run the full LinkedIn account audit and give me the top 5 priority actions."*

**Meta Ads (Facebook/Instagram):**

- *"Optimize my Meta account and tell me what to fix first."*
- *"Can I trust my Meta conversions? Run the CAPI signal health check."*
- *"Which of my Meta creatives are fatiguing? Check frequency and CTR decay."*
- *"Break my Meta spend down by placement — is Audience Network wasting money?"*
- *"Is Advantage+ Shopping actually working, or just harvesting existing customers?"*
- *"Run the full Meta audit and give me a prioritized action plan."*

The plugin walks you through the answer, asks follow-up questions if it needs context, and produces strategy documents and analyses you can take straight to your team or your weekly review.

## Skill hand-off pattern

The MMM skills are designed to compose. A typical end-to-end planning cycle:

1. **`mmm-health-check`** — confirm the model is trustworthy
2. **`mmm-trust-router`** — classify each channel: act vs. test vs. fix
3. **`mmm-attribution-reconciler`** — surface where platform data and MMM disagree
4. **`mmm-test-roadmap`** — schedule the tests for Validate-first and Model-insufficient channels
5. **`mmm-scenario-planner`** — compare candidate budget plans side-by-side
6. **`mmm-budget-reallocator`** — translate the chosen plan into a specific shift
7. **`mmm-launch-timing`** — project the week-by-week ramp
8. **`incrementality-test-runner`** — for any test scheduled in step 4, design and monitor

Each skill stands alone, but the chain is the planning loop.

LinkedIn skills follow a parallel pattern. Recommended cadence:

- **Weekly:** `linkedin-auto-optimize`, `linkedin-performance-digest`
- **Bi-weekly:** `linkedin-creative-fatigue-watchdog`, `linkedin-audience-health-check`
- **Monthly:** `linkedin-targeting-overlap-finder`, `linkedin-frequency-saturation-report`, `linkedin-bid-strategy-audit`
- **Quarterly:** `linkedin-demographic-deep-dive`, `linkedin-lead-form-quality-auditor`, `linkedin-full-monty`

## Setup

### Step 1 — Install the BlueAlpha MCP connector

1. Open Settings in the Claude desktop app
2. Go to Connectors → Add custom connector
3. Name it: `BlueAlpha MCP`
4. URL: `https://mcp.bluealpha.ai/mcp`
5. Click Connect and sign in with your BlueAlpha account

That single sign-in wires Claude up to your Meridian models, your Google Ads accounts, your Meta Ads accounts, your TikTok Ads accounts, and your LinkedIn Ads accounts (whichever you have). No keys, no IDs, no config files.

### Step 2 — Install the plugin

Pick the path that matches the Claude product you're using.

#### Option A — Cowork (drag-and-drop)

1. Go to [github.com/bluealpha-labs/bluealpha-mcp-plugins](https://github.com/bluealpha-labs/bluealpha-mcp-plugins)
2. Click Releases on the right rail and open the latest release (currently v0.6.2)
3. Expand Assets and click `bluealpha-marketing-plugin.plugin` to download
4. Drag the downloaded file into an open Cowork session and click Install when prompted

That's it. No CLI, no settings menu — one drag.

#### Option B — Claude Code (slash commands)

Inside Claude Code, run these two commands:

```
/plugin marketplace add https://github.com/bluealpha-labs/bluealpha-mcp-plugins.git
/plugin install bluealpha-marketing-plugin
```

The first registers the GitHub repo as a marketplace; the second installs the plugin from it. The same plugin contains the Google Ads, MMM, TikTok Ads, LinkedIn Ads, and Meta Ads skills — you install once, the right skill triggers based on what you ask.

## Versioning

- **v0.6.2** (current) — Trimmed the plugin + marketplace manifest descriptions to a safe margin under the 500-character Cowork install limit (v0.6.1 sat at exactly 500 bytes). No skill changes. Total skill count: 51.
- **v0.6.1** — Verified the Meta tool bindings live against a real Meta account: the connector exposes Meta under the `facebook_ads_*` family (not `meta_ads_*`), and all 12 Meta skills are bound to it. No skill additions. Total skill count: 51.
- **v0.6.0** — Added 12 Meta (Facebook/Instagram) Ads skills: auto-optimize, creative-fatigue-watchdog, creative-refresh, audience-intelligence, content-to-campaign, geo-expansion, incrementality-test, performance-digest, full-monty, plus three Meta-specific skills — advantage-plus-audit (ASC / Advantage+), placement-performance (publisher_platform × platform_position), and capi-signal-health (CAPI/dedup/EMQ/AEM/SKAN). Two skills are partially gated by current connector coverage (advantage-plus-audit and capi-signal-health) — each surfaces the limitation and produces a manual-validation checklist. Total skill count: 51.
- **v0.5.1** — Shortened the plugin manifest description to satisfy the 500-character limit (the v0.5.0 description blocked installation in Claude Cowork). No skill changes. Skill count unchanged: 39.
- **v0.5.0** — Added 10 LinkedIn Ads skills: auto-optimize, performance-digest, demographic-deep-dive, audience-health-check, targeting-overlap-finder, frequency-saturation-report, bid-strategy-audit, creative-fatigue-watchdog, lead-form-quality-auditor, and full-monty orchestrator. Three of the LinkedIn skills (audience-health-check, frequency-saturation-report, lead-form-quality-auditor) work as configuration audits + indirect signals due to current LinkedIn API constraints — each surfaces the limitation explicitly and produces a manual-validation checklist. Total skill count: 39.
- **v0.4.0** — Added 9 TikTok Ads skills: auto-optimize, audience-intelligence, content-to-campaign, creative-fatigue-watchdog, creative-refresh, full-monty, geo-expansion, incrementality-test, and performance-digest. Total skill count: 29.
- **v0.3.0** — Added 10 MMM skills covering budget reallocation, saturation, model health-check, performance digest, launch timing, channel deep-dive, trust routing, quarterly test roadmaps, MMM-vs-platform attribution reconciliation, and scenario planning.
- **v0.2.0** — Initial 10 Google Ads skills.
