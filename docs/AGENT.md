# AI Agent Guidelines

This file contains essential guidance for AI agents working on the Motive project. It serves as a living guide for maintaining high engineering quality and avoiding common pitfalls.

## Who is this for?

- **AI coding agents** executing changes end-to-end using tests and checklists
- **Human maintainers** instructing agents via named workflows

## Required Reading Order

**Before starting any work, read these documents in order:**

1. **[README.md](../README.md)** - Project overview, goals, and current status
2. **[CONTRIBUTORS.md](CONTRIBUTORS.md)** - Architecture, setup, and development workflows (READ THIS FIRST - contains essential setup and architecture info)
3. **[VIBECODER.md](VIBECODER.md)** - Human-LLM collaboration lessons
4. **This file (AGENT.md)** - AI-specific workflows and guidelines (builds on CONTRIBUTORS.md)

## Quick Links

- Project overview: [../README.md](../README.md)
- Contributors guide: [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Human‑LLM collaboration: [VIBECODER.md](VIBECODER.md)
- Player manual: [MANUAL.md](MANUAL.md)
- Documentation map: [DOCS.md](DOCS.md)
- Current priorities: [TODO.md](TODO.md)

## AI-Specific Context

This file assumes you've read [CONTRIBUTORS.md](CONTRIBUTORS.md) and understand the project architecture, setup, and development workflows. This section focuses on AI-specific considerations and workflows that differ from human contributors.

## AI-Specific Development Workflow

### At‑a‑Glance Workflow

- Write failing tests first (prefer integration tests)
- Implement the minimal change to pass
- Validate locally with `motive -c tests/configs/integration/game_test.yaml`
- Run full test suite: `pytest tests/ -v`
- Commit using the checklist below

## Named Workflows (Agent-Callable)

Each workflow has: purpose, when to use, required inputs, confidence gate, steps, and exit criteria. Agents should announce the workflow name when starting.

### 1) Debugging Workflow
- Purpose: Diagnose and fix a failing test or real-world issue
- Use when: A test fails, a regression is reported, or logs indicate a defect
- Inputs: Failing test name/path, error message/trace, recent changes (if any)
- Confidence gate: Proceed to run `motive` only at 9–10/10 confidence; otherwise stick to tests
- Steps:
  1. Reproduce with `pytest` targeted tests
  2. Add/adjust a failing test to capture the defect precisely
  3. Implement minimal fix; re-run targeted tests, then full suite
  4. If needed, validate with `motive -c tests/configs/integration/game_test.yaml`
  5. Prepare commit; run checklists
- Exit: All targeted tests pass; full suite green; optional `motive` run successful

### 2) New Feature Workflow (TDD)
- Purpose: Add a feature or action with confidence
- Use when: Implementing a new capability from TODOs or design
- Inputs: Feature description, acceptance criteria, impacted files
- Confidence gate: 8+/10 before code edits; 9–10/10 before `motive`
- Steps:
  1. Write failing tests expressing desired behavior (unit/integration)
  2. Implement minimal code to pass
  3. Refactor while keeping green
  4. Validate with test config if behavior spans configs
  5. Update docs (README/CONTRIBUTORS/AGENT/MANUAL as needed)
- Exit: Tests pass, docs updated, optional `motive` validation

### 3) Refactor Workflow (No Behavior Change)
- Purpose: Improve structure without altering behavior
- Use when: Code clarity/maintainability changes are needed
- Inputs: Scope and invariants; affected modules
- Confidence gate: Prohibit `motive` unless behavior could be impacted; rely on tests
- Steps:
  1. Establish safety nets (tests/coverage)
  2. Refactor in small steps; run tests often
  3. Keep public APIs stable; avoid config changes
- Exit: All tests green; no behavior changes observed

### 4) Config Change Workflow
- Purpose: Safely modify YAML configs (themes, editions, actions)
- Use when: Editing `configs/**.yaml` or adding content
- Inputs: Target file(s), intended change, merge/patch strategy
- Confidence gate: Validate with `motive-util config --validate`; run tests touching config
- Steps:
  1. Make minimal config change
  2. Validate includes/merges; inspect `--raw-config` if needed
  3. Run relevant tests; add integration tests if behavior-driven
- Exit: Validation clean; tests green

### 5) Commit Workflow
- Purpose: Safely stage and push changes
- Use when: After successful local validation
- Inputs: Summary of changes and linked tests/docs
- Confidence gate: 9–10/10 required before push
- Steps:
  1. Run Pre-Commit Assessment Checklist
  2. Generate message; stage; commit; push with platform-appropriate commands
  3. Verify via `git status` and recent log
- Exit: Changes pushed; repo clean

### 6) Training Data Workflow
- Purpose: Curate and publish training datasets from logs
- Use when: A high-quality run is ready to be processed
- Inputs: Source run ID/path; target dataset name
- Confidence gate: Ensure high data quality; follow publishing rules
- Steps:
  1. `motive-util training copy`
  2. `motive-util training process`
  3. `motive-util training publish -n <name> -f`
- Exit: Dataset published with metadata complete

### Testing Philosophy (CRITICAL)
- **Default to tests over paid runs**: Running `motive` triggers paid LLM calls. Prefer unit/integration tests which stub external LLMs
- **Favor integration tests over heavy mocking**: Write tests that exercise real code paths and types. Mock only external services (e.g., LLM APIs, filesystem/network), not core logic
- **Use real constructors and APIs**: Build objects with their true signatures so tests mirror production
- **Tests should prove real fixes**: Add integration tests that fail before a fix and pass after
- **Think about correct behavior from the game's perspective when fixing tests**: While fixing tests, always consider what the correct behavior should be from the game's perspective. The goal isn't just getting tests to pass—it's to end up with tests that are testing the intended/desired behavior.

### Quality Gates
- **Confidence scale (1–10) before paid runs**:
  - 9–10: Broad integration coverage, deterministic seeds, recent green runs, stable configs
  - 7–8: Integration tests cover new logic end-to-end with stubs, logs verified
  - 5–6: Unit tests pass but integration coverage is partial
  - ≤4: Significant unknowns, heavy mocking, or flakiness; do not run paid flows
- **Gate to run `motive`**: Only after tests are green, logs look correct, and configs are validated

### Test-Driven Development (TDD) Workflow
- **Write tests first**: When implementing new features or fixing bugs, always write tests first with the expectation that they will fail because the feature hasn't been implemented yet
- **Red-Green-Refactor cycle**: 
  1. **Red**: Write failing tests that describe the desired behavior
  2. **Green**: Implement the feature/bug fix to make tests pass
  3. **Refactor**: Improve code while keeping tests green
- **Learn from failures**: If something goes wrong during implementation, always walk away with a lesson to add to `AGENT.md` for how to prevent the mistake in the future
- **Test coverage before implementation**: Ensure comprehensive test coverage exists before writing production code

### Why TDD is Critical for AI Agents

**The Problem**: Implementing massive architectural changes without following TDD leads to:
- Breaking dozens of existing tests that were working before
- Spending extensive time in "fix everything that broke" mode
- Loss of confidence in the codebase state
- Difficulty determining what's actually working vs. what's broken

**The TDD Solution**: For large features, follow this approach:
1. **Write failing tests** that describe the new behavior you want
2. **Implement minimal changes** to make those tests pass
3. **Gradually migrate** existing tests to use the new system
4. **Refactor** while keeping all tests green

**Why This Matters**: The hierarchical config system change broke the fundamental contract between configs and the rest of the codebase (Pydantic objects → dictionaries). This should have been caught by tests written first, not discovered after implementation.

### Why Agents Don't Follow TDD Guidance

**Root Causes**:
- **Overconfidence**: Thinking "I understand the codebase well enough to implement this safely"
- **Impatience**: Wanting to see the feature working quickly rather than following the disciplined approach
- **Scope Creep**: Starting with a small change but then expanding it into a massive refactor
- **Not Reading Guidance**: Failing to re-read `AGENT.md` before starting major work

**Prevention Strategies**:
- **Always re-read `AGENT.md`** before starting any significant work
- **Break large features into smaller, testable increments**
- **Write the test first, even if it feels slow**
- **Ask yourself**: "What's the smallest change I can make to get this working?"
- **When in doubt, follow the TDD workflow explicitly**

### Testing Anti-Patterns to Avoid

**❌ NEVER DO THESE**:
- **Ad hoc Python scripts for testing**: Creating temporary `.py` files to test behavior instead of proper pytest tests
- **One-off debug scripts**: Writing scripts that test specific cases but aren't durable or reusable
- **Manual testing in REPL**: Using `python -c` or interactive sessions to test functionality
- **Print-based debugging**: Adding print statements instead of proper assertions

**✅ ALWAYS DO THESE**:
- **Write pytest tests**: All testing must be done through pytest with proper fixtures and assertions
- **Make tests durable**: Tests should be reusable, runnable in CI, and catch regressions
- **Test edge cases**: Include tests for error conditions, invalid inputs, and boundary cases
- **Use descriptive test names**: Test names should clearly describe what behavior is being tested

**Why This Matters**:
- **Ad hoc scripts are not durable**: They get deleted and don't catch regressions
- **Manual testing is not repeatable**: Can't be automated or run in CI
- **Proper tests document behavior**: They serve as living documentation of expected behavior
- **Tests catch regressions**: Only durable tests prevent future bugs

**Example Anti-Pattern**:
```python
# ❌ DON'T DO THIS
python -c "from motive.action_parser import _parse_whisper_parameters; print(_parse_whisper_parameters('test'))"
```

**Example Correct Pattern**:
```python
# ✅ DO THIS INSTEAD
def test_whisper_parsing_edge_case():
    result = _parse_whisper_parameters('test')
    assert result == expected_value
```

## Real-World Issue Resolution Workflow

When issues are found in `motive` that should have been caught by tests, follow this systematic approach:

### 1. **Issue Analysis**
- **Evaluate preventability**: Was this a preventable mistake? Could tests have caught this?
- **Identify root cause**: What specific code path or integration point failed?
- **Assess test gap**: What type of test was missing (unit, integration, end-to-end)?

### 2. **Test-First Fix Approach**
- **Write failing test first**: Create a test that reproduces the issue and would have failed before the fix
- **Confirm test fails**: Run the test to verify it catches the actual problem
- **Fix the root cause**: Implement the fix that makes the test pass
- **Verify test passes**: Confirm the new test now passes with the fix
- **Run full test suite**: Ensure no regressions were introduced

### 3. **Validation and Prevention**
- **Achieve high confidence**: Get to 9-10 confidence level before running `motive`
- **CRITICAL: Always validate in motive before committing**: Never start the commit workflow (git add/commit/push) without first validating changes in `motive`. Tests can pass but real-world integration may still fail.
- **Use hints for reproduction**: After fixing, use the hint system to try reproducing the original issue in `motive`
- **Document the lesson**: Add the specific test pattern to `AGENT.md` to prevent similar issues

### 4. **Learning and Generalization**
- **Identify generalizable patterns**: After fixing an issue, consider what broader lessons can be learned
- **Look for missing guidance**: Check if the issue reveals gaps in existing guidelines
- **Add preventive lessons**: Document specific patterns that could have prevented the issue
- **Update workflow if needed**: Enhance the workflow itself based on new insights

## Common Patterns and Lessons Learned

### Action System
- **Action parsing contract**: Parser only recognizes lines starting with `>` and finds actions by longest matching name
- **Event distribution timing**: Distribute events immediately after each action executes, not at the start of the next turn
- **Action effects must emit observable events**: Core actions should generate scoped events so nearby players see them

### Configuration Management
- **Prefer structured over freeform configuration**: Use structured objects/dictionaries instead of freeform strings
- **Design for extensibility**: Include placeholder fields for future expansion
- **Unify related configuration fields**: Integrate similar concepts into single structured fields
- **Use declarative over imperative configuration**: Describe what should happen rather than how to do it

### Error Handling
- **Log invalid/unexecutable actions clearly**: Include which action failed and why
- **UTF‑8 logging**: File handlers must specify `encoding="utf-8"` to preserve special characters
- **AP exhaustion is not an error**: Running out of AP should not mark the response invalid

### Testing Specifics
- **Check import paths when writing tests**: Verify correct import paths by checking where classes are actually defined
- **Test edge cases in configuration evaluation**: Test missing fields, empty values, and invalid combinations
- **Test both positive and negative cases**: Include boundary conditions and edge cases
- **Test requirement type implementations**: When adding new requirement types (like `player_in_room`), create integration tests that verify the requirement checking logic works correctly with real player and room data. Test both success and failure cases.
- **Verify Pydantic field names**: When working with configuration, always check the actual field names in the Pydantic model definitions rather than assuming names (e.g., `target_player_param` not `player_name_param`).
- **Inventory security is critical**: Always create comprehensive security tests for inventory management actions (pickup, drop, give, trade). Test for object duplication, unauthorized access, malicious input, and cross-room exploits.
- **Use test configs for validation**: Use `tests/configs/integration/game_test.yaml` or create specific test configs with hints before running `motive` to ensure LLM players test the specific functionality being validated. This keeps production configs clean.
- **Keep production configs clean**: Use test configs for validation instead of adding temporary hints to production files. This ensures production configurations remain clean and don't include test-specific content.
- **Tests should not depend on specific game.yaml content**: Tests that depend on specific configurations in `game.yaml` are fragile and will break whenever the configuration changes. Design tests to be independent of configuration content or use test-specific configurations.

### Design Principles
- **Actions should be verbs, parameters should be nouns**: Follow the pattern of `look inventory`, `pickup sword`, `move north` rather than `inventory`, `pickup sword`, `move north`
- **Consistent naming conventions**: Use clear, descriptive names that follow established patterns
- **Extend existing actions over creating new ones**: When possible, extend existing actions (like `look inventory`) rather than creating redundant actions

## Training Data Management (AI-Specific)

**Note**: Full training data management details are in [CONTRIBUTORS.md](CONTRIBUTORS.md). This section covers AI-specific considerations.

### AI-Specific Training Data Guidelines

When working with training data as an AI agent:
- **Always validate data quality** before publishing
- **Use descriptive names** for published datasets
- **Follow the pipeline**: Copy → Process → Publish
- **Check metadata completeness** for self-contained datasets
- **Respect git boundaries**: Only publish curated, high-quality data
- **Don't ask permission for high-confidence operations**: When confidence is 8+ and rationale is provided, just run the operation. The user will reject if they don't want it run.

## Critical Workflow Rules

### Pre-Commit Assessment Checklist
Before committing changes, verify all items are complete:

#### **Code Quality & Testing**
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linter errors: `pytest tests/ --tb=short` (check for any failures)
- [ ] Real-world validation passed: `motive` completed successfully
- [ ] No temporary debug code or print statements left in production code

#### **Configuration & Documentation**
- [ ] Configuration files updated correctly (e.g., `configs/core.yaml`, `configs/game.yaml`)
- [ ] **Production configs remain clean**: No temporary hints or test-specific configurations in production files
- [ ] Documentation updated: `AGENT.md`, `VIBECODER.md`, `README.md` as needed
- [ ] New lessons learned added to appropriate documentation files

#### **Pre-Validation Checklist (Before `motive`)
- [ ] **Use test configs for validation**: Use `tests/configs/integration/game_test.yaml` or create specific test configs with hints instead of modifying production `configs/game.yaml`
- [ ] **Verify test config syntax**: Ensure test configuration files are valid and won't cause parsing errors
- [ ] **Target specific actions**: Test configs should direct players to execute the exact actions needed to validate the new feature or bug fix

#### **Code Organization**
- [ ] New test files created for new functionality
- [ ] Test files follow naming convention: `test_*.py`
- [ ] No temporary test files left behind
- [ ] Code follows project patterns and conventions

### Commit Process
1. **Run assessment**: Execute the pre-commit checklist
2. **Generate commit message**: Based on changes made
3. **Stage changes**: `git add .` (or specific files)
4. **Commit**: `git commit -m "generated message"`
5. **Push**: `git push origin main` (with user approval)
6. **Verify operations**: Run `git status` and `git log --oneline -3` to confirm success

### Confidence Levels for Commits
- **9-10/10**: All tests pass, `motive` successful, documentation updated, no temporary code
- **7-8/10**: Most tests pass, minor issues that don't affect core functionality
- **<7/10**: Do not commit - fix issues first

## Critical Commands and Patterns

### Platform-Specific Commands
- **Use PowerShell syntax for git commands**: On Windows, use `;` instead of `&&` for command chaining. Example: `git add .; git commit -m "message"; git push`
- **Use `motive` with defaults for validation**: Simply run `motive` (no arguments needed) to validate changes, as it defaults to `configs/game.yaml` and auto-generates game IDs.
- **Use test configs for specific validation**: Use `motive -c tests/configs/integration/game_test.yaml` to test with specific configurations, hints, and shorter game rounds. This is especially useful for debugging specific actions or behaviors.

### Decision Making
- **Don't ask permission for high-confidence operations**: When confidence is 8+ and rationale is provided, just run the operation (like `motive`). The user will reject if they don't want it run.
- **Don't ask permission for high-confidence git commits**: When commit assessment is 9-10/10 AND after successful `motive` validation, just proceed with staging, committing, and pushing. The user will reject if they don't want it.
- **CRITICAL: Understand root cause before making changes**: Don't run off changing things before you understand the root cause of an issue. You're likely to do more harm than good. Always trace back to the source of the problem first - check config files, understand what's being merged, identify the actual issue before implementing fixes.

## What to Avoid

- **Don't use inline Python for testing**: Create proper test files instead of running inline code
- **Don't change tests to pass**: When a test exposes a real defect, update the implementation first
- **Don't self‑observe**: The acting player should not receive their own event as an observation
- **Don't use freeform configuration**: Structured config prevents security issues and improves maintainability
- **Don't clear unfinished TODOs without express permission**: TODOs represent work in progress and should only be cleared when explicitly authorized by the user
- **Don't YOLO large features**: Avoid implementing massive changes without following TDD workflow, as this leads to extensive cleanup and test fixing
- **Interrupting workflows**: Don't break LLM processes mid-execution
- **Asking for permission repeatedly**: Trust LLMs to follow established patterns
- **Ignoring error messages**: Read and understand errors before proceeding
- **Not documenting lessons**: Let valuable insights get lost
- **Ad-hoc problem solving**: Prefer systematic approaches over random fixes

## Getting Started

### Prerequisites
- Python 3.10+ with virtual environment
- Required packages from `requirements.txt`
- API keys for LLM providers (see `env.example.txt`)

### First Steps
1. Read this file completely
2. Review `README.md` for project overview
3. Check `configs/` directory for configuration structure
4. Run `pytest tests/` to verify test suite
5. Start with integration tests before running `motive`

### Where to Find More Info
- **`README.md`**: Project setup and overview
- **`CONTRIBUTORS.md`**: Architecture, setup, and development workflows
- **`configs/core.yaml`**: Core action definitions
- **`configs/game.yaml`**: Main game configuration
- **`tests/`**: Test examples and patterns
- **`logs/`**: Real game execution logs for reference
- **`VIBECODER.md`**: Human-LLM collaboration lessons
- **`TODO.md`**: Current development priorities

## Core Actions Definition

**Core actions** are actions that are defined in all themes and editions of Motive. These are fundamental actions available to all players regardless of the game theme or edition. They form the basic interaction layer that all games share.

Current core actions include: `move`, `say`, `look` (including `look inventory`), `help`, `whisper`, `shout`, `pickup`, `drop`, `read`, `pass`.

**Note**: The `inventory` action has been integrated into the `look` action as `look inventory` to follow the verb + noun design principle.

## Detailed Implementation Guidelines

### Motive-Specific Policies
- **Observation delivery and clearing**: Present queued observations in the player prompt and clear them only after the message is constructed/sent
- **Help and prompts consolidation**: Avoid duplicate prompts after `help`. Either include the prompt in the help feedback or suppress the immediate re‑prompt
- **Standardize messages and delimiters**: Use consistent headers (e.g., `**Recent Events:**`), bullet `•`, and delimiters (`===` for major, `---` for rounds)
- **Action set and guidance**: Use "Example actions" in prompts; keep the full list discoverable via `help`
- **Turn end confirmation**: Accept both `> continue` and `continue` (and the same for `quit`), but communicate a consistent format in prompts
- **Movement observations must include direction**: Exit/enter events should specify which direction players moved
- **Turn end confirmation handling**: During turn end confirmation, only accept "continue" or "quit" actions

This workflow ensures that every real-world issue becomes a learning opportunity that strengthens the test suite and prevents future similar issues.