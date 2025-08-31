"""
Multi-model support for Terminus CLI.
Supports Google Gemini and Ollama local models with automatic fallback.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp

from terminus.core.session import session as session_state
from terminus import ui
from terminus.core.config import update_config_file, ensure_config_structure

log = logging.getLogger(__name__)


class ModelProvider(Enum):
    GOOGLE = "google"
    OLLAMA = "ollama"


@dataclass
class ModelInfo:
    name: str
    provider: ModelProvider
    display_name: str
    context_length: int = 8192
    available: bool = True
    local: bool = False


class ModelManager:
    """Manages multiple AI model providers with automatic fallback."""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.current_model: Optional[str] = None
        self.offline_mode: bool = False
        self._ollama_available: Optional[bool] = None
        self._google_available: Optional[bool] = None
        
    async def initialize(self):
        """Initialize model manager and detect available models."""
        await self._detect_models()
        self._load_model_preferences()
        
    async def _detect_models(self):
        """Detect available models from different providers."""
        # Google Gemini models
        google_models = {
            "google-gla:gemini-2.0-flash-exp": ModelInfo(
                name="google-gla:gemini-2.0-flash-exp",
                provider=ModelProvider.GOOGLE,
                display_name="Gemini 2.0 Flash (Experimental)",
                context_length=1000000,
                local=False
            ),
            "google:gemini-1.5-pro": ModelInfo(
                name="google:gemini-1.5-pro",
                provider=ModelProvider.GOOGLE,
                display_name="Gemini 1.5 Pro",
                context_length=2000000,
                local=False
            )
        }
        
        # Check Google API availability
        self._google_available = await self._check_google_availability()
        for model in google_models.values():
            model.available = self._google_available
            
        self.models.update(google_models)
        
        # Ollama models
        ollama_models = await self._detect_ollama_models()
        self.models.update(ollama_models)
        
    async def _check_google_availability(self) -> bool:
        """Check if Google API is available."""
        try:
            config = ensure_config_structure()
            api_key = config.get("env", {}).get("GEMINI_API_KEY")
            if not api_key:
                return False
                
            # Quick test with minimal request
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": api_key},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            log.debug(f"Google API check failed: {e}")
            return False
            
    async def _detect_ollama_models(self) -> Dict[str, ModelInfo]:
        """Detect available Ollama models."""
        ollama_models = {}
        
        try:
            # Check if Ollama is running
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:11434/api/tags",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._ollama_available = True
                        
                        for model_data in data.get("models", []):
                            model_name = model_data["name"]
                            ollama_models[f"ollama:{model_name}"] = ModelInfo(
                                name=f"ollama:{model_name}",
                                provider=ModelProvider.OLLAMA,
                                display_name=f"Ollama: {model_name}",
                                context_length=4096,  # Default for most models
                                available=True,
                                local=True
                            )
                    else:
                        self._ollama_available = False
        except Exception as e:
            log.debug(f"Ollama detection failed: {e}")
            self._ollama_available = False
            
        return ollama_models
        
    def _load_model_preferences(self):
        """Load model preferences from config."""
        try:
            config = ensure_config_structure()
            default_model = config.get("default_model", "google-gla:gemini-2.0-flash-exp")
        except Exception:
            default_model = "google-gla:gemini-2.0-flash-exp"
        
        # Set current model if available
        if default_model in self.models and self.models[default_model].available:
            self.current_model = default_model
        else:
            # Fallback logic
            self.current_model = self._get_best_available_model()
            
    def _get_best_available_model(self) -> Optional[str]:
        """Get the best available model based on preferences."""
        # Priority: Google > Ollama
        available_models = [name for name, info in self.models.items() if info.available]
        
        if not available_models:
            return None
            
        # Prefer Google models
        google_models = [name for name in available_models 
                        if self.models[name].provider == ModelProvider.GOOGLE]
        if google_models:
            return google_models[0]
            
        # Fallback to Ollama
        ollama_models = [name for name in available_models 
                        if self.models[name].provider == ModelProvider.OLLAMA]
        if ollama_models:
            return ollama_models[0]
            
        return available_models[0]
        
    async def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        if model_name not in self.models:
            ui.error(f"Model '{model_name}' not found")
            return False
            
        if not self.models[model_name].available:
            ui.error(f"Model '{model_name}' is not available")
            return False
        
        old_model = self.current_model
        self.current_model = model_name
        
        # Update global session state (import the instance, not the module)
        session_state.current_model = model_name
        
        # Update config file 
        try:
            update_config_file({"default_model": model_name})
            log.debug(f"Updated config with new model: {model_name}")
        except Exception as e:
            log.error(f"Failed to update config: {e}")
        
        ui.success(f"Switched from {old_model} to {model_name}")
        return True
        
    def list_models(self) -> List[ModelInfo]:
        """List all available models."""
        return list(self.models.values())
        
    def get_current_model(self) -> Optional[ModelInfo]:
        """Get current model info."""
        if self.current_model:
            return self.models.get(self.current_model)
        return None
        
    async def auto_fallback(self) -> bool:
        """Automatically fallback to local model if API fails."""
        if self._ollama_available and self.current_model:
            current_info = self.models[self.current_model]
            
            # If current model is online and we have local alternatives
            if not current_info.local:
                local_models = [name for name, info in self.models.items() 
                               if info.available and info.local]
                
                if local_models:
                    await self.switch_model(local_models[0])
                    ui.warning("API unavailable - switched to local model")
                    return True
                    
        return False


# Global model manager instance
model_manager = ModelManager()
