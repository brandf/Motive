#!/usr/bin/env python3
"""
Test the use action parsing fix for multi-word arguments.
"""
import pytest
from motive.action_parser import _parse_use_parameters


class TestUseActionParsing:
    """Test the use action parsing with multi-word arguments."""
    
    def test_use_single_word_object(self):
        """Test use with single word object."""
        object_name, target = _parse_use_parameters("torch")
        assert object_name == "torch"
        assert target == ""
    
    def test_use_multi_word_object(self):
        """Test use with multi-word object (no quotes)."""
        object_name, target = _parse_use_parameters("fresh evidence")
        assert object_name == "fresh evidence"
        assert target == ""
    
    def test_use_quoted_object(self):
        """Test use with quoted multi-word object."""
        object_name, target = _parse_use_parameters('"magic sword"')
        assert object_name == "magic sword"
        assert target == ""
    
    def test_use_object_with_target(self):
        """Test use with object and target."""
        object_name, target = _parse_use_parameters("torch on door")
        assert object_name == "torch"
        assert target == "door"
    
    def test_use_multi_word_object_with_target(self):
        """Test use with multi-word object and target."""
        object_name, target = _parse_use_parameters("fresh evidence on mayor")
        assert object_name == "fresh evidence"
        assert target == "mayor"
    
    def test_use_quoted_object_with_target(self):
        """Test use with quoted object and target."""
        object_name, target = _parse_use_parameters('"magic sword" on "locked chest"')
        assert object_name == "magic sword"
        assert target == "locked chest"
    
    def test_use_object_with_at_preposition(self):
        """Test use with 'at' preposition."""
        object_name, target = _parse_use_parameters("torch at wall")
        assert object_name == "torch"
        assert target == "wall"
    
    def test_use_object_with_with_preposition(self):
        """Test use with 'with' preposition."""
        object_name, target = _parse_use_parameters("key with lock")
        assert object_name == "key"
        assert target == "lock"
    
    def test_use_empty_string(self):
        """Test use with empty string raises error."""
        with pytest.raises(ValueError, match="Use action requires an object name"):
            _parse_use_parameters("")
    
    def test_use_whitespace_only(self):
        """Test use with whitespace only raises error."""
        with pytest.raises(ValueError, match="Use action requires an object name"):
            _parse_use_parameters("   ")


if __name__ == "__main__":
    pytest.main([__file__])
