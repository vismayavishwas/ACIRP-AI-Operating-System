from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class TimelineEvent(BaseModel):
    timestamp: str
    stage: Literal["PERCEPTION", "PLANNER", "TOOL", "MONITOR", "VERIFY", "ESCALATION", "SYSTEM"]
    decision: str
    confidence: str
    reason: str
    next_action: str

class Strategy(BaseModel):
    name: str
    department: str
    sla_hours: int
    escalation_path: List[str]

class PlannerDecision(BaseModel):
    goal: str
    current_state: str
    chosen_strategy: Strategy
    reason: str
    next_action: str
    requires_human: bool
    confidence: float

class Incident(BaseModel):
    id: str
    status: Literal[
        "DETECTED", "AWAITING_REUPLOAD", "PLANNED", "SUBMITTED", 
        "MONITORING", "VERIFYING", "ESCALATED", "CLOSED"
    ]
    goal: str = ""
    complainant_name: str = "Anonymous Citizen"
    issue_type: Optional[Literal["pothole", "fallen_tree", "garbage"]] = None
    severity: Optional[Literal["low", "medium", "high"]] = None
    confidence: Optional[float] = None
    latitude: float
    longitude: float
    image_before_url: str
    image_after_url: Optional[str] = None
    official_token: Optional[str] = None
    current_strategy: Optional[Strategy] = None
    sla_deadline: Optional[str] = None
    escalation_level: int = 0
    timeline: List[TimelineEvent] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
