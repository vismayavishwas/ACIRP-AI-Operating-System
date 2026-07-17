import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure the parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Incident, Strategy, TimelineEvent
from agents.planner import PlanningAgent

@pytest.mark.anyio
async def test_planner_planned_to_submitted_default():
    mock_db = MagicMock()
    mock_db.find_nearby_resolved.return_value = []
    
    agent = PlanningAgent(db=mock_db)
    incident = Incident(
        id="inc_123",
        status="PLANNED",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        issue_type="garbage",
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident)
    
    assert updated.status == "SUBMITTED"
    assert updated.current_strategy.department == "Waste Management Dept"
    mock_db.find_nearby_resolved.assert_called_once()

@pytest.mark.anyio
async def test_planner_planned_to_submitted_with_similarity():
    mock_db = MagicMock()
    faster_strategy = Strategy(
        name="Express Waste Route",
        department="Waste Emergency Dept",
        sla_hours=4,
        escalation_path=["Area Supervisor"]
    )
    resolved_inc = Incident(
        id="inc_prev",
        status="CLOSED",
        complainant_name="Alice",
        latitude=12.9701,
        longitude=77.5901,
        issue_type="garbage",
        current_strategy=faster_strategy,
        image_before_url="http://example.com/prev.jpg"
    )
    mock_db.find_nearby_resolved.return_value = [resolved_inc]
    
    agent = PlanningAgent(db=mock_db)
    incident = Incident(
        id="inc_123",
        status="PLANNED",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        issue_type="garbage",
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident)
    
    assert updated.status == "SUBMITTED"
    assert updated.current_strategy.sla_hours == 4
    assert "Similarity search found resolved case" in updated.timeline[-1].reason

@pytest.mark.anyio
@patch("agents.planner.submit_to_portal_hybrid")
async def test_planner_submitted_success(mock_submit):
    mock_submit.return_value = "BBMP-TOKEN-123"
    mock_db = MagicMock()
    agent = PlanningAgent(db=mock_db)
    
    strategy = Strategy(
        name="Public Works Route",
        department="Public Works Dept (PWD)",
        sla_hours=72,
        escalation_path=["Chief PWD Engineer"]
    )
    incident = Incident(
        id="inc_123",
        status="SUBMITTED",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        current_strategy=strategy,
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident, submission_mode="api")
    
    assert updated.status == "MONITORING"
    assert updated.official_token == "BBMP-TOKEN-123"
    assert updated.sla_deadline is not None

@pytest.mark.anyio
@patch("agents.planner.submit_to_portal_hybrid")
async def test_planner_submitted_failure(mock_submit):
    mock_submit.side_effect = Exception("Portal Timeout")
    mock_db = MagicMock()
    agent = PlanningAgent(db=mock_db)
    
    incident = Incident(
        id="inc_123",
        status="SUBMITTED",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident, submission_mode="api")
    
    assert updated.status == "ESCALATED"
    assert "Portal submission timeout" in updated.timeline[-1].decision

@pytest.mark.anyio
async def test_planner_monitoring_sla_breach():
    from datetime import datetime, timedelta
    mock_db = MagicMock()
    agent = PlanningAgent(db=mock_db)
    
    strategy = Strategy(
        name="Waste Management Route",
        department="Waste Management Dept",
        sla_hours=24,
        escalation_path=["Area Supervisor", "Social Escalation"]
    )
    
    past_deadline = (datetime.now() - timedelta(hours=1)).isoformat()
    
    incident = Incident(
        id="inc_123",
        status="MONITORING",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        current_strategy=strategy,
        sla_deadline=past_deadline,
        escalation_level=0,
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident)
    
    assert updated.status == "ESCALATED"
    assert "SLA Breach Detected" in updated.timeline[-1].decision

@pytest.mark.anyio
async def test_planner_monitoring_sla_breach_exhausted():
    from datetime import datetime, timedelta
    mock_db = MagicMock()
    agent = PlanningAgent(db=mock_db)
    
    strategy = Strategy(
        name="Waste Management Route",
        department="Waste Management Dept",
        sla_hours=24,
        escalation_path=["Area Supervisor", "Social Escalation"]
    )
    
    past_deadline = (datetime.now() - timedelta(hours=1)).isoformat()
    
    incident = Incident(
        id="inc_123",
        status="MONITORING",
        complainant_name="Bob",
        latitude=12.97,
        longitude=77.59,
        current_strategy=strategy,
        sla_deadline=past_deadline,
        escalation_level=2,
        image_before_url="http://example.com/before.jpg"
    )
    
    updated = await agent.execute_step(incident)
    
    assert updated.status == "CLOSED"
    assert "SLA Breach - Routes Exhausted" in updated.timeline[-1].decision
