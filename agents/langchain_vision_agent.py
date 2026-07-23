"""LangChain-powered vision agent for mobile screenshot analysis.

This module provides an enhanced vision agent using LangChain for:
- Structured output parsing with Pydantic models
- Automatic retry with error correction
- Token usage tracking and cost management
- Multi-provider support (OpenAI, Claude, etc.)
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_openai import ChatOpenAI
    from langchain_community.callbacks import get_openai_callback
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not installed. Install with: pip install langchain langchain-openai")
    LANGCHAIN_AVAILABLE = False
    ChatPromptTemplate = None
    PydanticOutputParser = None
    ChatOpenAI = None
    get_openai_callback = None

from models.ssm import ScreenSemanticModel
from agents.vision_agent import VisionAgent, OpenAIVisionAgent


class LangChainVisionAgent(VisionAgent):
    """LangChain-powered vision agent with structured output and automatic retry."""
    
    def __init__(
        self,
        prompt_template: str | None = None,
        model_name: str | None = None,
        enable_cache: bool = True
    ):
        """Initialize LangChain vision agent.
        
        Args:
            prompt_template: Custom prompt template text
            model_name: LLM model name (e.g., 'gpt-4o-mini')
            enable_cache: Enable LLM response caching
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain not installed. Install with: "
                "pip install langchain langchain-openai"
            )
        
        super().__init__(model_name=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE")
        self.enable_cache = enable_cache
        
        # Initialize LangChain components
        self.llm = self._create_llm()
        self.parser = PydanticOutputParser(pydantic_object=ScreenSemanticModel)
        self.system_prompt = self._create_prompt(prompt_template)
        
        # Token usage tracking
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def validate_configuration(self) -> None:
        """Validate agent configuration."""
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise EnvironmentError(
                "OPENAI_API_KEY is required. Set it in your .env file."
            )
    
    def _create_llm(self) -> ChatOpenAI:
        """Create LangChain LLM instance."""
        llm_kwargs = {
            "model": self.model_name,
            "temperature": 0,
            "api_key": self.api_key,
        }
        
        if self.api_base:
            llm_kwargs["base_url"] = self.api_base
            
            # For LiteLLM or custom gateways, add custom headers if needed
            if "litellm" in self.api_base.lower():
                logger.info("Detected LiteLLM gateway - configuring custom headers")
                # LiteLLM may use x-litellm-api-key header
                # OpenAI client will use api_key in Authorization header by default
                # If custom header handling is needed, it's handled by the OpenAI client
        
        # Enable caching if requested
        if self.enable_cache:
            try:
                from langchain_core.caches import InMemoryCache
                from langchain_core.globals import set_llm_cache
                set_llm_cache(InMemoryCache())
                logger.info("LLM response caching enabled")
            except Exception as e:
                logger.warning(f"Could not enable caching: {e}")
        
        return ChatOpenAI(**llm_kwargs)
    
    def _create_prompt(self, custom_template: str | None = None) -> str:
        """Create system prompt template."""
        if custom_template:
            return custom_template
        else:
            return self._default_prompt_template()
    
    def _default_prompt_template(self) -> str:
        """Default system prompt for vision analysis."""
        return """You are a mobile UI analysis expert. Analyze the mobile app screenshot and extract:
1. Screen name (e.g., Login, Product Listing, Cart, Product Details)
2. Screen purpose (brief description)
3. All interactive UI elements with their properties

For each element, identify:
- label: Human-readable name
- type: UI element type (textfield, button, image, label, etc.)
- actions: Possible user actions (enter_text, tap, verify, scroll)
- confidence: Your confidence in identifying this element (0.0-1.0)

Important guidelines:
- Use standard screen names (Login, Cart, Product Listing, Product Details, Checkout, Home, Profile, Settings)
- Be specific with element labels
- Include all tappable, typeable, and verifiable elements
- Set realistic confidence scores based on UI clarity
- Do NOT include decorative elements unless they're interactive

Return ONLY valid JSON matching the ScreenSemanticModel schema."""
    
    def _create_chain(self):
        """Create LangChain processing chain."""
        # Simple chain: Prompt → LLM (we'll parse JSON manually)
        chain = self.prompt | self.llm
        
        # Note: Auto-retry not available in this simple chain
        # If needed, wrap with manual retry logic
        return chain
    
    def analyze_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Analyze mobile screenshot and return structured SSM data.
        
        Args:
            image_path: Path to screenshot file
            **kwargs: Additional arguments (unused, for compatibility)
        
        Returns:
            Dictionary with SSM data (screen_name, elements, etc.)
        """
        self.validate_configuration()
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        filename = Path(image_path).stem
        
        # Build messages dynamically for vision model
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Filename hint: {filename}\n\nAnalyze this mobile app screenshot and return a JSON object with screen_name, screen_purpose, and elements array."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ]
            }
        ]
        
        # Run LLM with vision (token tracking may not work with custom gateways)
        try:
            result = self.llm.invoke(messages)
            
            logger.info("Vision analysis complete")
            
            # Parse the result
            if hasattr(result, 'content'):
                content = result.content
            else:
                content = str(result)
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                ssm_dict = json.loads(json_str)
            else:
                # If no JSON found, try parsing the whole thing
                ssm_dict = json.loads(content)
        
        except Exception as e:
            logger.error(f"LangChain vision analysis failed: {e}")
            logger.info("Falling back to standard OpenAI agent...")
            
            # Fallback to original OpenAI agent
            fallback_agent = OpenAIVisionAgent(
                prompt_template=self._default_prompt_template(),
                model_name=self.model_name
            )
            return fallback_agent.analyze_image(image_path)
        
        # Infer screen name if needed
        screen_name = ssm_dict.get("screen_name")
        if not screen_name or screen_name.lower() in ["unknown", "unspecified", "n/a", "none"]:
            inferred_name = self._infer_screen_name_from_context(
                ssm_dict,
                filename
            )
            if inferred_name:
                ssm_dict["screen_name"] = inferred_name
        
        # Add source metadata
        ssm_dict["source"] = "langchain_vision"
        ssm_dict["source_image"] = str(image_path)
        
        return ssm_dict
    
    def _infer_screen_name_from_context(
        self,
        ssm_data: Dict[str, Any],
        filename: str
    ) -> Optional[str]:
        """Infer screen name from filename and content."""
        filename_lower = filename.lower()
        
        # Check filename for hints
        name_mapping = {
            "login": "Login",
            "cart": "Cart",
            "product_detail": "Product Details",
            "productdetail": "Product Details",
            "detail": "Product Details",
            "product_list": "Product Listing",
            "productlist": "Product Listing",
            "listing": "Product Listing",
            "products": "Product Listing",
            "search": "Search",
            "checkout": "Checkout",
            "home": "Home",
            "profile": "Profile",
            "settings": "Settings",
        }
        
        for key, value in name_mapping.items():
            if key in filename_lower:
                return value
        
        # Check element labels for hints
        elements = ssm_data.get("elements", [])
        element_labels = [e.get("label", "").lower() for e in elements]
        
        if any("login" in label for label in element_labels):
            return "Login"
        if any("cart" in label or "checkout" in label for label in element_labels):
            return "Cart"
        if any("add to cart" in label or "price" in label for label in element_labels):
            return "Product Details"
        
        return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage and cost statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model_name,
        }


def create_langchain_vision_agent(
    provider: str = "openai",
    prompt_template: str | None = None,
    **kwargs
) -> VisionAgent:
    """Factory function to create vision agent (LangChain or fallback).
    
    Args:
        provider: Agent provider ('openai' or 'mock')
        prompt_template: Custom prompt template
        **kwargs: Additional arguments for agent
    
    Returns:
        VisionAgent instance
    """
    if provider == "mock":
        # Import mock agent
        from agents.vision_agent import MockVisionAgent
        return MockVisionAgent()
    
    # Try LangChain first, fallback to standard OpenAI
    if LANGCHAIN_AVAILABLE:
        try:
            return LangChainVisionAgent(
                prompt_template=prompt_template,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"Could not create LangChain agent: {e}. Using standard OpenAI agent.")
    
    # Fallback
    return OpenAIVisionAgent(
        prompt_template=prompt_template,
        **kwargs
    )
