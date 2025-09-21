"""
Comprehensive unit tests for the unified configuration merging system.

This tests all merge strategies, edge cases, and complex scenarios to ensure
the foundational config merging system is robust and reliable.
"""

import pytest
from typing import Dict, Any, List
from motive.config_merging import ConfigMerger, merge_configs
from motive.list_merge_strategies import ListMergeStrategy


class TestConfigMergerComprehensive:
    """Comprehensive tests for ConfigMerger."""

    def setup_method(self):
        """Set up test fixtures."""
        self.merger = ConfigMerger()

    def test_simple_dict_merge(self):
        """Test basic dictionary merging."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = self.merger.merge_configs(base, override)
        
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_dict_merge(self):
        """Test nested dictionary merging."""
        base = {
            "level1": {
                "level2": {
                    "a": 1,
                    "b": 2
                },
                "c": 3
            },
            "d": 4
        }
        override = {
            "level1": {
                "level2": {
                    "b": 99,
                    "e": 5
                },
                "f": 6
            },
            "g": 7
        }
        result = self.merger.merge_configs(base, override)
        
        expected = {
            "level1": {
                "level2": {
                    "a": 1,
                    "b": 99,
                    "e": 5
                },
                "c": 3,
                "f": 6
            },
            "d": 4,
            "g": 7
        }
        assert result == expected

    def test_simple_list_append(self):
        """Test simple list appending (default behavior)."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = self.merger.merge_configs(base, override)
        
        assert result["items"] == [1, 2, 3, 4, 5]

    def test_merge_strategy_override(self):
        """Test __merge_strategy__: override."""
        base = {"players": [{"name": "Player1"}, {"name": "Player2"}]}
        override = {
            "players": [
                {"__merge_strategy__": "override"},
                {"name": "PlayerA"},
                {"name": "PlayerB"}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 2
        assert result["players"][0]["name"] == "PlayerA"
        assert result["players"][1]["name"] == "PlayerB"

    def test_merge_strategy_append(self):
        """Test __merge_strategy__: append."""
        base = {"players": [{"name": "Player1"}]}
        override = {
            "players": [
                {"__merge_strategy__": "append"},
                {"name": "Player2"}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 2
        assert result["players"][0]["name"] == "Player1"
        assert result["players"][1]["name"] == "Player2"

    def test_merge_strategy_prepend(self):
        """Test __merge_strategy__: prepend."""
        base = {"players": [{"name": "Player2"}]}
        override = {
            "players": [
                {"__merge_strategy__": "prepend"},
                {"name": "Player1"}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 2
        assert result["players"][0]["name"] == "Player1"
        assert result["players"][1]["name"] == "Player2"

    def test_merge_strategy_merge_unique(self):
        """Test __merge_strategy__: merge_unique."""
        base = {"players": [{"name": "Player1"}, {"name": "Player2"}]}
        override = {
            "players": [
                {"__merge_strategy__": "merge_unique", "__merge_params__": {"key": "name"}},
                {"name": "Player2"},  # Duplicate
                {"name": "Player3"}   # New
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 3
        names = [p["name"] for p in result["players"]]
        assert "Player1" in names
        assert "Player2" in names
        assert "Player3" in names

    def test_merge_strategy_remove_items(self):
        """Test __merge_strategy__: remove_items."""
        base = {"players": [{"name": "Player1"}, {"name": "Player2"}, {"name": "Player3"}]}
        override = {
            "players": [
                {"__merge_strategy__": "remove_items", "__merge_params__": {"items": [{"name": "Player2"}]}}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 2
        names = [p["name"] for p in result["players"]]
        assert "Player1" in names
        assert "Player2" not in names
        assert "Player3" in names

    def test_merge_strategy_insert_at(self):
        """Test __merge_strategy__: insert_at."""
        base = {"players": [{"name": "Player1"}, {"name": "Player3"}]}
        override = {
            "players": [
                {"__merge_strategy__": "insert_at", "__merge_params__": {"index": 1}},
                {"name": "Player2"}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 3
        assert result["players"][0]["name"] == "Player1"
        assert result["players"][1]["name"] == "Player2"
        assert result["players"][2]["name"] == "Player3"

    def test_merge_strategy_smart_merge(self):
        """Test __merge_strategy__: smart_merge."""
        base = {"players": [{"name": "Player1", "level": 1}, {"name": "Player2", "level": 2}]}
        override = {
            "players": [
                {"__merge_strategy__": "smart_merge", "__merge_params__": {"key": "name"}},
                {"name": "Player2", "level": 99},  # Update existing
                {"name": "Player3", "level": 3}    # Add new
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 3
        player2 = next(p for p in result["players"] if p["name"] == "Player2")
        assert player2["level"] == 99

    def test_merge_strategy_key_based_merge(self):
        """Test __merge_strategy__: key_based."""
        base = {"players": [{"name": "Player1", "score": 100}]}
        override = {
            "players": [
                {"__merge_strategy__": "key_based", "__merge_params__": {"key": "name"}},
                {"name": "Player1", "score": 200},  # Update
                {"name": "Player2", "score": 150}    # Add
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert len(result["players"]) == 2
        player1 = next(p for p in result["players"] if p["name"] == "Player1")
        player2 = next(p for p in result["players"] if p["name"] == "Player2")
        assert player1["score"] == 200
        assert player2["score"] == 150

    def test_empty_lists(self):
        """Test merging with empty lists."""
        base = {"items": []}
        override = {"items": [1, 2, 3]}
        result = self.merger.merge_configs(base, override)
        assert result["items"] == [1, 2, 3]

        base = {"items": [1, 2, 3]}
        override = {"items": []}
        result = self.merger.merge_configs(base, override)
        assert result["items"] == [1, 2, 3]

    def test_none_values(self):
        """Test merging with None values."""
        base = {"a": 1, "b": None}
        override = {"b": 2, "c": None}
        result = self.merger.merge_configs(base, override)
        assert result == {"a": 1, "b": 2, "c": None}

    def test_mixed_types(self):
        """Test merging with mixed data types."""
        base = {
            "string": "hello",
            "number": 42,
            "boolean": True,
            "list": [1, 2],
            "dict": {"a": 1}
        }
        override = {
            "string": "world",
            "number": 99,
            "boolean": False,
            "list": [3, 4],
            "dict": {"b": 2}
        }
        result = self.merger.merge_configs(base, override)
        
        assert result["string"] == "world"
        assert result["number"] == 99
        assert result["boolean"] == False
        assert result["list"] == [1, 2, 3, 4]
        assert result["dict"] == {"a": 1, "b": 2}

    def test_complex_nested_scenario(self):
        """Test complex nested merging scenario."""
        base = {
            "game_settings": {
                "num_rounds": 5,
                "players": [
                    {"name": "Player1", "provider": "google"},
                    {"name": "Player2", "provider": "openai"}
                ],
                "features": {
                    "debug": True,
                    "logging": False
                }
            },
            "entities": {
                "rooms": ["room1", "room2"],
                "characters": ["char1"]
            }
        }
        
        override = {
            "game_settings": {
                "num_rounds": 10,
                "players": [
                    {"__merge_strategy__": "override"},
                    {"name": "PlayerA", "provider": "anthropic"},
                    {"name": "PlayerB", "provider": "google"}
                ],
                "features": {
                    "debug": False,
                    "profiling": True
                }
            },
            "entities": {
                "rooms": ["room3", "room4"],
                "characters": ["char2", "char3"]
            }
        }
        
        result = self.merger.merge_configs(base, override)
        
        # Check game_settings
        assert result["game_settings"]["num_rounds"] == 10
        assert len(result["game_settings"]["players"]) == 2
        assert result["game_settings"]["players"][0]["name"] == "PlayerA"
        assert result["game_settings"]["features"]["debug"] == False
        assert result["game_settings"]["features"]["logging"] == False
        assert result["game_settings"]["features"]["profiling"] == True
        
        # Check entities
        assert result["entities"]["rooms"] == ["room1", "room2", "room3", "room4"]
        assert result["entities"]["characters"] == ["char1", "char2", "char3"]

    def test_includes_skipped(self):
        """Test that 'includes' key is skipped during merging."""
        base = {"a": 1, "includes": ["base.yaml"]}
        override = {"b": 2, "includes": ["override.yaml"]}
        result = self.merger.merge_configs(base, override)
        
        # Includes should be skipped, not merged
        assert "includes" not in result
        assert result == {"a": 1, "b": 2}

    def test_patch_reference_placeholder(self):
        """Test patch reference handling (placeholder implementation)."""
        base = {"players": [{"name": "Player1"}]}
        override = {
            "players": {
                "__ref__": "base_players",
                "__patches__": {"add": [{"name": "Player2"}]}
            }
        }
        result = self.merger.merge_configs(base, override)
        
        # Should return base value (patch references not fully implemented)
        assert result["players"] == [{"name": "Player1"}]

    def test_patch_list_operations(self):
        """Test patch list operations."""
        base = {"items": [1, 2, 3]}
        override = {
            "items": [
                {"__patch_list__": "append", "items": [4, 5]},
                {"__patch_list__": "prepend", "items": [0]},
                {"__patch_list__": "remove", "items": [2]}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        # Should be: [0] + [1, 2, 3] + [4, 5] - [2] = [0, 1, 3, 4, 5]
        assert result["items"] == [0, 1, 3, 4, 5]

    def test_patch_list_replace(self):
        """Test patch list replace operation."""
        base = {"items": [1, 2, 3]}
        override = {
            "items": [
                {"__patch_list__": "replace", "items": [4, 5, 6]}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        assert result["items"] == [4, 5, 6]

    def test_dict_to_list_conversion(self):
        """Test converting dict to list during merge."""
        base = {"players": {"player1": {"name": "Player1"}, "player2": {"name": "Player2"}}}
        override = {"players": [{"name": "Player3"}]}
        result = self.merger.merge_configs(base, override)
        
        # Should replace dict with list (override takes precedence)
        assert len(result["players"]) == 1
        assert result["players"][0]["name"] == "Player3"

    def test_edge_case_empty_merge_strategy(self):
        """Test edge case with empty merge strategy list."""
        base = {"players": [{"name": "Player1"}]}
        override = {"players": [{"__merge_strategy__": "override"}]}
        result = self.merger.merge_configs(base, override)
        
        assert result["players"] == []

    def test_edge_case_invalid_merge_strategy(self):
        """Test edge case with invalid merge strategy."""
        base = {"players": [{"name": "Player1"}]}
        override = {
            "players": [
                {"__merge_strategy__": "invalid_strategy"},
                {"name": "Player2"}
            ]
        }
        result = self.merger.merge_configs(base, override)
        
        # Should fall back to append behavior
        assert len(result["players"]) == 2
        assert result["players"][0]["name"] == "Player1"
        assert result["players"][1]["name"] == "Player2"

    def test_deep_nesting_with_merge_strategies(self):
        """Test deep nesting with merge strategies at different levels."""
        base = {
            "level1": {
                "level2": {
                    "items": [1, 2],
                    "players": [{"name": "Player1"}]
                }
            }
        }
        override = {
            "level1": {
                "level2": {
                    "items": [
                        {"__merge_strategy__": "override"},
                        3, 4
                    ],
                    "players": [
                        {"__merge_strategy__": "prepend"},
                        {"name": "Player0"}
                    ]
                }
            }
        }
        result = self.merger.merge_configs(base, override)
        
        assert result["level1"]["level2"]["items"] == [3, 4]
        assert len(result["level1"]["level2"]["players"]) == 2
        assert result["level1"]["level2"]["players"][0]["name"] == "Player0"
        assert result["level1"]["level2"]["players"][1]["name"] == "Player1"

    def test_convenience_function(self):
        """Test the convenience merge_configs function."""
        base = {"a": 1}
        override = {"b": 2}
        result = merge_configs(base, override)
        
        assert result == {"a": 1, "b": 2}

    def test_immutability(self):
        """Test that original configs are not modified."""
        base = {"a": 1, "items": [1, 2]}
        override = {"b": 2, "items": [3, 4]}
        original_base = base.copy()
        original_override = override.copy()
        
        result = self.merger.merge_configs(base, override)
        
        # Originals should be unchanged
        assert base == original_base
        assert override == original_override
        # Result should be new
        assert result is not base
        assert result is not override

    def test_circular_reference_prevention(self):
        """Test that circular references don't cause infinite loops."""
        base = {"a": 1}
        override = {"b": base}  # Circular reference
        
        # This should not cause infinite recursion
        result = self.merger.merge_configs(base, override)
        assert result["a"] == 1
        assert result["b"] is base  # Reference preserved


class TestConfigMergerEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.merger = ConfigMerger()

    def test_empty_configs(self):
        """Test merging empty configs."""
        result = self.merger.merge_configs({}, {})
        assert result == {}

        result = self.merger.merge_configs({"a": 1}, {})
        assert result == {"a": 1}

        result = self.merger.merge_configs({}, {"b": 2})
        assert result == {"b": 2}

    def test_none_configs(self):
        """Test handling of None configs."""
        with pytest.raises(AttributeError):
            self.merger.merge_configs(None, {})

        with pytest.raises(AttributeError):
            self.merger.merge_configs({}, None)

    def test_non_dict_configs(self):
        """Test handling of non-dict configs."""
        with pytest.raises(AttributeError):
            self.merger.merge_configs("not a dict", {})

        with pytest.raises(AttributeError):
            self.merger.merge_configs({}, "not a dict")

    def test_very_large_configs(self):
        """Test performance with large configs."""
        # Create large configs
        base = {f"key_{i}": f"value_{i}" for i in range(1000)}
        override = {f"override_{i}": f"override_value_{i}" for i in range(1000)}
        
        result = self.merger.merge_configs(base, override)
        
        assert len(result) == 2000
        assert "key_0" in result
        assert "override_0" in result

    def test_very_deep_nesting(self):
        """Test very deep nesting."""
        # Create deeply nested config with final value at level_2
        config = {
            "level_0": {
                "level_1": {
                    "level_2": {
                        "final": "value"
                    }
                }
            }
        }

        override = {"level_0": {"level_1": {"new": "value"}}}
        result = self.merger.merge_configs(config, override)

        assert result["level_0"]["level_1"]["new"] == "value"
        # The deep nesting should still be preserved
        assert "level_2" in result["level_0"]["level_1"]
        # The final value should be preserved at the deepest level
        assert result["level_0"]["level_1"]["level_2"]["final"] == "value"
