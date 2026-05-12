# MMM Performance Digest — Detailed Workflow

The job: produce the recurring MMM read — weekly or monthly — that a marketing leader actually reads. A scoreboard, a what-changed, and a what-to-watch, in the BlueAlpha narrative format. Not a data dump.

## Phase 0: Confirm Scope

1. **Pick the model:**
   ```
   list_models()
   ```
   If multiple KPIs are modeled (e.g., "Net New Customers" and "Revenue"), confirm which one the user wants the digest for. Most weekly digests are run on the primary revenue KPI; planning digests are sometimes run on a leading-indicator KPI.

2. **Confirm cadence:**
   - **Weekly digest** — last 1 week vs. previous 1 week, plus 4-week context
   - **Monthly digest** — last 4 weeks vs. previous 4 weeks, plus 12-week context
   - **Custom** — user-specified window

3. **Pull the model summary** for headline channels and time range:
   ```
   get_model_summary(model=<kpi_name>)
   ```

## Phase 1: The Scoreboard

Top-line numbers. The user reads this first.

```
get_reconciled_overview(model=<kpi_name>, last_n_weeks=<window>)
```

Capture:
- **Total revenue** in the window
- **Total paid spend** in the window
- **Overall ROI** (revenue / spend)
- **CAC** (cost per acquisition, if KPI is acquisition-based)
- **Baseline revenue** — the organic / always-on portion the model attributes outside of paid

If `rpk` shows any fallbacks (scale=1.0 with reason), note that the revenue numbers may underweight channels without registered revenue-per-KPI conversions.

Format the scoreboard as a small numeric block:

```
Window: <last N weeks>
Revenue:       $X.XM    (Y% vs prior period)
Paid spend:    $X.XM    (Y% vs prior period)
ROI:           X.Xx     (Y% vs prior period)
Baseline:      $X.XM    (Y% of revenue)
```

## Phase 2: Period-over-Period Change

```
get_reconciled_revenue_comparison(
  model=<kpi_name>,
  current_last_n_weeks=<window>,
  previous_last_n_weeks=<window>
)
```

This is the headline what-changed. For each metric (revenue, spend, ROI, CAC), report:
- Current window value
- Previous window value
- Percent change
- Absolute change

Call out the largest movers — anything that moved by more than 10% is worth a sentence. Don't just list percentages; tell the user *why* it moved if the model gives you signal. Combine with Phase 3 channel attribution to construct the why.

## Phase 3: Per-Channel Performance

```
query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=<window>)
```

Returns the per-channel scoreboard for the window: spend, revenue, incremental KPI, ROI, CAC, share %. Sorted by spend desc.

Build the channel table:

| Channel | Weekly spend | Revenue | ROI | Share of paid revenue | Δ ROI vs prior period |
|---|---|---|---|---|---|
| Meta | $120K | $130K | 1.1x | 18% | -12% |
| Google Search | $80K | $240K | 3.0x | 33% | +4% |
| YouTube | $40K | $180K | 4.5x | 25% | +18% |
| ... | ... | ... | ... | ... | ... |

Compute the per-channel ROI delta by running `query_reconciled_performance_table` for the previous window and joining.

## Phase 4: Weekly Trend

```
get_reconciled_channel_contributions(model=<kpi_name>, last_n_weeks=12, top_n=5)
```

A 12-week (or 4-week for weekly digest) channel contribution trend, top 5 by spend with everything else collapsed into "Other". Use this to:

1. Spot **trending channels** — channels whose contribution is steadily rising or falling over the trailing window, not just one bad/good week.
2. Spot **noise** — channels whose contribution oscillates without an obvious spend pattern. These are signs the decomposition is fitting noise.
3. Anchor the **what-to-watch** call-outs in Phase 6.

Note: the "Other" bucket in this response is NOT the organic baseline — it's smaller paid channels collapsed together. The true baseline is on `get_reconciled_overview.last_week_totals.baseline_kpi`.

## Phase 5: The Narrative

The BlueAlpha digest style is three paragraphs, not bullet vomit.

### Paragraph 1 — What happened
A one-paragraph plain-English read on the scoreboard and the period-over-period change. Lead with the headline number (revenue change), explain the spend context (did we spend more, less, or about the same), and name the single biggest contributor to the change.

Example: *"Revenue this month landed at $4.2M, up 9% over last month, on slightly higher spend (+3%). The lift was disproportionately driven by YouTube, whose contribution rose 18% as the new creative entered market. Meta declined for a third consecutive month and is now contributing less than its spend share would imply."*

### Paragraph 2 — Channel detail
A paragraph anchored on the channel table. Don't recite the table — pick the 3-4 stories worth telling. Format: best performer, worst performer, biggest mover (up or down), any channel where ROI diverged sharply from prior period.

### Paragraph 3 — What to watch
Forward-looking. What does next period look like? What's saturated, what's trending, what's at risk? This paragraph should link to recommended next actions — usually `mmm-saturation-report` for headroom planning, `mmm-budget-reallocator` for proposed shifts, or an incrementality test to validate a surprise mover.

## Phase 6: Output

Deliver to the user:

1. **The scoreboard** (Phase 1) — top-line block
2. **The period-over-period table** (Phase 2)
3. **The channel table** (Phase 3) — sorted by spend
4. **A 12-week (or 4-week for weekly) contribution chart** described in prose, with the top movers called out (Phase 4)
5. **The three-paragraph narrative** (Phase 5)
6. **Recommended follow-on skill** — saturation, reallocator, deep-dive, or incrementality test — based on what the data is screaming

## Inputs to Ask For

1. **Model / KPI** — which model (required; use `list_models` if unknown)
2. **Cadence** — weekly, monthly, or custom window (required)
3. **Audience** — exec (paragraphs only) vs. operator (full tables + paragraphs) (optional; default: full)
4. **KPI-to-revenue conversion** — if rpk isn't registered for the model, ask whether to report in KPI units or convert via a manual rate (optional)
5. **Prior digest reference** — if this is a recurring digest, pull last period's digest to anchor trend language (optional)

## Important Notes

- **Don't write the same digest every week.** If nothing meaningfully changed, say so. "ROI was flat, spend was flat, no major channel moves" is a perfectly valid digest paragraph. Pretending every week has a story is how digests stop being read.
- **Per-period change percentages are noisy at the channel level for short windows.** Weekly per-channel ROI changes can swing ±20% on small denominators. Don't lead with a percentage if the underlying spend is small. Use absolute dollar deltas instead.
- **Always reconciled, never raw, for the digest.** The reconciled numbers match the dashboard. The raw posterior numbers will not, and using them in a digest creates "why does this contradict the dashboard" follow-ups that distract from the read.
- **Caveat with model trust.** If a recent `mmm-health-check` flagged the model as B or worse, lead the digest with the trust grade. The narrative can still be useful but the user should know the foundation.
- **Recurring schedule:** the right cadence for this skill is automated — weekly on Monday morning, monthly on the 1st. Suggest setting up a scheduled task if the user runs this manually.
