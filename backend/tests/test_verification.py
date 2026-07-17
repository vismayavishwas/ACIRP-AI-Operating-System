import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure the parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Incident, Strategy
from agents.verification import VerificationAgent

@pytest.mark.anyio
async def test_verification_success():
    agent = VerificationAgent(api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.text = '{"is_resolved": true, "confidence": 0.95, "justification": "Road is clear"}'
    
    with patch.object(agent.client.models, 'generate_content', return_value=mock_response) as mock_gen:
        incident = Incident(
            id="inc_test",
            status="VERIFYING",
            latitude=12.97,
            longitude=77.59,
            image_before_url="http://example.com/before.jpg"
        )
        
        updated = await agent.verify(
            before_bytes=b"before",
            after_bytes=b"after",
            incident=incident,
            filename="after.jpg"
        )
        
        assert updated.status == "CLOSED"
        assert len(updated.timeline) == 1
        assert "verified resolved" in updated.timeline[0].decision
        mock_gen.assert_called_once()

@pytest.mark.anyio
async def test_verification_failed_escalate():
    agent = VerificationAgent(api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.text = '{"is_resolved": false, "confidence": 0.30, "justification": "Still blocked"}'
    
    with patch.object(agent.client.models, 'generate_content', return_value=mock_response):
        strategy = Strategy(
            name="Waste Management Route",
            department="Waste Management Dept",
            sla_hours=24,
            escalation_path=["Area Supervisor"]
        )
        incident = Incident(
            id="inc_test",
            status="VERIFYING",
            latitude=12.97,
            longitude=77.59,
            image_before_url="http://example.com/before.jpg",
            current_strategy=strategy,
            escalation_level=0
        )
        
        updated = await agent.verify(
            before_bytes=b"before",
            after_bytes=b"after",
            incident=incident,
            filename="after.jpg"
        )
        
        assert updated.status == "ESCALATED"
        assert len(updated.timeline) == 1
        assert "failed" in updated.timeline[0].decision.lower()

@pytest.mark.anyio
async def test_verification_fallback_success():
    agent = VerificationAgent(api_key="test-key")
    
    with patch.object(agent.client.models, 'generate_content', side_effect=Exception("API Error")):
        incident = Incident(
            id="inc_test",
            status="VERIFYING",
            latitude=12.97,
            longitude=77.59,
            image_before_url="http://example.com/before.jpg"
        )
        
        updated = await agent.verify(
            before_bytes=b"before",
            after_bytes=b"after",
            incident=incident,
            filename="resolution_proof.jpg"
        )
        
        assert updated.status == "CLOSED"
        assert "verified resolved" in updated.timeline[0].decision
        assert "Failover Verification Mock" in updated.timeline[0].reason

@pytest.mark.anyio
async def test_verification_fallback_failure():
    agent = VerificationAgent(api_key="test-key")
    
    with patch.object(agent.client.models, 'generate_content', side_effect=Exception("API Error")):
        strategy = Strategy(
            name="Waste Management Route",
            department="Waste Management Dept",
            sla_hours=24,
            escalation_path=["Area Supervisor"]
        )
        incident = Incident(
            id="inc_test",
            status="VERIFYING",
            latitude=12.97,
            longitude=77.59,
            image_before_url="http://example.com/before.jpg",
            current_strategy=strategy,
            escalation_level=0
        )
        
        updated = await agent.verify(
            before_bytes=b"before",
            after_bytes=b"after",
            incident=incident,
            filename="wrong_resolution.jpg"
        )
        
        assert updated.status == "ESCALATED"
