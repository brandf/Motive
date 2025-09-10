# Motive Game Manual

This document provides a comprehensive guide to the world of Motive, detailing the game mechanics, rules, environments, characters, and objects. It is designed to help players understand how to interact with the game world and achieve their objectives.

## Table of Contents

*   Game Overview
*   Game Mechanics: Turns, Actions, and Observability
*   Player Roles, Characters, and Motives (Win Conditions)
*   Game Environments: Rooms, Exits, and Objects
*   Player Actions: Categories and Parameters
*   Communication and Social Engineering

## Game Overview

Motive is a turn-based, round-based game designed for both human and AI players, with a strong emphasis on AI-driven simulations. The core of the game revolves around players interacting with a dynamic environment and each other through a chat interface, mediated by a "Game Master" program. Players are assigned unique characters with secret "motives," which act as their personal win conditions. The ultimate goal is for players to achieve their motive by the end of the final round.

A central tenet of Motive is "observability." Player actions not only change the game state but also generate events that may or may not be observed by other players, leading to strategic social engineering and information asymmetry.

## Game Mechanics: Turns, Actions, and Observability

The game unfolds over a series of rounds, with each player taking a turn within every round in a predetermined order. The interaction between a player and the Game Master (GM) is a 1-on-1 chat-based dialogue.

**Player Turn Sequence:**

1.  **Information from GM:** At the beginning of a player's turn, the GM provides the following information:
    *   (First round only) Your assigned character and motive - this must be accomplish to win the game.
    *   A list of 'observations' – these are the observable events triggered by other players' actions since your last turn, or on the first round it will be a description of the initial room.
    *   A subset of the available actions as examples for what can be done
      - the (1 AP) 'help' action provides the player a menu-like experience for choosing an action

2.  **Player Actions:** Each player is allotted a predetermined number of **action points** (AP) per turn. Players spend these points to perform actions. The player and the GM engage in a back-and-forth chat. The player proposes one action at a time, and the GM processes it, updates the game state, and provides immediate feedback, including any new observations or changes in the room description. This continues until the player's action points for that turn are fully spent.

3.  **Turn End:** Once a player has spent all their action points, their turn concludes. The player must confirm they want to continue to the next turn or quit the game. Actions submitted during turn end confirmation are ignored with a warning.

**Observability:**

A critical aspect of Motive is how information about actions is disseminated. When a player performs an action, it generates events that may (or may not) be observed by other players. The GM is solely responsible for determining which players observe which events, creating a dynamic environment where information is not always universally shared. This mechanism encourages strategic decision-making based on incomplete information and allows for social engineering tactics.

## Player Roles, Characters, and Motives (Win Conditions)

Each player is assigned a unique **character** at the beginning of the game, complete with a backstory and a secret **motive**. A motive serves as the player's individual win condition. Players keep their motives secret unless they choose to reveal them through in-game communication.

Motive conditions are independent, meaning that multiple players can achieve their motives and win the game simultaneously, or it's possible for no players to win. The compatibility or conflict between motives drives much of the player interaction and strategic depth. The game concludes after a set number of rounds, at which point players are informed whether they have successfully achieved their motive.

## Game Environment: Rooms, Exits, and Objects

The game world is structured as a collection of **rooms** connected by **exits**. Players navigate this environment by moving between rooms through these exits. Each room contains a description, and may also hold various **objects** that players can interact with, as well as other players.

**Key Environmental Elements:**

*   **Rooms:** Distinct locations within the game world. Each room has a descriptive text. All players begin the game in a designated starting room (e.g., a town square or dungeon entrance), though the specific theme and layout can vary.
*   **Exits:** Connections between rooms. Exits allow players to move from one room to an adjacent one. The GM will provide a list of visible exits from a player's current room.
*   **Objects:** Interactable items within the game. Objects can be located in rooms or carried by players in their **inventory**. To maintain simplicity in initial versions, there are no "container" type objects (e.g., chests that hold other items). Objects can be manipulated through player actions.

## Player Actions: Categories and Parameters

Players interact with the game world and other players by performing actions. Each action has an associated action point cost. Actions can be parameterized, requiring specific targets or inputs (e.g., "say <phrase>" or "pick up <object>"). The GM interprets these actions, updates the game state accordingly, and generates events that contribute to the observability mechanic.

### Action Syntax

Players communicate with the Game Master (GM) through natural language messages. Within these messages, specific actions are indicated by lines starting with a `>` character. This allows for both freeform communication and structured command input.

*   **Action Prefix:** Any line within a player's response that begins with `>` (after trimming leading whitespace) will be interpreted as an action. For example: `> look`.
*   **Single Line Actions:** Each action must be contained on a single line. Multi-line actions are not supported.
*   **Quoted Parameters:** If an action requires a parameter with multiple words (e.g., a phrase for a 'say' action), the parameter should be enclosed in single or double quotes. For example: `> say "Hello there!"` or `> whisper 'secret message' to John`.
*   **Multiple Actions:** A single player response can contain multiple action lines. These actions will be executed sequentially by the GM.
*   **Invalid Actions/No Actions Penalty:** If a player's response contains no lines prefixed with `>` or if any parsed action is invalid (e.g., unknown action name, incorrect parameters), the player's turn will immediately end, as if they had spent all their action points. This is a penalty for not following the action syntax rules. The GM will provide helpful feedback about valid actions and suggestions for similar actions when possible.

### Action Categories

Actions are organized into the following categories:

1.  **Movement**: Actions for navigating the game world (`move`, `look`)
2.  **Communication**: Actions for player-to-player interaction (`say`, `whisper`, `shout`)
3.  **Inventory**: Actions for managing carried items (`pickup`, `drop`, `look inventory`)
4.  **Interaction**: Actions for interacting with objects (`read`)
5.  **System**: Actions for game management (`help`, `pass`)

### Action Design Principles

Motive follows a consistent design pattern:
- **Actions are verbs**: Commands like `look`, `pickup`, `move`
- **Parameters are nouns**: Targets like `inventory`, `sword`, `north`
- **Costs are balanced**: Most actions cost 10 AP, with system actions costing less
- **Requirements are declarative**: Actions specify what conditions must be met
- **Effects are observable**: Actions generate events that other players may observe

Performing an action results in changes to the game state and the generation of events. These events are then processed by the GM to determine which players observe them, creating the observability mechanic that drives strategic gameplay.

### Current Core Actions

The following core actions are currently implemented and available to all players:

#### **Movement Actions**
- **`move`**: Move in a specified direction through room exits
- **`look`**: Look around the current room or examine specific objects
  - **Special syntax**: `> look inventory` - View your carried items

#### **Communication Actions**
- **`say`**: Speak to all players in the same room
- **`whisper`**: Send a private message to a specific player in the same room
- **`shout`**: Speak loudly, potentially heard in adjacent rooms

#### **Inventory Actions**
- **`pickup`**: Pick up an object from the current room (subject to inventory constraints)
- **`drop`**: Drop an object from your inventory into the current room
- **`look inventory`**: View your carried items and their properties

#### **Interaction Actions**
- **`read`**: Read text from objects like signs or books
- **`help`**: Get help with available actions (costs 1 AP)
- **`pass`**: End your turn without taking any action (costs 0 AP)

### Inventory Constraint System

Objects in Motive can have various constraints that prevent them from being picked up or transferred:

#### **Constraint Types**
- **`immovable`**: Object cannot be moved (e.g., fountains, statues)
- **`too_heavy`**: Object is too heavy for the player to carry
- **`magically_bound`**: Object is bound to a location by magic
- **`requires_size`**: Player must be a certain size (tiny, small, medium, large, huge)
- **`requires_class`**: Player must be a specific class (warrior, mage, rogue, etc.)
- **`requires_level`**: Player must be a certain level or higher
- **`custom_constraints`**: Complex constraints defined in object properties

#### **Constraint Examples**
- A `Legendary Sword` requires level 15+ to wield
- `Warrior's Armor` can only be worn by warrior-class characters
- A `Huge Boulder` requires large or huge size to move
- An `Elven Artifact` has custom constraints requiring elf race and good alignment

### Planned Future Actions

The following actions are planned for future implementation:

#### **Throw Action**
- **Syntax:** `> throw <inventory object> <exit>`
- **Description:** Removes an object from the player's inventory and places it in an adjacent room via the specified exit
- **Strategic Use:** Allows tactical positioning without being present

#### **Use Action (Generic Object Manipulation)**
- **Syntax:** `> use <inventory object>`
- **Description:** Generic object state manipulation defined declaratively in YAML
- **Examples:** 
  - `> use torch` could light/extinguish based on current state
  - `> use key` could unlock doors

#### **Give/Trade Actions**
- **Syntax:** `> give <object> to <player>` / `> trade <object> for <object> with <player>`
- **Description:** Safe item transfer between players with queued observation system

#### **Enhanced Look Action**
- **Syntax:** `> look <object>`
- **Description:** State-dependent object descriptions that change based on object tags and room conditions

## Communication and Social Engineering

Communication between players is a vital component of Motive, routed entirely through the Game Master (GM). The GM does not interpret the content of player communications but plays a crucial role in determining their observability. This controlled dissemination of information is central to the game's social engineering aspect.

**Examples of Communication Observability:**

*   **"whisper <player> <phrase>":** Only the specified target player observes this communication.
*   **"say <phrase>":** All players currently in the same room as the speaker observe this communication.
*   **"shout <phrase>":** All players in the same room and potentially players in adjacent rooms might observe this, depending on game rules and environment specifics.

**Examples of Movement Observability:**

*   **Movement between rooms:** When a player moves from one room to another, other players in both the source and destination rooms observe the movement with specific direction information.
    *   Players in the source room see: "[Player] left the room via [Direction]."
    *   Players in the destination room see: "[Player] entered the room from [Direction]."
*   **Strategic importance:** This direction-specific information is crucial when multiple exits exist, allowing players to track each other's movements and make informed tactical decisions.

This system allows LLM players to engage in complex social interactions, form alliances, spread misinformation, and strategize based on what they believe other players know or don't know. The ability to control who sees and hears what fosters a rich environment for emergent gameplay and offers significant potential for analyzing LLM reasoning and planning capabilities.
