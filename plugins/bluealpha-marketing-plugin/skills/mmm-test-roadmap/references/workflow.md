# MMM Test Roadmap — Detailed Workflow

The job: turn the trust-router's "Validate first" and "Model insufficient" buckets into a sequenced, scoped, calendared quarterly testing plan. Most analytics teams have a backlog of channels they "should test" and no operational framework for sequencing them. This skill produces the roadmap: which tests run in which weeks, why each one is worth the dollars, and what each one will tell you that you don't currently know.

Pairs cleanly with `mmm-trust-router` (upstream — produces the channel bucketing) and `incrementality-test-runner` (downstream — executes each test as it comes up in the calendar).

## Phase 0: Inputs

Three things must be known before scheduling.

1. **Trust router output** — the routed channel list. If the user hasn't run trust-router yet, run it now via the trust-router skill. Capture the per-channel route, confidence score, reason, and pre-staged test prior (expected lift, suggested duration).

2. **Test budget** — the quarter's total budget available for incrementality testing. Tests cost money in two ways:
   - **Holdout opportunity cost** — revenue forgone in control regions during the test window
   - **Incremental test spend** — for "structured spend ramp" tests on Model-insufficient channels, the cost of running the channel at materially different levels than business-as-usual
   Ask for both, OR ask for a single total budget and split it as needed.

3. **Concurrent test cap** — how many tests can run in parallel without interfering with each other. Three categories of interference:
   - **Operational** — the team can only manage N active tests at once
   - **Geographic** — if Test A uses Pittsburgh as control and Test B uses Pittsburgh as test, they collide
   - **Channel** — running an incrementality test on Meta while simultaneously running one on Display might create attribution confusion
   Most accounts can run 2-3 concurrent tests comfortably. Confirm with the user.

4. **Business priorities (optional)** — quarterly OKRs, channels under scrutiny from leadership, channels where a decision is blocked pending validation. These get a priority bump in scoring.

## Phase 1: Score Each Candidate Test

For every channel in "Validate first" or "Model insufficient" from the trust-router, compute a priority score combining information value and business value.

### Information value

What does running this test actually tell you?

```
get_marginal_roi(model=<kpi_name>, channels=[<channel>])
get_raw_channel_roi(model=<kpi_name>, channels=[<channel>])
get_raw_saturation_curves(model=<kpi_name>, channels=[<channel>])
```

Score each candidate on:

| Factor | Weight | Score |
|---|---|---|
| **Posterior CI width on ROI** | 0.3 | Wider CI = more to learn from the test. Map (high − low)/median to 0-1: <0.4 → 0.1, 0.4-0.8 → 0.5, >0.8 → 1.0 |
| **Channel size (current spend share)** | 0.3 | Bigger channels move the business more. Map share % to 0-1: <5% → 0.2, 5-15% → 0.6, >15% → 1.0 |
| **Distance from prior (data influence)** | 0.2 | Low data influence = test will substantially update the model. Inverse of overlap coefficient, 0-1. |
| **Proposed-shift sensitivity** | 0.2 | If the user has a specific proposed reallocation involving this channel, the test resolves a real planning question. Bump by 0.5 if a shift is on the table. |

Sum the weighted scores → channel's information value (0-1).

### Business value

Even high-information tests aren't worth running if no decision rides on them.

| Factor | Weight | Score |
|---|---|---|
| **Decision blocked pending test** | 0.5 | Binary: is there a real spend decision waiting for this test result? If yes → 1.0; if exploratory → 0.3 |
| **Recurring spend exposure** | 0.3 | If the channel runs at significant spend every quarter and the MMM read is unreliable, the test pays for itself across many future decisions. Map to current annualized spend exposure. |
| **Leadership scrutiny** | 0.2 | A channel where the CFO/CMO is asking "is this working?" needs a test for credibility, independent of the analytical case. Binary 0 or 1. |

Sum → channel's business value (0-1).

### Final priority score

> priority = 0.6 × information_value + 0.4 × business_value

Information leads because the test only generates value if it's actually informative — a perfectly priority-aligned test with nothing to learn is operational theater. Business value matters but doesn't outweigh "this test can't actually update our beliefs."

## Phase 2: Estimate Test Cost and Duration

For each candidate, size the test.

### Test duration

The minimum duration is the longer of:
- **Statistical floor** — enough conversions to detect the expected effect at 80% power
- **Adstock floor** — `2 × adstock half-life` to let carry-over effects settle into a stable contribution pattern
- **Operational floor** — 4 weeks minimum for any meaningful test

```
get_adstock_parameters(model=<kpi_name>, channels=[<channel>])
```

Use the channel's half-life from the MMM. A 1-week half-life channel needs ~4 weeks of test runtime; a 4-week half-life channel needs ~10 weeks. Slow channels are expensive to test.

### Test cost

Two cost components:

1. **Holdout opportunity cost** — for a 20% geo holdout running for N weeks at the channel's current spend efficiency: roughly 20% × N weeks × channel weekly revenue.

2. **For Model-insufficient channels with flat training spend**, the test isn't a holdout — it's a structured spend ramp. Three spend levels (e.g., 50%, 100%, 150% of current) over 4-6 weeks each. Incremental cost = the dollars spent above what would have been the steady-state plan.

Translate to a dollar estimate per candidate. Round to the nearest $5K for readability.

### Expected information gain × cost ratio

> ROI of testing = priority_score × $expected_decision_value / $test_cost

Where `expected_decision_value` is a rough estimate of the dollar impact of the budget decision the test will inform — typically the annualized spend on the channel times some plausible reallocation %. Ask the user for this when in doubt; a quarterly test budget of $200K should be allocated to tests where the eventual decisions move millions, not where they move thousands.

## Phase 3: Sequence the Tests

The goal: pack as many high-priority tests as possible into the quarter, subject to the budget and concurrency cap. This is a scheduling problem with three constraints:

1. **Budget constraint** — sum of test costs ≤ quarterly test budget
2. **Concurrency constraint** — no more than N tests overlapping in any week
3. **Geographic constraint** — tests can't share control regions

### The scheduling algorithm

1. Rank candidates by priority score descending.
2. Walk down the list. For each candidate:
   - Check budget remaining; skip if exceeded.
   - Find the earliest week where (a) the concurrency cap isn't exceeded, and (b) no geographic conflict exists with already-scheduled tests.
   - Schedule the test starting that week, running for its computed duration.
3. Continue until all candidates are placed or budget exhausted.

### Result: a calendar

Format the schedule as a 13-week Gantt:

```
Week:        1  2  3  4  5  6  7  8  9  10 11 12 13
YouTube      ▓▓ ▓▓ ▓▓ ▓▓ ▓▓ ▓▓ ▓▓ ▓▓
TikTok          ▓▓ ▓▓ ▓▓ ▓▓ ▓▓
CTV (ramp)               ▓▓ ▓▓ ▓▓ ▓▓ ▓▓ ▓▓
Display                              ▓▓ ▓▓ ▓▓ ▓▓ ▓▓
```

Or, more practically for output, a table with start week / end week / cost / channel.

## Phase 4: Pre-Stage Each Test

For every test on the calendar, prepare the hand-off package for `incrementality-test-runner`. This is what saves the testing team the most setup time — the roadmap doesn't just say "test YouTube in week 1," it says "test YouTube in week 1 with these specific parameters."

Per test:
- **Channel** under test
- **Expected lift** (from MMM response curve at the proposed spend level)
- **Minimum detectable effect** = 0.5 × expected lift (test needs to detect at half the model's prediction to be informative)
- **Geo split suggestion** — Matched-Market Pairs / Regional Holdout / Budget Suppression — based on channel size and operational complexity
- **Suggested holdout regions** — 2-4 DMAs/states that aren't already in use by another scheduled test
- **Primary KPI** — same as the MMM's KPI by default
- **Success criteria** — measured lift CI excludes zero (significant), AND measured lift is within 50% of MMM prediction (validates model)
- **Decision tree** — what action does each test outcome trigger:
  - Significant lift matching MMM ± 50% → Trust MMM on this channel, route Validate-first → Trust MMM
  - Significant lift but materially different from MMM → MMM is mis-calibrated, route to model re-train
  - No significant lift → Channel may be saturated or low-impact; cut and reallocate
  - Inconclusive → Extend test or accept that the channel is below detectable-impact threshold

## Phase 5: Output

Deliver to the user:

1. **The prioritized candidate list** — every "Validate first" + "Model insufficient" channel with its priority score, information value, business value, test cost, and duration
2. **The 13-week calendar** — which tests run in which weeks, accounting for concurrency and geographic constraints
3. **The budget reconciliation** — how much of the quarterly test budget is allocated to which tests, with the remaining buffer
4. **The pre-staged test cards** — for each scheduled test, the full hand-off package
5. **The "didn't make the cut" list** — channels that scored low or got squeezed out by budget/concurrency, with the reason and a note on what would need to change to get them on next quarter's roadmap
6. **The expected post-quarter trust-router delta** — after these tests resolve, how many channels move from Validate-first to Trust-MMM, and how many model-insufficient channels gain enough signal to bucket

## Inputs to Ask For

1. **Model / KPI** — which model the routing is built against (required)
2. **Trust router output** — pre-computed bucketing if available; else run trust-router first (required)
3. **Quarterly test budget** — total dollars available (required)
4. **Concurrent test cap** — operational maximum on parallel tests (required; default: 2)
5. **Test start week** — when the quarter begins for scheduling purposes (optional; default: next Monday)
6. **Business priorities** — channels under leadership scrutiny, blocked decisions (optional)
7. **Decision-value estimates** — rough dollar impact per channel decision (optional; default to formulaic estimate)

## Important Notes

- **The roadmap is a plan, not a guarantee.** Tests get delayed, contaminated, or extended. Budget over-runs happen. Re-run this skill mid-quarter when reality deviates from the plan — the algorithm will rebalance.
- **Slow-decay channels are roadmap-expensive.** A 4-week-half-life channel needs ~10 weeks of test runtime, which means one test eats most of a quarter's slot. Acknowledge this when CTV / Brand / OOH show up in the candidate list — they're high-value to test AND high-cost to test, and that trade-off shows up in the scoring.
- **Don't test a channel that just changed strategically.** If the creative refreshed last week or the audience targeting was overhauled, the channel's response curve is unstable. The test needs at least 2-3 weeks of post-change settle time before launching. Flag any candidate channel where a strategic change is in flight.
- **Reserve buffer.** Don't allocate 100% of the test budget to scheduled tests. Hold back 15-20% for surprise tests — a leadership ask, a competitive move, or a new channel launch that needs a test.
- **The calendar is iterable.** This skill produces version 1; expect 2-3 revisions before the user is happy with the prioritization and the timing. Make it easy to re-run with adjusted weights or business priorities.
- **Hand-off pattern:** trust-router → test-roadmap → incrementality-test-runner (one per scheduled test, fired in calendar order). After each test resolves, update the trust-router routings and re-run if more than 2 channels rebucket.
