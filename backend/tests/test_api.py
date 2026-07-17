import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock, mock_open

# Ensure the parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a temp file path for the test database before importing main/db_mock
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix="_test_db.json")
os.close(temp_db_fd)

import db.json_db
# Override the database file path
db.json_db.DB_FILE = temp_db_path

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

def test_list_incidents_empty():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert response.json() == []

def test_get_incident_not_found():
    response = client.get("/api/incidents/inc_missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"

def test_create_incident_api():
    dummy_incident = Incident(
        id="inc_mocked",
        status="PLANNED",
        latitude=12.97,
        longitude=77.59,
        issue_type="pothole",
        severity="medium",
        confidence=0.92,
        image_before_url="/static/inc_mocked_before.jpg"
    )
    
    with patch.object(db, 'upload_image', return_value=None), \
         patch.object(perception_agent, 'analyze', return_value=dummy_incident) as mock_analyze:
             
        files = {"image": ("test.jpg", b"fake-image-content", "image/jpeg")}
        data = {
            "latitude": 12.97,
            "longitude": 77.59,
            "complainant_name": "Test Citizen"
        }
        
        response = client.post("/api/incidents/submit", data=data, files=files)
        
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["id"] == "inc_mocked"
        assert res_data["status"] == "PLANNED"
        assert res_data["issue_type"] == "pothole"
        mock_analyze.assert_called_once()

def test_verify_incident_resolution_not_verifying():
    incident = Incident(
        id="inc_not_verifying",
        status="PLANNED",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    db.save_incident(incident)
    
    files = {"image": ("after.jpg", b"after-bytes", "image/jpeg")}
    response = client.post("/api/incidents/inc_not_verifying/verify-resolution", files=files)
    assert response.status_code == 400
    assert "not in verification phase" in response.json()["detail"]

def test_verify_incident_resolution_success():
    incident = Incident(
        id="inc_verifying",
        status="VERIFYING",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    db.save_incident(incident)
    
    dummy_resolved = Incident(
        id="inc_verifying",
        status="CLOSED",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg",
        image_after_url="http://example.com/after.jpg"
    )
    
    with patch.object(db, 'upload_image', return_value="http://example.com/after.jpg"), \
         patch("os.listdir", return_value=["inc_verifying_before.jpg"]), \
         patch("main.open", mock_open(read_data=b"dummy-before-bytes")), \
         patch.object(verification_agent, 'verify', return_value=dummy_resolved) as mock_verify:
             
        files = {"image": ("after.jpg", b"after-bytes", "image/jpeg")}
        response = client.post("/api/incidents/inc_verifying/verify-resolution", files=files)
        
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "CLOSED"

def test_simulator_mark_resolved():
    incident = Incident(
        id="inc_monitored",
        status="MONITORING",
        official_token="BBMP-TEST1",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    db.save_incident(incident)
    
    from main import MOCK_PORTAL_TICKETS
    MOCK_PORTAL_TICKETS["BBMP-TEST1"] = {
        "incident_id": "inc_monitored",
        "issue_type": "garbage",
        "status": "PENDING"
    }
    
    response = client.post("/api/simulator/mark-resolved/BBMP-TEST1")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    updated = db.get_incident("inc_monitored")
    assert updated.status == "VERIFYING"

def test_simulator_trigger_sla_breach_not_found():
    response = client.post("/api/simulator/trigger-sla-breach/inc_missing")
    assert response.status_code == 404

def test_simulator_simulate_crash_not_found():
    response = client.post("/api/simulator/simulate-crash/inc_missing")
    assert response.status_code == 404

def test_approve_escalation_not_found():
    response = client.post("/api/incidents/inc_missing/approve-escalation")
    assert response.status_code == 404

def test_approve_escalation_not_escalated():
    incident = Incident(
        id="inc_not_escalated",
        status="PLANNED",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    db.save_incident(incident)
    response = client.post("/api/incidents/inc_not_escalated/approve-escalation")
    assert response.status_code == 400
    assert "does not require escalation" in response.json()["detail"]

def test_re_upload_image_not_awaiting():
    incident = Incident(
        id="inc_not_awaiting",
        status="PLANNED",
        latitude=12.97,
        longitude=77.59,
        image_before_url="http://example.com/before.jpg"
    )
    db.save_incident(incident)
    files = {"image": ("test.jpg", b"fake-bytes", "image/jpeg")}
    response = client.post("/api/incidents/inc_not_awaiting/re-upload-image", files=files)
    assert response.status_code == 400
    assert "not awaiting photo re-upload" in response.json()["detail"]


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass
