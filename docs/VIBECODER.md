# VIBECODER.md

This guide explains how to collaborate effectively with AI coding assistants on Motive using workflow-driven practices, shared conventions, and ready-to-use prompts.

## Who is this for?

- **Human developers** collaborating with LLMs on Motive
- **AI agents** seeking to align with human collaboration patterns

## Collaboration Principles

- **Stay in a workflow**: Prefer named workflows over ad‑hoc steps
- **Be explicit**: State goals, constraints, and acceptance criteria
- **Gate expensive actions**: Require confidence estimates before paid/long operations
- **Keep docs live**: Update `AGENT.md` and this file when new patterns emerge
- **Prefer tests**: Validate with failing tests before running `motive`

## Named Collaboration Workflows

Use these from the human side to instruct an agent, or from the agent side to announce intent. Each includes: when to use, required inputs, steps, confidence gate, exit criteria, and a prompt template.

### 1) Pair Debugging Workflow
- When: A test fails or a runtime defect is suspected
- Inputs: failing test path/name, stack trace, last relevant edits
- Steps:
  1. Reproduce locally with targeted `pytest`
  2. Write or refine a failing test that isolates the defect
  3. Implement a minimal fix and re-run tests
  4. Run the full suite; optionally validate with `motive -c tests/configs/integration/game_test.yaml`
- Confidence gate: 9–10/10 before running `motive`
- Exit: Failing test passes, full suite green, optional `motive` pass
- Prompt template:
  """
  Start Pair Debugging Workflow on <test_path>::<test_name>.
  Provide: root cause hypothesis, failing test delta, minimal fix, confidence (1–10), and whether to run motive.
  """

### 2) Feature Delivery Workflow
- When: Implementing a new feature or action
- Inputs: feature summary, acceptance criteria, affected modules/configs
- Steps:
  1. Write failing tests capturing acceptance criteria
  2. Implement minimal code to pass
  3. Refactor with tests green
  4. Update docs (README/CONTRIBUTORS/AGENT/MANUAL)
- Confidence gate: 8+/10 before edits; 9–10/10 before `motive`
- Exit: Tests pass; docs updated; optional `motive` validation
- Prompt template:
  """
  Start Feature Delivery Workflow: <feature_title>.
  Provide: tests first, implementation diff summary, docs updated, confidence, and run plan.
  """

### 3) Refactor Safety Workflow
- When: Structural improvements without behavior changes
- Inputs: scope, invariants, impacted files
- Steps:
  1. Ensure coverage exists; add tests if needed
  2. Refactor in small steps; run tests frequently
  3. Keep APIs and schemas stable
- Confidence gate: Rely on tests; avoid `motive` unless behavior might change
- Exit: Tests green; no behavior change
- Prompt template:
  """
  Start Refactor Safety Workflow for <area>.
  Provide: scope, invariants, step plan, and test confirmation.
  """

### 4) Config Evolution Workflow
- When: Changing YAML configs (themes/editions/actions)
- Inputs: target config path(s), intended change, merge/patch strategy
- Steps:
  1. Apply minimal change
  2. Validate with `motive-util config --validate` (and `--raw-config` if needed)
  3. Add/execute integration tests that exercise the config
- Confidence gate: Validation must be clean before `motive`
- Exit: Validation passes; related tests green
- Prompt template:
  """
  Start Config Evolution Workflow on <config_path>.
  Provide: change summary, validation results, and test outcomes.
  """

### 5) Commit & Push Workflow
- When: After successful local validation
- Inputs: change summary, linked tests, docs updates
- Steps:
  1. Run Pre‑Commit Assessment Checklist (see AGENT.md)
  2. Generate message; stage; commit; push
  3. Verify status and recent log
- Confidence gate: 9–10/10 before push
- Exit: Changes pushed; repo clean
- Prompt template:
  """
  Start Commit & Push Workflow.
  Provide: checklist results, commit message, and verification outputs.
  """

### 6) Training Data Publication Workflow
- When: Curating and publishing a dataset from a high‑quality run
- Inputs: source log/run id, dataset name
- Steps:
  1. `motive-util training copy`
  2. `motive-util training process`
  3. `motive-util training publish -n <name> -f`
- Confidence gate: Ensure data quality and metadata completeness
- Exit: Published dataset with metadata
- Prompt template:
  """
  Start Training Data Publication Workflow for <run_id> as <dataset_name>.
  Provide: copy/process/publish outputs and a quality summary.
  """

## Communication Conventions

- **Confidence statement**: Provide a numeric confidence 1–10 with a brief rationale
- **Status updates**: 1–2 sentences before/after tool use outlining what happened and what’s next
- **Abort conditions**: If confidence <7/10, stop and switch to tests or ask for clarification
- **Tool assumptions**: Assume non‑interactive flags and no pagers when executing commands

## Quick Tips (Reference)

- Check Agent vs Ask mode before requesting actions
- Prefer integration tests; avoid heavy mocking
- Verify Pydantic field names and config paths
- Read errors carefully; fix root causes
- Keep docs updated when patterns change

This file evolves alongside `AGENT.md`. When you discover effective collaboration patterns, add them here with a concise workflow entry and prompt template.
