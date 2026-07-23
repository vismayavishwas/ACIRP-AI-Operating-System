import os
import sys
import tempfile
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, AsyncMock
from config import DEFAULT_ROUTING

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a temp file path for testing JSON database
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix="_integration_test_db.json")
os.close(temp_db_fd)

import db.json_db
db.json_db.DB_FILE = temp_db_path

from fastapi.testclient import TestClient
from main import app, db, perception_agent, planner_agent, verification_agent
from models import Incident, Strategy, TimelineEvent

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_database():
    with open(temp_db_path, "w") as f:
        f.write("{}")
    yield
    if os.path.exists(temp_db_path):
        with open(temp_db_path, "w") as f:
            f.write("{}")

def test_full_incident_lifecycle_and_sla_breach_flow():
    """
    Integration Test:
    Upload -> Perception -> Strategy Planning -> Portal Submission -> SLA Breach -> Human Escalation -> Closure
    """
    dummy_detected = Incident(
        id="inc_lifecycle_1",
        status="PLANNED",
        latitude=12.9716,
        longitude=77.5946,
        issue_type="pothole",
        severity="high",
        confidence=0.95,
        image_before_url="/static/inc_lifecycle_1_before.jpg",
        current_strategy=DEFAULT_ROUTING["pothole"],
        timeline=[
            TimelineEvent(
                timestamp="23 Jul 14:00",
                stage="PERCEPTION",
                decision="Detected pothole",
                confidence="95%",
                reason="Severe pothole identified on road",
                next_action="Plan complaint submission"
            )
        ]
    )

    # 1. Citizen Uploads Photo
    with patch.object(db, 'upload_image', return_value="/static/inc_lifecycle_1_before.jpg"), \
         patch.object(perception_agent, 'analyze', return_value=dummy_detected):
        
        files = {"image": ("pothole.jpg", b"pothole-image-bytes", "image/jpeg")}
        data = {"latitude": 12.9716, "longitude": 77.5946, "complainant_name": "Alice Citizen"}
        res = client.post("/api/incidents/submit", data=data, files=files)
        assert res.status_code == 200
        incident_data = res.json()
        assert incident_data["id"] == "inc_lifecycle_1"
        assert incident_data["status"] == "PLANNED"

    # 2. Trigger Agent Ticks (Tick 1: PLANNED -> SUBMITTED, Tick 2: SUBMITTED -> MONITORING)
    with patch("agents.planner.submit_to_portal_hybrid", new=AsyncMock(return_value="BBMP-TOKEN-99")):
        tick1_res = client.post("/api/incidents/inc_lifecycle_1/tick")
        assert tick1_res.status_code == 200
        assert tick1_res.json()["status"] == "SUBMITTED"

        tick2_res = client.post("/api/incidents/inc_lifecycle_1/tick")
        assert tick2_res.status_code == 200
        tick_data = tick2_res.json()
        assert tick_data["status"] == "MONITORING"
        assert tick_data["official_token"] == "BBMP-TOKEN-99"

    # 3. Simulate SLA Breach Time-Travel
    sla_res = client.post("/api/simulator/trigger-sla-breach/inc_lifecycle_1")
    assert sla_res.status_code == 200

    # 4. Agent Tick after SLA breach -> Escalates ticket
    escalate_tick = client.post("/api/incidents/inc_lifecycle_1/tick")
    assert escalate_tick.status_code == 200
    escalated_data = escalate_tick.json()
    assert escalated_data["status"] == "ESCALATED"
    assert escalated_data["escalation_level"] == 0

    # 5. Verify Escalated Decision Endpoint (Requires Human Approval)
    dec_res = client.get("/api/incidents/inc_lifecycle_1/decision")
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["requires_human"] is True

    # 6. Human-in-the-Loop Approves Escalation -> Advances strategy and resets to MONITORING
    approve_res = client.post("/api/incidents/inc_lifecycle_1/approve-escalation")
    assert approve_res.status_code == 200
    approved_inc = db.get_incident("inc_lifecycle_1")
    assert approved_inc.escalation_level == 1
    assert approved_inc.status == "MONITORING"

def test_portal_crash_simulation_workflow():
    """
    Integration Test:
    Tests simulate-crash endpoint and verifies ticket transition to CLOSED with failover logs.
    """
    incident = Incident(
        id="inc_crash_test",
        status="MONITORING",
        latitude=12.97,
        longitude=77.59,
        issue_type="garbage",
        image_before_url="http://example.com/garbage.jpg",
        current_strategy=DEFAULT_ROUTING["garbage"]
    )
    db.save_incident(incident)

    res = client.post("/api/simulator/simulate-crash/inc_crash_test")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    updated = db.get_incident("inc_crash_test")
    assert updated.status == "CLOSED"
    last_event = updated.timeline[-1]
    assert last_event.decision == "Portal submission failed"

def test_verification_hazard_rejection_guardrail():
    """
    Integration Test:
    Verifies that uploading a photo containing unresolved garbage/hazard fails verification.
    """
    incident = Incident(
        id="inc_verify_fail",
        status="VERIFYING",
        latitude=12.97,
        longitude=77.59,
        issue_type="garbage",
        image_before_url="http://example.com/garbage_before.jpg",
        current_strategy=DEFAULT_ROUTING["garbage"]
    )
    db.save_incident(incident)

    failed_verification_incident = Incident(
        id="inc_verify_fail",
        status="ESCALATED",
        latitude=12.97,
        longitude=77.59,
        issue_type="garbage",
        image_before_url="http://example.com/garbage_before.jpg",
        image_after_url="http://example.com/garbage_after.jpg",
        current_strategy=DEFAULT_ROUTING["garbage"],
        timeline=[
            TimelineEvent(
                timestamp="23 Jul 14:15",
                stage="VERIFY",
                decision="Verification failed",
                confidence="30%",
                reason="Hazard still present in proof photo",
                next_action="Escalate ticket to higher authority for review."
            )
        ]
    )

    with patch.object(db, 'upload_image', return_value="http://example.com/garbage_after.jpg"), \
         patch("os.listdir", return_value=["inc_verify_fail_before.jpg"]), \
         patch("main.open", mock_open(read_data=b"garbage-before-bytes")), \
         patch.object(verification_agent, 'verify', return_value=failed_verification_incident):

        files = {"image": ("garbage_still_here.jpg", b"garbage-bytes", "image/jpeg")}
        res = client.post("/api/incidents/inc_verify_fail/verify-resolution", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ESCALATED"
        assert data["timeline"][-1]["decision"] == "Verification failed"

def test_download_escalation_letter_and_petition_forms():
    """
    Integration Test:
    Tests HTML/PDF download endpoints for filed complaints and escalation letters.
    """
    incident = Incident(
        id="inc_download_test",
        status="ESCALATED",
        official_token="TOKEN-123",
        complainant_name="Bob Citizen",
        latitude=12.97,
        longitude=77.59,
        issue_type="fallen_tree",
        severity="medium",
        confidence=0.91,
        image_before_url="http://example.com/tree.jpg",
        current_strategy=DEFAULT_ROUTING["fallen_tree"]
    )
    db.save_incident(incident)

    form_res = client.get("/api/incidents/inc_download_test/download-form")
    assert form_res.status_code == 200
    assert "Civic Complaint Form" in form_res.text or "FORMAL COMPLAINT" in form_res.text

    letter_res = client.get("/api/incidents/inc_download_test/download-escalation-letter")
    assert letter_res.status_code == 200
    assert "FORMAL COMPLAINT ESCALATION" in letter_res.text

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass
