from typing import Type
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
}

# Mapping of provider names to their typical API key environment variable names
# THIS IS THE DICTIONARY THAT WAS MISSING
PROVIDER_API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    # Add other provider API keys here
    # "cohere": "COHERE_API_KEY",
}


def create_llm_client(provider: str, model: str) -> BaseChatModel:
    """
    Factory function to create an LLM client based on the provider string from config.
    It checks if the required LangChain integration is available and attempts
    to instantiate the chat model.
    """
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
        return llm_class(model=model, temperature=0.7)
    except Exception as e:
        raise RuntimeError(
            f"Failed to instantiate LLM for provider '{provider}' with model '{model}'. "
            f"Error: {e}. Check API key or model name."
        ) from e
