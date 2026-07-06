---
name: empirical-prompt-tuning
description: Methodology for iteratively improving agent-facing instructions (skills / slash commands / CLAUDE.md / code-gen prompts) via bias-free executor + two-sided evaluation (self-report + instruction-side metrics). Meta-skill, invoke ONLY when the user explicitly asks for an "empirical" eval of a prompt or skill, or for the Iter-0 description / body consistency check. Do NOT auto-invoke after every skill edit; this loop is operator-triggered by name.
---

# Empirical Prompt Tuning

The author of a prompt cannot judge its quality. The clearer the writer thinks something is, the more likely another agent will stumble on it. The core of this skill is to have a bias-free executor actually run the instruction, evaluate it two-sidedly, and iterate. Do not stop until improvements plateau.

## When to use

Use only when the operator explicitly asks for empirical evaluation, empirical prompt tuning, or an Iter-0 description/body consistency check.

Good targets:

- Right after creating or substantially revising a skill / slash command / task prompt, when the operator explicitly asks to evaluate it.
- When an agent does not behave as expected and the operator wants to test whether instruction ambiguity caused it.
- When hardening high-importance instructions such as frequently used skills, automation-core prompts, or code-generation prompts.

Do not use:

- Automatically after every skill edit.
- For one-off throwaway prompts where evaluation cost does not pay off.
- When the goal is not to improve success rate but only to reflect the writer's subjective preferences.

## Workflow

0. Iteration 0: description / body consistency check
   - Read the triggers and use cases claimed by the frontmatter `description`.
   - Read the scope the body actually covers.
   - If there is a gap, reconcile the description or body before moving to iteration 1.
   - Example: description says "navigation / form filling / data extraction" but the body is only a CLI reference for `npx playwright test`.
   - If this is skipped, the subagent may reinterpret the body to match the description and create a false positive.

1. Baseline preparation
   - Fix the target prompt.
   - Prepare 2 to 3 evaluation scenarios: 1 median realistic case plus 1 to 2 edge cases.
   - Prepare a requirements checklist for each scenario with 3 to 7 items.
   - Include at least one `[critical]` item per checklist.
   - Accuracy = satisfied items / total items. Score `○ = 1`, `partial = 0.5`, `× = 0`.
   - Do not change checklist items or `[critical]` tags after evaluation starts.

2. Bias-free read
   - Dispatch a fresh blank-slate executor via a subagent mechanism.
   - Do not substitute this with a self-reread.
   - When running multiple scenarios in parallel, dispatch multiple fresh executors in one message if the environment supports it.

3. Execution
   - Hand the executor a prompt following the Subagent Invocation Contract below.
   - The executor runs the scenario and returns a deliverable plus self-report.

4. Two-sided evaluation
   - Extract executor self-report: unclear points, discretionary fill-ins, stuck places.
   - Interpret trace phases: Understanding / Planning / Execution / Formatting.
   - Require each unclear point as `Issue / Cause / General Fix Rule`.
   - Record instruction-side measurements:
     - Success/failure: success `○` only when all `[critical]` items are `○`; otherwise failure `×`.
     - Accuracy: checklist achievement rate.
     - Step count: use `tool_uses` from the subagent return metadata as-is, including reads/searches.
     - Duration: use `duration_ms` from subagent usage metadata.
     - Retry count: extract from the executor self-report.
   - On failure, add one line to unclear points stating which `[critical]` item dropped.

5. Apply the diff
   - Before editing, state which requirement item or judgment wording the fix satisfies.
   - Consult the failure pattern ledger first.
   - Apply the minimum fix to eliminate the unclear points.
   - Use one theme per iteration. Multiple related micro-fixes are allowed; unrelated fixes go to the next iteration.

6. Re-evaluate
   - Repeat steps 2 to 5 with a new executor.
   - Do not reuse the previous executor because it learned the earlier prompt.

7. Convergence check
   - Stop after 2 consecutive iterations with zero new unclear points and metric improvements below threshold.
   - Use 3 consecutive clears for high-importance prompts.
   - Add one hold-out scenario at convergence. If accuracy drops by 15 points or more vs the recent average, treat it as overfitting and revise scenario design.

## Evaluation Axes

| Axis | How to capture | Meaning |
|---|---|---|
| Success/failure | Binary `○` / `×` from `[critical]` items | Minimum bar |
| Accuracy | % of checklist points satisfied | Partial success |
| Step count | `tool_uses` from executor metadata | Instruction waste |
| Duration | `duration_ms` from executor metadata | Cognitive load proxy |
| Retry count | Executor self-report | Ambiguity signal |
| Unclear points | Executor self-report bullets | Qualitative improvement material |
| Discretionary fill-ins | Executor self-report bullets | Implicit specification |

Qualitative feedback is primary. Quantitative metrics are auxiliary. Chasing only time reduction can make the prompt too thin.

### Interpreting `tool_uses`

Use `tool_uses` as a relative value across scenarios.

- If one scenario uses 3-5x more tool calls than the others, the skill may be too decision-tree-index-leaning and not self-contained enough.
- Example: most scenarios use 1-3 tool calls but one uses 15+, suggesting the skill lacks a recipe for that case.
- Countermeasure: add an inline minimum complete example or guidance on when to read references.

Even at 100% accuracy, a large `tool_uses` skew can justify another iteration.

## Fix Propagation Patterns

Fix effects are not linear:

- Conservative swing: one fix aimed at multiple axes but moved only one.
- Overshoot: one structural detail satisfied several judgment items at once.
- Zero-shoot: a fix inferred from an axis name did not satisfy any judgment wording.

Before applying a diff, tie the fix to the exact checklist item or judgment wording it is intended to satisfy.

## Subagent Invocation Contract

Use this prompt shape for each executor:

```text
You are an executor reading <target prompt name> with a blank slate.

## Target prompt
<Paste the full body of the target prompt, or specify a path to read>

## Scenario
<One paragraph setting the scenario context>

## Requirements checklist
1. [critical] <minimum-bar item>
2. <normal item>
3. <normal item>

Judgment rules:
- Success is ○ only when all [critical] items are ○.
- Accuracy: ○ = 1, partial = 0.5, × = 0.

## Task
1. Follow the target prompt to execute the scenario and produce the deliverable.
2. On completion, respond with the report structure below.

## Report structure
- Deliverable: <artifact or execution summary>
- Requirement achievement: ○ / × / partial, with reason, for each item
- Trace:
  - Understanding: OK / stuck / skipped, with reason when not OK
  - Planning: OK / stuck / skipped, with reason when not OK
  - Execution: OK / stuck / skipped, with reason when not OK
  - Formatting: OK / stuck / skipped, with reason when not OK
  - Collapsed form allowed: if all phases are OK, write `Trace: all OK`
- Unclear points (structured):
  - Issue: <what observably happened>
  - Cause: <why, diagnosed at the instruction level>
  - General Fix Rule: <class-level rule that prevents this class of mistake>
- Discretionary fill-ins: <bullets>
- Retries: <number of repeated decisions and why>
```

The caller extracts the report and fills the evaluation table with metadata from the subagent tool return.

## Environment Constraints

If dispatching a fresh executor is not possible, do not run empirical evaluation.

- Alternative 1: ask the parent session's user to start a separate session and delegate evaluation there.
- Alternative 2: report `empirical evaluation skipped: dispatch unavailable`.
- Do not substitute with a self-reread.

Structural review mode is allowed when the user asks only for consistency and clarity review. State explicitly: `this round is structural review mode: text consistency check, not execution`. Structural review helps iteration 0 but does not count as empirical convergence.

## Iteration Stopping Criteria

Convergence:

- 2 consecutive rounds with zero new unclear points.
- Accuracy improvement vs previous is +3 points or less.
- Step count variation vs previous is within +/-10%.
- Duration variation vs previous is within +/-15%.
- Hold-out scenario does not drop by 15 points or more vs recent average.

Divergence:

- If new unclear points do not decrease across 3+ iterations, stop patching and rewrite the prompt structure.

Resource cutoff:

- Stop when importance and improvement cost no longer balance.

## Failure Pattern Ledger

Maintain a per-target-prompt ledger.

Entry format:

```text
- Pattern name: <short descriptive handle>
  - Example: <representative Issue wording>
  - General Fix Rule: <class-level rule>
  - Seen in: iter N, iter M
```

Rules:

- Before generating a fix, scan the ledger.
- If the current `General Fix Rule` matches an entry, update `Seen in` and investigate why the existing fix did not prevent recurrence.
- A pattern recurring 3+ times despite targeted fixes is a structural signal; escalate to divergence.

## Variant Exploration

Use only when plateau is suspected but convergence criteria are not met.

- Conservative variant: current prompt + next-best minor fix.
- Exploratory variant: one structural change such as reordering sections, splitting dense paragraphs, dropping redundancy, or adding a worked example.
- Dispatch fresh executors on the same scenarios.
- Keep the variant with higher accuracy; on tie, prefer fewer unclear points; on further tie, prefer lower `tool_uses`.

Do not ask a subagent to directly rate "A vs B"; compare objective axes.

## Presentation Format

```text
## Iteration N

### Changes (diff from previous)
- <one-line fix content>
- Pattern applied: <pattern name from ledger, or "(new)">

### Execution results (per scenario)
| Scenario | Success/Failure | Accuracy | steps | duration | retries | Weak phase |
|---|---|---|---|---|---|---|
| A | ○ | 90% | 4 | 20s | 0 | - |
| B | × | 60% | 9 | 41s | 2 | Execution |

### Structured reflection (newly surfaced this time)
- <Scenario B>: [critical] item N is × - <one-line reason for drop>
  - Issue: <what observably happened>
  - Cause: <why, at the instruction level>
  - General Fix Rule: <class-level abstraction>
- <Scenario A>: nothing new

### Discretionary fill-ins (newly surfaced this time)
- <Scenario B>: <fill-in content>

### Ledger updates
- Added: <pattern name> (from Scenario B)
- Re-seen: <pattern name> (originally iter K) - existing fix did not prevent recurrence because <reason>

### Next fix proposal
- <one-line minimum fix>

Convergence check: X consecutive clears / Y rounds remaining to stop condition
```

## Red Flags

| Rationalization | Reality |
|---|---|
| "Rereading it myself has the same effect" | You cannot view text you just wrote objectively. Dispatch a new executor. |
| "One scenario is enough" | One scenario overfits. Use at least 2. |
| "Zero unclear points once, so we're done" | Finalize with 2 consecutive clears. |
| "Let's knock out multiple unclear points at once" | You lose track of what worked. Use one theme per iteration. |
| "Metrics are good, so ignore qualitative feedback" | Qualitative feedback is primary. |
| "Let's reuse the same subagent" | It has learned prior improvements. Always dispatch a new one. |

## Common Failures

- Scenario too easy or too hard: neither produces signal.
- Only looking at metrics: can strip needed guidance.
- Too many changes per iteration: attribution becomes impossible.
- Tuning scenarios to match the fix: makes the evaluation meaningless.

## Related

- `skill-creator`: skill creation and validation guidance.
- `retrospective-codify`: codifying learnings after a task ends; this skill is for prompt development during iteration.
- Parallel subagent dispatch tools, when available, for running multiple scenarios in parallel.
