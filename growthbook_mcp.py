"""
GrowthBook MCP Server - Feature Flags, A/B Testing & Dynamic Configs

Open-source alternative to Statsig for:
- Feature Flags (Gates): Enable/disable agents in production
- A/B Experiments: Test email variants, timing strategies
- Dynamic Configs: Adjust lead scoring, quality gates
- Stale Flag Detection: Remove deprecated agents/workflows

Based on: https://docs.growthbook.io
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


class FeatureStatus(str, Enum):
    """Feature flag status"""
    ACTIVE = "active"
    STALE = "stale"
    PERMANENT = "permanent"
    DRAFT = "draft"


class ExperimentStatus(str, Enum):
    """Experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    STOPPED = "stopped"
    ARCHIVED = "archived"


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    key: str
    description: str = ""
    enabled: bool = False
    default_value: Any = None
    rules: List[Dict] = field(default_factory=list)
    status: FeatureStatus = FeatureStatus.ACTIVE
    environment: str = "production"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_evaluated: Optional[datetime] = None
    
    def is_stale(self, days: int = 30) -> bool:
        """Check if flag hasn't been evaluated in X days"""
        if not self.last_evaluated:
            return True
        return (datetime.utcnow() - self.last_evaluated).days > days


@dataclass
class Experiment:
    """A/B Test experiment definition"""
    key: str
    name: str
    hypothesis: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variations: List[Dict] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    targeting_rules: List[Dict] = field(default_factory=list)
    traffic_percent: float = 100.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


@dataclass
class DynamicConfig:
    """Dynamic configuration object"""
    key: str
    description: str = ""
    value: Dict[str, Any] = field(default_factory=dict)
    rules: List[Dict] = field(default_factory=list)
    environment: str = "production"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class GrowthBookClient:
    """
    GrowthBook API Client for feature flags and experiments.
    
    Can operate in two modes:
    1. API Mode: Connect to self-hosted GrowthBook instance
    2. Local Mode: Use in-memory storage (for development/testing)
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        client_key: Optional[str] = None,
        local_mode: bool = False,
    ):
        self.api_url = api_url or os.getenv("GROWTHBOOK_API_URL", "http://localhost:3100")
        self.api_key = api_key or os.getenv("GROWTHBOOK_API_KEY")
        self.client_key = client_key or os.getenv("GROWTHBOOK_CLIENT_KEY")
        self.local_mode = local_mode or not self.api_key
        
        # Local storage for development mode
        self._features: Dict[str, FeatureFlag] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._configs: Dict[str, DynamicConfig] = {}
        self._evaluation_log: List[Dict] = []
        
        if self.local_mode:
            self._init_default_features()
    
    def _init_default_features(self):
        """Initialize default feature flags for SDR agents"""
        default_features = [
            FeatureFlag(
                key="enable_research_agent",
                description="Enable/disable Research Agent",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_copywriting_agent",
                description="Enable/disable Copywriting Agent",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_qualifier_agent",
                description="Enable/disable Qualifier Agent",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_timing_agent",
                description="Enable/disable Timing Optimizer Agent",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_negotiation_agent",
                description="Enable/disable Negotiation Agent (uAgents)",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_approval_agent",
                description="Enable/disable Approval Agent",
                enabled=True,
                default_value=True,
            ),
            FeatureFlag(
                key="enable_x402_payments",
                description="Enable x402 stablecoin payments",
                enabled=False,
                default_value=False,
            ),
        ]
        
        for feature in default_features:
            self._features[feature.key] = feature
        
        # Default dynamic configs
        default_configs = [
            DynamicConfig(
                key="lead_qualification_config",
                description="Lead scoring thresholds and parameters",
                value={
                    "min_qualification_score": 60,
                    "auto_approve_threshold": 90,
                    "research_quality_threshold": 70,
                    "max_cost_per_lead": 0.25,
                },
            ),
            DynamicConfig(
                key="negotiation_parameters",
                description="Agent negotiation settings",
                value={
                    "max_discount_percent": 15,
                    "min_agents_for_consensus": 2,
                    "budget_allocation_strategy": "quality_weighted",
                },
            ),
            DynamicConfig(
                key="email_generation_config",
                description="Email copywriting parameters",
                value={
                    "variants_count": 3,
                    "max_subject_length": 60,
                    "max_body_length": 200,
                    "tone": "professional",
                    "include_personalization": True,
                },
            ),
        ]
        
        for config in default_configs:
            self._configs[config.key] = config
    
    # ==================== Feature Flags ====================
    
    async def get_feature_flags(
        self,
        environment: str = "production",
        status: Optional[FeatureStatus] = None,
    ) -> List[Dict]:
        """Get all feature flags"""
        if self.local_mode:
            features = list(self._features.values())
            if status:
                features = [f for f in features if f.status == status]
            return [self._feature_to_dict(f) for f in features]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/features",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"environment": environment},
            )
            response.raise_for_status()
            return response.json().get("features", [])
    
    async def get_feature_flag(self, key: str) -> Optional[Dict]:
        """Get a specific feature flag"""
        if self.local_mode:
            feature = self._features.get(key)
            return self._feature_to_dict(feature) if feature else None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/features/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def create_feature_flag(
        self,
        key: str,
        description: str = "",
        enabled: bool = False,
        default_value: Any = None,
        rules: Optional[List[Dict]] = None,
    ) -> Dict:
        """Create a new feature flag"""
        feature = FeatureFlag(
            key=key,
            description=description,
            enabled=enabled,
            default_value=default_value,
            rules=rules or [],
        )
        
        if self.local_mode:
            self._features[key] = feature
            return self._feature_to_dict(feature)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/features",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "id": key,
                    "description": description,
                    "defaultValue": default_value,
                    "rules": rules or [],
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def update_feature_flag(
        self,
        key: str,
        enabled: Optional[bool] = None,
        default_value: Any = None,
        rules: Optional[List[Dict]] = None,
    ) -> Dict:
        """Update a feature flag"""
        if self.local_mode:
            if key not in self._features:
                raise ValueError(f"Feature flag '{key}' not found")
            
            feature = self._features[key]
            if enabled is not None:
                feature.enabled = enabled
            if default_value is not None:
                feature.default_value = default_value
            if rules is not None:
                feature.rules = rules
            feature.updated_at = datetime.utcnow()
            
            return self._feature_to_dict(feature)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.api_url}/api/v1/features/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "defaultValue": default_value,
                    "rules": rules,
                },
            )
            response.raise_for_status()
            return response.json()
    
    def is_on(self, key: str, attributes: Optional[Dict] = None) -> bool:
        """Check if a feature flag is enabled"""
        if self.local_mode:
            feature = self._features.get(key)
            if not feature:
                return False
            
            # Update last evaluated
            feature.last_evaluated = datetime.utcnow()
            self._log_evaluation(key, feature.enabled, attributes)
            
            # Check targeting rules
            if feature.rules and attributes:
                for rule in feature.rules:
                    if self._evaluate_rule(rule, attributes):
                        return rule.get("value", feature.enabled)
            
            return feature.enabled
        
        # For API mode, would need to call GrowthBook SDK
        return False
    
    def get_feature_value(self, key: str, default: Any = None, attributes: Optional[Dict] = None) -> Any:
        """Get the value of a feature flag"""
        if self.local_mode:
            feature = self._features.get(key)
            if not feature:
                return default
            
            feature.last_evaluated = datetime.utcnow()
            self._log_evaluation(key, feature.default_value, attributes)
            
            return feature.default_value if feature.default_value is not None else default
        
        return default
    
    async def get_stale_flags(self, days: int = 30) -> List[Dict]:
        """Get feature flags that haven't been evaluated recently"""
        if self.local_mode:
            stale = [f for f in self._features.values() if f.is_stale(days)]
            return [self._feature_to_dict(f) for f in stale]
        
        # For API mode, would need custom logic
        return []
    
    # ==================== Experiments ====================
    
    async def get_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
    ) -> List[Dict]:
        """Get all experiments"""
        if self.local_mode:
            experiments = list(self._experiments.values())
            if status:
                experiments = [e for e in experiments if e.status == status]
            return [self._experiment_to_dict(e) for e in experiments]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/experiments",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"status": status.value if status else None},
            )
            response.raise_for_status()
            return response.json().get("experiments", [])
    
    async def get_experiment(self, key: str) -> Optional[Dict]:
        """Get a specific experiment"""
        if self.local_mode:
            exp = self._experiments.get(key)
            return self._experiment_to_dict(exp) if exp else None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/experiments/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def create_experiment(
        self,
        key: str,
        name: str,
        hypothesis: str = "",
        variations: Optional[List[Dict]] = None,
        metrics: Optional[List[str]] = None,
        traffic_percent: float = 100.0,
    ) -> Dict:
        """Create a new A/B test experiment"""
        if not variations:
            variations = [
                {"key": "control", "name": "Control", "weight": 50},
                {"key": "treatment", "name": "Treatment", "weight": 50},
            ]
        
        experiment = Experiment(
            key=key,
            name=name,
            hypothesis=hypothesis,
            variations=variations,
            weights=[v.get("weight", 50) for v in variations],
            metrics=metrics or [],
            traffic_percent=traffic_percent,
        )
        
        if self.local_mode:
            self._experiments[key] = experiment
            return self._experiment_to_dict(experiment)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/experiments",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "trackingKey": key,
                    "name": name,
                    "hypothesis": hypothesis,
                    "variations": variations,
                    "metrics": metrics or [],
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def start_experiment(self, key: str) -> Dict:
        """Start an experiment"""
        if self.local_mode:
            if key not in self._experiments:
                raise ValueError(f"Experiment '{key}' not found")
            
            exp = self._experiments[key]
            exp.status = ExperimentStatus.RUNNING
            exp.started_at = datetime.utcnow()
            return self._experiment_to_dict(exp)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/experiments/{key}/start",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
    
    async def stop_experiment(self, key: str) -> Dict:
        """Stop an experiment"""
        if self.local_mode:
            if key not in self._experiments:
                raise ValueError(f"Experiment '{key}' not found")
            
            exp = self._experiments[key]
            exp.status = ExperimentStatus.STOPPED
            exp.ended_at = datetime.utcnow()
            return self._experiment_to_dict(exp)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/experiments/{key}/stop",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
    
    def get_experiment_variant(
        self,
        key: str,
        user_id: str,
        attributes: Optional[Dict] = None,
    ) -> Optional[str]:
        """Get the variant for a user in an experiment"""
        if self.local_mode:
            exp = self._experiments.get(key)
            if not exp or exp.status != ExperimentStatus.RUNNING:
                return None
            
            # Simple hash-based assignment
            hash_input = f"{key}:{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = hash_value % 100
            
            # Check traffic allocation
            if bucket >= exp.traffic_percent:
                return None
            
            # Assign to variation based on weights
            cumulative = 0
            normalized_bucket = (bucket / exp.traffic_percent) * 100
            
            for variation in exp.variations:
                cumulative += variation.get("weight", 50)
                if normalized_bucket < cumulative:
                    return variation.get("key")
            
            return exp.variations[-1].get("key") if exp.variations else None
        
        return None
    
    # ==================== Dynamic Configs ====================
    
    async def get_dynamic_configs(self) -> List[Dict]:
        """Get all dynamic configs"""
        if self.local_mode:
            return [self._config_to_dict(c) for c in self._configs.values()]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/saved-groups",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json().get("savedGroups", [])
    
    async def get_dynamic_config(self, key: str) -> Optional[Dict]:
        """Get a specific dynamic config"""
        if self.local_mode:
            config = self._configs.get(key)
            return self._config_to_dict(config) if config else None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/saved-groups/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def create_dynamic_config(
        self,
        key: str,
        description: str = "",
        value: Optional[Dict] = None,
    ) -> Dict:
        """Create a new dynamic config"""
        config = DynamicConfig(
            key=key,
            description=description,
            value=value or {},
        )
        
        if self.local_mode:
            self._configs[key] = config
            return self._config_to_dict(config)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/saved-groups",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "id": key,
                    "description": description,
                    "values": value or {},
                },
            )
            response.raise_for_status()
            return response.json()
    
    async def update_dynamic_config(
        self,
        key: str,
        value: Dict,
    ) -> Dict:
        """Update a dynamic config"""
        if self.local_mode:
            if key not in self._configs:
                raise ValueError(f"Config '{key}' not found")
            
            config = self._configs[key]
            config.value = value
            config.updated_at = datetime.utcnow()
            return self._config_to_dict(config)
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.api_url}/api/v1/saved-groups/{key}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"values": value},
            )
            response.raise_for_status()
            return response.json()
    
    def get_config_value(self, key: str, default: Optional[Dict] = None) -> Dict:
        """Get config value for use in agents"""
        if self.local_mode:
            config = self._configs.get(key)
            return config.value if config else (default or {})
        
        return default or {}
    
    # ==================== Helpers ====================
    
    def _evaluate_rule(self, rule: Dict, attributes: Dict) -> bool:
        """Evaluate a targeting rule"""
        condition = rule.get("condition", {})
        attr_key = condition.get("attribute")
        operator = condition.get("operator", "equals")
        target_value = condition.get("value")
        
        if not attr_key or attr_key not in attributes:
            return False
        
        attr_value = attributes[attr_key]
        
        if operator == "equals":
            return attr_value == target_value
        elif operator == "not_equals":
            return attr_value != target_value
        elif operator == "contains":
            return target_value in str(attr_value)
        elif operator == "greater_than":
            return attr_value > target_value
        elif operator == "less_than":
            return attr_value < target_value
        elif operator == "in":
            return attr_value in target_value
        
        return False
    
    def _log_evaluation(self, key: str, value: Any, attributes: Optional[Dict]):
        """Log feature evaluation for analytics"""
        self._evaluation_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "feature_key": key,
            "value": value,
            "attributes": attributes,
        })
    
    def _feature_to_dict(self, feature: FeatureFlag) -> Dict:
        """Convert FeatureFlag to dictionary"""
        return {
            "key": feature.key,
            "description": feature.description,
            "enabled": feature.enabled,
            "defaultValue": feature.default_value,
            "rules": feature.rules,
            "status": feature.status.value,
            "environment": feature.environment,
            "createdAt": feature.created_at.isoformat(),
            "updatedAt": feature.updated_at.isoformat(),
            "lastEvaluated": feature.last_evaluated.isoformat() if feature.last_evaluated else None,
            "isStale": feature.is_stale(),
        }
    
    def _experiment_to_dict(self, exp: Experiment) -> Dict:
        """Convert Experiment to dictionary"""
        return {
            "key": exp.key,
            "name": exp.name,
            "hypothesis": exp.hypothesis,
            "status": exp.status.value,
            "variations": exp.variations,
            "weights": exp.weights,
            "metrics": exp.metrics,
            "trafficPercent": exp.traffic_percent,
            "createdAt": exp.created_at.isoformat(),
            "startedAt": exp.started_at.isoformat() if exp.started_at else None,
            "endedAt": exp.ended_at.isoformat() if exp.ended_at else None,
        }
    
    def _config_to_dict(self, config: DynamicConfig) -> Dict:
        """Convert DynamicConfig to dictionary"""
        return {
            "key": config.key,
            "description": config.description,
            "value": config.value,
            "rules": config.rules,
            "environment": config.environment,
            "createdAt": config.created_at.isoformat(),
            "updatedAt": config.updated_at.isoformat(),
        }


# ==================== MCP Server ====================

class GrowthBookMCPServer:
    """
    MCP Server for GrowthBook integration.
    
    Provides tools for:
    - Feature flag management
    - A/B experiment creation & updates
    - Dynamic config retrieval
    - Stale flag detection
    """
    
    def __init__(self, client: Optional[GrowthBookClient] = None):
        self.client = client or GrowthBookClient(local_mode=True)
        self.app = FastAPI(title="GrowthBook MCP Server")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        def health():
            return {"status": "healthy", "service": "growthbook-mcp"}
        
        # Feature Flags
        @self.app.get("/api/features")
        async def list_features(
            environment: str = "production",
            status: Optional[str] = None,
        ):
            status_enum = FeatureStatus(status) if status else None
            return await self.client.get_feature_flags(environment, status_enum)
        
        @self.app.get("/api/features/{key}")
        async def get_feature(key: str):
            feature = await self.client.get_feature_flag(key)
            if not feature:
                raise HTTPException(status_code=404, detail="Feature not found")
            return feature
        
        @self.app.post("/api/features")
        async def create_feature(data: Dict):
            return await self.client.create_feature_flag(
                key=data["key"],
                description=data.get("description", ""),
                enabled=data.get("enabled", False),
                default_value=data.get("defaultValue"),
                rules=data.get("rules"),
            )
        
        @self.app.put("/api/features/{key}")
        async def update_feature(key: str, data: Dict):
            return await self.client.update_feature_flag(
                key=key,
                enabled=data.get("enabled"),
                default_value=data.get("defaultValue"),
                rules=data.get("rules"),
            )
        
        @self.app.get("/api/features/stale")
        async def get_stale_features(days: int = 30):
            return await self.client.get_stale_flags(days)
        
        @self.app.post("/api/features/{key}/evaluate")
        async def evaluate_feature(key: str, data: Dict = None):
            attributes = data.get("attributes") if data else None
            is_on = self.client.is_on(key, attributes)
            value = self.client.get_feature_value(key, attributes=attributes)
            return {"key": key, "isOn": is_on, "value": value}
        
        # Experiments
        @self.app.get("/api/experiments")
        async def list_experiments(status: Optional[str] = None):
            status_enum = ExperimentStatus(status) if status else None
            return await self.client.get_experiments(status_enum)
        
        @self.app.get("/api/experiments/{key}")
        async def get_experiment(key: str):
            exp = await self.client.get_experiment(key)
            if not exp:
                raise HTTPException(status_code=404, detail="Experiment not found")
            return exp
        
        @self.app.post("/api/experiments")
        async def create_experiment(data: Dict):
            return await self.client.create_experiment(
                key=data["key"],
                name=data["name"],
                hypothesis=data.get("hypothesis", ""),
                variations=data.get("variations"),
                metrics=data.get("metrics"),
                traffic_percent=data.get("trafficPercent", 100.0),
            )
        
        @self.app.post("/api/experiments/{key}/start")
        async def start_experiment(key: str):
            return await self.client.start_experiment(key)
        
        @self.app.post("/api/experiments/{key}/stop")
        async def stop_experiment(key: str):
            return await self.client.stop_experiment(key)
        
        @self.app.post("/api/experiments/{key}/assign")
        async def assign_variant(key: str, data: Dict):
            user_id = data.get("userId")
            attributes = data.get("attributes")
            variant = self.client.get_experiment_variant(key, user_id, attributes)
            return {"key": key, "userId": user_id, "variant": variant}
        
        # Dynamic Configs
        @self.app.get("/api/configs")
        async def list_configs():
            return await self.client.get_dynamic_configs()
        
        @self.app.get("/api/configs/{key}")
        async def get_config(key: str):
            config = await self.client.get_dynamic_config(key)
            if not config:
                raise HTTPException(status_code=404, detail="Config not found")
            return config
        
        @self.app.post("/api/configs")
        async def create_config(data: Dict):
            return await self.client.create_dynamic_config(
                key=data["key"],
                description=data.get("description", ""),
                value=data.get("value", {}),
            )
        
        @self.app.put("/api/configs/{key}")
        async def update_config(key: str, data: Dict):
            return await self.client.update_dynamic_config(key, data.get("value", {}))
    
    def run(self, host: str = "0.0.0.0", port: int = 8105):
        """Run the MCP server"""
        uvicorn.run(self.app, host=host, port=port)


# Singleton instance for use across agents
_growthbook_client: Optional[GrowthBookClient] = None


def get_growthbook_client() -> GrowthBookClient:
    """Get or create GrowthBook client singleton"""
    global _growthbook_client
    if _growthbook_client is None:
        _growthbook_client = GrowthBookClient(local_mode=True)
    return _growthbook_client


if __name__ == "__main__":
    server = GrowthBookMCPServer()
    server.run()
