#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_telephone_shout_say_whisper(tmp_path):
    # Use real H&S config with two players; we will reposition to simulate the relay
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    # Arrange two players; we will move them between rooms across tavern -> town_square -> bank
    with llm_script({
        "Player_1": "> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_telephone", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Clear them from any starting rooms, then place
        for p in (p1, p2):
            old = p.character.current_room_id
            if old in gm.rooms:
                gm.rooms[old].remove_player(p.character.id)

        gm.rooms['tavern'].add_player(p1.character)
        gm.rooms['town_square'].add_player(p2.character)

        # Ensure fresh AP
        initial_ap = gm.game_initializer.initial_ap_per_turn
        p1.character.action_points = initial_ap
        p2.character.action_points = initial_ap
        

        # Turn A: P1 shouts from tavern. Expect P2 (square) hears (adjacent)
        with llm_script({
            "Player_1": "> shout \"relay one\"\n> pass",
            "Player_2": "> pass",
        }):
            await gm._execute_player_turn(p1, round_num=1)
            p2_obs = gm.player_observations.get(p2.character.id, [])
            p2_debug = [(getattr(ev, "message", ""), getattr(ev, "observers", []), getattr(ev, "related_player_id", None)) for ev in p2_obs]
            print("DEBUG P2 OBS:", p2_debug)
            assert any(
                isinstance(getattr(ev, "observers", []), list)
                and ("adjacent_rooms_characters" in getattr(ev, "observers", []) or "adjacent_rooms_characters_characters" in getattr(ev, "observers", []))
                and getattr(ev, "related_player_id", None) == p1.character.id
                for ev in p2_obs
            ), p2_debug

        # Reset AP and reposition for relay hop: move P1 to bank; P2 is in town_square and will shout
        p2.character.action_points = initial_ap
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        gm.rooms['bank'].add_player(p1.character)

        # Turn B: P2 shouts from town_square. Expect P1 (now in bank) hears; this completes the relay hop.
        with llm_script({
            "Player_1": "> pass",
            "Player_2": "> shout \"relay two\"\n> pass",
        }):
            await gm._execute_player_turn(p2, round_num=1)
            p1_obs = gm.player_observations.get(p1.character.id, [])
            p1_debug = [(getattr(ev, "message", ""), getattr(ev, "observers", []), getattr(ev, "related_player_id", None)) for ev in p1_obs]
            print("DEBUG P1 OBS:", p1_debug)
            assert any(
                isinstance(getattr(ev, "observers", []), list)
                and ("adjacent_rooms_characters" in getattr(ev, "observers", []) or "adjacent_rooms_characters_characters" in getattr(ev, "observers", []))
                and getattr(ev, "related_player_id", None) == p2.character.id
                for ev in p1_obs
            ), p1_debug

        # Reset AP for P2
        p2.character.action_points = initial_ap

        # Sanity: say is room-local (P2 says in town_square; P1 in bank should not observe)
        with llm_script({
            "Player_1": "> pass",
            "Player_2": "> say \"square local\"\n> pass",
        }):
            await gm._execute_player_turn(p2, round_num=1)
            p1_obs = gm.player_observations.get(p1.character.id, [])
            p1_msgs = [getattr(ev, "message", "") or "" for ev in p1_obs]
            assert not any(("says" in m.lower()) and ("square local" in m.lower()) for m in p1_msgs), p1_msgs

        # Whisper privacy: P2 whispers to P1 in different rooms should fail gate and not deliver
        # First attempt (invalid - different rooms): ensure no delivery, executed during active turn
        p2.character.action_points = initial_ap
        with llm_script({
            "Player_1": "> pass",
            "Player_2": "> whisper \"Player_1\" \"secret\"\n> pass",
        }):
            await gm._execute_player_turn(p2, round_num=2)
            p1_obs = gm.player_observations.get(p1.character.id, [])
            p1_msgs = [getattr(ev, "message", "") or "" for ev in p1_obs]
            assert not any(("whispers to you" in m.lower()) and ("secret" in m.lower()) for m in p1_msgs), p1_msgs

        # (Whisper positive case is covered in minimal tests; skip here to avoid brittleness with turn confirmation.)


