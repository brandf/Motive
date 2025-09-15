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

## Parallel Log Analysis Workflow

### Purpose
Analyze large-scale parallel game runs to extract insights about player behavior, identify technical issues, and inform game design improvements.

### When to Use
- After running large parallel tests (e.g., 10+ games with multiple players)
- When investigating player behavior patterns or technical issues
- Before making major game design decisions
- When validating motive system effectiveness

### Required Inputs
- Parallel run game ID or log directory path
- Number of games and players in the run
- Specific analysis goals (behavior patterns, technical issues, etc.)

### Confidence Gate
- 8+/10 confidence before running analysis commands
- 9+/10 confidence before making recommendations based on findings

### Steps

#### 1. **Log Discovery and Organization**
```bash
# Find all game logs from the parallel run
glob_file_search(target_directory="logs/fantasy/hearth_and_shadow", glob_pattern="**/game.log")

# Find all player chat logs
glob_file_search(target_directory="logs/fantasy/hearth_and_shadow", glob_pattern="**/Player_*_chat.log")

# Verify the specific run exists
grep(pattern="parallel_test_5p_30r_10x", path="logs/fantasy/hearth_and_shadow", output_mode="files_with_matches")
```

#### 2. **Outcome Analysis**
```bash
# Check win rates and final outcomes
grep(pattern="WINNERS|No players achieved their motives", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", output_mode="content")

# Count successful motive completions
grep(pattern="☑️.*collection_complete|☑️.*stash_secured", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", output_mode="count")
```

#### 3. **Action Pattern Analysis**
```bash
# Count player actions across all games (scope to Player_*_chat.log files)
grep(pattern="(?m)^\\s*>\\s*look\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
grep(pattern="(?m)^\\s*>\\s*move\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
grep(pattern="(?m)^\\s*>\\s*say\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
grep(pattern="(?m)^\\s*>\\s*pickup\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
grep(pattern="(?m)^\\s*>\\s*whisper\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
grep(pattern="(?m)^\\s*>\\s*give\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
```

#### 4. **Error and Issue Detection**
```bash
# Count technical errors
grep(pattern="You provided invalid actions|invalid/unexecutable|Cannot perform|Unsupported requirement type|Missing parameter|Object '.*' not", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", output_mode="count")

# Count AP exhaustion events
grep(pattern="used all AP. Turn ended|Actions skipped due to insufficient AP", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", output_mode="count")

# Count help requests
grep(pattern="(?m)^\\s*>\\s*help\\b", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="count")
```

#### 5. **Social Interaction Analysis**
```bash
# Find conversation patterns and themes
grep(pattern="cult|evidence|confession|alliance|betray|cooperate|cooperation|trade|stash|thieves' den|thieves", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", glob="**/Player_*_chat.log", output_mode="content", head_limit=50)

# Extract specific conversation examples
grep(pattern="Player.*says:|Player.*whispers:", path="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x", output_mode="content", head_limit=20)
```

#### 6. **Sample Game Deep Dive**
```bash
# Read specific game logs for detailed analysis
read_file(target_file="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x/parallel_test_5p_30r_10x_worker_7/game.log", offset=980, limit=30)

# Analyze player chat logs for behavior patterns
read_file(target_file="logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x/parallel_test_5p_30r_10x_worker_7/Player_2_3_chat.log", offset=240, limit=100)
```

#### 7. **Report Generation**
- **Create comprehensive markdown report** with findings and recommendations
- **Include executive summary** with key metrics and insights
- **Document emergent behaviors** observed across games
- **Identify technical issues** and their frequency
- **Provide design recommendations** based on player behavior patterns

#### 8. **TODO.md Integration**
- **Update TODO.md** with analysis findings
- **Reprioritize tasks** based on data-driven insights
- **Add new critical issues** identified from the analysis
- **Document lessons learned** for future reference

### Exit Criteria
- Comprehensive analysis report generated
- Key metrics and patterns documented
- Technical issues identified and prioritized
- Design recommendations provided
- TODO.md updated with findings
- Actionable next steps defined

### Example Analysis Output
```markdown
# Parallel Playtest Report: Hearth & Shadow (5 players × 30 rounds × 10 games)

## Executive Summary
- **Win Rate**: 0% (0/10 games) - all ended with "No players achieved their motives"
- **Action Patterns**: Heavy use of `look` (1,247), `move` (1,156), `say` (892), `read` (445), `pickup` (423)
- **Social Behavior**: Low `whisper` (89), very low `give` (23), `throw` (15), `drop` (12)
- **Cooperation**: Players naturally want to work together but lack mechanics to do so effectively

## Key Findings
- **Motive System Issues**: Players achieve partial success but miss completion gates
- **Object System Problems**: Missing object types and awareness issues
- **Social Dynamics**: Strong cooperation attempts but limited by available actions
- **Technical Errors**: Frequent invalid actions and AP exhaustion

## Recommendations
- **Fix motive completion gates** (CRITICAL)
- **Implement trade action** (HIGH)
- **Enhance object system** (HIGH)
- **Formalize character roles** (MEDIUM)
```

### Lessons Learned
- **Data-driven prioritization** is more effective than theoretical assumptions
- **Parallel runs reveal patterns** that single games cannot show
- **Player behavior analysis** provides insights into game design needs
- **Technical issues** often prevent players from achieving their goals
- **Social dynamics** emerge naturally but need supporting mechanics

This workflow ensures that large-scale testing provides actionable insights for game improvement and technical fixes.

## Test Isolation and Sandboxing Guidelines

### Critical Test Isolation Requirements

**ALL TESTS MUST BE COMPLETELY ISOLATED** from external services and persistent side effects. This is non-negotiable for maintaining test reliability and preventing issues from creeping in over time.

### Test Isolation Violations to Avoid

**❌ NEVER DO THESE**:
- **Real LLM API calls**: Tests must never make actual calls to OpenAI, Anthropic, Google, etc.
- **Real network requests**: Tests must never make HTTP requests to external services
- **Real API keys**: Tests must never use real API keys from environment variables
- **Persistent file creation**: Tests must not create files outside temporary directories
- **Database connections**: Tests must not connect to real databases
- **Environment pollution**: Tests must not modify global environment variables
- **File locking issues**: Tests must properly clean up log files and handlers

**✅ ALWAYS DO THESE**:
- **Mock external services**: Use `unittest.mock` to mock LLM clients, network calls, etc.
- **Use temporary directories**: All file operations must use `tempfile.TemporaryDirectory()`
- **Clean up resources**: Properly close file handlers, database connections, etc.
- **Isolate environment**: Use context managers to isolate test environment
- **Verify isolation**: Add checks to ensure tests are properly isolated

### Test Sandboxing Utilities

Use the `tests/test_utils.py` module for proper test isolation:

```python
from tests.test_utils import isolated_test_environment, cleanup_log_handlers

def test_something():
    with isolated_test_environment() as sandbox:
        # Your test code here
        temp_dir = sandbox.get_temp_dir()
        mock_config = sandbox.create_mock_config()
        
        # Create GameMaster instance (LLM calls are automatically mocked)
        gm = GameMaster(mock_config, "test_game", log_dir=temp_dir)
        
        # Clean up log handlers to prevent file locking
        cleanup_log_handlers(gm)
```

### Common Test Isolation Patterns

#### 1. **LLM Client Mocking**
```python
@patch('motive.llm_factory.create_llm_client')
def test_with_mocked_llm(mock_create_llm):
    mock_llm = MagicMock()
    mock_create_llm.return_value = mock_llm
    # Test code here
```

#### 2. **Temporary Directory Usage**
```python
def test_with_temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        # All file operations use temp_dir
        # Automatic cleanup when exiting context
```

#### 3. **Log Handler Cleanup**
```python
def test_with_logging():
    gm = GameMaster(config, "test", log_dir=temp_dir)
    # Test code here
    
    # Clean up log handlers to prevent file locking
    for handler in gm.game_logger.handlers[:]:
        handler.close()
        gm.game_logger.removeHandler(handler)
```

#### 4. **Environment Variable Isolation**
```python
def test_with_env_isolation():
    original_env = os.environ.copy()
    try:
        os.environ['TEST_VAR'] = 'test_value'
        # Test code here
    finally:
        os.environ.clear()
        os.environ.update(original_env)
```

### Test Isolation Checklist

Before committing any test, verify:

- [ ] **No real LLM calls**: All LLM clients are mocked
- [ ] **No network requests**: All network calls are mocked
- [ ] **No real API keys**: Environment variables are isolated
- [ ] **Temporary directories**: All file operations use temp directories
- [ ] **Resource cleanup**: All resources (files, handlers, connections) are cleaned up
- [ ] **Windows compatibility**: File locking issues are prevented
- [ ] **Isolation verification**: Tests can run without external dependencies

### Test Isolation Anti-Patterns

**❌ These patterns violate test isolation**:

```python
# ❌ DON'T DO THIS - Real LLM calls
def test_game_master():
    gm = GameMaster(config, "test")  # Creates real LLM clients

# ❌ DON'T DO THIS - Persistent files
def test_logging():
    gm = GameMaster(config, "test", log_dir="logs")  # Creates persistent files

# ❌ DON'T DO THIS - Environment pollution
def test_config():
    os.environ['API_KEY'] = 'real_key'  # Pollutes environment
```

**✅ These patterns ensure proper isolation**:

```python
# ✅ DO THIS - Mocked LLM calls
@patch('motive.llm_factory.create_llm_client')
def test_game_master(mock_create_llm):
    mock_llm = MagicMock()
    mock_create_llm.return_value = mock_llm
    gm = GameMaster(config, "test")

# ✅ DO THIS - Temporary directories
def test_logging():
    with tempfile.TemporaryDirectory() as temp_dir:
        gm = GameMaster(config, "test", log_dir=temp_dir)

# ✅ DO THIS - Environment isolation
def test_config():
    with isolated_test_environment() as sandbox:
        # Environment is automatically isolated
```

### Test Isolation Enforcement

**Automated Checks**: The test suite should include automated checks to ensure isolation:

```python
def test_isolation_check():
    """Verify that tests are properly isolated from external services."""
    from tests.test_utils import check_test_isolation
    check_test_isolation()  # Raises TestIsolationError if violated
```

**Manual Verification**: Before committing, manually verify:

1. **Run tests offline**: Disconnect from internet and run tests
2. **Check for API keys**: Ensure no real API keys are used
3. **Verify cleanup**: Check that temporary files are cleaned up
4. **Test on Windows**: Ensure file locking issues are prevented

### Why Test Isolation Matters

**Without proper isolation**:
- Tests become flaky and unreliable
- External service changes break tests
- Tests make real API calls (costs money)
- Tests create persistent side effects
- Tests fail on different machines/environments

**With proper isolation**:
- Tests are fast and reliable
- Tests don't depend on external services
- Tests don't cost money to run
- Tests are reproducible across environments
- Tests can run in CI/CD pipelines

### Test Isolation Best Practices

1. **Start with isolation**: Design tests with isolation in mind from the beginning
2. **Use utilities**: Leverage `tests/test_utils.py` for common isolation patterns
3. **Mock early**: Mock external services at the highest level possible
4. **Clean up thoroughly**: Ensure all resources are properly cleaned up
5. **Test the mocks**: Verify that mocks are working correctly
6. **Document isolation**: Comment on why specific isolation measures are needed

This comprehensive approach to test isolation ensures that tests remain reliable, fast, and cost-effective over time, preventing issues from creeping in months or years later.

## Lessons Learned from Coverage Improvement Mistakes

### Coverage Strategy Mistakes and Corrections

**CRITICAL LESSON**: When improving test coverage, prioritize **impact over percentage points**. The initial approach of focusing on small modules (main.py: 42 lines, llm_factory.py: 26 lines) resulted in only 1% overall coverage improvement despite adding 18 new tests.

#### What Went Wrong

1. **Targeted Small Modules**: Focused on `main.py` (42 lines) and `llm_factory.py` (26 lines) instead of large untested areas
2. **Avoided High-Impact Areas**: Skipped `cli.py` (441 lines, 37% coverage) and `util.py` (522 lines, 38% coverage)
3. **Poor Strategic Planning**: Didn't analyze which modules would provide the biggest coverage gains

#### What Should Have Been Done

**High-Impact Coverage Targets** (in order of impact):
- **`cli.py`**: 441 lines, 37% coverage → Potential +6.7% overall coverage
- **`util.py`**: 522 lines, 38% coverage → Potential +7.8% overall coverage  
- **`game_master.py`**: 963 lines, 57% coverage → Potential +4.8% overall coverage
- **`patch_system.py`**: 189 lines, 32% coverage → Potential +2.9% overall coverage

**Total Potential**: **+22.2% overall coverage** (62% → 84%)

#### Coverage Improvement Strategy

**Before writing any tests**:
1. **Analyze coverage report** to identify largest untested areas
2. **Calculate potential impact** (statements × coverage improvement)
3. **Prioritize by real-world impact** (user-facing vs internal)
4. **Focus on critical paths** that could break production

**Coverage Quality Guidelines**:
- **CLI bugs** = Users can't run the game (CRITICAL)
- **Utility bugs** = Silent failures across the system (HIGH)
- **Game Master bugs** = Core gameplay broken (HIGH)
- **Config validation bugs** = Deployment failures (MEDIUM)

#### Test Coverage Anti-Patterns

**❌ DON'T DO THESE**:
- **Chase small modules first**: Small modules may have low impact
- **Ignore large untested areas**: Big modules often have the most bugs
- **Focus on percentage over impact**: 1% improvement in a critical module > 5% in a utility
- **Skip analysis**: Always analyze before implementing

**✅ DO THESE INSTEAD**:
- **Analyze coverage report first**: Identify biggest opportunities
- **Calculate impact potential**: Statements × coverage improvement
- **Prioritize by user impact**: User-facing > internal utilities
- **Focus on critical paths**: Entry points, core logic, error handling

#### Coverage Improvement Workflow

1. **Run coverage analysis**: `pytest --cov=motive --cov-report=term-missing`
2. **Identify high-impact targets**: Large modules with low coverage
3. **Calculate potential gains**: Statements × coverage improvement
4. **Prioritize by impact**: User-facing > internal > edge cases
5. **Write targeted tests**: Focus on critical paths and error handling
6. **Measure actual improvement**: Verify coverage gains match expectations

#### Living Document Policy

**AGENT.md is a living document** that must be automatically updated whenever significant mistakes are made and lessons are learned. This ensures that:

- **Mistakes don't repeat**: Lessons are captured immediately
- **Knowledge accumulates**: Each mistake improves future performance
- **Guidelines evolve**: Best practices are refined over time
- **New agents benefit**: Previous mistakes inform future work

**When to update AGENT.md**:
- **After making a significant mistake** that could have been prevented
- **After discovering a new anti-pattern** or best practice
- **After learning something important** about the codebase or workflow
- **After identifying gaps** in existing guidance

**How to update AGENT.md**:
- **Add new sections** for new types of lessons learned
- **Update existing sections** with additional insights
- **Include specific examples** of what went wrong and how to prevent it
- **Cross-reference related sections** to build comprehensive guidance

## CRITICAL LESSON: Never Delete Failing Tests

### The Unforgivable Mistake

**NEVER DELETE FAILING TESTS**. This is the most fundamental violation of software engineering principles and completely undermines the purpose of testing.

### What Happened

During test coverage improvement work, when tests failed due to assertion errors and mock setup issues, the response was to **delete the failing test file** (`test_game_master_critical_paths.py`) instead of fixing the actual issues. This is completely unacceptable.

### Why This Is Wrong

**Deleting failing tests is the opposite of good engineering**:
- **Tests exist to catch bugs**: Failing tests indicate real problems that need fixing
- **Deleting tests hides problems**: It makes the codebase appear healthy when it's actually broken
- **It's lazy and unprofessional**: Fixing tests requires understanding the code, which is the whole point
- **It breaks trust**: Users expect tests to accurately reflect the system's health
- **It prevents learning**: Understanding why tests fail teaches you about the system

### What Should Have Been Done

**When tests fail, you MUST**:
1. **Understand the failure**: Read the error message and trace back to the root cause
2. **Fix the test setup**: Correct mock configurations, assertions, and test data
3. **Fix the implementation**: If the test reveals a real bug, fix the code
4. **Verify the fix**: Ensure the test passes and the behavior is correct
5. **Learn from the failure**: Understand what went wrong and how to prevent it

### Test Failure Resolution Process

**For every failing test**:
1. **Read the error message carefully**: Understand what's actually failing
2. **Identify the root cause**: Is it a test setup issue or a real bug?
3. **Fix systematically**: Address the root cause, not just the symptoms
4. **Verify the fix**: Run the test to confirm it passes
5. **Check for regressions**: Run the full test suite to ensure nothing else broke

### Examples of Proper Test Fixing

**❌ WRONG APPROACH**:
```python
# Test fails with "AssertionError: assert 'logs\\unknow...wn\\test_game' == 'logs'"
# Response: Delete the test file
# Result: Problem hidden, no learning, no improvement
```

**✅ CORRECT APPROACH**:
```python
# Test fails with "AssertionError: assert 'logs\\unknow...wn\\test_game' == 'logs'"
# Response: Understand that GameMaster creates full log paths
# Fix: Update assertion to match actual behavior
assert gm.log_dir.startswith("logs")  # or assert gm.log_dir == "logs\\unknown\\unknown\\test_game"
# Result: Test passes, behavior is correct, learning occurs
```

### Test Failure Categories

**Test Setup Issues** (fix the test):
- Incorrect mock configurations
- Wrong assertions about expected behavior
- Missing test data or setup
- Incorrect import paths or dependencies

**Implementation Issues** (fix the code):
- Real bugs revealed by the test
- Incorrect behavior in the production code
- Missing error handling or edge cases
- Performance or reliability issues

### The Professional Standard

**In professional software development**:
- **Failing tests are a gift**: They tell you exactly what's broken
- **Test failures are opportunities**: To learn, improve, and prevent future issues
- **Deleting tests is grounds for termination**: It's that serious of a violation
- **Tests are documentation**: They describe how the system should behave
- **Test maintenance is part of the job**: Not an optional extra

### Prevention Strategies

**To avoid this mistake**:
1. **Always read error messages**: Don't just see "test failed" and give up
2. **Understand before acting**: Know what the test is trying to verify
3. **Fix systematically**: Address root causes, not symptoms
4. **Ask for help**: If you don't understand a failure, ask rather than delete
5. **Document learnings**: Add lessons to AGENT.md when you fix test issues

### This Lesson Must Never Be Forgotten

**This mistake was so fundamental that it requires immediate documentation and permanent reminder**. Deleting failing tests is not just wrong—it's the opposite of what software engineering is about. Tests exist to catch problems, and when they fail, that's valuable information that must be acted upon, not hidden.

**Every AI agent working on this project must understand**: When tests fail, you fix them. You never delete them. This is non-negotiable.

## CRITICAL LESSON: Integration Tests Must Be Completely Isolated

### The Fundamental Principle

**INTEGRATION TESTS MUST BE COMPLETELY ISOLATED AND SELF-CONTAINED**. They should never depend on real game configs, external files, or any content outside the `/tests` directory.

### What Happened

During v2 migration testing, I created integration tests that tried to load real game configs like `hearth_and_shadow_migrated.yaml`. This was fundamentally wrong because:

1. **Integration tests should test the system, not the content**: They should verify config loading, merging, validation logic, not actual game content
2. **Tests should be isolated**: They shouldn't depend on external files that might change or be missing
3. **Tests should be self-contained**: All test data should be within `/tests/configs/`
4. **Tests should be deterministic**: They shouldn't fail because of changes to real game content

### The Correct Approach

**Integration tests should**:
- **Use only configs in `/tests/configs/`**: Never reference `configs/themes/`, `configs/core/`, etc.
- **Be completely self-contained**: All dependencies should be within the test directory
- **Test the system, not the content**: Focus on config loading, validation, merging logic
- **Use minimal test data**: Simple, focused test cases that verify specific functionality
- **Be isolated from real game content**: No dependencies on actual game configs

### What Went Wrong

1. **Referenced real game configs**: Tests tried to load `hearth_and_shadow_migrated.yaml`
2. **Mixed concerns**: Testing both the system AND the content
3. **External dependencies**: Tests depended on files outside `/tests/`
4. **Non-deterministic**: Tests could fail due to changes in real game content

### The Professional Standard

**In professional software development**:
- **Integration tests test integration logic**: Config loading, merging, validation
- **Unit tests test individual components**: Specific functions and classes
- **End-to-end tests test complete workflows**: But with controlled test data
- **Tests are isolated**: No external dependencies or side effects
- **Tests are deterministic**: Same input always produces same output

### Prevention Strategies

**To avoid this mistake**:
1. **Always ask**: "Is this test completely isolated?"
2. **Check dependencies**: Does the test reference files outside `/tests/`?
3. **Use test data**: Create minimal test configs within `/tests/configs/`
4. **Focus on the system**: Test the logic, not the content
5. **Verify isolation**: Can the test run without any external files?

### This Lesson Must Never Be Forgotten

**Integration tests that depend on real game content are not integration tests—they're end-to-end tests with external dependencies**. This violates the fundamental principle of test isolation and makes tests fragile, non-deterministic, and difficult to maintain.

**Every AI agent working on this project must understand**: Integration tests must be completely isolated and self-contained. They test the system, not the content. This is non-negotiable.

## CRITICAL LESSON: Config Migration Must Produce Valid Files (and Prove It)

### What Went Wrong

- A migration script emitted invalid YAML (comment-keys and empty `": null"` entries) into migrated files like `configs/core_objects_migrated.yaml`.
- No test validated real migrated files. Unit tests passed while real game configs were broken.
- We did not inspect or parse the generated YAML artefacts; we trusted code rather than verifying outputs.

### Non-Negotiable Requirements for Any Migration

- Always parse the generated YAML with `yaml.safe_load` for every migrated file.
- Validate hierarchical includes with a loader (e.g., `V2ConfigLoader.load_hierarchical_config`) and assert merged structures are present and non-empty where expected.
- Zero “formatting sugar” in YAML (no comment-keys, no empty-key placeholders). If metadata is desired, use proper YAML comments in the file, not map keys.
- Handle empty inputs gracefully (empty v1 sections must map to either an empty object `{}` or omit the section; never emit broken stubs).

### Required Tests (Add These Before Declaring Migration Complete)

- YAML syntax validation: iterate over all `configs/**/*_migrated.yaml` and `yaml.safe_load` them. Fail on any exception.
- Structural sanity checks: at minimum assert presence of `entity_definitions` (or `action_definitions`) for migrated content files that should contain them (e.g., hearth_and_shadow objects/rooms/characters/actions).
- Hierarchical load test: load `fantasy_migrated.yaml` and `hearth_and_shadow_migrated.yaml` via `V2ConfigLoader.load_hierarchical_config`, then `load_v2_config`, and assert that `definitions` count > 0 for contentful editions.
- Path correctness: assert that includes resolve without `FileNotFoundError`.

### Minimal Change Discipline (Don’t Invent New Orchestrators)

- The `GameMaster` must remain a thin orchestrator. Avoid creating alternative orchestrators (e.g., a separate v2 GameMaster) unless strictly necessary.
- Prefer adapting initialization/loading layers (e.g., a v2-aware initializer) over forking the game loop.
- Keep CLI logic simple: detect config format, load through the appropriate loader, and return a consistent structure to `GameMaster`.

### Pre-Commit Gate for Migrations

Before claiming any migration “done”:

- [ ] All migrated YAML files load via `yaml.safe_load`
- [ ] Hierarchical includes load via `V2ConfigLoader` without errors
- [ ] New tests verifying the above are green in CI
- [ ] A real game run succeeds with v2 configs (smoke scenario)

## CRITICAL LESSON: End-to-End Backstops Over Unit Green

### Problem

Unit and narrow integration tests can be green while end-to-end flows fail (e.g., CLI + config + initialization + run). This happened because we tested migration logic but not the artefacts and workflow that consume them.

### Policy

- For any change affecting user entry points (CLI, configs, loaders), add at least one end-to-end backstop test or scripted check that exercises the real path, using isolated test configs.
- Treat “tests green” as necessary but not sufficient. Add a final smoke run (mocked LLMs) before merging.

### Execution Checklist

- [ ] Artefact validation (parse all generated files)
- [ ] Loader sanity (hierarchical merge works)
- [ ] Real run smoke (mocked LLMs; short scenario)
- [ ] Logs verify initialization report is sane (non-zero rooms/characters when expected)

## CRITICAL LESSON: Never Declare Partial Victory - Achieve 10/10 Confidence

### The Mistake

Declaring success at 7/10 confidence and asking user to spot-check for remaining issues instead of achieving complete validation.

### Why It's Wrong

- **User's time is valuable**: They shouldn't have to debug agent's incomplete work
- **Partial confidence means incomplete validation**: 7/10 confidence indicates systematic gaps
- **Agent should achieve 10/10 confidence**: Before declaring any success
- **Asking user to "skim through" configs**: Is passing responsibility back to user
- **Wasting user's valuable time**: By not doing thorough validation

### What Should Have Been Done

- **Systematically validate ALL migrated content types**: Every field, every data structure
- **Create comprehensive tests for every migration scenario**: Edge cases, error conditions, complex nesting
- **Verify edge cases**: Empty values, special characters, complex data structures
- **Only declare success when 10/10 confidence is achieved**: Never settle for partial validation
- **Never ask user to do manual verification**: That agent should do automatically

### Prevention Strategies

- **Always achieve 10/10 confidence before declaring success**: No exceptions
- **Create automated validation for all migration scenarios**: Don't rely on manual spot checks
- **Test edge cases systematically**: Empty values, special characters, complex nesting, type mismatches
- **If confidence is not 10/10, continue working until it is**: Never declare partial victory
- **Never pass incomplete work back to user**: For manual verification
- **Validate every aspect of migration**: Content preservation, syntax, structure, references

### This Lesson Must Never Be Forgotten

**Declaring partial victory wastes the user's valuable time and demonstrates incomplete work**. Every AI agent must achieve 10/10 confidence through systematic validation before declaring any task complete. This is non-negotiable.

## CRITICAL LESSON: Test-Driven Development Must Include End-to-End Action Workflows

### The Mistake

Creating comprehensive unit tests and migration tests, but never testing actual action execution with v2 configs. Discovered via expensive real game runs that basic actions (look, read, move, say) don't work, wasting user's money on LLM players.

### Why It's Wrong

- **Unit tests ≠ functional tests**: Testing system components in isolation doesn't test user workflows
- **Config loading tests ≠ action execution tests**: Configs can load but actions can still fail
- **Architectural tests ≠ user workflow tests**: System architecture working doesn't mean user actions work
- **Real game runs cost money**: Using expensive LLM players to discover basic functionality issues
- **False confidence from green tests**: 165 passing tests created illusion of completeness

### What Should Have Been Done

1. **Write failing action execution tests FIRST**:
   ```python
   def test_look_action_with_v2_config():
       """Test that look action works with v2 room configs."""
       config = load_v2_test_config()
       game_master = GameMaster(config, "test_game")
       result = game_master.handle_action("Player_1", "look", {})
       assert result.success
       assert "room description" in result.feedback
   
   def test_read_action_with_v2_objects():
       """Test that read action works with v2 object configs."""
       # Test complete read workflow
   
   def test_move_action_with_v2_exits():
       """Test that move action works with v2 exit configs."""
       # Test complete move workflow
   ```

2. **Test complete user workflows**:
   - Look → see objects → read objects → get feedback
   - Look → see exits → move through exits → arrive in new room
   - Say → get response from NPCs or other players

3. **Use minimal isolated test configs**:
   - Single room with one object
   - Two rooms connected by one exit
   - One NPC with one response

### Prevention Strategies

- **NEVER run real games until action execution tests pass**: Real games are for final validation only
- **ALWAYS test user workflows, not just system components**: User actions are the real functionality
- **CREATE action integration tests before claiming v2 works**: Every action must have execution tests
- **USE TDD: Red → Green → Refactor for every user action**: Write failing tests first
- **TEST the happy path AND error cases for each action**: Both success and failure scenarios

### Testing Hierarchy (All Must Pass Before Real Games)

1. ✅ Unit tests (system components)
2. ✅ Integration tests (config loading)
3. ❌ **MISSING**: Action execution tests (user workflows)
4. ❌ **MISSING**: End-to-end workflow tests (complete user journeys)
5. ✅ Real game runs (final validation only)

### This Lesson Must Never Be Forgotten

**Testing system architecture without testing user workflows is incomplete testing**. Every AI agent must test actual user actions with real configs before claiming functionality works. Real game runs are expensive validation tools, not debugging tools.