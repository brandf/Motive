# Motive Game Manual

This document will contain detailed information about the game mechanics, rules, environments, characters, and objects within the Motive platform. It will serve as a comprehensive guide for understanding how to play, balance, and interact with the game world, especially when designing system prompts for LLM players.

## Table of Contents

*   Game Overview
*   Game Mechanics: Turns, Actions, and Observability
*   Player Roles, Characters, and Motives (Win Conditions)
*   Game Environments: Rooms, Exits, and Objects
*   Player Actions: Categories and Parameters
*   Communication and Social Engineering
*   Future Development: Environment Generation and Training Data

## Game Overview

Motive is a turn-based, round-based game designed for both human and AI players, with a strong emphasis on AI-driven simulations. The core of the game revolves around players interacting with a dynamic environment and each other through a chat interface, mediated by a "Game Master" program. Players are assigned unique characters with secret "motives," which act as their personal win conditions. The ultimate goal is for players to achieve their motive by the end of the final round.

A central tenet of Motive is "observability." Player actions not only change the game state but also generate events that may or may not be observed by other players, leading to strategic social engineering and information asymmetry. The game is envisioned as a platform for generating extensive gameplay data, particularly from LLM-driven players, which can be used for advanced AI training, benchmarking, and research into planning and reasoning.

## Game Mechanics: Turns, Actions, and Observability

The game unfolds over a series of rounds, with each player taking a turn within every round in a predetermined order. The interaction between a player and the Game Master (GM) is a 1-on-1 chat-based dialogue.

**Player Turn Sequence:**

1.  **Information from GM:** At the beginning of a player's turn, the GM provides the following information:
    *   A description of their current room.
    *   A description of any other visible players or notable objects within the room.
    *   A list of visible exits from the current room.
    *   (After the first round) A list of 'observations' – these are all events triggered by other players' actions since this player's last turn that were observable by the current player.
    *   A list of available actions (which can be parameterized) and their corresponding action point costs.

2.  **Player Actions:** Each player is allotted a predetermined number of **action points** per turn. Players spend these points to perform actions. The player and the GM engage in a back-and-forth chat. The player proposes one action at a time, and the GM processes it, updates the game state, and provides immediate feedback, including any new observations or changes in the room description. This continues until the player's action points for that turn are fully spent.

3.  **Turn End:** Once a player has spent all their action points, their turn concludes, and the GM proceeds to the next player in the turn order.

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

Actions are broadly categorized as:

1.  **Common Actions:** These are general actions available to all players. Examples include: "say" (to speak to everyone in the room), "whisper" (to speak privately to a specific player), "shout" (to speak loudly, potentially heard in adjacent rooms), "pick up" (to add an object from the room to inventory), "drop" (to place an object from inventory into the current room), and "move" (to traverse an exit).
2.  **Character-Specific Actions:** These actions are unique to certain character types, reflecting their abilities or roles. Examples might include: "steal," "heal," or "arrest."
3.  **Inventory-Enabled Actions:** These actions require a specific object to be present in the player's inventory to be performed. Examples include: "attack <target> with <weapon>," or "unlock <door> with <key>."

Performing an action results in changes to the game state (e.g., an object moves from a room to an inventory) and the generation of events. These events are then processed by the GM to determine which players observe them.

## Communication and Social Engineering

Communication between players is a vital component of Motive, routed entirely through the Game Master (GM). The GM does not interpret the content of player communications but plays a crucial role in determining their observability. This controlled dissemination of information is central to the game's social engineering aspect.

**Examples of Communication Observability:**

*   **"whisper <player> <phrase>":** Only the specified target player observes this communication.
*   **"say <phrase>":** All players currently in the same room as the speaker observe this communication.
*   **"shout <phrase>":** All players in the same room and potentially players in adjacent rooms might observe this, depending on game rules and environment specifics.

This system allows LLM players to engage in complex social interactions, form alliances, spread misinformation, and strategize based on what they believe other players know or don't know. The ability to control who sees and hears what fosters a rich environment for emergent gameplay and offers significant potential for analyzing LLM reasoning and planning capabilities.

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
