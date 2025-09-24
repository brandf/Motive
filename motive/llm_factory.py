from typing import Type
import time
import asyncio
from langchain_core.language_models.chat_models import BaseChatModel

# Dynamic imports for specific chat models
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

# A mapping of provider names to their respective LangChain ChatModel classes
# Add more providers here as you discover them and install their langchain-xxx package
LLM_PROVIDER_MAP: dict[str, Type[BaseChatModel] | None] = {
    "openai": ChatOpenAI,
    "google": ChatGoogleGenerativeAI,
    "anthropic": ChatAnthropic,
    "dummy": None,  # Special test provider that doesn't need real LLM
}

# Mapping of provider names to their typical API key environment variable names
# THIS IS THE DICTIONARY THAT WAS MISSING
PROVIDER_API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "dummy": None,  # Dummy provider doesn't need API key
    # Add other provider API keys here
    # "cohere": "COHERE_API_KEY",
}

# Rate limiting configuration for different providers
# Format: {"provider": {"requests_per_minute": int, "requests_per_hour": int, "max_retries": int, "retry_delay": float}}
RATE_LIMIT_CONFIG = {
    "openai": {
        "requests_per_minute": 60,
        "requests_per_hour": 3000,
        "max_retries": 3,
        "retry_delay": 1.0,
        "backoff_multiplier": 2.0
    },
    "google": {
        "requests_per_minute": 60,
        "requests_per_hour": 1500,
        "max_retries": 5,
        "retry_delay": 2.0,
        "backoff_multiplier": 1.5
    },
    "anthropic": {
        "requests_per_minute": 50,
        "requests_per_hour": 2000,
        "max_retries": 3,
        "retry_delay": 1.5,
        "backoff_multiplier": 2.0
    },
    "dummy": {
        "requests_per_minute": 1000,  # No real limits for dummy
        "requests_per_hour": 10000,
        "max_retries": 0,
        "retry_delay": 0.0,
        "backoff_multiplier": 1.0
    }
}

# Global rate limiting state
_rate_limit_state = {
    "request_counts": {},  # {"provider": {"minute": count, "hour": count}}
    "last_reset": {},      # {"provider": {"minute": timestamp, "hour": timestamp}}
    "active_requests": {}  # {"provider": count}
}


def _check_rate_limit(provider: str) -> bool:
    """
    Check if the provider is within rate limits.
    Returns True if request can proceed, False if rate limited.
    """
    if provider not in RATE_LIMIT_CONFIG:
        return True  # No rate limiting for unknown providers
    
    config = RATE_LIMIT_CONFIG[provider]
    current_time = time.time()
    
    # Initialize state for provider if needed
    if provider not in _rate_limit_state["request_counts"]:
        _rate_limit_state["request_counts"][provider] = {"minute": 0, "hour": 0}
        _rate_limit_state["last_reset"][provider] = {"minute": current_time, "hour": current_time}
        _rate_limit_state["active_requests"][provider] = 0
    
    state = _rate_limit_state["request_counts"][provider]
    last_reset = _rate_limit_state["last_reset"][provider]
    
    # Reset counters if time windows have passed
    if current_time - last_reset["minute"] >= 60:
        state["minute"] = 0
        last_reset["minute"] = current_time
    
    if current_time - last_reset["hour"] >= 3600:
        state["hour"] = 0
        last_reset["hour"] = current_time
    
    # Check limits
    if state["minute"] >= config["requests_per_minute"]:
        return False
    if state["hour"] >= config["requests_per_hour"]:
        return False
    
    return True


def _increment_rate_limit(provider: str):
    """Increment the rate limit counters for a provider."""
    if provider not in RATE_LIMIT_CONFIG:
        return  # No rate limiting for unknown providers
    
    current_time = time.time()
    
    # Initialize state for provider if needed
    if provider not in _rate_limit_state["request_counts"]:
        _rate_limit_state["request_counts"][provider] = {"minute": 0, "hour": 0}
        _rate_limit_state["last_reset"][provider] = {"minute": current_time, "hour": current_time}
        _rate_limit_state["active_requests"][provider] = 0
    
    # Reset counters if time windows have passed
    state = _rate_limit_state["request_counts"][provider]
    last_reset = _rate_limit_state["last_reset"][provider]
    
    if current_time - last_reset["minute"] >= 60:
        state["minute"] = 0
        last_reset["minute"] = current_time
    
    if current_time - last_reset["hour"] >= 3600:
        state["hour"] = 0
        last_reset["hour"] = current_time
    
    # Increment counters
    state["minute"] += 1
    state["hour"] += 1


async def _rate_limited_request(provider: str, llm_client: BaseChatModel, messages, max_retries: int = None):
    """
    Make a rate-limited request to the LLM client.
    Handles retries with exponential backoff for rate limit errors.
    """
    if provider not in RATE_LIMIT_CONFIG:
        # No rate limiting for unknown providers
        return await llm_client.ainvoke(messages)
    
    config = RATE_LIMIT_CONFIG[provider]
    if max_retries is None:
        max_retries = config["max_retries"]
    
    retry_count = 0
    retry_delay = config["retry_delay"]
    
    while retry_count <= max_retries:
        # Check rate limit before making request
        if not _check_rate_limit(provider):
            if retry_count < max_retries:
                print(f"Rate limit exceeded for {provider}, waiting {retry_delay}s before retry {retry_count + 1}/{max_retries}")
                await asyncio.sleep(retry_delay)
                retry_delay *= config["backoff_multiplier"]
                retry_count += 1
                continue
            else:
                raise RuntimeError(f"Rate limit exceeded for {provider} after {max_retries} retries")
        
        try:
            # Make the request
            _increment_rate_limit(provider)
            result = await llm_client.ainvoke(messages)
            return result
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                if retry_count < max_retries:
                    print(f"Rate limit error for {provider}: {e}")
                    print(f"Retrying in {retry_delay}s (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= config["backoff_multiplier"]
                    retry_count += 1
                    continue
                else:
                    raise RuntimeError(f"Rate limit exceeded for {provider} after {max_retries} retries: {e}")
            else:
                # Non-rate-limit error, don't retry
                raise e
    
    raise RuntimeError(f"Unexpected error in rate-limited request for {provider}")


def create_llm_client(provider: str, model: str) -> BaseChatModel:
    """
    Factory function to create an LLM client based on the provider string from config.
    It checks if the required LangChain integration is available and attempts
    to instantiate the chat model with rate limiting.
    """
    # Handle dummy provider for testing
    if provider == "dummy":
        from unittest.mock import MagicMock, AsyncMock
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "> look"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        return mock_llm

    llm_class = LLM_PROVIDER_MAP.get(provider)

    if not llm_class:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Available providers are: {list(LLM_PROVIDER_MAP.keys())}. "
            "Ensure the necessary 'langchain-xxx' package is installed "
            f"and '{provider}' is added to LLM_PROVIDER_MAP in llm_factory.py."
        )

    if llm_class is None: # This means the import failed
         raise ImportError(
            f"The LangChain integration for '{provider}' could not be imported. "
            f"Please ensure `langchain-{provider.lower()}` is installed (e.g., `pip install langchain-openai`)."
         )

    try:
        # Most chat models accept 'model' and 'temperature'
        base_llm = llm_class(model=model, temperature=0.7)
        
        # Create a rate-limited wrapper
        class RateLimitedLLM:
            def __init__(self, base_llm, provider):
                self.base_llm = base_llm
                self.provider = provider
                # Copy other attributes from base_llm
                for attr in dir(base_llm):
                    if not attr.startswith('_') and not callable(getattr(base_llm, attr)):
                        setattr(self, attr, getattr(base_llm, attr))
            
            async def ainvoke(self, messages, **kwargs):
                return await _rate_limited_request(self.provider, self.base_llm, messages)
            
            def invoke(self, messages, **kwargs):
                # For synchronous calls, we'll need to handle this differently
                # For now, just call the base method
                return self.base_llm.invoke(messages, **kwargs)
        
        return RateLimitedLLM(base_llm, provider)
        
    except Exception as e:
        raise RuntimeError(
            f"Failed to instantiate LLM for provider '{provider}' with model '{model}'. "
            f"Error: {e}. Check API key or model name."
        ) from e
