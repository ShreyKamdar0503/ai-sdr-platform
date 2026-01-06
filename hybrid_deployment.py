"""
Hybrid Deployment Manager - PaaS + SaaS Architecture

Supports two deployment modes:
1. SaaS Mode: Out-of-box ready-to-deploy solution with pre-built agents
2. PaaS Mode: n8n as execution layer for custom workflows by consulting partners

Design Philosophy:
- SaaS: Quick deployment, limited customization (code changes required)
- PaaS: Full flexibility via n8n workflows, custom data/integrations
"""

from __future__ import annotations

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import httpx


class DeploymentMode(str, Enum):
    """Deployment mode for the platform"""
    SAAS = "saas"  # Out-of-box solution
    PAAS = "paas"  # Platform with n8n execution layer


class WorkflowExecutor(ABC):
    """Abstract base for workflow execution"""
    
    @abstractmethod
    async def execute(self, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_status(self, execution_id: str) -> Dict[str, Any]:
        pass


@dataclass
class AgentConfig:
    """Configuration for a pre-built agent"""
    agent_id: str
    name: str
    description: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    # SaaS mode: uses built-in logic
    # PaaS mode: delegates to n8n workflow
    n8n_workflow_id: Optional[str] = None


@dataclass
class WorkspaceConfig:
    """Configuration for a tenant workspace"""
    workspace_id: str
    name: str
    mode: DeploymentMode
    agents: List[AgentConfig] = field(default_factory=list)
    n8n_base_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
    custom_workflows: Dict[str, str] = field(default_factory=dict)  # action -> n8n webhook
    integrations: Dict[str, Dict] = field(default_factory=dict)  # service -> config
    created_at: datetime = field(default_factory=datetime.utcnow)


class N8NExecutor(WorkflowExecutor):
    """
    n8n Workflow Executor for PaaS mode.
    
    Consulting partners can build custom workflows in n8n
    that integrate with their client's specific tools.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
    
    async def execute(
        self,
        workflow_id: str,
        payload: Dict[str, Any],
        wait_for_completion: bool = True,
    ) -> Dict[str, Any]:
        """Execute an n8n workflow via webhook"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        # Determine if workflow_id is a full URL or just an ID
        if workflow_id.startswith("http"):
            url = workflow_id
        else:
            url = f"{self.base_url}/webhook/{workflow_id}"
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json() if response.content else {"success": True}
            
            # Add execution metadata
            result["_n8n_execution"] = {
                "workflow_id": workflow_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed" if response.status_code == 200 else "error",
            }
            
            return result
    
    async def get_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status (requires n8n API)"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/executions/{execution_id}",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "unknown", "execution_id": execution_id}
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows"""
        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/workflows",
                headers=headers,
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []


class BuiltInExecutor(WorkflowExecutor):
    """
    Built-in executor for SaaS mode.
    
    Uses pre-built agent logic without n8n dependency.
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
    
    def register_handler(self, workflow_id: str, handler: Callable):
        """Register a built-in workflow handler"""
        self._handlers[workflow_id] = handler
    
    async def execute(self, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a built-in workflow"""
        handler = self._handlers.get(workflow_id)
        if not handler:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        result = await handler(payload)
        result["_builtin_execution"] = {
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return result
    
    async def get_status(self, execution_id: str) -> Dict[str, Any]:
        """Built-in executions are synchronous"""
        return {"status": "completed", "execution_id": execution_id}


class HybridDeploymentManager:
    """
    Manages hybrid PaaS/SaaS deployments.
    
    Routes agent actions to either:
    - Built-in logic (SaaS mode)
    - n8n workflows (PaaS mode)
    """
    
    def __init__(self):
        self.workspaces: Dict[str, WorkspaceConfig] = {}
        self.builtin_executor = BuiltInExecutor()
        self.n8n_executors: Dict[str, N8NExecutor] = {}
        
        # Register default built-in handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default SaaS workflow handlers"""
        
        async def research_handler(payload: Dict) -> Dict:
            """Built-in company research"""
            from agentic_mesh.agents.research_agent import ResearchAgent
            agent = ResearchAgent()
            return await agent.process(payload)
        
        async def copywriting_handler(payload: Dict) -> Dict:
            """Built-in email generation"""
            from agentic_mesh.agents.copywriting_agent import CopywritingAgent
            agent = CopywritingAgent()
            return await agent.generate_emails(
                payload.get("lead_data", {}),
                payload.get("research_results", {}),
            )
        
        async def scoring_handler(payload: Dict) -> Dict:
            """Built-in lead scoring"""
            from agentic_mesh.agents.qualifier_agent import QualifierAgent
            agent = QualifierAgent()
            score = await agent.score_lead(
                payload.get("lead_data", {}),
                payload.get("research_results", {}),
            )
            return {"score": score}
        
        self.builtin_executor.register_handler("research", research_handler)
        self.builtin_executor.register_handler("copywriting", copywriting_handler)
        self.builtin_executor.register_handler("scoring", scoring_handler)
    
    def register_workspace(self, config: WorkspaceConfig):
        """Register a workspace configuration"""
        self.workspaces[config.workspace_id] = config
        
        # Initialize n8n executor for PaaS mode
        if config.mode == DeploymentMode.PAAS and config.n8n_base_url:
            self.n8n_executors[config.workspace_id] = N8NExecutor(
                base_url=config.n8n_base_url,
                api_key=config.n8n_api_key,
            )
    
    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceConfig]:
        """Get workspace configuration"""
        return self.workspaces.get(workspace_id)
    
    async def execute_action(
        self,
        workspace_id: str,
        action: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute an action for a workspace.
        
        Routes to n8n (PaaS) or built-in handlers (SaaS) based on config.
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Unknown workspace: {workspace_id}")
        
        # PaaS mode: Check for custom n8n workflow
        if workspace.mode == DeploymentMode.PAAS:
            n8n_workflow = workspace.custom_workflows.get(action)
            if n8n_workflow:
                executor = self.n8n_executors.get(workspace_id)
                if executor:
                    return await executor.execute(n8n_workflow, {
                        "workspace_id": workspace_id,
                        "action": action,
                        "payload": payload,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
        
        # SaaS mode or no custom workflow: Use built-in handler
        return await self.builtin_executor.execute(action, payload)
    
    async def process_lead(
        self,
        workspace_id: str,
        lead_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a lead through the complete workflow.
        
        Orchestrates all agents based on workspace configuration.
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Unknown workspace: {workspace_id}")
        
        results = {
            "workspace_id": workspace_id,
            "lead_id": lead_data.get("id", "unknown"),
            "mode": workspace.mode.value,
            "started_at": datetime.utcnow().isoformat(),
            "stages": {},
        }
        
        # Stage 1: Research
        research_result = await self.execute_action(
            workspace_id, "research", {"lead_data": lead_data}
        )
        results["stages"]["research"] = research_result
        
        # Stage 2: Scoring
        scoring_result = await self.execute_action(
            workspace_id, "scoring", {
                "lead_data": lead_data,
                "research_results": research_result,
            }
        )
        results["stages"]["scoring"] = scoring_result
        results["lead_score"] = scoring_result.get("score", 0)
        
        # Stage 3: Copywriting (only if score is high enough)
        if results["lead_score"] >= 60:
            copy_result = await self.execute_action(
                workspace_id, "copywriting", {
                    "lead_data": lead_data,
                    "research_results": research_result,
                }
            )
            results["stages"]["copywriting"] = copy_result
            results["email_variants"] = copy_result.get("variants", [])
        
        results["completed_at"] = datetime.utcnow().isoformat()
        return results


class WorkspaceConfigStore:
    """
    Persistent storage for workspace configurations.
    
    Can be backed by:
    - JSON file (development)
    - PostgreSQL (production)
    - Redis (caching)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.getenv(
            "WORKSPACE_CONFIG_PATH",
            "./config/workspaces.json"
        )
        self._cache: Dict[str, WorkspaceConfig] = {}
    
    def load_all(self) -> Dict[str, WorkspaceConfig]:
        """Load all workspace configurations"""
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for ws_id, ws_data in data.items():
                    self._cache[ws_id] = self._dict_to_config(ws_data)
        except FileNotFoundError:
            pass
        return self._cache
    
    def save(self, config: WorkspaceConfig):
        """Save a workspace configuration"""
        self._cache[config.workspace_id] = config
        self._persist()
    
    def get(self, workspace_id: str) -> Optional[WorkspaceConfig]:
        """Get a workspace configuration"""
        if workspace_id not in self._cache:
            self.load_all()
        return self._cache.get(workspace_id)
    
    def _persist(self):
        """Persist all configurations to storage"""
        data = {
            ws_id: self._config_to_dict(config)
            for ws_id, config in self._cache.items()
        }
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _config_to_dict(self, config: WorkspaceConfig) -> Dict:
        """Convert WorkspaceConfig to dictionary"""
        return {
            "workspace_id": config.workspace_id,
            "name": config.name,
            "mode": config.mode.value,
            "n8n_base_url": config.n8n_base_url,
            "n8n_api_key": config.n8n_api_key,
            "custom_workflows": config.custom_workflows,
            "integrations": config.integrations,
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "description": a.description,
                    "enabled": a.enabled,
                    "parameters": a.parameters,
                    "n8n_workflow_id": a.n8n_workflow_id,
                }
                for a in config.agents
            ],
        }
    
    def _dict_to_config(self, data: Dict) -> WorkspaceConfig:
        """Convert dictionary to WorkspaceConfig"""
        return WorkspaceConfig(
            workspace_id=data["workspace_id"],
            name=data["name"],
            mode=DeploymentMode(data.get("mode", "saas")),
            n8n_base_url=data.get("n8n_base_url"),
            n8n_api_key=data.get("n8n_api_key"),
            custom_workflows=data.get("custom_workflows", {}),
            integrations=data.get("integrations", {}),
            agents=[
                AgentConfig(
                    agent_id=a["agent_id"],
                    name=a["name"],
                    description=a.get("description", ""),
                    enabled=a.get("enabled", True),
                    parameters=a.get("parameters", {}),
                    n8n_workflow_id=a.get("n8n_workflow_id"),
                )
                for a in data.get("agents", [])
            ],
        )


# Convenience function to create a pre-configured SaaS workspace
def create_saas_workspace(
    workspace_id: str,
    name: str,
    integrations: Optional[Dict] = None,
) -> WorkspaceConfig:
    """Create a pre-configured SaaS workspace with all agents enabled"""
    default_agents = [
        AgentConfig(
            agent_id="research",
            name="Research Agent",
            description="Company & contact intelligence gathering",
        ),
        AgentConfig(
            agent_id="qualifier",
            name="Qualifier Agent",
            description="Lead scoring and prioritization",
        ),
        AgentConfig(
            agent_id="copywriting",
            name="Copywriting Agent",
            description="Personalized email generation",
        ),
        AgentConfig(
            agent_id="timing",
            name="Timing Optimizer",
            description="Optimal send-time prediction",
        ),
        AgentConfig(
            agent_id="negotiation",
            name="Negotiation Agent",
            description="Multi-agent consensus building",
        ),
        AgentConfig(
            agent_id="approval",
            name="Approval Agent",
            description="Human-in-the-loop coordination",
        ),
    ]
    
    return WorkspaceConfig(
        workspace_id=workspace_id,
        name=name,
        mode=DeploymentMode.SAAS,
        agents=default_agents,
        integrations=integrations or {},
    )


# Convenience function to create a PaaS workspace for consulting partners
def create_paas_workspace(
    workspace_id: str,
    name: str,
    n8n_base_url: str,
    n8n_api_key: Optional[str] = None,
    custom_workflows: Optional[Dict[str, str]] = None,
    integrations: Optional[Dict] = None,
) -> WorkspaceConfig:
    """Create a PaaS workspace with n8n execution layer"""
    return WorkspaceConfig(
        workspace_id=workspace_id,
        name=name,
        mode=DeploymentMode.PAAS,
        n8n_base_url=n8n_base_url,
        n8n_api_key=n8n_api_key,
        custom_workflows=custom_workflows or {},
        integrations=integrations or {},
        agents=[],  # Agents defined by n8n workflows
    )


__all__ = [
    "DeploymentMode",
    "AgentConfig",
    "WorkspaceConfig",
    "HybridDeploymentManager",
    "WorkspaceConfigStore",
    "N8NExecutor",
    "BuiltInExecutor",
    "create_saas_workspace",
    "create_paas_workspace",
]
