"""Test exit aliases and movement paths for logical navigation."""

import pytest
from unittest.mock import Mock
from motive.game_master import GameMaster
from motive.character import Character
from motive.config import GameConfig, GameSettings, PlayerConfig


def test_town_square_exits_have_good_aliases():
    """Test that Town Square has good aliases for all major destinations."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Get town square room
    town_square = game_master.rooms.get("town_square")
    assert town_square is not None, "Town Square room should exist"
    
    exits = town_square.exits
    
    # Test that major destinations have good aliases
    assert "tavern" in exits, "Should have tavern exit"
    tavern_exit = exits["tavern"]
    assert "bar" in tavern_exit["aliases"], "Tavern should have 'bar' alias"
    assert "inn" in tavern_exit["aliases"], "Tavern should have 'inn' alias"
    
    assert "church" in exits, "Should have church exit"
    church_exit = exits["church"]
    assert "temple" in church_exit["aliases"], "Church should have 'temple' alias"
    assert "sanctuary" in church_exit["aliases"], "Church should have 'sanctuary' alias"
    
    assert "forest" in exits, "Should have forest exit"
    forest_exit = exits["forest"]
    assert "woods" in forest_exit["aliases"], "Forest should have 'woods' alias"
    assert "path" in forest_exit["aliases"], "Forest should have 'path' alias"


def test_hidden_observatory_has_good_exit_aliases():
    """Test that Hidden Observatory has good aliases for navigation."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Get hidden observatory room
    observatory = game_master.rooms.get("hidden_observatory")
    assert observatory is not None, "Hidden Observatory room should exist"
    
    exits = observatory.exits
    
    # Test that it has good aliases for returning to forest
    assert "forest" in exits, "Should have forest exit"
    forest_exit = exits["forest"]
    assert "woods" in forest_exit["aliases"], "Forest exit should have 'woods' alias"
    assert "path" in forest_exit["aliases"], "Forest exit should have 'path' alias"
    assert "down" in forest_exit["aliases"], "Forest exit should have 'down' alias for return"


def test_abandoned_warehouse_has_logical_exits():
    """Test that Abandoned Warehouse has logical exits for navigation."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Get abandoned warehouse room
    warehouse = game_master.rooms.get("abandoned_warehouse")
    assert warehouse is not None, "Abandoned Warehouse room should exist"
    
    exits = warehouse.exits
    
    # Test that it has logical exits
    assert "square" in exits, "Should have square exit"
    assert "market" in exits, "Should have market exit"
    assert "tunnels" in exits, "Should have tunnels exit"
    
    # Test that tunnels exit has good aliases
    tunnels_exit = exits["tunnels"]
    assert "underground" in tunnels_exit["aliases"], "Tunnels should have 'underground' alias"
    assert "passages" in tunnels_exit["aliases"], "Tunnels should have 'passages' alias"


def test_church_has_underground_tunnel_access():
    """Test that Church has access to underground tunnels."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Get church room
    church = game_master.rooms.get("church")
    assert church is not None, "Church room should exist"
    
    exits = church.exits
    
    # Test that it has tunnels exit
    assert "tunnels" in exits, "Church should have tunnels exit"
    tunnels_exit = exits["tunnels"]
    assert "underground" in tunnels_exit["aliases"], "Tunnels should have 'underground' alias"
    assert "passages" in tunnels_exit["aliases"], "Tunnels should have 'passages' alias"


def test_movement_aliases_are_intuitive():
    """Test that movement aliases are intuitive for players."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Test specific intuitive aliases
    town_square = game_master.rooms.get("town_square")
    exits = town_square.exits
    
    # Test tavern aliases
    tavern_exit = exits["tavern"]
    assert "bar" in tavern_exit["aliases"], "Players should be able to say 'move bar'"
    assert "inn" in tavern_exit["aliases"], "Players should be able to say 'move inn'"
    
    # Test church aliases  
    church_exit = exits["church"]
    assert "temple" in church_exit["aliases"], "Players should be able to say 'move temple'"
    assert "sanctuary" in church_exit["aliases"], "Players should be able to say 'move sanctuary'"
    
    # Test forest aliases
    forest_exit = exits["forest"]
    assert "woods" in forest_exit["aliases"], "Players should be able to say 'move woods'"
    assert "path" in forest_exit["aliases"], "Players should be able to say 'move path'"


def test_directional_aliases_exist():
    """Test that directional aliases exist for common movements."""
    # Create real game master instance
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    # Use the Hearth and Shadow configuration
    from motive.config_loader import ConfigLoader
    loader = ConfigLoader("configs")
    hearth_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Merge players into the hearth config
    hearth_config['players'] = players
    
    game_master = GameMaster(hearth_config, "test_game")
    
    # Test that observatory has directional aliases
    observatory = game_master.rooms.get("hidden_observatory")
    exits = observatory.exits
    
    forest_exit = exits["forest"]
    # Should have directional aliases for intuitive movement
    assert "down" in forest_exit["aliases"], "Should have 'down' alias for returning to forest"
    assert "back" in forest_exit["aliases"], "Should have 'back' alias for returning"
    
    # Test that forest has directional aliases to observatory
    forest = game_master.rooms.get("old_forest_path")
    forest_exits = forest.exits
    
    observatory_exit = forest_exits["observatory"]
    assert "up" in observatory_exit["aliases"], "Should have 'up' alias for going to observatory"
    assert "upward" in observatory_exit["aliases"], "Should have 'upward' alias"
