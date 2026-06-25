# BlueAlpha Plugins for Claude Growth Marketers

Turn Claude into a senior paid-media strategist and marketing-mix-model (MMM) analyst. The **BlueAlpha Marketing Plugin** lets you audit ad accounts, reallocate budget, and design incrementality tests across **Google Ads, TikTok Ads, and LinkedIn Ads** — by asking questions in plain English. No spreadsheets, no SQL, no dashboards.

This is BlueAlpha's official public marketplace for Claude plugins. It's free to add, installs in two commands, and works in both **Claude Code** and **Claude Cowork**.

## What is the BlueAlpha Marketing Plugin?

The BlueAlpha Marketing Plugin is a Claude plugin — a bundle of **39 skills** — built for performance marketers and analytics teams. It connects Claude to your **Google Ads, TikTok Ads, and LinkedIn Ads** accounts plus a **Meridian marketing mix model**, then runs audits, analysis, and media-planning workflows through natural conversation.

It is **analysis-first**: every skill reads your live data and returns recommendations, diagnostics, and plans. Actually executing changes is routed through the BlueAlpha pipeline — the plugin does not make unsupervised edits to your ad accounts.

## What can it do?

The plugin covers four areas of paid-media work.

### Google Ads optimization (10 skills)

Full-account audits, audience analysis and targeting refinement, creative-fatigue detection with ad-copy generation, competitor conquest campaigns, auction-share defense, SEO-and-paid coverage-gap analysis, new-market geo expansion, and geo-holdout incrementality test design.

### TikTok Ads management (9 skills)

TikTok account optimization, hook/hold/completion creative-fatigue scoring, creative-brief production, audience and DMA tiering, geo expansion, geo-holdout incrementality testing, content-to-campaign specs, and weekly/monthly performance digests.

### LinkedIn Ads auditing (10 skills)

LinkedIn account health checks, audience-health and targeting-overlap analysis, bid-strategy and frequency-cap audits, creative-fatigue scoring, Lead Gen Form quality auditing, demographic deep-dives (spend vs. intended targeting by seniority, job function, company size, and industry), performance digests, and a full-account orchestrator.

### Marketing mix modeling & incrementality (10 skills)

Budget-reallocation simulation with credible intervals, saturation and diminishing-returns analysis, model trust grading (convergence, prior dominance, fit), per-channel "act vs. test" routing, MMM-vs-platform attribution reconciliation, adstock and launch-timing projection, quarterly incrementality test roadmaps, and side-by-side budget scenario planning.

➡️ **Full skill list, example prompts, and recommended cadence:** see the [plugin README](./plugins/bluealpha-marketing-plugin/README.md).

## Who is it for?

Performance marketers, growth leads, paid-media managers, in-house Google Ads / TikTok / LinkedIn owners, and marketing analytics teams who want senior media-strategist and MMM-analyst judgment on demand — without senior-strategist hourly rates or agency lag.

## Example questions you can ask

Once installed, you talk to Claude in plain English. For example:

- *"Audit my Google Ads account and tell me what to fix first."*
- *"Which of my channels are saturated and which still have headroom?"*
- *"If I move $50K/week from Meta to YouTube, what does the MMM say happens to revenue?"*
- *"Run the full LinkedIn account audit and give me the top 5 priority actions."*
- *"Check TikTok creative fatigue — which videos are tired?"*
- *"Design a geo holdout test to prove my brand campaign is incremental."*
- *"Reconcile what Google Ads is reporting vs. what the MMM says — where do they disagree?"*

Claude routes each question to the right skill, pulls your live data, and walks you through the answer.

## How it works

The plugin ships **skills** — structured, repeatable workflows Claude follows. Each skill calls the **BlueAlpha MCP connector** (`https://mcp.bluealpha.ai/mcp`), which securely reads your ad-platform and marketing-mix-model data. You install once; Claude selects the right skill based on what you ask.

## Install

In **Claude Code**, type:

```
/plugin marketplace add https://github.com/bluealpha-labs/bluealpha-plugins.git
/plugin install bluealpha-marketing-plugin
```

The first time you use a skill, Claude prompts you to connect your BlueAlpha account — one sign-in, with no API keys or account IDs to copy.

### Prefer a file install (Claude Cowork)?

Download the single `.plugin` file from the [latest release](https://github.com/bluealpha-labs/bluealpha-plugins/releases/latest) and drag it into a Cowork session. Click **Install** when prompted.

## What data does it connect to?

A BlueAlpha account and the BlueAlpha MCP connector. Through that one connection, the plugin reads whichever of these you have connected: **Google Ads**, **TikTok Ads**, **LinkedIn Ads**, and your **Meridian marketing mix model**. Don't have a BlueAlpha account yet? Visit [bluealpha.ai](https://bluealpha.ai).

## Frequently asked questions

**What is a Claude plugin?**
A Claude plugin is a packaged set of skills (reusable, structured workflows) plus connectors that extend what Claude can do. The BlueAlpha Marketing Plugin adds 39 paid-media and MMM skills to Claude.

**Does it change my ad campaigns automatically?**
No. The plugin is analysis-only. It reads your data and returns recommendations; any execution is routed through the BlueAlpha pipeline, not performed directly by Claude.

**Which ad platforms are supported?**
Google Ads, TikTok Ads, and LinkedIn Ads — plus Meridian-based marketing mix modeling (MMM) and geo-holdout incrementality testing.

**Do I need to know SQL or build dashboards?**
No. You ask questions in plain English; the plugin pulls the live data and analyzes it for you.

**Is it free?**
Adding the marketplace and installing the plugin is free. The skills require a connected BlueAlpha account.

**Does it work in both Claude Code and Claude Cowork?**
Yes. Install via slash commands in Claude Code, or drag the `.plugin` file into Claude Cowork.

**What is a marketing mix model (MMM)?**
A marketing mix model is a statistical model that estimates how each marketing channel contributes to revenue, accounting for diminishing returns and carry-over (adstock) effects. BlueAlpha uses Meridian-based MMM to ground budget and incrementality recommendations.

## Available plugins

| Plugin | What it does | Skills |
| --- | --- | --- |
| **bluealpha-marketing-plugin** | Paid media strategy, analysis, and measurement for Google Ads, TikTok Ads, and LinkedIn Ads, with Meridian MMM and incrementality testing. [Read more →](./plugins/bluealpha-marketing-plugin/README.md) | 39 |

## Support

Questions or access requests: email **ai@bluealpha.ai** or visit [bluealpha.ai](https://bluealpha.ai).
