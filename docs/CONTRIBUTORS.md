# Contributing to Motive

This guide is for human contributors who want to understand the architecture, development workflows, and how to contribute to the Motive project.

## Quick Start

1. **Read the project overview**: Start with [README.md](../README.md) to understand what Motive is and its goals
2. **Set up development environment**: Follow the setup instructions below
3. **Understand the architecture**: Review the architecture section
4. **Run tests**: Ensure everything works with `pytest tests/`
5. **Start contributing**: Follow the development workflow guidelines

## Development Environment Setup

### Prerequisites

- **Python 3.10+**: Ensure you have a compatible Python version installed and added to your system PATH
- **Git**: For cloning the repository
- **API Keys**: Access to API keys for your desired LLM providers (e.g., OpenAI, Google Generative AI, Anthropic). Refer to `env.example.txt` and `configs/game.yaml`

### Automated Setup (Recommended)

The easiest way to set up the project is using the provided setup scripts:

#### Windows (PowerShell)

**First, install Python if you haven't already:**
1. Download Python 3.10+ from https://www.python.org/downloads/
2. **Important**: During installation, check "Add Python to PATH"
3. Verify installation: `python --version` and `pip --version`

**Then run the setup script:**
```powershell
# Fix PowerShell execution policy (run as Administrator if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the automated setup script
./setup.ps1
```

#### macOS/Linux (Bash)

```bash
# Make the script executable and run it
chmod +x setup.sh
./setup.sh
```

### Manual Setup (Alternative)

If you prefer to set up manually or the automated scripts don't work:

#### Create Virtual Environment

```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .  # Install project in editable mode
```

#### Set Up Configuration

```bash
# Copy environment template
# On Windows:
copy env.example.txt .env
# On macOS/Linux:
cp env.example.txt .env

# Create logs directory
mkdir logs
```

### Configure API Keys

1. Open the `.env` file in a text editor
2. Replace the placeholder values with your actual API keys:
   - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
   - `GOOGLE_API_KEY` - Get from https://console.cloud.google.com/
   - `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

**Note**: Never commit your `.env` file to version control.

### Configure Game (Optional)

Review and modify `configs/game.yaml` to adjust game settings, players, and LLM models. Ensure the models specified are compatible with your chosen providers and available in your region/plan.

## Architecture Overview

Motive is built around several key architectural components:

### Core Components

- **Game Master (`motive/game_master.py`)**: Central orchestrator that manages game state, processes player actions, and coordinates between players
- **Configuration System (`motive/config.py`)**: Hierarchical YAML-based configuration with Pydantic validation
- **Action System (`motive/action_parser.py`)**: Parses and validates player actions with requirement checking
- **Event System**: Observable events that drive the social engineering aspects of gameplay
- **Theme/Edition System**: Modular content organization (core → fantasy → hearth_and_shadow)

### Key Design Principles

- **Action-based interaction**: Players interact through structured actions (e.g., `> move north`, `> whisper Player "hello"`)
- **Event-driven system**: Actions generate events that are distributed to relevant observers
- **Configuration-driven**: Game behavior is defined through YAML configuration files
- **Observability**: Information asymmetry drives strategic gameplay

### File Organization

```
motive/
├── game_master.py          # Core game orchestration
├── action_parser.py        # Action parsing and validation
├── config.py              # Configuration models and validation
├── config_loader.py       # YAML loading and merging
├── character.py           # Character and player management
├── room.py                # Room and environment management
├── game_object.py         # Object system and inventory
├── player.py              # Player state and communication
├── hooks/                 # Action implementations
│   ├── core_hooks.py      # Core action handlers
│   └── themes/           # Theme-specific action handlers
└── util.py               # Utility tools and training data management
```

## Development Workflow

### Testing Philosophy

- **Default to tests over paid runs**: Running `motive` triggers paid LLM calls. Prefer unit/integration tests which stub external LLMs
- **Favor integration tests over heavy mocking**: Write tests that exercise real code paths and types. Mock only external services (e.g., LLM APIs, filesystem/network), not core logic
- **Use real constructors and APIs**: Build objects with their true signatures so tests mirror production
- **Tests should prove real fixes**: Add integration tests that fail before a fix and pass after

### Running Tests

```bash
# First, ensure the project is installed in editable mode
pip install -e .

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_pickup_action.py -v
pytest tests/test_inventory_constraints.py -v

# Run with coverage
pytest tests/ --cov=motive --cov-report=html
```

### Running the Application

After running the setup script (which installs the project in editable mode), you can start the game:

```bash
# Activate virtual environment (if not already active)
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Run the application
motive                                    # Run with default config (with validation)
motive -c configs/game_new.yaml          # Run with hierarchical config
motive -c configs/game_test.yaml         # Run test configuration
motive --no-validate                     # Run without Pydantic validation (debugging)
motive --game-id my-custom-game          # Run with custom game ID (default: auto-generated timestamp)
```

### Configuration Analysis

Use the included configuration analysis tool to explore available actions, objects, and game elements:

```bash
# Show all available actions
motive-util config -A

# Show all objects in fantasy theme
motive-util config -c configs/themes/fantasy/fantasy.yaml -O

# Show complete configuration summary
motive-util config -a

# Show include information for hierarchical configs
motive-util config -I

# Validate configuration
motive-util config --validate

# Output merged config as YAML (useful for debugging)
motive-util config --raw-config
```

### Training Data Management

Motive includes comprehensive tools for managing training data from successful game runs:

```bash
# Copy latest game run (auto-detects most recent)
motive-util training copy

# Copy with custom name
motive-util training copy -n "excellent_20_round_game"

# Process raw data into training formats
motive-util training process

# Publish processed data to curated folder
motive-util training publish -n "final_dataset" -f

# List available runs
motive-util training list

# Show statistics
motive-util training stats
```

## Configuration System

Motive uses a flexible hierarchical configuration system that allows you to organize game content across multiple YAML files. This system supports both simple additive merging and advanced patch-based composition.

### Basic Configuration Structure

The main entry point is `configs/game.yaml`, which can include other configs using the `includes` directive:

```yaml
# configs/game.yaml
# Include other configs (processed first, then this config merges on top)
includes:
  - "themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml"

game_settings:
  num_rounds: 2
  initial_ap_per_turn: 20

players:
  - name: "Arion"
    provider: "google"
    model: "gemini-2.5-flash"
```

**Best Practice**: Always place `includes` directives at the top of your config files to make dependencies clear and easy to understand.

### Hierarchical Organization

Configs are organized in a logical hierarchy:
- **`core.yaml`** - Core game mechanics and actions
- **`themes/fantasy/fantasy.yaml`** - Fantasy theme content (includes core.yaml)
- **`themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml`** - Specific edition (includes fantasy.yaml)

### Include Processing

1. **Include directives are processed first** (like C++ includes)
2. **Later includes override earlier ones** in merge order
3. **Current config merges on top** of all included configs
4. **Circular dependencies are detected** and reported clearly

### Merging Strategies

#### Simple Merging (Default)
- **Dictionaries**: Merge keys, with later values overriding earlier ones
- **Lists**: Append items (additive only)
- **Nested structures**: Recursively merge

#### Advanced Merging
For sophisticated composition, you can use merge strategies:

```yaml
# List merging strategies
tags:
  - __merge_strategy__: "merge_unique"  # Remove duplicates
  - "base"
  - "advanced"
  - "base"  # Duplicate will be removed

priority_actions:
  - __merge_strategy__: "prepend"  # Add to beginning
  - id: urgent_action
    name: Urgent Action
    cost: 1
```

#### Patch References (Advanced)
Reference and modify existing objects:

```yaml
# Reference an existing action and patch it
patched_action:
  __ref__: "actions.base_action"
  __patches__:
    - operation: "set"
      field: "cost"
      value: 5
    - operation: "add"
      field: "tags"
      items: ["patched"]
```

### Available Merge Strategies

- `override` - Replace entire list
- `append` - Add to end (default)
- `prepend` - Add to beginning  
- `merge_unique` - Remove duplicates
- `remove_items` - Remove specific items
- `insert` - Insert at specific positions
- `key_based` - Merge objects by ID field
- `smart_merge` - Auto-detect appropriate strategy

### Testing Configurations

- **Unit tests**: Use isolated configs in `tests/configs/` (no main game dependencies)
- **Integration tests**: Use configs in `tests/configs/integration/` (can reference main game configs)
- **Standalone testing**: Create self-contained configs for testing specific features

## Troubleshooting

### Common Setup Issues

#### Windows PowerShell Execution Policy Error
If you get an error like "cannot be loaded because running scripts is disabled on this system":

```powershell
# Run as Administrator or use this command:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Python Not Found
If `python` or `pip` commands are not recognized:

1. **Install Python** from https://www.python.org/downloads/
2. **Check "Add Python to PATH"** during installation
3. **Restart your terminal** after installation
4. **Verify installation**:
   ```bash
   python --version
   pip --version
   ```

#### Virtual Environment Issues
If you have trouble with the virtual environment:

```bash
# Remove existing venv and recreate
rm -rf venv  # On Windows: rmdir /s venv
python -m venv venv

# Activate and install dependencies
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

#### API Key Issues
If the application fails to start:

1. **Check your `.env` file** exists and has valid API keys
2. **Verify API keys** are active and have sufficient credits
3. **Check the `configs/game.yaml`** file for correct model names
4. **Review logs** in the `logs/` directory for detailed error messages

## Git Workflow

### Pre-Commit Checklist

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

#### **Pre-Validation Checklist (Before `motive`)**
- [ ] **Use test configs for validation**: Use `configs/game_test.yaml` or create specific test configs with hints instead of modifying production `configs/game.yaml`
- [ ] **Verify test config syntax**: Ensure test configuration files are valid and won't cause parsing errors
- [ ] **Target specific actions**: Test configs should direct players to execute the exact actions needed to validate the new feature or bug fix

#### **Code Organization**
- [ ] New test files created for new functionality
- [ ] Test files follow naming convention: `test_*.py`
- [ ] No temporary test files left behind
- [ ] Code follows project patterns and conventions

### Commit Message Standards

- **Format**: `feat/fix/docs/test: brief description`
- **Types**: `feat` (new features), `fix` (bug fixes), `docs` (documentation), `test` (tests), `refactor` (code changes)
- **Description**: Clear, concise description of what changed
- **Examples**:
  - `feat: implement whisper and shout communication actions`
  - `fix: correct help action AP cost to match manual (1 AP)`
  - `docs: add git commit workflow to CONTRIBUTORS.md`

### Commit Process

1. **Run assessment**: Execute the pre-commit checklist
2. **Generate commit message**: Based on changes made
3. **Stage changes**: `git add .` (or specific files)
4. **Commit**: `git commit -m "generated message"`
5. **Push**: `git push origin main` (with user approval)
6. **Verify operations**: Run `git status` and `git log --oneline -3` to confirm success

## Current Features

### Hierarchical Configuration System

Motive features a powerful hierarchical configuration system that allows you to organize game content across multiple YAML files:

- **Include Support**: Use `includes` directive to merge multiple config files
- **Circular Dependency Detection**: Prevents infinite loops in include chains
- **Advanced Merging**: Support for various list merging strategies (override, append, prepend, unique, etc.)
- **Pydantic Validation**: All merged configurations are validated through Pydantic models for type safety
- **Debugging Tools**: Raw config output and validation tools for troubleshooting

### Configuration Validation

The system includes comprehensive validation to catch configuration errors early:

- **Type Safety**: Ensures all data matches expected Pydantic models
- **Error Reporting**: Detailed error messages showing exactly what's wrong and where
- **Runtime Validation**: Configs are validated when games start (can be disabled for debugging)
- **Analysis Tools**: Built-in tools to validate and debug configurations

### Inventory Constraint System

Motive includes a sophisticated inventory constraint system that prevents object duplication and ensures realistic gameplay:

- **Size Requirements**: Objects can require specific player sizes (tiny, small, medium, large, huge)
- **Class Requirements**: Items can be restricted to specific character classes (warrior, mage, rogue)
- **Level Requirements**: Powerful items require minimum player levels
- **Custom Constraints**: Complex constraints defined in object properties
- **Immovable Objects**: Objects that cannot be moved (fountains, statues)

### Action Point System

Players have limited Action Points (AP) per turn, creating strategic decision-making:

- **Default AP**: 20 AP per turn
- **Action Costs**: Most actions cost 10 AP, system actions cost less
- **AP Exhaustion**: Clear feedback when actions are skipped due to insufficient AP

### Observability System

Actions generate events that may or may not be observed by other players:

- **Private Actions**: Some actions (like `look inventory`) are only visible to the acting player
- **Room-Scoped Actions**: Actions like `say` are visible to all players in the same room
- **Adjacent Room Actions**: Actions like `pickup` may be visible to players in adjacent rooms
- **Game Logging**: All game events are logged to `logs/{theme_id}/{edition_id}/{game_id}/` with human-readable game IDs like `2025-09-09_18hr_52min_48sec_a1b2c3d4`

## Future Development

The Motive platform is designed with future expansion and AI research in mind. Key areas for future development include sophisticated environment generation and leveraging gameplay data for machine learning.

**Environment Generation Phases:**

1.  **Initial Static Environment:** Begin with a single, pre-designed environment (e.g., 20 rooms) potentially created with LLM assistance.
2.  **Randomized Layouts:** Introduce a randomizer to vary room layouts and initial object placements across different games.
3.  **Full Random Environment Generation:** Develop a robust system capable of generating large-scale, themed environments (e.g., fantasy dungeons, sci-fi spaceports) dynamically.

**Training Data and AI Research:**

Each game played by LLM agents will generate valuable training data from the perspective of every player. This data can be utilized for various AI research purposes:

*   **Fine-tuning LLMs:** Recordings of LLM gameplay can be used for reinforcement learning and long-context training to improve player AI.
*   **LLM Leaderboards/Benchmarks:** The platform can serve as a benchmark for evaluating different LLMs' ability to play the game effectively.
*   **Predictive Modeling:** Experiments could involve training LLMs to predict the gameplay actions of other players, enhancing their planning and reasoning abilities.
*   **Gameplay Analysis:** Analyzing player-specific training data to understand winning and losing strategies, e.g., identifying crucial actions like finding a key to escape a dungeon or how information shared (or withheld) influenced outcomes.

Beyond environments, variations in characters and objects will also be explored, with LLMs assisting in generating diverse backstories, motives, and interactable items, including puzzles, traps, and locks.

## Getting Help

- **Project Overview**: [README.md](../README.md)
- **Player Manual**: [MANUAL.md](MANUAL.md) - Everything players need to know
- **AI Agent Guidelines**: [AGENT.md](AGENT.md) - For AI coding agents
- **LLM Collaboration**: [VIBECODER.md](VIBECODER.md) - Human-LLM collaboration lessons
- **Current TODOs**: [TODO.md](TODO.md) - Active development tasks
