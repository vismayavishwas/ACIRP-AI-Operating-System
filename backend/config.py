import os
from dotenv import load_dotenv
from models import Strategy

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Core Agent Thresholds
PHOTO_CONFIDENCE_THRESHOLD = 0.70  # Min confidence to accept incident photo
VERIFICATION_THRESHOLD = 0.65      # Min confidence to verify task resolution
ESCALATION_THRESHOLD = 0.85        # Threshold to trigger automatic escalation

# Simulated/Mock Configuration
MONITOR_SLEEP_INTERVAL_SEC = 10    # (Simulated time) Seconds between status updates
MAX_PORTAL_RETRIES = 3             # Playwright browser failure retries

# Standard Strategic Workflows
DEFAULT_ROUTING = {
    "garbage": Strategy(
        name="Waste Management Route",
        department="Waste Management Dept",
        sla_hours=24,
        escalation_path=["Area Supervisor", "Social Escalation"]
    ),
    "pothole": Strategy(
        name="Public Works Route",
        department="Public Works Dept (PWD)",
        sla_hours=72,
        escalation_path=["Chief PWD Engineer", "Social Escalation"]
    ),
    "fallen_tree": Strategy(
        name="Forestry Emergency Route",
        department="Forest & Parks Dept",
        sla_hours=12,
        escalation_path=["Horticulture Officer", "Social Escalation"]
    )
}
