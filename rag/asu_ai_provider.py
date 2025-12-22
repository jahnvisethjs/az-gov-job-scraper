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
        
        Uses nest_asyncio to handle Streamlit's existing event loop.
        
        Args:
            prompt: Input prompt for the model
            model: Optional model override
            
        Returns:
            Generated text response
        """
        import nest_asyncio
        nest_asyncio.apply()
        
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running (like in Streamlit), create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    lambda: asyncio.run(self.generate_content(prompt, model))
                ).result()
        else:
            return asyncio.run(self.generate_content(prompt, model))
    
    
    def generate_embedding(
        self,
        text: str,
        model: str = "te3s",  # ASU AI abbreviation for text-embedding-3-small
        provider: str = "openai",
        dimensions: Optional[int] = 1024
    ) -> List[float]:
        """
        Generate embedding vector using ASU AI /embeddings endpoint.
        
        NOTE: Uses synchronous requests library instead of aiohttp because
        ASU AI server returns 500 errors with aiohttp async requests.
        
        Uses ASU AI Platform embeddings API as documented:
        POST /embeddings
        {
            "query": "text to embed",
            "embeddings_provider": "openai",
            "embeddings_model": "text-embedding-3-small",
            "dimensions": 1024
        }
        
        Args:
            text: Text to embed
            model: Embeddings model name (default: "text-embedding-3-small")
            provider: Embeddings provider (default: "openai")
            dimensions: Embedding dimensions (default: 1024, OpenAI models support this)
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If the response format is unexpected
        """
        import requests
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build payload according to ASU AI embeddings API spec
        payload = {
            "query": text,
            "embeddings_provider": provider,
            "embeddings_model": model
        }
        
        # Add dimensions if specified (OpenAI te3s/te3l support this)
        if dimensions:
            payload["dimensions"] = dimensions
        
        try:
            import logging
            logging.basicConfig(level=logging.DEBUG)
            logger = logging.getLogger(__name__)
            
            logger.info(f"Making embedding request to {url}")
            logger.info(f"Payload: {payload}")
            logger.info(f"Using requests library (not aiohttp)")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()

            
            # Parse response - try common embedding response formats
            if "response" in result:
                # ASU AI format: {"response": [...]}
                return result["response"]
            elif "embeddings" in result:
                # Format: {"embeddings": [...]}
                return result["embeddings"]
            elif "embedding" in result:
                # Format: {"embedding": [...]}
                return result["embedding"]
            elif "data" in result and len(result["data"]) > 0:
                # OpenAI-style format: {"data": [{"embedding": [...]}]}
                if isinstance(result["data"], list) and "embedding" in result["data"][0]:
                    return result["data"][0]["embedding"]
            else:
                raise ValueError(f"Unexpected embedding response format: {result}")
                
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(
                    f"ASU AI embeddings endpoint not found at {url}. "
                    "Verify the endpoint is available and the base URL is correct."
                )
            elif e.response.status_code == 401:
                raise ValueError("ASU AI API authentication failed. Check your API key.")
            elif e.response.status_code == 400:
                raise ValueError(f"Bad request to ASU AI embeddings API: {e.response.text}")
            raise
    
    def generate_embedding_sync(self, text: str, model: str = "te3s", provider: str = "openai", dimensions: Optional[int] = 1024) -> List[float]:
        """
        Synchronous wrapper for generate_embedding.
        
        Since generate_embedding is already synchronous, this just calls it directly.
        
        Args:
            text: Text to embed
            model: Embeddings model abbreviation
            provider: Embeddings provider
            dimensions: Embedding dimensions
            
        Returns:
            Embedding vector
        """
        return self.generate_embedding(text, model, provider, dimensions)
    
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
