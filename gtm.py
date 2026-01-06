"""GTM / RevOps event endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class GTMEvent(BaseModel):
    workspace_id: str = Field(..., description="Tenant/workspace identifier")
    event_type: str
    payload: dict = Field(default_factory=dict)
    execute_actions: bool = Field(default=False, description="If true, trigger n8n webhooks")


@router.post("/event")
async def handle_event(evt: GTMEvent):
    from agentic_mesh.gtm_orchestrator import GTMOrchestrator

    orch = GTMOrchestrator()
    result = await orch.handle_event(evt.workspace_id, evt.event_type, evt.payload)

    if evt.execute_actions:
        from integrations.n8n import N8NGateway

        gateway = N8NGateway()
        executed = []
        for action in result.get("actions", []):
            if action.get("type") == "n8n_webhook":
                executed.append(
                    await gateway.trigger_webhook(action["webhook"], action.get("payload", {}))
                )
        result["executed"] = executed

    return result
