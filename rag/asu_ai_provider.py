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
        import concurrent.futures
        
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.generate_content(prompt, model))
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(_run).result()
    
    
    def generate_embedding(
        self,
        text: str,
        model: str = "te3s",  # ASU AI abbreviation for text-embedding-3-small
        provider: str = "openai",
        dimensions: Optional[int] = 1024
    ) -> List[float]:
        """
        Generate embedding vector using ASU AI /embeddings endpoint.
        
        Uses synchronous requests library (ASU AI server returns 500 with aiohttp).
        
        Args:
            text: Text to embed
            model: Embeddings model name
            provider: Embeddings provider (default: "openai")
            dimensions: Embedding dimensions (default: 1024)
            
        Returns:
            Embedding vector as list of floats
        """
        import requests
        import time
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": text,
            "embeddings_provider": provider,
            "embeddings_model": model
        }
        
        if dimensions:
            payload["dimensions"] = dimensions
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                # Parse response - try common embedding response formats
                if "response" in result:
                    return result["response"]
                elif "embeddings" in result:
                    return result["embeddings"]
                elif "embedding" in result:
                    return result["embedding"]
                elif "data" in result and len(result["data"]) > 0:
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
                elif e.response.status_code >= 500 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 0.5
                    print(f"[ASU AI] Server error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise
            except requests.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 0.5
                    print(f"[ASU AI] Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise
    
    def generate_embedding_sync(self, text: str, model: str = "te3s", provider: str = "openai", dimensions: Optional[int] = 1024) -> List[float]:
        """Synchronous wrapper for generate_embedding (already synchronous)."""
        return self.generate_embedding(text, model, provider, dimensions)
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        model: str = "te3s",
        provider: str = "openai",
        dimensions: Optional[int] = 1024,
        max_workers: int = 5
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in parallel using ThreadPoolExecutor.
        
        Args:
            texts: List of texts to embed
            model: Embeddings model name
            provider: Embeddings provider
            dimensions: Embedding dimensions
            max_workers: Number of parallel workers
            
        Returns:
            List of embedding vectors (same order as input texts)
        """
        import concurrent.futures
        
        if not texts:
            return []
        
        def _embed_single(text):
            return self.generate_embedding(text, model, provider, dimensions)
        
        embeddings = [None] * len(texts)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(_embed_single, text): i 
                for i, text in enumerate(texts)
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    embeddings[idx] = future.result()
                except Exception as e:
                    print(f"[ASU AI] Warning: embedding failed for text {idx}: {e}")
                    # Use None as fallback - callers should handle this
                    embeddings[idx] = None
        
        # Replace any None embeddings with zero vectors (same dimension as first valid one)
        valid = next((e for e in embeddings if e is not None), None)
        if valid is not None:
            dim = len(valid)
            embeddings = [e if e is not None else [0.0] * dim for e in embeddings]
        
        return embeddings
    
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
