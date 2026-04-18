from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_chat_model(provider: str | None = None, **kwargs: object) -> ChatOpenAI:
    """Return a LangChain ChatModel for the specified provider.

    Both Nebius AI and OpenRouter expose OpenAI-compatible APIs,
    so ChatOpenAI works for both with different base_url/api_key.
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER

    if provider == "nebius":
        return ChatOpenAI(
            model=settings.NEBIUS_MODEL,
            openai_api_key=settings.NEBIUS_API_KEY,
            openai_api_base=settings.NEBIUS_BASE_URL,
            **kwargs,
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
