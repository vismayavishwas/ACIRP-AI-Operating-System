import os
import uuid
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional

from models import Incident, TimelineEvent, PlannerDecision, Strategy
from db_mock import MockDB
from config import GEMINI_API_KEY
from agents.perception import PerceptionAgent
from agents.planner import PlanningAgent
from agents.verification import VerificationAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("acirp.api")

app = FastAPI(title="ACIRP Backend & Simulator API")

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mock Database & AI Agents
db = MockDB()
perception_agent = PerceptionAgent(api_key=GEMINI_API_KEY)
planner_agent = PlanningAgent(db=db)
verification_agent = VerificationAgent(api_key=GEMINI_API_KEY)

# Directory to save mock image files locally
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory database representing the external Government Portal Tickets
MOCK_PORTAL_TICKETS = {}

# ---------------------------------------------------------
# 1. CORE CITIZEN PORTAL ENDPOINTS
# ---------------------------------------------------------

@app.post("/api/incidents/submit")
async def create_incident(
    latitude: float = Form(...),
    longitude: float = Form(...),
    complainant_name: str = Form("Anonymous Citizen"),
    image: UploadFile = File(...)
):
    """
    Step 1: Citizen uploads incident image.
    Generates incident document, saves image, runs Perception Agent.
    """
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    
    # Save the uploaded file
    file_ext = image.filename.split(".")[-1]
    image_path = os.path.join(UPLOAD_DIR, f"{incident_id}_before.{file_ext}")
    
    image_bytes = await image.read()
    with open(image_path, "wb") as f:
        f.write(image_bytes)
        
    # Initialize basic incident state
    incident = Incident(
        id=incident_id,
        status="DETECTED",
        complainant_name=complainant_name,
        latitude=latitude,
        longitude=longitude,
        image_before_url=f"/static/{incident_id}_before.{file_ext}"
    )
    
    # Append initial detection event
    incident.timeline.append(TimelineEvent(
        timestamp=datetime.now().strftime("%d %b %H:%M"),
        stage="SYSTEM",
        decision="Incident upload received",
        confidence="100%",
        reason="Citizen filed new incident with GPS coordinates.",
        next_action="Trigger Perception Agent Vision classifier"
    ))
    
    # Run the Perception Agent directly (passing the dynamic MIME type)
    incident = await perception_agent.analyze(image_bytes, incident, mime_type=image.content_type or "image/jpeg")
    
    # Save to mock database
    db.save_incident(incident)
    return incident

@app.post("/api/incidents/{incident_id}/verify-resolution")
async def verify_incident_resolution(
    incident_id: str,
    image: UploadFile = File(...)
):
    """
    Step 2: Citizen uploads resolution proof image when portal marks it resolved.
    Triggers Verification Agent to compare before/after images.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != "VERIFYING":
        raise HTTPException(status_code=400, detail="Incident is not in verification phase")

    # Save resolution file
    file_ext = image.filename.split(".")[-1]
    image_after_path = os.path.join(UPLOAD_DIR, f"{incident_id}_after.{file_ext}")
    
    image_after_bytes = await image.read()
    with open(image_after_path, "wb") as f:
        f.write(image_after_bytes)
        
    incident.image_after_url = f"/static/{incident_id}_after.{file_ext}"
    
    import mimetypes
    # Read the original before image bytes
    before_filename = incident.image_before_url.split("/")[-1]
    image_before_path = os.path.join(UPLOAD_DIR, before_filename)
    
    # Determine dynamic MIME types for both files
    before_mime, _ = mimetypes.guess_type(image_before_path)
    if not before_mime:
        before_mime = "image/jpeg"
    after_mime = image.content_type or "image/jpeg"
    
    with open(image_before_path, "rb") as f:
        image_before_bytes = f.read()
        
    # Trigger Verification Agent with dynamic MIME types
    incident = await verification_agent.verify(
        image_before_bytes, image_after_bytes, incident, 
        before_mime=before_mime, after_mime=after_mime
    )
    db.save_incident(incident)
    return incident

@app.post("/api/incidents/{incident_id}/approve-escalation")
async def approve_escalation(incident_id: str):
    """
    Step 3: Human-in-the-loop approval to proceed with escalation.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != "ESCALATED":
        raise HTTPException(status_code=400, detail="Incident does not require escalation approval")
        
    incident.escalation_level += 1
    escalation_paths = incident.current_strategy.escalation_path if incident.current_strategy else []
    
    timestamp = datetime.now().strftime("%d %b %H:%M")
    
    if incident.escalation_level <= len(escalation_paths):
        escalation_target = escalation_paths[incident.escalation_level - 1]
        
        # Reset status back to monitoring after escalation action
        incident.status = "MONITORING"
        # Grant a fresh 12h SLA window for escalated authority checks
        incident.sla_deadline = (datetime.now() + timedelta(hours=12)).isoformat()
        
        incident.timeline.append(TimelineEvent(
            timestamp=timestamp,
            stage="ESCALATION",
            decision=f"Escalated to {escalation_target}",
            confidence="100%",
            reason=f"Human approved escalation. Strategy shifting to level {incident.escalation_level}.",
            next_action=f"Monitoring response from {escalation_target}"
        ))
    else:
        # Escalation paths exhausted: suggest direct emergency help
        incident.status = "CLOSED"
        incident.timeline.append(TimelineEvent(
            timestamp=timestamp,
            stage="ESCALATION",
            decision="All escalation routes exhausted",
            confidence="100%",
            reason="Unable to resolve through digital municipal channels.",
            next_action="Recommending user call direct citizen ward helpline."
        ))

    db.save_incident(incident)
    return incident

@app.post("/api/incidents/{incident_id}/re-upload-image")
async def re_upload_image(incident_id: str, image: UploadFile = File(...)):
    """
    Emergency re-upload if perception agent failed to confirm confidence.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != "AWAITING_REUPLOAD":
        raise HTTPException(status_code=400, detail="Incident not awaiting photo re-upload")

    # Overwrite the original before image
    before_filename = incident.image_before_url.split("/")[-1]
    image_before_path = os.path.join(UPLOAD_DIR, before_filename)
    
    image_bytes = await image.read()
    with open(image_before_path, "wb") as f:
        f.write(image_bytes)

    incident.status = "DETECTED"
    incident.timeline.append(TimelineEvent(
        timestamp=datetime.utcnow().strftime("%H:%M"),
        stage="SYSTEM",
        decision="Re-uploaded image received",
        confidence="100%",
        reason="Citizen provided higher quality evidence.",
        next_action="Rerunning Perception Agent analysis"
    ))
    
    incident = await perception_agent.analyze(image_bytes, incident, mime_type=image.content_type or "image/jpeg")
    db.save_incident(incident)
    return incident

# ---------------------------------------------------------
# 2. AGENT ORCHESTRATOR & SIMULATOR CONTROL ENDPOINTS
# ---------------------------------------------------------

@app.get("/api/incidents/{incident_id}/decision")
async def get_agent_brain_decision(incident_id: str) -> PlannerDecision:
    """
    Returns the formatted PlannerDecision model read by the frontend dashboard.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return planner_agent.get_brain_decision(incident)

@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str) -> Incident:
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@app.get("/api/incidents")
async def list_incidents() -> List[Incident]:
    return db.list_incidents()

@app.post("/api/incidents/{incident_id}/tick")
async def trigger_agent_tick(incident_id: str, mode: str = "api"):
    """
    Forces the central planner orchestrator loop to run a tick (step transition).
    Useful to run via REST or frontend trigger.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    updated_incident = await planner_agent.execute_step(incident, submission_mode=mode)
    db.save_incident(updated_incident)
    return updated_incident

# ---------------------------------------------------------
# 3. MOCK GOVERNMENT PORTAL SYSTEM
# ---------------------------------------------------------

@app.post("/api/mock-portal/submit")
async def submit_mock_portal_complaint(data: dict):
    """
    The endpoint hit by our portal submission tools (Playwright / direct API).
    Generates a tracking token and maps status.
    """
    incident_id = data.get("incident_id")
    issue_type = data.get("issue_type")
    
    # Generate unique complaint token
    token = f"BBMP-{uuid.uuid4().hex[:5].upper()}"
    MOCK_PORTAL_TICKETS[token] = {
        "incident_id": incident_id,
        "issue_type": issue_type,
        "status": "PENDING",
        "created_at": datetime.utcnow().isoformat()
    }
    logger.info(f"Mock Portal Ticket Created: {token}")
    return {"status": "success", "complaint_token": token}

@app.get("/api/mock-portal/tickets/{token}")
async def get_mock_portal_ticket(token: str):
    ticket = MOCK_PORTAL_TICKETS.get(token)
    if not ticket:
         raise HTTPException(status_code=404, detail="Ticket token not found")
    return ticket

# ---------------------------------------------------------
# 4. SIMULATION DASHBOARD TICKET MANIPULATIONS
# ---------------------------------------------------------

@app.post("/api/simulator/mark-resolved/{token}")
async def simulator_mark_resolved(token: str):
    """
    Forces the portal database status of a token to 'RESOLVED'.
    Allows the monitoring agent to detect change and transition state.
    """
    if token not in MOCK_PORTAL_TICKETS:
         raise HTTPException(status_code=404, detail="Token not found in Mock Portal")
         
    MOCK_PORTAL_TICKETS[token]["status"] = "RESOLVED"
    
    # Locate the active incident mapping to this token and transition it
    for inc in db.list_incidents():
        if inc.official_token == token:
            inc.status = "VERIFYING"
            inc.timeline.append(TimelineEvent(
                timestamp=datetime.now().strftime("%d %b %H:%M"),
                stage="MONITOR",
                decision="Portal resolution detected",
                confidence="100%",
                reason="External portal marked ticket status as RESOLVED.",
                next_action="Request citizen upload a resolution verification photo"
            ))
            db.save_incident(inc)
            return {"status": "success", "message": "Ticket marked resolved. Incident transitioned to VERIFYING."}
            
    return {"status": "success", "message": "Ticket status marked RESOLVED in portal database."}

@app.post("/api/simulator/trigger-sla-breach/{incident_id}")
async def simulator_trigger_sla_breach(incident_id: str):
    """
    Fast-forwards time by setting the SLA deadline to 1 hour in the past.
    Next tick of the monitoring agent will trigger an SLA breach and escalate.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident.sla_deadline = (datetime.now() - timedelta(hours=1)).isoformat()
    db.save_incident(incident)
    return {"status": "success", "message": "SLA deadline fast-forwarded. Triggering breach on next agent tick."}

@app.post("/api/simulator/simulate-crash/{incident_id}")
async def simulator_simulate_crash(incident_id: str):
    """
    Forces the incident into ESCALATED state, simulating a playwright or API portal submission crash.
    """
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident.status = "ESCALATED"
    incident.timeline.append(TimelineEvent(
        timestamp=datetime.now().strftime("%d %b %H:%M"),
        stage="TOOL",
        decision="Portal submission failed",
        confidence="0%",
        reason="Simulator override: Government submission database returned 504 Gateway Timeout.",
        next_action="Triggering automated human-in-the-loop escalation dispatch"
    ))
    incident.updated_at = datetime.now().isoformat()
    db.save_incident(incident)
    return {"status": "success", "message": "Portal crash simulation triggered."}

@app.get("/mock-portal", response_class=HTMLResponse)
async def serve_mock_portal():
    """
    Serves a simple visual HTML Form page representing the government portal.
    This page is loaded and filled in by Playwright browser automation.
    """
    return """
    <html>
        <head>
            <title>BBMP Municipal Incident Registration</title>
            <style>
                body { font-family: sans-serif; background: #0f172a; color: #f1f5f9; padding: 40px; }
                .form-box { max-width: 500px; margin: auto; background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; }
                input, select { width: 100%; padding: 8px; margin: 10px 0; background: #0f172a; color: #fff; border: 1px solid #475569; border-radius: 4px; }
                button { background: #10b981; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px; width: 100%; font-weight: bold; }
                button:hover { background: #059669; }
            </style>
        </head>
        <body>
            <div class="form-box">
                <h2>Mock BBMP Civic Portal</h2>
                <form id="portal-form" onsubmit="event.preventDefault(); submitForm();">
                    <label>Incident ID:</label>
                    <input type="text" id="incident-id" required>
                    <label>Issue Type:</label>
                    <select id="issue-type">
                        <option value="garbage">Garbage</option>
                        <option value="pothole">Pothole</option>
                        <option value="fallen_tree">Fallen Tree</option>
                    </select>
                    <label>Latitude:</label>
                    <input type="text" id="latitude" required>
                    <label>Longitude:</label>
                    <input type="text" id="longitude" required>
                    <label>Severity:</label>
                    <select id="severity">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                    <button type="submit" id="submit-btn">File Official Complaint</button>
                </form>
                <div id="result-box" style="margin-top:20px; display:none;">
                    <p>Submission Successful!</p>
                    <label>Tracking Token:</label>
                    <input type="text" id="complaint-token" readonly>
                </div>
            </div>
            <script>
                async function submitForm() {
                    const payload = {
                        incident_id: document.getElementById("incident-id").value,
                        issue_type: document.getElementById("issue-type").value,
                        latitude: parseFloat(document.getElementById("latitude").value),
                        longitude: parseFloat(document.getElementById("longitude").value),
                        severity: document.getElementById("severity").value
                    };
                    const response = await fetch("/api/mock-portal/submit", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    const res = await response.json();
                    document.getElementById("complaint-token").value = res.complaint_token;
                    document.getElementById("portal-form").style.display = "none";
                    document.getElementById("result-box").style.display = "block";
                }
            </script>
        </body>
    </html>
    """

@app.get("/api/incidents/{incident_id}/download-form")
async def download_incident_form(incident_id: str):
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    strategy_name = incident.current_strategy.name if incident.current_strategy else "Pending"
    dept_name = incident.current_strategy.department if incident.current_strategy else "Pending"
    sla_val = f"{incident.current_strategy.sla_hours} Hours" if incident.current_strategy else "Pending"
    conf_val = f"{int(incident.confidence * 100)}%" if incident.confidence else "0%"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ACIRP Civic Complaint Form - {incident.id}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1e293b;
      margin: 40px;
      line-height: 1.6;
      background: #ffffff;
    }}
    .header {{
      border-bottom: 3px double #cbd5e1;
      padding-bottom: 20px;
      margin-bottom: 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .header-text h1 {{
      margin: 0;
      font-size: 22px;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .header-text p {{
      margin: 4px 0 0 0;
      font-size: 11px;
      color: #64748b;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 1px;
    }}
    .badge {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1d4ed8;
      font-size: 10px;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .grid {{
      display: grid;
      grid-template-cols: 1fr 1fr;
      gap: 30px;
      margin-bottom: 30px;
    }}
    .section-title {{
      font-size: 11px;
      font-weight: 700;
      color: #475569;
      text-transform: uppercase;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 6px;
      margin-bottom: 12px;
      letter-spacing: 0.8px;
    }}
    .meta-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .meta-table td {{
      padding: 8px 0;
      vertical-align: top;
    }}
    .meta-table td.label {{
      color: #64748b;
      width: 130px;
      font-weight: 500;
    }}
    .meta-table td.value {{
      font-weight: 600;
      color: #0f172a;
    }}
    .statement-box {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px;
      font-size: 13px;
      color: #334155;
      margin-bottom: 40px;
      border-left: 4px solid #1a73e8;
    }}
    .footer {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-top: 60px;
      font-size: 11px;
      color: #64748b;
      border-top: 1px solid #cbd5e1;
      padding-top: 20px;
    }}
    .signature {{
      text-align: right;
    }}
    .signature-line {{
      width: 220px;
      border-top: 1px solid #0f172a;
      margin-bottom: 6px;
      margin-left: auto;
    }}
    .signature-title {{
      font-weight: 600;
      color: #0f172a;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="header-text">
      <h1>Municipal Civic Complaint Form</h1>
      <p>Automatically Compiled by ACIRP Orchestration System</p>
    </div>
    <div class="badge">Official AI Filing Node</div>
  </div>

  <div class="grid">
    <div>
      <div class="section-title">Complainant Details</div>
      <table class="meta-table">
        <tr>
          <td class="label">Filer Name</td>
          <td class="value">{incident.complainant_name}</td>
        </tr>
        <tr>
          <td class="label">Filer Type</td>
          <td class="value">Autonomous AI Filer Agent (ACIRP Platform)</td>
        </tr>
        <tr>
          <td class="label">Filing Agency</td>
          <td class="value">Google Build with AI Hackathon Node</td>
        </tr>
        <tr>
          <td class="label">Core Engine</td>
          <td class="value">ACIRP System Node v1.2.0</td>
        </tr>
      </table>
    </div>

    <div>
      <div class="section-title">Complaint Specifications</div>
      <table class="meta-table">
        <tr>
          <td class="label">Reference ID</td>
          <td class="value" style="font-family: monospace; font-size: 12px;">{incident.id}</td>
        </tr>
        <tr>
          <td class="label">Tracking Token</td>
          <td class="value" style="font-family: monospace; font-size: 12px;">{incident.official_token or "Awaiting Dispatch"}</td>
        </tr>
        <tr>
          <td class="label">Filing Date</td>
          <td class="value">{incident.created_at}</td>
        </tr>
        <tr>
          <td class="label">Current Status</td>
          <td class="value" style="color: #1d4ed8; text-transform: uppercase;">{incident.status}</td>
        </tr>
      </table>
    </div>
  </div>

  <div class="section-title">Filing Parameters & Routing Strategy</div>
  <div class="grid">
    <div>
      <table class="meta-table">
        <tr>
          <td class="label">GPS Coordinates</td>
          <td class="value">Lat: {incident.latitude}, Lng: {incident.longitude}</td>
        </tr>
        <tr>
          <td class="label">Issue Category</td>
          <td class="value" style="text-transform: uppercase;">{incident.issue_type or "Unclassified"}</td>
        </tr>
        <tr>
          <td class="label">Severity Level</td>
          <td class="value" style="text-transform: uppercase;">{incident.severity or "Low"}</td>
        </tr>
      </table>
    </div>

    <div>
      <table class="meta-table">
        <tr>
          <td class="label">Target Department</td>
          <td class="value">{dept_name}</td>
        </tr>
        <tr>
          <td class="label">Routing Strategy</td>
          <td class="value">{strategy_name}</td>
        </tr>
        <tr>
          <td class="label">Resolution SLA</td>
          <td class="value">{sla_val}</td>
        </tr>
      </table>
    </div>
  </div>

  <div class="section-title">Detailed Statement & AI Certification</div>
  <div class="statement-box">
    This complaint is filed automatically regarding a civic hazard detected at the coordinates listed above. 
    Our perception vision analysis has confirmed the issue with <strong>{conf_val}</strong> confidence.
    <br><br>
    The target authority (<strong>{dept_name}</strong>) is requested to dispatch a resolution team. 
    ACIRP will continuously monitor the portal status and escalate this complaint if it is not resolved within the SLA period.
  </div>

  <div class="footer">
    <div>
      System Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    <div class="signature">
      <div class="signature-line"></div>
      <div class="signature-title">ACIRP Autonomous Agent Engine</div>
      <div>Verification Node Cryptographic Signature</div>
    </div>
  </div>
</body>
</html>
"""
    from fastapi.responses import Response
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=ACIRP_Complaint_{incident_id}.html"
        }
    )

@app.get("/api/incidents/{incident_id}/download-escalation-letter")
async def download_escalation_letter(incident_id: str):
    incident = db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    escalation_paths = incident.current_strategy.escalation_path if incident.current_strategy else []
    # If level is 0, default to the first one in the list, otherwise use the level index
    target_idx = max(0, incident.escalation_level - 1)
    escalation_target = escalation_paths[target_idx] if target_idx < len(escalation_paths) else "Zonal Administration Commissioner"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>OFFICIAL ESCALATION NOTICE - {incident.id}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1e293b;
      margin: 50px;
      line-height: 1.8;
      background: #ffffff;
    }}
    .letterhead {{
      border-bottom: 2px solid #0f172a;
      padding-bottom: 15px;
      margin-bottom: 30px;
      text-align: center;
    }}
    .letterhead h1 {{
      margin: 0;
      font-size: 24px;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .letterhead p {{
      margin: 5px 0 0 0;
      font-size: 11px;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: 2px;
      font-weight: 600;
    }}
    .date-row {{
      text-align: right;
      font-size: 13px;
      color: #475569;
      margin-bottom: 30px;
    }}
    .recipient {{
      margin-bottom: 30px;
      font-size: 14px;
      font-weight: 600;
      color: #0f172a;
    }}
    .subject {{
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 30px;
      border-bottom: 1px dashed #cbd5e1;
      padding-bottom: 8px;
      font-size: 14px;
      color: #0f172a;
    }}
    .body-text {{
      font-size: 14px;
      margin-bottom: 40px;
      text-align: justify;
    }}
    .metadata-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 13px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
    }}
    .metadata-table th, .metadata-table td {{
      border: 1px solid #e2e8f0;
      padding: 10px 12px;
      text-align: left;
    }}
    .metadata-table th {{
      background: #f1f5f9;
      color: #475569;
      font-weight: 600;
      width: 160px;
    }}
    .signatures {{
      display: flex;
      justify-content: space-between;
      margin-top: 60px;
      font-size: 13px;
    }}
    .sig-block {{
      width: 250px;
      text-align: center;
    }}
    .sig-line {{
      border-top: 1px solid #0f172a;
      margin-top: 50px;
      margin-bottom: 6px;
    }}
    .sig-name {{
      font-weight: 600;
      color: #0f172a;
    }}
  </style>
</head>
<body>
  <div class="letterhead">
    <h1>ACIRP Autonomous Escalation Dispatch</h1>
    <p>Official Public Grievance Notification Node</p>
  </div>

  <div class="date-row">
    Date: {datetime.now().strftime("%d %B, %Y")}<br>
    Notice Ref: ACIRP-ESC-{incident.id}-{incident.escalation_level}
  </div>

  <div class="recipient">
    To,<br>
    The Office of the {escalation_target},<br>
    Municipal Administration Division,<br>
    Bengaluru, Karnataka.
  </div>

  <div class="subject">
    SUBJECT: FORMAL COMPLAINT ESCALATION REGARDING UNRESOLVED CIVIC SAFETY HAZARD
  </div>

  <div class="body-text">
    Dear Sir/Madam,
    <br><br>
    This is an official escalation notice issued automatically by the ACIRP Autonomous Sensing Network on behalf of citizen <strong>{incident.complainant_name}</strong>. 
    <br><br>
    A civic safety hazard representing a <strong>{incident.issue_type.upper().replace('_', ' ')}</strong> was identified and registered in the municipal database on <strong>{incident.created_at}</strong>. Despite the lapse of the designated Service Level Agreement (SLA) window of <strong>{incident.current_strategy.sla_hours} hours</strong>, the status of this ticket in the municipal portal remains unresolved (Portal Tracking Token: <strong>{incident.official_token or "PENDING"}</strong>).
    <br><br>
    Due to the persistent delay in local execution and corresponding safety risks, the case has been officially escalated to your office for immediate review and administrative dispatch.
    
    <table class="metadata-table">
      <tr>
        <th>Incident Reference ID</th>
        <td style="font-family: monospace;">{incident.id}</td>
      </tr>
      <tr>
        <th>GPS Coordinates</th>
        <td>Latitude: {incident.latitude}, Longitude: {incident.longitude}</td>
      </tr>
      <tr>
        <th>Visual Confidence</th>
        <td>{int((incident.confidence or 0.0) * 100)}% (Verified by Gemini Vision Core)</td>
      </tr>
      <tr>
        <th>Severity Level</th>
        <td style="text-transform: uppercase;">{incident.severity}</td>
      </tr>
      <tr>
        <th>Assigned Department</th>
        <td>{incident.current_strategy.department}</td>
      </tr>
    </table>
    
    We urge your office to issue immediate directions to the relevant field engineers to clear this hazard and update the municipal database registry.
  </div>

  <div class="signatures">
    <div class="sig-block">
      <div class="sig-line"></div>
      <div class="sig-name">{incident.complainant_name}</div>
      <div>Complainant (Citizen Filer)</div>
    </div>
    <div class="sig-block">
      <div class="sig-line"></div>
      <div class="sig-name">ACIRP Agent Node v1.2</div>
      <div>Autonomous Verification Authority</div>
    </div>
  </div>
</body>
</html>
"""
    from fastapi.responses import Response
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=ACIRP_Escalation_Letter_{incident_id}.html"
        }
    )

# ---------------------------------------------------------
# STATIC FILE SERVING FOR UPLOADED IMAGES
# ---------------------------------------------------------
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
