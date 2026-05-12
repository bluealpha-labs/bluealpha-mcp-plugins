# BlueAlpha Marketing Plugin

A Claude-powered toolkit for performance marketers and analytics teams. Talk to Claude in plain English and get back account audits, keyword strategies, geo expansion plans, audience reviews, creative refresh ideas, full incrementality test designs, MMM-driven budget reallocations, saturation diagnostics, channel deep-dives, per-channel trust routing, attribution reconciliation, and quarterly scenario plans — all backed by your live Google Ads data and BlueAlpha's Meridian marketing mix model.

No spreadsheets. No SQL. No agency lag.

## Who this is for

Performance marketers, growth leads, in-house Google Ads owners, and analytics teams who want a senior media strategist *and* a senior MMM analyst in their corner without paying senior-strategist hourly rates.

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

Confidence, testing, and planning (new in v0.4):

- `mmm-trust-router` — per-channel "Trust MMM / Validate first / Model insufficient" classifier
- `mmm-test-roadmap` — quarterly incrementality testing calendar from trust-router output
- `mmm-attribution-reconciler` — MMM channel ROI vs. platform-reported ROAS, with disagreement routing
- `mmm-scenario-planner` — 3-5 budget scenarios side-by-side with comparison matrix

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

## Setup

### Step 1 — Install the BlueAlpha MCP connector

1. Open Settings in the Claude desktop app
2. Go to Connectors → Add custom connector
3. Name it: `BlueAlpha MCP`
4. URL: `https://mcp.bluealpha.ai/mcp`
5. Click Connect and sign in with your BlueAlpha account

That single sign-in wires Claude up to your Meridian models (and your Google Ads accounts, if you have them). No keys, no IDs, no config files.

### Step 2 — Install the plugin

Pick the path that matches the Claude product you're using.

#### Option A — Cowork (drag-and-drop)

1. Go to [github.com/bluealpha-labs/bluealpha-plugins](https://github.com/bluealpha-labs/bluealpha-plugins)
2. Click Releases on the right rail and open the latest release (currently v0.3.0)
3. Expand Assets and click `bluealpha-marketing-plugin.plugin` to download
4. Drag the downloaded file into an open Cowork session and click Install when prompted

That's it. No CLI, no settings menu — one drag.

#### Option B — Claude Code (slash commands)

Inside Claude Code, run these two commands:

```
/plugin marketplace add https://github.com/bluealpha-labs/bluealpha-plugins.git
/plugin install bluealpha-marketing-plugin
```

The first registers the GitHub repo as a marketplace; the second installs the plugin from it. The same plugin contains both the Google Ads skills and the MMM skills — you install once, the right skill triggers based on what you ask.

## Versioning

- **v0.3.0** (current) — Added 10 MMM skills covering budget reallocation, saturation, model health-check, performance digest, launch timing, channel deep-dive, trust routing, quarterly test roadmaps, MMM-vs-platform attribution reconciliation, and scenario planning.
- **v0.2.0** — Initial 10 Google Ads skills.
