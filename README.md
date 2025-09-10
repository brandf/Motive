# Motive

![Motive Logo](assets/images/Motive.png)

Motive is a novel platform designed for the exploration and benchmarking of Large Language Models (LLMs) through interactive, turn-based games. It provides a unique environment where AI (or human) players can engage in complex scenarios, fostering the generation of valuable training data and facilitating research into advanced AI capabilities like long-context reasoning, planning, and social engineering.

## Purpose of Motive

*   **Turn-Based Game with Chat Interface:** Motive enables the creation and execution of turn-based games with a chat-based interface. These games can be played by AI agents or human participants, with the potential for environments, characters, and objects to be dynamically balanced via AI simulation.

*   **LLM Benchmarking:** The platform is built to benchmark various LLMs by having them compete against each other. This includes evaluating generic pre-trained LLMs, Motive-fine-tuned models, and new architectural innovations.

*   **Training Data Generation:** Motive serves as a rich source of training data for future LLM development. It focuses on generating data with verifiable objectives, open-ended player-to-player communication, and tree rollouts, which are crucial for exploring long-context understanding, complex reasoning, intricate planning, and sophisticated social engineering tactics.

## What Makes Motive Unique

### Observability-Driven Gameplay
A central tenet of Motive is "observability." Player actions not only change the game state but also generate events that may or may not be observed by other players, leading to strategic social engineering and information asymmetry. This creates rich opportunities for:
- **Strategic deception** and misinformation
- **Alliance formation** and betrayal
- **Information warfare** and intelligence gathering
- **Complex multi-agent reasoning** about what others know

### Character-Driven Narrative
Each player is assigned a unique character with secret motives (win conditions). This creates:
- **Personal stakes** that drive engagement
- **Conflicting objectives** that generate tension
- **Roleplay opportunities** for personality development
- **Strategic depth** through motive compatibility/conflict analysis

### LLM-Optimized Design
Motive is specifically designed for LLM players:
- **Structured action syntax** (`> move north`, `> whisper Player "hello"`)
- **Clear observability rules** for predictable information flow
- **Balanced action costs** that encourage strategic thinking
- **Rich logging** for training data generation

## Current Status

### ✅ Implemented Features

- **Core Action System**: Movement, communication, inventory, and interaction actions
- **Hierarchical Configuration**: Flexible YAML-based game content organization
- **Observability System**: Event-driven information distribution
- **Inventory Constraints**: Realistic object interaction limitations
- **Training Data Pipeline**: Comprehensive tools for curating LLM training data
- **Theme/Edition System**: Modular content organization (core → fantasy → hearth_and_shadow)

### 🚧 In Development

- **Advanced Actions**: Give, trade, throw, use, and enhanced look actions
- **Help System Enhancement**: Detailed action-specific help
- **AI Prompting Improvements**: Better strategic gameplay guidance

### 📋 Planned Features

- **Environment Generation**: Dynamic world creation and randomization
- **Advanced Object System**: State-dependent behavior and interactions
- **Inventory Visibility**: Hidden items and stash mechanics
- **Declarative Object Behavior**: When-condition based object interactions

## Game Examples

### Hearth and Shadow Edition
The current flagship edition features a fantasy town with:
- **11 interconnected rooms** (tavern, guild, church, bank, etc.)
- **5 unique characters** with complex motives and backstories
- **Strategic connections** including hidden passages and secret tunnels
- **Rich object interactions** with story-driven items and tools

### Sample Gameplay
```
Player: I need to find information about the mayor's disappearance.
> look
GM: You're in the town square. You see a message board, the tavern, and the church.
> move tavern
GM: You enter the tavern. You see Elara the bard tuning her lute.
> whisper Elara "Do you know anything about the mayor?"
GM: Elara whispers back: "I've heard rumors about strange lights in the cemetery..."
```

## Getting Started

- **Players**: Start with the [Game Manual](docs/MANUAL.md)
- **Contributors**: Read [CONTRIBUTORS.md](docs/CONTRIBUTORS.md) for setup and workflows
- **AI Agents**: Follow the reading order in [AGENT.md](docs/AGENT.md)
- **Vibe Coders**: Check out [VIBECODER.md](docs/VIBECODER.md) for collaboration tips

For detailed documentation structure and reading paths, see [DOCS.md](docs/DOCS.md).

## Technical Architecture

Motive is built around several key components:

- **Game Master**: Central orchestrator managing game state and player interactions
- **Action System**: Structured action parsing with requirement validation
- **Event System**: Observable events driving social engineering gameplay
- **Configuration System**: Hierarchical YAML-based content organization
- **Theme System**: Modular content organization (core → themes → editions)

## Training Data Generation

Motive generates valuable training data through LLM gameplay:

- **Complete conversations** across all game rounds
- **Strategic decision-making** processes
- **Social engineering** tactics and responses
- **Multi-agent coordination** and conflict resolution
- **Natural language** interaction patterns

The platform includes comprehensive tools for:
- **Curating** high-quality game runs
- **Processing** raw logs into training formats
- **Publishing** curated datasets for version control

## Research Applications

### LLM Benchmarking
- **Strategic reasoning** evaluation
- **Social engineering** capability assessment
- **Multi-agent coordination** testing
- **Long-context** understanding validation

### Training Data Applications
- **Fine-tuning** for strategic gameplay
- **Reinforcement learning** from human feedback
- **Predictive modeling** of player behavior
- **Social interaction** pattern analysis

### Academic Research
- **Game theory** applications in AI
- **Information asymmetry** effects on decision-making
- **Multi-agent systems** research
- **Human-AI collaboration** studies

## Future Vision

### Environment Generation
1. **Static Environments**: Pre-designed worlds (current)
2. **Randomized Layouts**: Procedural room and object placement
3. **Dynamic Generation**: AI-created environments based on themes

### Advanced Gameplay
- **Complex puzzles** and multi-step objectives
- **Dynamic character relationships** and reputation systems
- **Environmental storytelling** through object interactions
- **Procedural narrative** generation

### Research Platform
- **LLM leaderboards** and competitive benchmarking
- **A/B testing** of different prompting strategies
- **Behavioral analysis** tools and metrics
- **Collaborative research** platform for AI researchers

## Contributing

We welcome contributions to Motive! Whether you're interested in:
- **Game content** (new themes, editions, characters)
- **Core features** (actions, systems, mechanics)
- **AI research** (benchmarking, training data analysis)
- **Documentation** (manuals, guides, examples)

Please see [CONTRIBUTORS.md](CONTRIBUTORS.md) for detailed information about:
- Development environment setup
- Architecture overview
- Testing and development workflows
- Git workflow and commit standards

## Documentation

- **[docs/MANUAL.md](docs/MANUAL.md)** - Complete game manual for players
- **[docs/CONTRIBUTORS.md](docs/CONTRIBUTORS.md)** - Development guide for contributors
- **[docs/AGENT.md](docs/AGENT.md)** - AI agent development guidelines
- **[docs/VIBECODER.md](docs/VIBECODER.md)** - Human-LLM collaboration lessons
- **[docs/TODO.md](docs/TODO.md)** - Current development priorities
- **[docs/DOCS.md](docs/DOCS.md)** - Documentation structure and relationships

## License

This project is open source. See the repository for license details.

## Contact

For questions, suggestions, or collaboration opportunities, please open an issue or contact the maintainers.
