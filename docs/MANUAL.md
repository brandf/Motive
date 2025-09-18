# Motive Game Manual

This document provides a comprehensive guide to the world of Motive, detailing the game mechanics, rules, environments, characters, and objects. It is designed to help players understand how to interact with the game world and achieve their objectives.

## Who is this for?

- **Players** learning how to play and win (both human and AI players)

## Table of Contents

*   [Game Overview](#game-overview)
*   [Game Mechanics: Turns, Actions, and Observability](#game-mechanics-turns-actions-and-observability)
*   [Player Roles, Characters, and Motives (Win Conditions)](#player-roles-characters-and-motives-win-conditions)
*   [Game Environments: Rooms, Exits, and Objects](#game-environment-rooms-exits-and-objects)
*   [Player Actions: Categories and Parameters](#player-actions-categories-and-parameters)
*   [Communication and Social Engineering](#communication-and-social-engineering)

## Game Overview

Motive is a turn-based, round-based game designed for both human and AI players, with a strong emphasis on AI-driven simulations. The core of the game revolves around players interacting with a dynamic environment and each other through a chat interface, mediated by a "Game Master" program. Players are assigned unique characters with secret "motives," which act as their personal win conditions. The ultimate goal is for players to achieve their motive by the end of the final round.

A central tenet of Motive is "observability." Player actions not only change the game state but also generate events that may or may not be observed by other players, leading to strategic social engineering and information asymmetry.

## Game Mechanics: Turns, Actions, and Observability

The game unfolds over a series of rounds, with each player taking a turn within every round in a predetermined order. The interaction between a player and the Game Master (GM) is a 1-on-1 chat-based dialogue.

**Player Turn Sequence:**

1.  **Information from GM:** At the beginning of a player's turn, the GM provides the following information:
    *   (First round only) Your assigned character and motive - this must be accomplished to win the game.
    *   (First round only) Your initial location with a narrative reason explaining why you're there.
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

*   **Rooms:** Distinct locations within the game world. Each room has a descriptive text. Players begin the game in character-specific starting locations that make narrative sense for their role and backstory.
*   **Exits:** Connections between rooms. Exits allow players to move from one room to an adjacent one. The GM will provide a list of visible exits from a player's current room.
*   **Objects:** Interactable items within the game. Objects can be located in rooms or carried by players in their **inventory**. Objects can be manipulated through player actions.

## Player Actions: Categories and Parameters

Players interact with the game world and other players by performing actions. Each action has an associated action point cost. Actions can be parameterized, requiring specific targets or inputs (e.g., "say <phrase>" or "pick up <object>"). The GM interprets these actions, updates the game state accordingly, and generates events that contribute to the observability mechanic.

### Action Syntax

Players communicate with the Game Master (GM) through natural language messages. Within these messages, specific actions are indicated by lines starting with a `>` character. This allows for both freeform communication and structured command input.

*   **Action Prefix:** Any line within a player's response that begins with `>` (after trimming leading whitespace) will be interpreted as an action. For example: `> look`.
*   **Single Line Actions:** Each action must be contained on a single line. Multi-line actions are not supported.
*   **Quoted Parameters:** If an action requires a parameter with multiple words (e.g., a phrase for a 'say' action), the parameter should be enclosed in single or double quotes. For example: `> say "Hello there!"` or `> whisper "John" "secret message"`.
*   **Multiple Actions:** A single player response can contain multiple action lines. These actions will be executed sequentially by the GM.
*   **Invalid Actions/No Actions Penalty:** If a player's response contains no lines prefixed with `>` or if any parsed action is invalid (e.g., unknown action name, incorrect parameters), the player's turn will immediately end, as if they had spent all their action points. This is a penalty for not following the action syntax rules. The GM will provide helpful feedback about valid actions and suggestions for similar actions when possible.

### Action Categories

Actions are organized into the following categories:

1.  **Movement**: Actions for navigating the game world (`move`, `look`)
2.  **Communication**: Actions for player-to-player interaction (`say`, `whisper`, `shout`)
3.  **Inventory**: Actions for managing carried items (`pickup`, `drop`, `look inventory`)
4.  **Interaction**: Actions for interacting with objects (`read`)
5.  **System**: Actions for game management (`help`, `pass`)

Performing an action results in changes to the game state and the generation of events. These events are then processed by the GM to determine which players observe them, creating the observability mechanic that drives strategic gameplay.

### Current Core Actions

The following core actions are currently implemented and available to all players:

#### **Movement Actions**
- **`move`**: Move in a specified direction through room exits
- **`look`**: Look around the current room or examine specific objects
  - **Special syntax**: `> look inventory` - View your carried items

#### **Communication Actions**
- **`say`**: Speak to all players in the same room
  - Format: `> say "message"`
  - Example: `> say "Hello everyone!"`
- **`whisper`**: Send a private message to a specific player in the same room
  - Format: `> whisper "player_name" "message"`
  - Example: `> whisper "John" "Meet me in the library"`
  - Note: Both player name and message must be quoted. Only the target player will see this message.
- **`shout`**: Speak loudly, potentially heard in adjacent rooms

#### **Inventory Actions**
- **`pickup`**: Pick up an object from the current room (subject to inventory constraints)
- **`drop`**: Drop an object from your inventory into the current room
- **`give`**: Give an object from your inventory to another player in the same room
  - Format: `> give "player_name" "object_name"`
  - Example: `> give "John" "torch"`
  - Note: Both player name and object name must be quoted. The transfer is visible to all players in the room.
- **`throw`**: Throw an object from your inventory through an exit to an adjacent room
  - Format: `> throw "object_name" "exit"`
  - Example: `> throw "torch" "north"`
  - Note: Both object name and exit must be quoted. The action is visible to players in both rooms.
- **`look inventory`**: View your carried items and their properties

#### **Interaction Actions**
- **`help`**: Get help with available actions (costs 1 AP)
- **`pass`**: End your turn without taking any action (costs 0 AP)

### Action Aliases

Some objects in the game define **action aliases** that allow you to use alternative command names. These aliases redirect to core actions, making interactions more intuitive and thematic.

**Examples:**
- **`read`**: Many readable objects (like signs, books, journals) accept `read` as an alias for `look`
- **`investigate`**: Objects that can be examined in detail (like evidence, clues) accept `investigate` as an alias for `look`
- **`examine`**: Similar to investigate, some objects accept `examine` as an alias for `look`

**How it works:**
- When you type `> read "Quest Board"`, the system checks if the Quest Board object has a `read` alias
- If it does, the command is automatically redirected to `> look "Quest Board"`
- The action executes normally with the same cost and effects as the core action
- If an object doesn't have the alias you're trying to use, you'll get an "unknown action" error

**Benefits:**
- More intuitive commands: `read` feels natural for books, `investigate` for evidence
- Thematic consistency: Different objects can have different interaction verbs
- Flexible design: Objects can define their own aliases without changing core actions

### Inventory Constraints

Some objects in the game cannot be picked up or moved due to various constraints:

- **Immovable objects**: Fountains, statues, and other fixed structures
- **Heavy objects**: Items too heavy for the player to carry
- **Magically bound items**: Objects bound to a location by magic
- **Restricted items**: Objects that require specific character attributes (size, class, level, etc.)

When you attempt to pick up a constrained object, the GM will inform you why it cannot be moved.


## Communication and Social Engineering

Communication between players is a vital component of Motive, routed entirely through the Game Master (GM). The GM does not interpret the content of player communications but plays a crucial role in determining their observability. This controlled dissemination of information is central to the game's social engineering aspect.

**Examples of Communication Observability:**

*   **`whisper "player" "phrase"`:** Only the specified target player observes this communication.
*   **`say "phrase"`:** All players currently in the same room as the speaker observe this communication.
*   **`shout "phrase"`:** All players in the same room and potentially players in adjacent rooms might observe this, depending on game rules and environment specifics.

**Examples of Movement Observability:**

*   **Movement between rooms:** When a player moves from one room to another, other players in both the source and destination rooms observe the movement with specific direction information.
    *   Players in the source room see: "[Player] left the room via [Direction]."
    *   Players in the destination room see: "[Player] entered the room from [Direction]."
*   **Strategic importance:** This direction-specific information is crucial when multiple exits exist, allowing players to track each other's movements and make informed tactical decisions.

This system allows players to engage in complex social interactions, form alliances, spread misinformation, and strategize based on what they believe other players know or don't know. The ability to control who sees and hears what fosters a rich environment for emergent gameplay and strategic depth.
