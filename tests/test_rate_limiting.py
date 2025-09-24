"""
Test suite for the rate limiting functionality in LLM factory.

Following AGENT.md guidelines:
- Tests are completely isolated from external services
- Use real constructors and APIs
- Test both positive and negative cases
- Include boundary conditions and edge cases
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from motive.llm_factory import (
    create_llm_client, 
    _check_rate_limit, 
    _increment_rate_limit,
    _rate_limited_request,
    RATE_LIMIT_CONFIG,
    _rate_limit_state
)


class TestRateLimiting:
    """Test the rate limiting functionality."""
    
    def test_check_rate_limit_initial_state(self):
        """Test that rate limit check works for initial state."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        # Test unknown provider (should always pass)
        assert _check_rate_limit("unknown_provider") is True
        
        # Test known provider with no previous requests
        assert _check_rate_limit("openai") is True
        assert _check_rate_limit("google") is True
        assert _check_rate_limit("anthropic") is True
    
    def test_check_rate_limit_after_requests(self):
        """Test rate limit check after making requests."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        provider = "openai"
        config = RATE_LIMIT_CONFIG[provider]
        
        # Make requests up to the limit
        for i in range(config["requests_per_minute"]):
            _increment_rate_limit(provider)
        
        # Should be rate limited (we made exactly the limit)
        assert _check_rate_limit(provider) is False
        
        # Make one more request to exceed limit
        _increment_rate_limit(provider)
        
        # Should still be rate limited
        assert _check_rate_limit(provider) is False
    
    def test_increment_rate_limit(self):
        """Test that rate limit increment works correctly."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        provider = "google"
        
        # Initial state
        assert provider not in _rate_limit_state["request_counts"]
        
        # Increment once
        _increment_rate_limit(provider)
        assert _rate_limit_state["request_counts"][provider]["minute"] == 1
        assert _rate_limit_state["request_counts"][provider]["hour"] == 1
        
        # Increment again
        _increment_rate_limit(provider)
        assert _rate_limit_state["request_counts"][provider]["minute"] == 2
        assert _rate_limit_state["request_counts"][provider]["hour"] == 2
    
    @pytest.mark.asyncio
    async def test_rate_limited_request_success(self):
        """Test successful rate-limited request."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        # Create mock LLM client
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "test response"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        # Test successful request
        result = await _rate_limited_request("dummy", mock_llm, "test message")
        
        assert result == mock_response
        assert mock_llm.ainvoke.called
    
    @pytest.mark.asyncio
    async def test_rate_limited_request_rate_limit_error(self):
        """Test rate-limited request with rate limit error."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        # Create mock LLM client that raises rate limit error
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        
        # Test that it raises RuntimeError after max retries
        with pytest.raises(RuntimeError, match="Rate limit exceeded for dummy after 0 retries"):
            await _rate_limited_request("dummy", mock_llm, "test message")
    
    @pytest.mark.asyncio
    async def test_rate_limited_request_non_rate_limit_error(self):
        """Test rate-limited request with non-rate-limit error."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        # Create mock LLM client that raises non-rate-limit error
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Authentication failed"))
        
        # Test that it raises the original error without retrying
        with pytest.raises(Exception, match="Authentication failed"):
            await _rate_limited_request("dummy", mock_llm, "test message")
    
    def test_create_llm_client_with_rate_limiting(self):
        """Test that create_llm_client returns a rate-limited client."""
        # Test dummy provider (should work without rate limiting)
        client = create_llm_client("dummy", "test")
        
        # Should have ainvoke method
        assert hasattr(client, 'ainvoke')
        assert hasattr(client, 'invoke')
        
        # Test that it's callable
        assert callable(client.ainvoke)
        assert callable(client.invoke)
    
    def test_rate_limit_config_coverage(self):
        """Test that all providers in LLM_PROVIDER_MAP have rate limit config."""
        from motive.llm_factory import LLM_PROVIDER_MAP
        
        for provider in LLM_PROVIDER_MAP.keys():
            if provider != "dummy":  # Skip dummy provider
                assert provider in RATE_LIMIT_CONFIG, f"Provider {provider} missing from RATE_LIMIT_CONFIG"
                
                config = RATE_LIMIT_CONFIG[provider]
                required_keys = ["requests_per_minute", "requests_per_hour", "max_retries", "retry_delay", "backoff_multiplier"]
                for key in required_keys:
                    assert key in config, f"Provider {provider} missing {key} in rate limit config"
    
    def test_rate_limit_config_values(self):
        """Test that rate limit config values are reasonable."""
        for provider, config in RATE_LIMIT_CONFIG.items():
            assert config["requests_per_minute"] > 0, f"{provider}: requests_per_minute must be positive"
            assert config["requests_per_hour"] > 0, f"{provider}: requests_per_hour must be positive"
            assert config["max_retries"] >= 0, f"{provider}: max_retries must be non-negative"
            assert config["retry_delay"] >= 0, f"{provider}: retry_delay must be non-negative"
            assert config["backoff_multiplier"] >= 1.0, f"{provider}: backoff_multiplier must be >= 1.0"
            
            # Reasonable bounds
            assert config["requests_per_minute"] <= 1000, f"{provider}: requests_per_minute seems too high"
            assert config["requests_per_hour"] <= 10000, f"{provider}: requests_per_hour seems too high"
            assert config["max_retries"] <= 10, f"{provider}: max_retries seems too high"
            assert config["retry_delay"] <= 60, f"{provider}: retry_delay seems too high"
            assert config["backoff_multiplier"] <= 10, f"{provider}: backoff_multiplier seems too high"


class TestRateLimitingIntegration:
    """Integration tests for rate limiting."""
    
    def test_rate_limit_state_isolation(self):
        """Test that rate limit state is properly isolated between providers."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        # Make requests for different providers
        _increment_rate_limit("openai")
        _increment_rate_limit("openai")
        _increment_rate_limit("google")
        
        # Check that counts are separate
        assert _rate_limit_state["request_counts"]["openai"]["minute"] == 2
        assert _rate_limit_state["request_counts"]["google"]["minute"] == 1
        
        # Check that rate limits are independent
        assert _check_rate_limit("openai") is True
        assert _check_rate_limit("google") is True
    
    def test_rate_limit_reset_behavior(self):
        """Test that rate limits reset after time windows."""
        # Reset state
        _rate_limit_state["request_counts"] = {}
        _rate_limit_state["last_reset"] = {}
        
        provider = "openai"
        config = RATE_LIMIT_CONFIG[provider]
        
        # Make requests up to the limit
        for i in range(config["requests_per_minute"]):
            _increment_rate_limit(provider)
        
        # Should be rate limited
        assert _check_rate_limit(provider) is False
        
        # Manually reset the time to simulate time passing
        current_time = time.time()
        _rate_limit_state["last_reset"][provider]["minute"] = current_time - 61  # 61 seconds ago
        
        # Should reset and allow requests again
        assert _check_rate_limit(provider) is True
