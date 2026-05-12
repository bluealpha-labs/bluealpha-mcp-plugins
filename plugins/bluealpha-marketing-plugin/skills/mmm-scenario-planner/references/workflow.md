# MMM Scenario Planner — Detailed Workflow

The job: take 3-5 candidate budget mixes and run them all through the MMM simulator at the same time, producing one comparison matrix. The marketer is choosing between alternatives, not optimizing a single shift — and "compare these three plans" is a different conversation from "should I move $50K from Meta to YouTube." This skill is the quarterly-planning artifact: the side-by-side that goes in front of leadership when picking next quarter's mix.

Pairs with `mmm-budget-reallocator` (use it for the single-shift question), `mmm-saturation-report` (use it to generate scenario candidates), and `mmm-trust-router` (apply trust caveats per scenario).

## Phase 0: Frame the Scenarios

Two paths to a scenario set.

### Path A — User-defined scenarios

The user comes in with 2-4 specific plans to compare. Examples:
- *"Plan A: hold current. Plan B: cut Meta 20%, add to YouTube. Plan C: cut Meta 20%, split between YouTube and TikTok."*
- *"Aggressive: pile into YouTube. Defensive: maintain everything. Reallocator-recommended: whatever the MMM says."*

Capture each scenario as a `proposed_budgets` dict and confirm dollar amounts back to the user before simulating. Add the always-on **Scenario 0 = Status Quo** if not already included — every scenario comparison needs the no-change baseline.

### Path B — Skill-generated scenarios

The user wants the skill to propose a useful set. Generate four scenarios spanning the strategic decision space:

1. **Status Quo** — current mix unchanged. Always Scenario 0.
2. **Headroom Capture** — shift budget from low-mROI channels into the highest-mROI channels. The MMM's "best mathematical" answer. Use `get_marginal_roi` ordering.
3. **Defensive** — modest moves within ±10%, preserving channel diversity. Trades off some projected lift for lower variance and lower confound risk.
4. **Bold** — bigger moves than the user would normally make, typically 25-40% shifts on 1-2 channels. Stress-tests whether the model's projection holds up at the edge of training range.

Optionally add a fifth scenario based on a known qualitative input the user provides — e.g., "we want a scenario where we test TikTok with a $50K bump."

Always tag each scenario with a one-line strategic descriptor — leadership decision conversations need labels, not just dollar deltas.

## Phase 1: Baseline Anchor

```
list_models()
get_model_summary(model=<kpi_name>)
query_reconciled_performance_table(model=<kpi_name>, last_n_weeks=4)
get_reconciled_overview(model=<kpi_name>, last_n_weeks=4)
```

Capture current per-channel weekly spend (Scenario 0), current paid revenue, current total revenue (paid + baseline), current overall ROI. These are the comparison baseline for every other scenario.

## Phase 2: Validate Scenario Inputs

For each scenario, sanity-check the proposed budget dict before simulating:

1. **Channel names match the model's channel list** — typos or aliased names will produce silent errors or simulate against a channel that doesn't exist.
2. **No negative budgets.**
3. **Total spend matches the user's intent.** If the user said "this is a reallocation" the sum should equal current total spend ± a small rounding tolerance. If the user said "this is +$50K total," verify the sum reflects that. Pure-reallocation accidents from incorrect dict math are the most common bug in this skill.
4. **Operating points inside training range** — pull `get_raw_saturation_curves` to get the observed spend max per channel. Flag any proposed channel-level spend that exceeds 1.25× the observed max. The projection on extrapolation channels will have wide credible intervals; the user should see that flag before reading too much into the point estimate.

If any scenario fails validation, show the user what's off and ask to confirm or revise before continuing.

## Phase 3: Run All Simulations

For each scenario (including Status Quo as a sanity-check baseline):

```
simulate_budget_reallocation(
  model=<kpi_name>,
  proposed_budgets=<scenario_dict>,
  n_weeks=4,
  credible_interval=0.9
)
```

Use the same `n_weeks` projection horizon across all scenarios so they're directly comparable. 4 weeks is the default; 12 weeks for quarterly planning conversations.

Capture per scenario:
- **Projected incremental KPI** (median, low, high)
- **Projected revenue** (median, low, high), if RPK is registered
- **Per-channel projected contribution** (where the simulator surfaces it)

## Phase 4: Compute Scenario Metrics

For each scenario relative to Status Quo:

| Metric | Calculation |
|---|---|
| **Total spend delta** | Scenario spend − Status Quo spend |
| **Projected revenue delta** | Scenario revenue − Status Quo revenue |
| **Projected revenue % change** | Delta / Status Quo revenue |
| **Marginal $ per $ shifted** | Revenue delta / Total spend delta (or absolute spend reallocated, for pure-reallocation scenarios) |
| **Confidence width** | (High − Low) / Median of projected revenue |
| **Worst-case revenue** | The low end of the credible interval. The "what does the CFO see if this goes badly" number. |
| **Best-case revenue** | The high end. |

Also compute a **risk-adjusted score** combining expected gain and CI width:

> risk_adjusted_score = (median_revenue_delta) − 0.5 × (CI_width × baseline_revenue)

This penalizes scenarios with wide credible intervals — useful when comparing a bold scenario with high expected lift but wide uncertainty against a defensive scenario with smaller but tighter projected lift.

## Phase 5: Trust-Router Overlay

A scenario's projection inherits the trust of its underlying channels. Pull the trust-router routing (or run it) and tag each scenario with a trust caveat:

- **All movements happen on Trust-MMM channels** → "Decision-grade projection. Act on this scenario's number directly."
- **Some movements involve Validate-first channels** → "Scenario lift is plausible but unconfirmed for the [Channel X, Channel Y] portions. Recommend running the test before committing to this scenario."
- **Movements onto Model-insufficient channels** → "The projection for [Channel Z] is largely the prior. Treat this scenario's lift as a directional estimate, not a forecast."

Don't disqualify scenarios that involve uncertain channels — those scenarios are often the most interesting strategically — but make the uncertainty visible. A scenario that requires acting on a Model-insufficient channel needs a test scheduled before it ships.

## Phase 6: The Comparison Matrix

The headline deliverable. Format as a side-by-side table with scenarios as columns:

```
                              Status Quo    Headroom    Defensive    Bold
Total weekly spend             $400K         $400K       $400K        $400K
Projected weekly revenue       $1.20M        $1.27M      $1.23M       $1.34M
Δ vs Status Quo                —             +$70K       +$30K        +$140K
Δ %                            —             +5.8%       +2.5%        +11.7%
90% credible interval          —             [+$40K,    [+$18K,      [+$60K,
                                              +$100K]     +$42K]       +$220K]
Marginal $ per $ shifted       —             $2.20       $1.50         $1.80
Risk-adjusted score            0             +$52K       +$26K        +$95K
Trust caveat                   —             1 Validate  All Trust    2 Validate
                                              channel                  channels
                                              (YouTube)               (YouTube, TikTok)
```

Sort columns left-to-right: Status Quo first, then scenarios ordered by risk-adjusted score descending. This puts the strongest scenario nearest the baseline for easy comparison.

## Phase 7: Per-Channel View

Below the headline matrix, a second table showing per-channel spend per scenario — so the user can see exactly what each plan does:

```
Channel              Status Quo    Headroom    Defensive    Bold
Google Search        $100K         $105K       $103K        $110K
Meta                 $120K         $96K        $108K        $84K
YouTube              $40K          $64K        $48K         $90K
TikTok               $15K          $15K        $15K         $25K
Display              $50K          $40K        $48K         $40K
... (others)         ...           ...         ...          ...
                     —————         —————       —————        —————
Total                $400K         $400K       $400K        $400K
```

This is the table that gets screenshotted into the planning deck.

## Phase 8: Strategic Reads

Three paragraphs of narrative. Don't make leadership read the matrix and guess at the recommendation.

### Paragraph 1 — What the matrix says

The headline result. Which scenario produces the most lift, what it costs, what it requires. Plain language.

### Paragraph 2 — Trade-offs

The honest comparison. Bold has higher upside but wider uncertainty and requires acting on channels the model isn't fully confident on. Defensive trades some projected lift for tighter confidence. Status Quo is the "do nothing" anchor — what the user gives up by not moving.

### Paragraph 3 — Recommendation

A clear pick, with conditions. Format: *"Of the four scenarios, [name] offers the best risk-adjusted return at $X projected lift with credible interval $[low, high]. Two prerequisites before shipping: (1) run the [channel] incrementality test currently slotted in week 3 of the test roadmap, and (2) cap the [channel] shift at half the proposed magnitude in week 1, with a 2-week check-in before completing the move."*

The recommendation should always carry conditions when any scenario component touches a Validate-first or Model-insufficient channel.

## Phase 9: Output

Deliver to the user:

1. **The comparison matrix** (Phase 6) — headline numbers per scenario
2. **The per-channel view** (Phase 7) — exact spend allocations per scenario
3. **The risk-adjusted ranking** with one-line trust caveats per scenario
4. **The three-paragraph strategic read** (Phase 8)
5. **A clear scenario recommendation** with prerequisites and conditions
6. **Hand-off to next skill** — for the recommended scenario, point at the right downstream skill:
   - `mmm-budget-reallocator` for the campaign-level execution translation
   - `mmm-launch-timing` for the week-by-week ramp projection
   - `mmm-test-roadmap` if the scenario depends on tests that need to be scheduled
   - `incrementality-test-runner` for any single test needed before the scenario can ship

## Inputs to Ask For

1. **Model / KPI** — which model (required)
2. **Scenario set** — user-defined OR ask the skill to generate (required)
3. **Projection horizon** — default 4 weeks (snapshot) or 12 weeks (quarterly planning) (optional)
4. **Trust-router output** — if available; else run trust-router first (recommended)
5. **Specific qualitative scenarios to include** — e.g., "must include a TikTok-heavy option" (optional)
6. **Audience** — exec (matrix + 3 paragraphs) vs. analyst (full output) (optional; default: full)

## Important Notes

- **More than 5 scenarios is noise.** The point of a side-by-side is to support a decision; 7 columns force the eye to skim. Cap at 5 — usually 3-4 is the sweet spot. If the user has more candidates, narrow to the top 4 before running.
- **Status Quo is always Scenario 0.** Even when the user doesn't ask for it. Every other scenario reads as "vs. doing nothing," and without an explicit baseline column the lift numbers float without context.
- **Same horizon, same window, same model.** Mixing horizons across scenarios is the most common subtle error in scenario planning. A 4-week projection on Scenario A and a 12-week projection on Scenario B are not comparable. Standardize.
- **The "bold" scenario is the most likely to be wrong.** Bold scenarios push channels into spend levels the model has seen less of, so their credible intervals widen — both the upside and the downside expand. If the recommendation lands on a bold scenario, it should always come with the test prerequisites attached.
- **Trust caveats matter more than risk-adjusted score.** A scenario with a slightly lower risk-adjusted score but all-Trust-MMM channels is often a better quarterly bet than a scenario with a higher score but Model-insufficient channel exposure. The user wants to ship, not start a stalled "well the model said X but..." debate three weeks in.
- **Re-run this skill at quarterly planning checkpoints.** Scenarios are perishable — the saturation curves shift as channels accumulate more data. A scenario set generated two months ago will use stale curves and may understate the available headroom.
