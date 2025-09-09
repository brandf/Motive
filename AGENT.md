# AI Agent Guidelines

This file contains essential guidance for AI agents working on the Motive project. It serves as a living guide for maintaining high engineering quality and avoiding common pitfalls.

## Project Context

**Motive** is a platform for LLM benchmarking through turn-based games. It provides a structured environment where AI players can interact, make decisions, and be evaluated on their strategic thinking and communication abilities.

### Key Architectural Decisions
- **Action-based interaction**: Players interact through structured actions (e.g., `> move north`, `> whisper Player "hello"`)
- **Event-driven system**: Actions generate events that are distributed to relevant observers
- **Theme/edition system**: Core actions are available across all themes, with theme-specific actions for specialized gameplay
- **Configuration-driven**: Game behavior is defined through YAML configuration files

### Current State and Priorities
- **Core actions implementation**: Building fundamental actions available to all players
- **Testing infrastructure**: Establishing robust test coverage for reliable development
- **Real-world validation**: Using `motive.main` runs to validate functionality with actual LLM players

## Development Workflow

### Testing Philosophy
- **Default to tests over paid runs**: Running `python -m motive.main` triggers paid LLM calls. Prefer unit/integration tests which stub external LLMs.
- **Favor integration tests over heavy mocking**: Write tests that exercise real code paths and types. Mock only external services (e.g., LLM APIs, filesystem/network), not core logic.
- **Use real constructors and APIs**: Build objects with their true signatures so tests mirror production.
- **Tests should prove real fixes**: Add integration tests that fail before a fix and pass after.

### Quality Gates
- **Confidence scale (1–10) before paid runs**:
  - 9–10: Broad integration coverage, deterministic seeds, recent green runs, stable configs
  - 7–8: Integration tests cover new logic end-to-end with stubs, logs verified
  - 5–6: Unit tests pass but integration coverage is partial
  - ≤4: Significant unknowns, heavy mocking, or flakiness; do not run paid flows
- **Gate to run `motive.main`**: Only after tests are green, logs look correct, and configs are validated

### Code Organization Principles
- **Use convention-based imports**: Rely on naming conventions rather than explicit module specifications
- **Separate concerns**: Break complex methods into smaller, focused functions for better testability
- **Design for testability**: Structure code so individual components can be tested in isolation

## Common Patterns

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

## Lessons Learned

### What Works Well
- **Integration tests with real objects**: Use actual Pydantic models instead of mocks
- **Test configuration parsing separately from logic**: Verify config structure before testing business logic
- **Test both positive and negative cases**: Include boundary conditions and edge cases
- **Mock external dependencies in tests**: Avoid instantiating full system objects that require external deps

### What to Avoid
- **Don't use inline Python for testing**: Create proper test files instead of running inline code
- **Don't change tests to pass**: When a test exposes a real defect, update the implementation first
- **Don't self‑observe**: The acting player should not receive their own event as an observation
- **Don't use freeform configuration**: Structured config prevents security issues and improves maintainability

### Real-World Issue Resolution
When issues are found in `motive.main` that should have been caught by tests:

1. **Issue Analysis**: Evaluate preventability, identify root cause, assess test gap
2. **Test-First Fix**: Write failing test first, confirm it fails, fix root cause, verify test passes
3. **Validation**: Achieve high confidence, use hints for reproduction, document the lesson

## Git Commit Workflow

### Pre-Commit Assessment Checklist
Before committing changes, verify all items are complete:

#### **Code Quality & Testing**
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linter errors: `pytest tests/ --tb=short` (check for any failures)
- [ ] Real-world validation passed: `motive.main` completed successfully
- [ ] No temporary debug code or print statements left in production code

#### **Configuration & Documentation**
- [ ] Configuration files updated correctly (e.g., `configs/core.yaml`, `configs/game.yaml`)
- [ ] Temporary hint configurations removed from `configs/game.yaml` (if added for testing)
- [ ] Documentation updated: `AGENT.md`, `VIBECODER.md`, `README.md` as needed
- [ ] New lessons learned added to appropriate documentation files

#### **Code Organization**
- [ ] New test files created for new functionality
- [ ] Test files follow naming convention: `test_*.py`
- [ ] No temporary test files left behind
- [ ] Code follows project patterns and conventions

#### **Commit Message Standards**
- **Format**: `feat/fix/docs/test: brief description`
- **Types**: `feat` (new features), `fix` (bug fixes), `docs` (documentation), `test` (tests), `refactor` (code changes)
- **Description**: Clear, concise description of what changed
- **Examples**:
  - `feat: implement whisper and shout communication actions`
  - `fix: correct help action AP cost to match manual (1 AP)`
  - `docs: add git commit workflow to AGENT.md`

### Commit Process
1. **Run assessment**: Execute the pre-commit checklist
2. **Generate commit message**: Based on changes made
3. **Stage changes**: `git add .` (or specific files)
4. **Commit**: `git commit -m "generated message"`
5. **Push**: `git push origin main` (with user approval)

### Confidence Levels for Commits
- **9-10/10**: All tests pass, `motive.main` successful, documentation updated, no temporary code
- **7-8/10**: Most tests pass, minor issues that don't affect core functionality
- **<7/10**: Do not commit - fix issues first

## Getting Started

### Prerequisites
- Python 3.13+ with virtual environment
- Required packages from `requirements.txt`
- API keys for LLM providers (see `env.example.txt`)

### First Steps
1. Read this file completely
2. Review `README.md` for project overview
3. Check `configs/` directory for configuration structure
4. Run `pytest tests/` to verify test suite
5. Start with integration tests before running `motive.main`

### Where to Find More Info
- **`README.md`**: Project setup and overview
- **`configs/core.yaml`**: Core action definitions
- **`configs/game.yaml`**: Main game configuration
- **`tests/`**: Test examples and patterns
- **`logs/`**: Real game execution logs for reference

## Core Actions Definition

**Core actions** are actions that are defined in all themes and editions of Motive. These are fundamental actions available to all players regardless of the game theme or edition. They form the basic interaction layer that all games share.

Current core actions include: `move`, `say`, `look`, `help`, `whisper`, `shout`, `pickup`, `drop`, `inventory`, `read`, `continue`, `quit`.

## Detailed Implementation Guidelines

### Motive-Specific Policies
- **Observation delivery and clearing**: Present queued observations in the player prompt and clear them only after the message is constructed/sent
- **Help and prompts consolidation**: Avoid duplicate prompts after `help`. Either include the prompt in the help feedback or suppress the immediate re‑prompt
- **Standardize messages and delimiters**: Use consistent headers (e.g., `**Recent Events:**`), bullet `•`, and delimiters (`===` for major, `---` for rounds)
- **Action set and guidance**: Use "Example actions" in prompts; keep the full list discoverable via `help`
- **Turn end confirmation**: Accept both `> continue` and `continue` (and the same for `quit`), but communicate a consistent format in prompts
- **Movement observations must include direction**: Exit/enter events should specify which direction players moved
- **Turn end confirmation handling**: During turn end confirmation, only accept "continue" or "quit" actions

### Testing Specifics
- **Check import paths when writing tests**: Verify correct import paths by checking where classes are actually defined
- **Test edge cases in configuration evaluation**: Test missing fields, empty values, and invalid combinations
- **Test both positive and negative cases**: Include boundary conditions and edge cases
- **Test requirement type implementations**: When adding new requirement types (like `player_in_room`), create integration tests that verify the requirement checking logic works correctly with real player and room data. Test both success and failure cases.
- **Verify Pydantic field names**: When working with configuration, always check the actual field names in the Pydantic model definitions rather than assuming names (e.g., `target_player_param` not `player_name_param`).
- **Don't ask permission for high-confidence operations**: When confidence is 8+ and rationale is provided, just run the operation (like `motive.main`). The user will reject if they don't want it run.
- **Don't ask permission for high-confidence git commits**: When commit assessment is 9-10/10, just proceed with staging, committing, and pushing. The user will reject if they don't want it.
- **Batch git operations**: Use `&&` to chain git commands (e.g., `git add . && git commit -m "message" && git push`) to reduce approval requests.

### Configuration Security
- **Prefer structured over freeform configuration**: Use structured objects/dictionaries instead of freeform strings that require evaluation
- **Design for extensibility**: Include placeholder fields for future expansion even if not immediately implemented
- **Unify related configuration fields**: Integrate similar concepts into single structured fields
- **Use declarative over imperative configuration**: Describe what should happen rather than how to do it

## Real-World Issue Resolution Workflow

When issues are found in `motive.main` that should have been caught by tests, follow this systematic approach:

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

### 3. **Test Categories to Consider**
- **Integration tests with real objects**: Use actual Pydantic models instead of mocks
- **Configuration loading tests**: Test real YAML parsing and object instantiation
- **End-to-end action flow tests**: Test complete action execution pipelines
- **Error condition tests**: Test edge cases and failure modes
- **Cross-component interaction tests**: Test how different modules work together

### 4. **Validation and Prevention**
- **Achieve high confidence**: Get to 9-10 confidence level before running `motive.main`
- **Use hints for reproduction**: After fixing, use the hint system to try reproducing the original issue in `motive.main`
- **Document the lesson**: Add the specific test pattern to `AGENT.md` to prevent similar issues

### 5. **Learning and Generalization**
- **Identify generalizable patterns**: After fixing an issue, consider what broader lessons can be learned
- **Look for missing guidance**: Check if the issue reveals gaps in existing guidelines
- **Add preventive lessons**: Document specific patterns that could have prevented the issue
- **Update workflow if needed**: Enhance the workflow itself based on new insights
- **Update VIBECODER.md**: Add human-LLM collaboration lessons to help future developers

### 6. **Example Workflow**
```
Issue: "Unsupported requirement type: player_in_room" in whisper action
1. Analysis: Missing integration test for requirement checking
2. Write test: test_whisper_action_with_player_in_room_requirement()
3. Confirm fails: Test fails with current code
4. Fix: Implement player_in_room requirement checking
5. Verify: Test passes, full suite passes
6. Validate: Run motive.main with whisper hints to confirm fix
7. Document: Add lesson about testing requirement types
8. Generalize: Add lesson about verifying Pydantic field names
9. Update workflow: Add learning and generalization step
10. Update VIBECODER.md: Add lesson about mode awareness and systematic workflows
```

This workflow ensures that every real-world issue becomes a learning opportunity that strengthens the test suite and prevents future similar issues.
