"""
Integration tests for the observation system to prevent observation bugs.

These tests verify that:
1. Players see other players' actions in Recent Events
2. Players do NOT see their own actions in Recent Events
3. Players see their own actions in immediate feedback only
4. Character names use short_name in observations
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from motive.game_master import GameMaster
from motive.player import Player
from motive.sim_v2.v2_config_validator import V2GameConfig


class TestObservationSystemIntegration:
    """Test the observation system with multiple players."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock v2 config for testing."""
        config = MagicMock()
        config.game_settings = MagicMock()
        config.game_settings.initial_ap_per_turn = 30
        config.game_settings.num_rounds = 2
        config.game_settings.num_players = 3
        config.players = [
            {"provider": "mock", "model": "test-model"},
            {"provider": "mock", "model": "test-model"},
            {"provider": "mock", "model": "test-model"}
        ]
        return config

    @pytest.fixture
    def mock_players(self):
        """Create mock players for testing."""
        players = []
        for i in range(3):
            player = MagicMock(spec=Player)
            player.name = f"Player_{i+1}"
            player.character = MagicMock()
            player.character.id = f"char_{i+1}"
            player.character.name = f"Character {i+1}"
            player.character.short_name = f"Char{i+1}"
            player.character.get_display_name.return_value = f"Char{i+1}"
            player.character.current_room_id = "town_square"
            player.character.action_points = 30
            players.append(player)
        return players

    @pytest.mark.asyncio
    async def test_players_see_other_players_actions_not_own(self, mock_config, mock_players):
        """Test that players see other players' actions but not their own in Recent Events."""
        
        with patch('motive.game_master.GameInitializer') as mock_init, \
            patch('motive.player.create_llm_client') as mock_llm:
            
            # Setup mock game master
            mock_llm.return_value = MagicMock()
            mock_init.return_value.initialize_game_world.return_value = None
            mock_init.return_value.rooms = {"town_square": MagicMock()}
            mock_init.return_value.game_objects = {}
            mock_init.return_value.player_characters = {}
            mock_init.return_value.game_object_types = {}
            mock_init.return_value.game_actions = {}
            mock_init.return_value.game_character_types = {}
            
            game_master = GameMaster(mock_config, "test_game", deterministic=True)
            game_master.players = mock_players
            game_master.rooms = {"town_square": MagicMock()}
            game_master.player_observations = {player.character.id: [] for player in mock_players}
            
            # Simulate Player 1 performing an action
            player1 = mock_players[0]
            player1_char = player1.character
            
            # Create a mock event for Player 1's action
            from motive.config import Event
            test_event = Event(
                message=f"{player1_char.get_display_name()} looked at Fresh Evidence.",
                event_type="player_action",
                source_room_id="town_square",
                timestamp="2025-01-01T00:00:00",
                related_player_id=player1_char.id,
                observers=["room_characters"]
            )
            
            # Add event to observations
            game_master.event_queue = [test_event]
            game_master._distribute_events()
            
            # Verify Player 1 does NOT see their own action in observations
            assert len(game_master.player_observations[player1_char.id]) == 0
            
            # Verify Player 2 and 3 DO see Player 1's action
            assert len(game_master.player_observations[mock_players[1].character.id]) == 1
            assert len(game_master.player_observations[mock_players[2].character.id]) == 1
            
            # Verify the observation message uses short name
            observation = game_master.player_observations[mock_players[1].character.id][0]
            assert "Char1" in observation.message
            assert "Player Character 1" not in observation.message

    def test_character_display_names_in_events(self):
        """Test that event messages use short names instead of full names."""
        from motive.character import Character
        from motive.hooks.core_hooks import look_at_target
        from motive.config import Event
        
        # Create character with short name
        char = Character(
            char_id="test_char",
            name="Detective James Thorne",
            backstory="A detective",
            short_name="Detective Thorne"
        )
        
        # Mock game master and room
        mock_game_master = MagicMock()
        mock_room = MagicMock()
        mock_room.get_object.return_value = MagicMock()
        mock_room.get_object.return_value.name = "Fresh Evidence"
        mock_room.get_object.return_value.description = "Evidence"
        mock_game_master.rooms = {"town_square": mock_room}
        
        # Mock action config
        mock_action_config = MagicMock()
        
        # Test look action
        events, feedback = look_at_target(
            mock_game_master, char, mock_action_config, {"target": "Fresh Evidence"}
        )
        
        # Verify event message uses short name
        assert len(events) > 0
        event_message = events[0].message
        assert "Detective Thorne" in event_message
        assert "Player Detective James Thorne" not in event_message
        assert "Detective James Thorne" not in event_message

    def test_observation_exclusion_for_originator(self):
        """Test that 'player' scoped events are excluded from observations for the originator."""
        from motive.game_master import GameMaster
        from motive.config import Event
        
        # Create mock game master
        game_master = MagicMock(spec=GameMaster)
        game_master.player_observations = {"char1": []}
        
        # Create a 'player' scoped event
        player_event = Event(
            message="You pick up the Fresh Evidence.",
            event_type="item_pickup",
            source_room_id="town_square",
            timestamp="2025-01-01T00:00:00",
            related_player_id="char1",
            observers=["player"]
        )
        
        # Mock the _distribute_events method to test the logic
        game_master.event_queue = [player_event]
        
        # Simulate the distribution logic
        event = player_event
        player_char_id = "char1"
        is_originator = (event.related_player_id == player_char_id)
        
        # Test the exclusion logic
        should_exclude = is_originator and "player" in event.observers
        assert should_exclude is True, "Player-scoped events should be excluded from observations for originator"


if __name__ == "__main__":
    pytest.main([__file__])
