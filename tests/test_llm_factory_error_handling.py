"""
Tests for llm_factory.py error handling and edge cases.
These tests focus on critical LLM client creation failures that could break the game.
"""
import pytest
from unittest.mock import patch, MagicMock
from motive.llm_factory import create_llm_client, LLM_PROVIDER_MAP, PROVIDER_API_KEYS


class TestLLMFactoryErrorHandling:
    """Test critical error handling paths in llm_factory.py"""
    
    def test_unsupported_provider(self):
        """Test handling of unsupported LLM provider - common config mistake"""
        with pytest.raises(ValueError) as exc_info:
            create_llm_client("unsupported_provider", "gpt-4")
        
        assert "Unsupported LLM provider" in str(exc_info.value)
        assert "Available providers are" in str(exc_info.value)
    
    def test_llm_factory_provider_validation(self):
        """Test that LLM factory validates provider existence"""
        # This test verifies the provider validation logic works
        with pytest.raises(ValueError) as exc_info:
            create_llm_client("nonexistent_provider", "gpt-4")
        
        assert "Unsupported LLM provider" in str(exc_info.value)
        assert "Available providers are" in str(exc_info.value)
    
    def test_provider_api_keys_mapping(self):
        """Test that all providers have API key mappings - configuration completeness"""
        for provider in LLM_PROVIDER_MAP.keys():
            assert provider in PROVIDER_API_KEYS, f"Provider {provider} missing API key mapping"
    
    def test_api_keys_mapping_completeness(self):
        """Test that API key mappings don't have orphaned entries"""
        for provider in PROVIDER_API_KEYS.keys():
            assert provider in LLM_PROVIDER_MAP, f"API key mapping for {provider} but no provider class"
    
    def test_llm_factory_configuration_completeness(self):
        """Test that LLM factory configuration is complete and consistent"""
        # Verify all providers in the map have corresponding API key mappings
        for provider in LLM_PROVIDER_MAP.keys():
            assert provider in PROVIDER_API_KEYS, f"Provider {provider} missing API key mapping"
        
        # Verify no orphaned API key mappings
        for provider in PROVIDER_API_KEYS.keys():
            assert provider in LLM_PROVIDER_MAP, f"API key mapping for {provider} but no provider class"
