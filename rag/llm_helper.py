"""
Simple helper to get the configured LLM provider.

This makes it easy to get the right provider (Gemini or ASU AI) 
based on your configuration without manual checking.

Usage:
    from rag.llm_helper import get_llm_provider
    
    provider = get_llm_provider()
    response = await provider.generate_content("Your prompt")
"""
from config import LLM_PROVIDER, ASU_AI_ENABLED


def get_llm_provider():
    """
    Get the configured LLM provider based on settings.
    
    Returns:
        ASUAIProvider or raises ImportError if Gemini is selected
        
    Raises:
        ImportError: If trying to use Gemini (not implemented in this helper)
        ValueError: If configuration is invalid
    """
    if LLM_PROVIDER == "asu_ai" or ASU_AI_ENABLED:
        from rag.asu_ai_provider import ASUAIProvider
        return ASUAIProvider()
    elif LLM_PROVIDER == "gemini":
        raise ImportError(
            "Gemini provider requested but this helper only supports ASU AI. "
            "Use the existing resume_parser.py implementation for Gemini."
        )
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def get_provider_name():
    """
    Get the name of the currently configured provider.
    
    Returns:
        str: "ASU AI" or "Gemini"
    """
    if LLM_PROVIDER == "asu_ai" or ASU_AI_ENABLED:
        return "ASU AI"
    elif LLM_PROVIDER == "gemini":
        return "Gemini"
    else:
        return f"Unknown ({LLM_PROVIDER})"


async def ask_llm(prompt: str, model: str = None) -> str:
    """
    Convenience function to ask a question to the configured LLM.
    
    Args:
        prompt: Your question or prompt
        model: Optional model override
        
    Returns:
        str: The LLM's response
        
    Example:
        response = await ask_llm("What is Python?")
        print(response)
    """
    provider = get_llm_provider()
    return await provider.generate_content(prompt, model)


# Synchronous wrapper for non-async contexts
def ask_llm_sync(prompt: str, model: str = None) -> str:
    """
    Synchronous version of ask_llm for use in non-async code.
    
    Args:
        prompt: Your question or prompt
        model: Optional model override
        
    Returns:
        str: The LLM's response
        
    Example:
        response = ask_llm_sync("What is Python?")
        print(response)
    """
    provider = get_llm_provider()
    return provider.generate_content_sync(prompt, model)
