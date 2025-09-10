# Documentation Structure and Relationships

This document shows how all the documentation files reference and link to each other.

## Who is this for?

- **Anyone navigating docs** who needs to understand what to read next
- **Maintainers** ensuring documentation consistency

## Document Hierarchy and Target Audiences

```
README.md (Root - Contributors and developers read this first)
├── Project overview, goals, background, functionality, status
├── Entry point for contributors, developers, and AI agents
└── References all other docs

docs/
├── MANUAL.md (Players only)
│   ├── Complete game manual for players
│   ├── System prompt ready
│   └── Referenced by: README.md, configs/game.yaml
│
├── CONTRIBUTORS.md (Human contributors + AI agents)
│   ├── Architecture, setup, development workflows
│   ├── Referenced by: README.md, AGENT.md
│   └── References: README.md, MANUAL.md, AGENT.md, VIBECODER.md, TODO.md
│
├── AGENT.md (AI coding agents only)
│   ├── AI-specific workflows and guidelines
│   ├── Builds on CONTRIBUTORS.md
│   ├── Referenced by: README.md, CONTRIBUTORS.md, VIBECODER.md
│   └── References: README.md, CONTRIBUTORS.md, VIBECODER.md
│
├── VIBECODER.md (Vibe coding humans only)
│   ├── Human-LLM collaboration lessons
│   ├── Referenced by: README.md, CONTRIBUTORS.md, AGENT.md
│   └── References: AGENT.md, VIBECODER.md (self-references)
│
└── TODO.md (All contributors)
    ├── Current development priorities
    ├── Referenced by: README.md, CONTRIBUTORS.md
    └── References: None (standalone)
```

## Reading Order for Different Audiences

### Players
1. **docs/MANUAL.md** - Game manual (system prompt ready)

### Human Contributors
1. **README.md** - Project overview
2. **docs/CONTRIBUTORS.md** - Architecture and workflows
3. **docs/TODO.md** - Current priorities

### AI Coding Agents
1. **README.md** - Project overview
2. **docs/CONTRIBUTORS.md** - Architecture and workflows (READ FIRST)
3. **docs/VIBECODER.md** - Human-LLM collaboration lessons
4. **docs/AGENT.md** - AI-specific workflows (builds on CONTRIBUTORS.md)

### Vibe Coding Humans
1. **README.md** - Project overview
2. **docs/VIBECODER.md** - Human-LLM collaboration lessons

## Cross-Reference Map

### README.md References
- `docs/MANUAL.md` - Game manual for players
- `docs/CONTRIBUTORS.md` - Development guide for contributors
- `docs/AGENT.md` - AI agent development guidelines
- `docs/VIBECODER.md` - Human-LLM collaboration lessons
- `docs/TODO.md` - Current development priorities
- `docs/COMPETITIVE_ANALYSIS.md` - Comparison with similar platforms and research environments

### docs/CONTRIBUTORS.md References
- `../README.md` - Project overview
- `MANUAL.md` - Player manual
- `AGENT.md` - AI agent guidelines
- `VIBECODER.md` - Human-LLM collaboration
- `TODO.md` - Current TODOs

### docs/AGENT.md References
- `../README.md` - Project overview
- `CONTRIBUTORS.md` - Architecture and workflows (PRIMARY REFERENCE)
- `VIBECODER.md` - Human-LLM collaboration lessons

### docs/VIBECODER.md References
- `AGENT.md` - AI agent guidelines (self-references for updates)

### docs/MANUAL.md References
- None (standalone player manual)

### docs/TODO.md References
- None (standalone task list)

### Config File References
- `configs/game.yaml` → `../docs/MANUAL.md` - Manual path for system prompt
 - Edition docs: e.g., `configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.md` (narrative reference next to config)

## Key Design Principles

1. **README.md is the root for contributors** - Contributors and developers read this first
2. **MANUAL.md is standalone for players** - Players only need the game manual
3. **No circular dependencies** - Clear hierarchy prevents loops
4. **Audience-specific paths** - Different reading orders for different users
5. **AI agents read CONTRIBUTORS.md first** - Contains essential setup and architecture
6. **AGENT.md builds on CONTRIBUTORS.md** - Avoids duplication, focuses on AI-specific workflows
7. **Cross-references use relative paths** - Works from docs/ folder structure

## File Organization

```
Motive/
├── README.md                    # Root documentation (everyone reads)
├── docs/                        # All other documentation
│   ├── MANUAL.md               # Player manual (system prompt ready)
│   ├── CONTRIBUTORS.md         # Human contributors + AI agents
│   ├── AGENT.md                # AI coding agents only
│   ├── VIBECODER.md            # Vibe coding humans only
│   ├── TODO.md                 # All contributors
│   └── DOCS.md                 # Documentation structure and relationships (this file)
└── configs/
    └── game.yaml               # References docs/MANUAL.md
```

Note: Edition and theme narrative docs may live alongside their configuration for proximity, e.g., `configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.md`. Reference them from `docs/` as needed.

This structure ensures:
- Clear separation of concerns
- No redundant information
- Appropriate audience targeting (players only need MANUAL.md)
- Easy navigation and maintenance
- System prompt integration ready
