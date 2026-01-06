"""Canonical GTM OS models.

These models intentionally stay small and portable.

Rule of thumb:
- Put *fields and semantics* here.
- Put *tool-specific IDs/mappings* in WorkspaceConfig.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LifecycleStage(str, Enum):
    lead = "lead"
    mql = "mql"
    sql = "sql"
    opp = "opp"
    poc = "poc"
    closed_won = "closed_won"
    closed_lost = "closed_lost"


class Contact(BaseModel):
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    account_id: Optional[str] = None
    source: Optional[str] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.lead
    icp_score: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific fields")


class Account(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    location: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    icp_score: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class Deal(BaseModel):
    id: str
    account_id: Optional[str] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    stage: Optional[str] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.opp
    owner: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class ActivityType(str, Enum):
    email = "email"
    call = "call"
    meeting = "meeting"
    note = "note"
    task = "task"
    webhook = "webhook"
    other = "other"


class Activity(BaseModel):
    id: str
    type: ActivityType
    contact_id: Optional[str] = None
    account_id: Optional[str] = None
    deal_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    blocked = "blocked"
    done = "done"


class Task(BaseModel):
    id: str
    title: str
    status: TaskStatus = TaskStatus.todo
    owner: Optional[str] = None
    due_at: Optional[datetime] = None
    contact_id: Optional[str] = None
    account_id: Optional[str] = None
    deal_id: Optional[str] = None
    checklist: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class SignalType(str, Enum):
    intent = "intent"
    visitor = "visitor"
    hiring = "hiring"
    news = "news"
    competitor = "competitor"
    product_usage = "product_usage"
    event = "event"
    other = "other"


class Signal(BaseModel):
    id: str
    type: SignalType
    account_domain: Optional[str] = None
    contact_email: Optional[str] = None
    strength: int = Field(ge=0, le=100, default=50)
    summary: Optional[str] = None
    source: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttributionEvent(BaseModel):
    id: str
    contact_id: Optional[str] = None
    account_id: Optional[str] = None
    deal_id: Optional[str] = None
    event: str
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
