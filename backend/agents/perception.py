import json
from google import genai
from google.genai import types
from models import Incident, TimelineEvent
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from config import PHOTO_CONFIDENCE_THRESHOLD

class PerceptionAgent:
    def __init__(self, api_key: str):
        # The new Google GenAI SDK client
        self.client = genai.Client(api_key=api_key)

    async def analyze(self, image_bytes: bytes, incident: Incident, mime_type: str = "image/jpeg") -> Incident:
        prompt = f"""
        Analyze this image representing a civic incident.
        Classify it into one of: 'pothole', 'fallen_tree', 'garbage'.
        CRITICAL: If the image shows a clean road, normal street scene, empty pavement, or does not contain any obvious pothole, fallen tree, or garbage pile, you MUST classify it as 'unknown' with a confidence of 0.0.
        If it does not fit these categories, or is blurred, low-quality, or hard to verify, output a confidence below {PHOTO_CONFIDENCE_THRESHOLD} and set category to 'unknown'.
        Estimate severity (low, medium, high) based on safety risk.
        Provide a concise engineering reason for the detection.
        """
        
        # Declare response schema structure for structured output
        class AnalysisResult(BaseModel):
            issue_type: Literal["pothole", "fallen_tree", "garbage", "unknown"]
            confidence: float = Field(description="Score between 0.0 and 1.0")
            severity: Literal["low", "medium", "high"]
            reasoning: str

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                ),
            )
            result = json.loads(response.text)
        except Exception as e:
            # Failure recovery fallback if Gemini API is down or invalid image format
            result = {
                "issue_type": "unknown",
                "confidence": 0.0,
                "severity": "low",
                "reasoning": f"Gemini analysis failed: {str(e)}"
            }
            
        conf_percent = f"{int(result['confidence'] * 100)}%"
        
        # Format standardized timeline details
        next_action_step = "Plan complaint submission" if result["confidence"] >= PHOTO_CONFIDENCE_THRESHOLD else "Request citizen photo re-upload"
        
        event = TimelineEvent(
            timestamp=datetime.now().strftime("%d %b %H:%M"),
            stage="PERCEPTION",
            decision=f"Detected {result['issue_type']}" if result["issue_type"] != "unknown" else "No valid incident detected",
            confidence=conf_percent,
            reason=result["reasoning"],
            next_action=next_action_step
        )
        
        incident.timeline.append(event)
        
        if result["confidence"] < PHOTO_CONFIDENCE_THRESHOLD or result["issue_type"] == "unknown":
            incident.status = "AWAITING_REUPLOAD"
        else:
            incident.status = "PLANNED"
            incident.issue_type = result["issue_type"]
            incident.severity = result["severity"]
            incident.confidence = result["confidence"]
            incident.goal = f"Resolve {result['issue_type'].replace('_', ' ')} incident with {result['severity']} severity"
            
        incident.updated_at = datetime.now().isoformat()
        return incident
