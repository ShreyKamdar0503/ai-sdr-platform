"""Shared helpers for agents.

This codebase intentionally mixes:
- Deterministic rules (preferred for reliability)
- LLM assistance (preferred for summarization & recommendations)

Agents should:
1) Read state / inputs
2) Produce decisions or structured outputs
3) Hand off execution to n8n / adapters

Now with GrowthBook integration for:
- Feature flags (enable/disable agents)
- A/B experiments (test variants)
- Dynamic configs (adjust parameters)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore


@dataclass
class AgentRunContext:
    workspace_id: str
    config: Dict[str, Any]
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None  # For experiment assignment


class BaseAgent:
    """Base class with optional LLM wiring and GrowthBook integration."""

    # Feature flag key for this agent (override in subclass)
    feature_flag_key: Optional[str] = None
    
    # Dynamic config key for this agent (override in subclass)
    config_key: Optional[str] = None

    def __init__(self, model: Optional[str] = None, temperature: float = 0.2):
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self._llm: Optional[ChatOpenAI] = None
        self._gb_client = None

    @property
    def llm(self) -> ChatOpenAI:
        if ChatOpenAI is None:  # pragma: no cover
            raise RuntimeError(
                "langchain_openai is not installed. Install dependencies or avoid LLM calls."
            )
        if self._llm is None:
            self._llm = ChatOpenAI(model=self.model, temperature=self.temperature)
        return self._llm

    @property
    def growthbook(self):
        """Get GrowthBook client for feature flags and configs"""
        if self._gb_client is None:
            try:
                from mcp_servers.growthbook_mcp import get_growthbook_client
                self._gb_client = get_growthbook_client()
            except ImportError:
                # Fallback: return a mock that always returns True/default
                self._gb_client = _MockGrowthBook()
        return self._gb_client

    async def should_run(self, context: Optional[AgentRunContext] = None) -> bool:
        """Check if this agent is enabled via feature flag"""
        if not self.feature_flag_key:
            return True  # No feature flag defined, always run
        
        attributes = {}
        if context:
            attributes["workspace_id"] = context.workspace_id
            if context.user_id:
                attributes["user_id"] = context.user_id
        
        return self.growthbook.is_on(self.feature_flag_key, attributes)

    def get_config(self, key: Optional[str] = None, default: Optional[Dict] = None) -> Dict[str, Any]:
        """Get dynamic configuration for this agent"""
        config_key = key or self.config_key
        if not config_key:
            return default or {}
        
        return self.growthbook.get_config_value(config_key, default or {})

    def get_experiment_variant(
        self,
        experiment_key: str,
        user_id: str,
        attributes: Optional[Dict] = None,
    ) -> Optional[str]:
        """Get the variant for a user in an A/B experiment"""
        return self.growthbook.get_experiment_variant(experiment_key, user_id, attributes)

    async def _llm_json(self, system: str, user: str) -> Dict[str, Any]:
        """Best-effort JSON helper.

        For production: replace with a structured output parser / JSON schema.
        """
        msg = await self.llm.ainvoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        text = getattr(msg, "content", "")
        # Naive parse to keep dependencies light.
        # Production: use pydantic/structured output.
        import json

        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    async def run_with_feature_check(
        self,
        run_func,
        context: Optional[AgentRunContext] = None,
        *args,
        **kwargs
    ):
        """
        Wrapper to run agent logic with feature flag check.
        
        Usage:
            result = await agent.run_with_feature_check(
                agent.process,
                context,
                lead_data
            )
        """
        if not await self.should_run(context):
            return {
                "status": "skipped",
                "reason": f"Feature flag '{self.feature_flag_key}' is disabled",
                "agent": self.__class__.__name__,
            }
        
        return await run_func(*args, **kwargs)


class _MockGrowthBook:
    """Mock GrowthBook client for when the real one isn't available"""
    
    def is_on(self, key: str, attributes: Optional[Dict] = None) -> bool:
        return True  # Default to enabled
    
    def get_feature_value(self, key: str, default: Any = None, attributes: Optional[Dict] = None) -> Any:
        return default
    
    def get_config_value(self, key: str, default: Optional[Dict] = None) -> Dict:
        return default or {}
    
    def get_experiment_variant(self, key: str, user_id: str, attributes: Optional[Dict] = None) -> Optional[str]:
        return "control"  # Default to control group