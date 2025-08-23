"""
Ollama integration for Terminus CLI.
Provides local AI model support with automatic fallback.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
import aiohttp

log = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama local AI models."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=60)
        
    async def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/version") as response:
                    return response.status == 200
        except Exception as e:
            log.debug(f"Ollama availability check failed: {e}")
            return False
            
    async def list_models(self) -> List[Dict]:
        """List available Ollama models."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    return []
        except Exception as e:
            log.error(f"Failed to list Ollama models: {e}")
            return []
            
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model from Ollama registry."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                payload = {"name": model_name}
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        # Stream the pull progress
                        async for line in response.content:
                            try:
                                progress = json.loads(line.decode())
                                if "status" in progress:
                                    print(f"Pull progress: {progress['status']}")
                            except json.JSONDecodeError:
                                continue
                        return True
                    return False
        except Exception as e:
            log.error(f"Failed to pull model {model_name}: {e}")
            return False
            
    async def generate(self, model: str, prompt: str, system: str = None) -> Optional[str]:
        """Generate text using Ollama model."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if system:
                payload["system"] = system
                
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response")
                    else:
                        log.error(f"Ollama generate failed: {response.status}")
                        return None
        except Exception as e:
            log.error(f"Failed to generate with Ollama: {e}")
            return None
            
    async def generate_stream(self, model: str, prompt: str, system: str = None) -> AsyncGenerator[str, None]:
        """Generate text using Ollama model with streaming."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True
            }
            
            if system:
                payload["system"] = system
                
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            try:
                                chunk = json.loads(line.decode())
                                if "response" in chunk:
                                    yield chunk["response"]
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            log.error(f"Failed to stream generate with Ollama: {e}")
            
    async def chat(self, model: str, messages: List[Dict]) -> Optional[str]:
        """Chat with Ollama model using conversation format."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("message", {}).get("content")
                    else:
                        log.error(f"Ollama chat failed: {response.status}")
                        return None
        except Exception as e:
            log.error(f"Failed to chat with Ollama: {e}")
            return None


class OllamaManager:
    """Manages Ollama integration and model recommendations."""
    
    def __init__(self):
        self.client = OllamaClient()
        self.recommended_models = [
            "llama3.2:3b",     # Fast, lightweight
            "codellama:7b",    # Code-focused
            "mistral:7b",      # Good general purpose
            "phi3:3.8b",       # Microsoft's small model
            "qwen2.5:7b",      # Good multilingual
        ]
        
    async def setup_ollama(self) -> bool:
        """Set up Ollama with recommended models."""
        if not await self.client.is_available():
            return False
            
        models = await self.client.list_models()
        installed_models = [m["name"] for m in models]
        
        # Check if we have any models installed
        if not installed_models:
            print("No Ollama models found. Recommending installation...")
            print("Recommended models:")
            for i, model in enumerate(self.recommended_models, 1):
                print(f"{i}. {model}")
                
            # For now, just return True - actual installation would be interactive
            return True
            
        return True
        
    async def get_best_available_model(self) -> Optional[str]:
        """Get the best available Ollama model."""
        if not await self.client.is_available():
            return None
            
        models = await self.client.list_models()
        if not models:
            return None
            
        # Prefer recommended models
        for recommended in self.recommended_models:
            for model in models:
                if recommended in model["name"]:
                    return model["name"]
                    
        # Fallback to first available model
        return models[0]["name"] if models else None


# Global Ollama manager
ollama = OllamaManager()
