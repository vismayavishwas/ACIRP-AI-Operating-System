import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure the parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Incident
from agents.perception import PerceptionAgent

@pytest.mark.anyio
async def test_perception_analysis_success():
    agent = PerceptionAgent(api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.text = '{"issue_type": "pothole", "confidence": 0.95, "severity": "high", "reasoning": "Large pothole"}'
    
    with patch.object(agent.client.models, 'generate_content', return_value=mock_response) as mock_gen:
        incident = Incident(
            id="inc_test",
            status="DETECTED",
            complainant_name="Alice",
            latitude=12.97,
            longitude=77.59,
            image_before_url="/static/inc_test_before.jpg"
        )
        
        updated_incident = await agent.analyze(
            image_bytes=b"dummy-bytes",
            incident=incident,
            filename="pothole.jpg"
        )
        
        assert updated_incident.status == "PLANNED"
        assert updated_incident.issue_type == "pothole"
        assert updated_incident.severity == "high"
        assert updated_incident.confidence == 0.95
        assert len(updated_incident.timeline) == 1
        mock_gen.assert_called_once()

@pytest.mark.anyio
async def test_perception_low_confidence():
    agent = PerceptionAgent(api_key="test-key")
    
    mock_response = MagicMock()
    # Confidence is 0.50, which is below standard 0.70 PHOTO_CONFIDENCE_THRESHOLD
    mock_response.text = '{"issue_type": "pothole", "confidence": 0.50, "severity": "low", "reasoning": "Too blurry"}'
    
    with patch.object(agent.client.models, 'generate_content', return_value=mock_response):
        incident = Incident(
            id="inc_test",
            status="DETECTED",
            complainant_name="Alice",
            latitude=12.97,
            longitude=77.59,
            image_before_url="/static/inc_test_before.jpg"
        )
        
        updated_incident = await agent.analyze(
            image_bytes=b"dummy-bytes",
            incident=incident,
            filename="blurry.jpg"
        )
        
        assert updated_incident.status == "AWAITING_REUPLOAD"
        assert len(updated_incident.timeline) == 1

@pytest.mark.anyio
async def test_perception_fallback_on_exception():
    agent = PerceptionAgent(api_key="test-key")
    
    # Force generate_content to raise an error
    with patch.object(agent.client.models, 'generate_content', side_effect=Exception("API limit exceeded")):
        incident = Incident(
            id="inc_test",
            status="DETECTED",
            complainant_name="Alice",
            latitude=12.97,
            longitude=77.59,
            image_before_url="/static/inc_test_before.jpg"
        )
        
        updated_incident = await agent.analyze(
            image_bytes=b"dummy-bytes",
            incident=incident,
            filename="my_fallen_tree_hazard.jpg"
        )
        
        # Fallback uses name keyword matching -> detects fallen_tree, sets confidence 0.88 (PLANNED)
        assert updated_incident.status == "PLANNED"
        assert updated_incident.issue_type == "fallen_tree"
        assert updated_incident.severity == "medium"
        assert updated_incident.confidence == 0.88
        assert "Failover Mock Active" in updated_incident.timeline[0].reason
