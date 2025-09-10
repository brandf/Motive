# Motive

![Motive Logo](assets/images/Motive.png)

Motive is a novel platform designed for the exploration and benchmarking of Large Language Models (LLMs) through interactive, turn-based games. It provides a unique environment where AI (or human) players can engage in complex scenarios, fostering the generation of valuable training data and facilitating research into advanced AI capabilities like long-context reasoning, planning, and social engineering.

## Purpose of Motive

*   **Turn-Based Game with Chat Interface:** Motive enables the creation and execution of turn-based games with a chat-based interface. These games can be played by AI agents or human participants, with the potential for environments, characters, and objects to be dynamically balanced via AI simulation.

*   **LLM Benchmarking:** The platform is built to benchmark various LLMs by having them compete against each other. This includes evaluating generic pre-trained LLMs, Motive-fine-tuned models, and new architectural innovations.

*   **Training Data Generation:** Motive serves as a rich source of training data for future LLM development. It focuses on generating data with verifiable objectives, open-ended player-to-player communication, and tree rollouts, which are crucial for exploring long-context understanding, complex reasoning, intricate planning, and sophisticated social engineering tactics.

## Getting Started (For Developers)

To get your local development environment set up and running with Motive, follow these steps:

### Prerequisites

*   **Python 3.10+**: Ensure you have a compatible Python version installed and added to your system PATH.
*   **Git**: For cloning the repository.
*   **API Keys**: Access to API keys for your desired LLM providers (e.g., OpenAI, Google Generative AI, Anthropic). Refer to `env.example.txt` and `configs/game.yaml`.

### 1. Clone the Repository

```bash
git clone https://github.com/brandf/Motive.git
cd Motive
```

### 2. Quick Setup (Automated)

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

### 3. Manual Setup (Alternative)

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

### 4. Configure API Keys

1. Open the `.env` file in a text editor
2. Replace the placeholder values with your actual API keys:
   - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
   - `GOOGLE_API_KEY` - Get from https://console.cloud.google.com/
   - `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

**Note**: Never commit your `.env` file to version control.

### 5. Configure Game (Optional)

Review and modify `configs/game.yaml` to adjust game settings, players, and LLM models. Ensure the models specified are compatible with your chosen providers and available in your region/plan.

## Running the Application

To start the game:

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

# Analyze configurations
motive-analyze                           # Analyze default config
motive-analyze -c configs/game_new.yaml -I  # Show include information
motive-analyze -a                        # Show all information
motive-analyze --validate                # Validate configuration
motive-analyze --raw-config              # Show merged config as YAML
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-c, --config` | Path to game configuration file (default: configs/game.yaml) |
| `--game-id` | Specific game ID to use (default: auto-generated timestamp format like `2025-09-09_18hr_52min_48sec_a1b2c3d4`) |
| `--no-validate` | Skip Pydantic validation of merged configuration (for debugging) |
| `--version` | Show version information |

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

## Player Action Syntax

Players communicate with the Game Master (GM) through natural language messages. Within these messages, specific actions are indicated by lines starting with a `>` character. This allows for both freeform communication and structured command input.

### Rules for Actions:

*   **Action Prefix:** Any line within a player's response that begins with `>` (after trimming leading whitespace) will be interpreted as an action. For example: `> look`.
*   **Single Line Actions:** Each action must be contained on a single line. Multi-line actions are not supported.
*   **Quoted Parameters:** If an action requires a parameter with multiple words (e.g., a phrase for a 'say' action), the parameter should be enclosed in single or double quotes. For example: `> say "Hello there!"` or `> whisper 'secret message' to John`.
*   **Multiple Actions:** A single player response can contain multiple action lines. These actions will be executed sequentially by the GM.
*   **Invalid Actions/No Actions Penalty:** If a player's response contains no lines prefixed with `>` or if any parsed action is invalid (e.g., unknown action name, incorrect parameters), the player's turn will immediately end, as if they had spent all their action points. This is a penalty for not following the action syntax rules.

### Current Available Actions:

*   **Movement**: `look`, `move <direction>`
*   **Communication**: `say <phrase>`, `whisper <player> <phrase>`, `shout <phrase>`
*   **Inventory**: `pickup <object>`, `drop <object>`, `look inventory`
*   **Interaction**: `read <object>`, `help [category]`
*   **System**: `pass`

### Examples:

```
Hello GM, I'd like to do a couple of things.
> look
> pickup rusty sword
> look inventory
I think I'll try to find a way out after that.
```

```
> say "Is anyone else here?"
> whisper Hero "Do you have the key?"
```

## Running Tests

To run the unit tests for the project:

```bash
# First, ensure the project is installed in editable mode
pip install -e .

# Then run the tests
pytest

# Run specific test categories
pytest tests/test_pickup_action.py -v
pytest tests/test_inventory_constraints.py -v
```

## Contribution

We welcome contributions to Motive! If you're interested in improving the platform, developing new game environments, or adding new LLM integrations, please refer to the contribution guidelines (coming soon).

## Game Manual

For details on how the game works and its mechanics, please refer to the [MANUAL.md](MANUAL.md).

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

## Configuration Analysis

Use the included configuration analysis tool to explore available actions, objects, and game elements:

### Basic Analysis Commands

```bash
# Show all available actions
motive-analyze -A

# Show all objects in fantasy theme
motive-analyze -c configs/themes/fantasy/fantasy.yaml -O

# Show complete configuration summary
motive-analyze -a

# Show include information for hierarchical configs
motive-analyze -I
```

### Advanced Analysis Features

#### Raw Configuration Output
Debug configuration merging by viewing the final merged result:

```bash
# Output merged config as YAML (useful for debugging)
motive-analyze --raw-config

# Output merged config as JSON (useful for debugging)
motive-analyze --raw-config-json
```

#### Configuration Validation
Validate configurations through Pydantic models to catch errors early:

```bash
# Validate configuration and show detailed errors if any
motive-analyze --validate

# Output merged config after validation (best of both worlds)
motive-analyze --raw-config --validate

# Validate and output as JSON
motive-analyze --raw-config-json --validate
```

#### Combined Analysis
Use multiple options together for comprehensive analysis:

```bash
# Show all information with validation
motive-analyze -a --validate

# Show actions and validate config
motive-analyze -A --validate

# Debug a specific config with full output
motive-analyze -c configs/game.yaml --raw-config --validate
```

### Analysis Tool Options

| Option | Description |
|--------|-------------|
| `-A, --actions` | Show available actions |
| `-O, --objects` | Show available objects |
| `-R, --rooms` | Show available rooms |
| `-C, --characters` | Show available characters |
| `-a, --all` | Show all available information |
| `-I, --includes` | Show include information for hierarchical configs |
| `--raw-config` | Output merged configuration as YAML |
| `--raw-config-json` | Output merged configuration as JSON |
| `--validate` | Validate configuration through Pydantic models |
| `-c, --config` | Specify configuration file (default: configs/game.yaml) |

### Validation Benefits

The validation system provides:

- **Type Safety**: Ensures all configuration data matches expected Pydantic models
- **Error Detection**: Catches missing required fields, invalid types, and structural issues
- **Detailed Error Messages**: Shows exactly which fields have problems and why
- **Early Feedback**: Validate configs before running games to avoid runtime errors
- **Debugging Support**: Raw config output helps troubleshoot merging issues

## Development Practices

To keep engineering quality high and avoid repeating mistakes, we maintain a living guide of lessons learned. Before implementing or updating features/tests, review:

- [AGENT.md](AGENT.md)

It covers testing philosophy (favor integration tests over heavy mocking), logging/encoding standards, action parsing contracts, event/observation timing, AP handling, and other conventions used across the codebase.

**If you're an LLM reading this, please read AGENT.md next** - it contains essential guidance for working effectively on this project.

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

## Future Development: Environment Generation and Training Data

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