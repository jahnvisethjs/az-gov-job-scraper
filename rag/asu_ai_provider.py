"""
ASU AI Platform provider for LLM functionalities (chat completions and embeddings).

This module provides integration with the ASU AI Platform API (CreateAI) 
for resume parsing, job matching, and other AI-powered features.

API Response Format:
{
    "response": "The actual text response from the model",
    "metadata": {
        "query_id": "unique_query_identifier",
        "usage_metric": {
            "input_token_count": 30,
            "output_token_count": 10,
            "input_token_cost": 0.00006,
            "output_token_cost": 0.00002
        }
    }
}
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
from config import ASU_AI_API_KEY, ASU_AI_BASE_URL, ASU_AI_MODEL


class ASUAIProvider:
    """
    ASU AI Platform API client for text generation and embeddings.
    
    Features:
    - Async text generation via /query endpoint
    - Support for multiple models (GPT-4, GPT-4o-mini, Claude, etc.)
    - Token usage tracking via metadata
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        Initialize ASU AI provider.
        
        Args:
            api_key: ASU AI API token (defaults to config.ASU_AI_API_KEY)
            base_url: API base URL (defaults to config.ASU_AI_BASE_URL)
            model: Model to use (defaults to config.ASU_AI_MODEL)
        """
        self.api_key = api_key or ASU_AI_API_KEY
        self.base_url = base_url or ASU_AI_BASE_URL
        self.model = model or ASU_AI_MODEL
        
        if not self.api_key:
            raise ValueError("ASU AI API key is required. Set ASU_AI_API_KEY environment variable.")
        
    async def generate_content(self, prompt: str, model: str = None) -> str:
        """
        Generate text content using the /query endpoint.
        
        Args:
            prompt: Input prompt for the model
            model: Optional model override (uses instance default if not specified)
            
        Returns:
            Generated text response
            
        Raises:
            aiohttp.ClientError: If the API request fails
            ValueError: If the response format is unexpected
        """
        url = f"{self.base_url}/query"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "model": model or self.model
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                result = await response.json()
                
                # ASU AI returns {"response": "...", "metadata": {...}}
                if "response" in result:
                    return result["response"]
                elif "message" in result:
                    # Error message format
                    raise ValueError(f"API error: {result['message']}")
                else:
                    raise ValueError(f"Unexpected response format: {result}")
    
    def generate_content_sync(self, prompt: str, model: str = None) -> str:
        """
        Synchronous wrapper for generate_content.
        
        Args:
            prompt: Input prompt for the model
            model: Optional model override
            
        Returns:
            Generated text response
        """
        return asyncio.run(self.generate_content(prompt, model))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector using /embeddings endpoint.
        
        Note: ASU AI Platform may have a dedicated embeddings endpoint.
        This is a placeholder implementation. Verify the actual endpoint format.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            NotImplementedError: If embeddings endpoint format is unknown
        """
        # TODO: Verify actual ASU AI embeddings endpoint format
        # The integration guide mentions /embeddings but we need to confirm the request/response format
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            # May need additional parameters like "model": "text-embedding-ada-002" or similar
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    # Common formats: {"embedding": [...]} or {"data": [{"embedding": [...]}]}
                    if "embedding" in result:
                        return result["embedding"]
                    elif "data" in result and len(result["data"]) > 0:
                        return result["data"][0].get("embedding", [])
                    else:
                        raise ValueError(f"Unexpected embedding response format: {result}")
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                # Embeddings endpoint might not be available
                raise NotImplementedError(
                    "ASU AI embeddings endpoint not available or has different format. "
                    "Consider using Gemini embeddings as fallback."
                )
            raise
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """
        Synchronous wrapper for generate_embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return asyncio.run(self.generate_embedding(text))
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = None) -> str:
        """
        Generate chat completion from messages (ChatGPT-style API).
        
        Args:
            messages: List of message dicts with "role" and "content" keys
                     Example: [{"role": "user", "content": "Hello"}]
            model: Optional model override
            
        Returns:
            Generated text response
        """
        # Convert messages to a single prompt
        # ASU AI /query endpoint uses "prompt" field, so we need to format messages
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return await self.generate_content(prompt, model)
    
    def get_usage_info(self) -> Dict:
        """
        Get API usage information.
        
        Note: The ASU AI API returns usage metrics in the response metadata.
        This method returns configuration info. For per-request usage, 
        parse the "metadata" field from the response.
        
        Returns:
            Dict with provider configuration
        """
        return {
            "provider": "ASU AI Platform",
            "base_url": self.base_url,
            "model": self.model,
            "has_api_key": bool(self.api_key)
        }
