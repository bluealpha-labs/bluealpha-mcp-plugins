---
name: meta-capi-signal-health
description: Audit the measurement signal feeding Meta (Facebook/Instagram) — Conversions API (CAPI) coverage and deduplication, pixel/browser event health, Event Match Quality (EMQ), Aggregated Event Measurement (AEM 8-event) priority, attribution settings (7d-click/1d-view), and iOS/SKAN coverage — to decide whether Meta's reported conversions can even be trusted before acting on them. Use when the user says "Meta signal health", "is my CAPI working", "Event Match Quality", "pixel vs CAPI dedup", "Meta attribution settings", "AEM 8 events", "SKAN / iOS tracking on Meta", "why is Meta under-reporting conversions", or wants to validate Meta's conversion signal. Run BEFORE trusting Meta CPA/ROAS in any other skill.
---

Read references/workflow.md for the full workflow. Tool surface: see ../meta-auto-optimize/references/meta-mcp-tools.md (verified `facebook_ads_*` — verify against the live connector). Some checks are configuration-level and require manual validation in Events Manager (checklist provided).
