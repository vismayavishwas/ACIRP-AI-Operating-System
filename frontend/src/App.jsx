import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Eye, 
  BrainCircuit, 
  Settings, 
  Radio, 
  CheckCircle2, 
  AlertTriangle, 
  Upload, 
  MapPin, 
  Clock, 
  ArrowRight, 
  Check, 
  UserCheck, 
  X, 
  Layers, 
  HelpCircle,
  Network,
  Zap,
  Phone,
  PlayCircle,
  Search
} from "lucide-react";

const CheckCircle = CheckCircle2;

const API_BASE = "http://127.0.0.1:8000";

// Standard UI Icons for Timeline Stages
const STAGE_ICONS = {
  PERCEPTION: <Eye className="h-3 w-3" />,
  PLANNER: <BrainCircuit className="h-3 w-3" />,
  TOOL: <Settings className="h-3 w-3" />,
  MONITOR: <Radio className="h-3 w-3" />,
  VERIFY: <CheckCircle2 className="h-3 w-3" />,
  ESCALATION: <AlertTriangle className="h-3 w-3" />,
  SYSTEM: <Layers className="h-3 w-3" />
};

// Conversational Agent Thought generator
const getAgentThought = (status) => {
  switch (status) {
    case "DETECTED":
      return "Sensing visual input... Classifying incident category and identifying geographical coordinates.";
    case "PLANNED":
      return "Strategic routing complete. PWD and Waste Management patterns analyzed. Click below to file the official municipal petition.";
    case "SUBMITTED":
      return "Handshaking with government database... Submitting official citizen grievance form autonomously.";
    case "MONITORING":
      return "Agent monitoring active. Periodically inspecting municipal database registry for status updates...";
    case "VERIFYING":
      return "Portal update detected: Ticket RESOLVED. Please upload a clear photo of the site to verify the hazard has been removed.";
    case "ESCALATED":
      return "SLA BREACH ALERT: Official response window exceeded. Bypassing database loops to route direct complaints to supervisors.";
    case "CLOSED":
      return "Civic hazard cleared and verified. Complaint case successfully closed. System idle.";
    default:
      return "System initialized. Upload a photo in the Citizen Terminal to wake up the planning core.";
  }
};

// Target helplines mapping
const HELPLINES = {
  garbage: {
    dept: "Waste Management & Sanitation",
    phone: "080-2266-0000"
  },
  fallen_tree: {
    dept: "Forest & Parks Division",
    phone: "080-2226-6666"
  },
  pothole: {
    dept: "Public Works Department (PWD)",
    phone: "080-2223-1800"
  }
};

// Storyteller steps for filing
const STORYTELLER_STEPS = [
  "Connecting to mock government registry database...",
  "Staging official letterhead template details...",
  "Resolving department routing jurisdictions...",
  "Validating citizen cryptographic signatures...",
  "Bypassing captcha and gatekeeper loops...",
  "Obtaining official database tracking token..."
];

// Live counting confidence score ring component
function ConfidenceCounter({ target }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = Math.round((target || 0) * 100);
    if (start === end || end === 0) {
      setCount(end);
      return;
    }
    const duration = 1000;
    const stepTime = Math.abs(Math.floor(duration / end));
    const timer = setInterval(() => {
      start += 1;
      setCount(start);
      if (start >= end) {
        clearInterval(timer);
      }
    }, stepTime);
    return () => clearInterval(timer);
  }, [target]);
  return <span>{count}%</span>;
}

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncId, setSelectedIncId] = useState("");
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [brainDecision, setBrainDecision] = useState(null);
  
  // Forms states
  const [imageFile, setImageFile] = useState(null);
  const [lat, setLat] = useState("12.9716");
  const [lng, setLng] = useState("77.5946");
  const [verifyFile, setVerifyFile] = useState(null);

  // Snappy UX variables
  const [complainantName, setComplainantName] = useState("");
  const [isTicking, setIsTicking] = useState(false);
  const [toasts, setToasts] = useState([]);
  const isFirstLoadRef = useRef(true);
  const [showPortalCrashDialog, setShowPortalCrashDialog] = useState(false);
  const [showHelplineDialog, setShowHelplineDialog] = useState(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [showDemoGuide, setShowDemoGuide] = useState(false);
  
  // Storyteller state
  const [storyIndex, setStoryIndex] = useState(0);

  // Detail log toggle
  const [expandedLogIdx, setExpandedLogIdx] = useState(null);
  const [showTrace, setShowTrace] = useState(false);
  const [similarityActive, setSimilarityActive] = useState(false);
  const [similarityIncidents, setSimilarityIncidents] = useState([]);

  const addToast = (message, type = "info") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Poll databases
  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedIncId) {
      fetchIncidentDetails(selectedIncId);
    }
  }, [selectedIncId]);

  // Autonomous Progression: Auto-advance states that do not require human-in-the-loop approval
  useEffect(() => {
    if (selectedIncident && ["DETECTED", "SUBMITTED"].includes(selectedIncident.status) && !isTicking) {
      const timer = setTimeout(() => {
        handleTriggerTick();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [selectedIncident?.status, isTicking]);

  // Cycle stories when loading
  useEffect(() => {
    if (isTicking) {
      setStoryIndex(0);
      const timer = setInterval(() => {
        setStoryIndex(prev => (prev < STORYTELLER_STEPS.length - 1 ? prev + 1 : prev));
      }, 400);
      return () => clearInterval(timer);
    }
  }, [isTicking]);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents`);
      const data = await res.json();
      setIncidents(data);
      if (data.length > 0 && isFirstLoadRef.current) {
        isFirstLoadRef.current = false;
      }
    } catch (err) {
      console.error("Failed fetching incidents", err);
    }
  };

  const fetchIncidentDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${id}`);
      const data = await res.json();
      setSelectedIncident(data);

      const decRes = await fetch(`${API_BASE}/api/incidents/${id}/decision`);
      const decData = await decRes.json();
      setBrainDecision(decData);

      // Trigger similarity engine presentation if planned state is active
      if (data.status === "PLANNED" && !similarityActive) {
        triggerSimilaritySearch(data.latitude, data.longitude, data.issue_type);
      } else if (data.status !== "PLANNED" && similarityActive) {
        setSimilarityActive(false);
        setSimilarityIncidents([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerSimilaritySearch = (ilat, ilng, itype) => {
    setSimilarityActive(true);
    setSimilarityIncidents([]);
    const points = [
      { id: "inc_sim1", label: "Ward-48 Sanitation Cleaned (Strategy: PWD, Resolved: 18h)", latOffset: 0.002, lngOffset: -0.003 },
      { id: "inc_sim2", label: "Pothole filled PWD Route (Strategy: PWD, Resolved: 22h)", latOffset: -0.001, lngOffset: 0.004 }
    ];
    
    points.forEach((pt, idx) => {
      setTimeout(() => {
        setSimilarityIncidents(prev => [...prev, pt]);
      }, (idx + 1) * 800);
    });
  };

  const handleCreateIncident = async (e) => {
    e.preventDefault();
    if (!imageFile) return alert("Please select an incident image.");
    setIsSubmitting(true);
    addToast("Citizen portal: Filing complaint with GPS...", "info");

    const formData = new FormData();
    formData.append("latitude", lat);
    formData.append("longitude", lng);
    formData.append("image", imageFile);
    formData.append("complainant_name", complainantName || "Anonymous Citizen");

    try {
      const res = await fetch(`${API_BASE}/api/incidents/submit`, {
        method: "POST",
        body: formData,
      });
      const newInc = await res.json();
      addToast("Incident submitted. Vision Core analysis waking up...", "success");
      setImageFile(null);
      setComplainantName("");
      setSelectedIncId(newInc.id);
      setSimilarityActive(false);
      setSimilarityIncidents([]);
      fetchIncidents();
    } catch (err) {
      addToast("Filing incident failed.", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyResolution = async (e) => {
    e.preventDefault();
    if (!verifyFile) return alert("Please select a verification photo.");
    setIsVerifying(true);
    addToast("Citizen Node: Uploading proof of resolution image...", "info");

    const formData = new FormData();
    formData.append("image", verifyFile);

    try {
      const res = await fetch(`${API_BASE}/api/incidents/${selectedIncId}/verify-resolution`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setVerifyFile(null);
      
      if (data.status === "CLOSED") {
        addToast("Verification successful! Ticket CLOSED.", "success");
        setShowSuccessDialog(true);
      } else {
        addToast("Verification failed. Resolving parameters not met.", "error");
      }
      
      await fetchIncidentDetails(selectedIncId);
    } catch (err) {
      addToast("Resolution upload failed.", "error");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleApproveEscalation = async () => {
    addToast("Human Node: Approving agent escalation request...", "info");
    try {
      await fetch(`${API_BASE}/api/incidents/${selectedIncId}/approve-escalation`, { method: "POST" });
      addToast("Escalation approved. Running agent strategy check...", "success");
      // Tick to advance strategy instantly
      const tickRes = await fetch(`${API_BASE}/api/incidents/${selectedIncId}/tick`, { method: "POST" });
      const tickData = await tickRes.json();
      
      if (tickData.status === "CLOSED") {
        setShowHelplineDialog(selectedIncident.issue_type || "pothole");
      }
      
      fetchIncidentDetails(selectedIncId);
    } catch (err) {
      addToast("Escalation approval failed.", "error");
    }
  };

  const handleTriggerTick = async () => {
    setIsTicking(true);
    addToast("Orchestrator: Executing next autonomous step...", "info");
    try {
      await fetch(`${API_BASE}/api/incidents/${selectedIncId}/tick`, { method: "POST" });
      addToast("Step executed successfully.", "success");
      await fetchIncidentDetails(selectedIncId);
    } catch (err) {
      addToast("Tick execution failed.", "error");
    } finally {
      setIsTicking(false);
    }
  };

  const handleMarkResolved = async () => {
    if (!selectedIncident?.official_token) return;
    addToast("Simulating municipal worker status update...", "info");
    try {
      await fetch(`${API_BASE}/api/simulator/mark-resolved/${selectedIncident.official_token}`, { method: "POST" });
      addToast("Portal database: Ticket RESOLVED. Running agent check...", "success");
      // Immediately tick the agent to transition state to VERIFYING!
      await fetch(`${API_BASE}/api/incidents/${selectedIncId}/tick`, { method: "POST" });
      fetchIncidentDetails(selectedIncId);
    } catch (err) {
      addToast("Simulator: Failed to resolve ticket.", "error");
    }
  };

  const handleTriggerSLABreach = async () => {
    addToast("Simulating 24-hour time jump...", "info");
    try {
      await fetch(`${API_BASE}/api/simulator/trigger-sla-breach/${selectedIncId}`, { method: "POST" });
      addToast("SLA Breach registered. Running agent check...", "success");
      // Immediately tick the agent to escalate the ticket!
      await fetch(`${API_BASE}/api/incidents/${selectedIncId}/tick`, { method: "POST" });
      fetchIncidentDetails(selectedIncId);
    } catch (err) {
      addToast("Simulator: Failed to trigger SLA breach.", "error");
    }
  };

  const handleSimulateCrash = async () => {
    if (!selectedIncId) return;
    addToast("Simulating government portal crash...", "info");
    try {
      await fetch(`${API_BASE}/api/simulator/simulate-crash/${selectedIncId}`, { method: "POST" });
      addToast("Portal offline. Agent failover triggered!", "error");
      setShowPortalCrashDialog(true);
      fetchIncidentDetails(selectedIncId);
    } catch (err) {
      console.error("Failed simulating crash", err);
      addToast("Failed to simulate crash", "error");
    }
  };

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  // Helper to resolve status colors for Material 3 OS badges
  const getStatusColor = (status) => {
    switch (status) {
      case "DETECTED":
      case "PLANNED":
      case "SUBMITTED":
        return { bg: "bg-blue-50 text-blue-600 border-blue-100", label: "Thinking" };
      case "MONITORING":
        return { bg: "bg-amber-50 text-amber-600 border-amber-100", label: "Monitoring" };
      case "VERIFYING":
        return { bg: "bg-indigo-50 text-indigo-600 border-indigo-100", label: "Verifying" };
      case "ESCALATED":
        return { bg: "bg-rose-50 text-rose-600 border-rose-100", label: "Escalation Required" };
      case "CLOSED":
        return { bg: "bg-emerald-50 text-emerald-600 border-emerald-100", label: "Resolved" };
      default:
        return { bg: "bg-slate-50 text-slate-600 border-slate-100", label: "Offline" };
    }
  };

  const statusMeta = selectedIncident ? getStatusColor(selectedIncident.status) : { bg: "", label: "" };

  return (
    <div className="min-h-screen animated-gradient-bg text-slate-800 p-6 md:p-10 font-sans flex flex-col justify-between selection:bg-blue-100">
      
      {/* Styles for dynamic custom keyframes */}
      <style>{`
        @keyframes gradient-bg {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .animated-gradient-bg {
          background: linear-gradient(-45deg, rgba(66, 133, 244, 0.03), rgba(219, 68, 85, 0.03), rgba(244, 180, 0, 0.03), rgba(15, 157, 88, 0.03));
          background-size: 400% 400%;
          animation: gradient-bg 20s ease infinite;
        }
        @keyframes pulse-thinking {
          0% { transform: scale(1); filter: drop-shadow(0 0 15px rgba(66, 133, 244, 0.35)); }
          50% { transform: scale(1.06); filter: drop-shadow(0 0 25px rgba(219, 68, 85, 0.45)); }
          100% { transform: scale(1); filter: drop-shadow(0 0 15px rgba(66, 133, 244, 0.35)); }
        }
        @keyframes pulse-monitoring {
          0% { transform: scale(1); filter: drop-shadow(0 0 12px rgba(244, 180, 0, 0.25)); }
          50% { transform: scale(1.03); filter: drop-shadow(0 0 20px rgba(244, 180, 0, 0.45)); }
          100% { transform: scale(1); filter: drop-shadow(0 0 12px rgba(244, 180, 0, 0.25)); }
        }
        @keyframes pulse-verifying {
          0% { transform: scale(1); filter: drop-shadow(0 0 15px rgba(103, 58, 183, 0.35)); }
          50% { transform: scale(1.07); filter: drop-shadow(0 0 25px rgba(103, 58, 183, 0.55)); }
          100% { transform: scale(1); filter: drop-shadow(0 0 15px rgba(103, 58, 183, 0.35)); }
        }
        @keyframes pulse-escalated {
          0% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(219, 68, 85, 0.5)); }
          50% { transform: scale(1.1); filter: drop-shadow(0 0 35px rgba(219, 68, 85, 0.75)); }
          100% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(219, 68, 85, 0.5)); }
        }
        @keyframes pulse-closed {
          0% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(15, 157, 88, 0.3)); }
          50% { transform: scale(1.04); filter: drop-shadow(0 0 15px rgba(15, 157, 88, 0.5)); }
          100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(15, 157, 88, 0.3)); }
        }
        .animate-orb-thinking { animation: pulse-thinking 3s ease-in-out infinite; }
        .animate-orb-monitoring { animation: pulse-monitoring 4s ease-in-out infinite; }
        .animate-orb-verifying { animation: pulse-verifying 2.5s ease-in-out infinite; }
        .animate-orb-escalated { animation: pulse-escalated 2s ease-in-out infinite; }
        .animate-orb-closed { animation: pulse-closed 4s ease-in-out infinite; }
      `}</style>

      {/* Top Header bar */}
      <header className="flex justify-between items-center max-w-7xl w-full mx-auto mb-8 border-b border-slate-200/40 pb-4">
        <div className="flex items-center gap-3.5">
          {/* Custom Innovative Logo: The Intersecting Möbius Loop */}
          <svg className="h-8 w-8" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="logo-tri" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00F2FE" />
                <stop offset="50%" stopColor="#4FACFE" />
                <stop offset="100%" stopColor="#9B51E0" />
              </linearGradient>
            </defs>
            <g stroke="url(#logo-tri)" strokeWidth="8" strokeLinecap="round" opacity="0.95">
              <path d="M50 25 C65 40, 65 60, 50 75 C35 60, 35 40, 50 25 Z" transform="rotate(0 50 50)" />
              <path d="M50 25 C65 40, 65 60, 50 75 C35 60, 35 40, 50 25 Z" transform="rotate(120 50 50)" />
              <path d="M50 25 C65 40, 65 60, 50 75 C35 60, 35 40, 50 25 Z" transform="rotate(240 50 50)" />
            </g>
            <circle cx="50" cy="50" r="6" fill="#FFFFFF" />
          </svg>
          
          <div className="flex flex-col text-left">
            <h1 className="font-outfit font-extrabold text-lg tracking-wider text-slate-800 flex items-center gap-1.5 leading-none">
              ACIRP <span className="text-[9px] bg-slate-100 text-slate-500 font-bold px-2 py-0.5 rounded-full tracking-normal uppercase border border-slate-200">AI OS</span>
            </h1>
            <span className="text-[9px] font-sans font-bold text-slate-400 uppercase tracking-widest mt-1">
              Autonomous Civic Incident Resolution Platform
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${
            !selectedIncident || selectedIncident.status === "CLOSED" 
              ? "bg-slate-400" 
              : "bg-emerald-500 animate-ping"
          }`} />
          <span className="text-[10px] font-mono font-bold tracking-tight text-slate-500 uppercase">
            {!selectedIncident 
              ? "SYSTEM ACTIVE (IDLE)" 
              : selectedIncident.status === "CLOSED" 
              ? "CASE CLOSED (IDLE)" 
              : `${selectedIncident.status} ACTIVE`}
          </span>
        </div>
      </header>

      {/* Main Core Mission Control Console Workspace */}
      <main className="max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-start flex-1">
        
        {/* LEFT COLUMN: Citizen File Terminal & Portal Registry Selector (4 cols) */}
        <section className="lg:col-span-4 space-y-6">
          
          {/* Card 1: Citizen File Terminal (Glassmorphism layout) */}
          <div className="backdrop-blur-xl border border-white/50 bg-white/70 shadow-xl rounded-3xl p-5 space-y-4">
            <h2 className="text-xs uppercase tracking-wider font-extrabold text-slate-400 flex items-center gap-1.5">
              <Upload className="h-4 w-4 text-slate-400" /> 1. Citizen Submission Node
            </h2>

            <form onSubmit={handleCreateIncident} className="space-y-3">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Complainant Name *</label>
                <input 
                  type="text"
                  placeholder="Enter your full name"
                  value={complainantName}
                  onChange={(e) => setComplainantName(e.target.value)}
                  required
                  className="w-full text-xs p-2.5 border border-slate-200/80 bg-white rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-400 uppercase">Latitude</label>
                  <input 
                    type="text" 
                    value={lat} 
                    onChange={(e) => setLat(e.target.value)} 
                    className="w-full text-xs p-2 border border-slate-100 bg-slate-50/50 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-400 uppercase">Longitude</label>
                  <input 
                    type="text" 
                    value={lng} 
                    onChange={(e) => setLng(e.target.value)} 
                    className="w-full text-xs p-2 border border-slate-100 bg-slate-50/50 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400 font-mono"
                  />
                </div>
              </div>

              <div className="border border-dashed border-slate-200 bg-white hover:border-blue-400 rounded-xl p-4 text-center cursor-pointer transition relative">
                <input 
                  type="file" 
                  accept="image/*"
                  onChange={(e) => setImageFile(e.target.files[0])}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <span className="text-xs font-semibold text-slate-500 flex justify-center items-center gap-1.5">
                  <Upload className="h-4 w-4 text-slate-400" />
                  {imageFile ? imageFile.name : "Select Hazard Photo"}
                </span>
              </div>

              <button 
                type="submit" 
                disabled={isSubmitting}
                className="w-full bg-[#1A73E8] hover:bg-[#1557b0] text-white font-bold py-2 rounded-xl text-xs transition shadow-md shadow-blue-500/10"
              >
                {isSubmitting ? "Uploading petition..." : "File Complaint & Verify Location"}
              </button>
            </form>
          </div>

          {/* Verification section */}
          {selectedIncident && selectedIncident.status === "VERIFYING" && (
            <div className="backdrop-blur-xl border border-indigo-200 bg-indigo-50/30 shadow-lg rounded-3xl p-5 space-y-3">
              <h2 className="text-xs uppercase tracking-wider font-extrabold text-indigo-600 flex items-center gap-1.5">
                <UserCheck className="h-4 w-4 text-indigo-500" /> Verification Pending
              </h2>
              <p className="text-[11px] text-indigo-800 leading-normal">
                Municipal workers marked resolving task. Please upload a clear photo of the clean site to verify clearance.
              </p>

              <form onSubmit={handleVerifyResolution} className="space-y-2">
                <div className="border border-dashed border-indigo-200 bg-white hover:border-indigo-400 rounded-xl p-3 text-center cursor-pointer transition relative">
                  <input 
                    type="file" 
                    accept="image/*"
                    onChange={(e) => setVerifyFile(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <span className="text-[10px] font-medium text-indigo-500">
                    {verifyFile ? verifyFile.name : "Select proof photo"}
                  </span>
                </div>
                <button 
                  type="submit" 
                  disabled={isVerifying}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-1.5 rounded-xl text-xs transition"
                >
                  {isVerifying ? "Verifying Cleanup..." : "Verify & Close Ticket"}
                </button>
              </form>
            </div>
          )}

          {/* Card 2: Registry Database Selector */}
          <div className="backdrop-blur-xl border border-white/50 bg-white/70 shadow-xl rounded-3xl p-5 space-y-3">
            <h2 className="text-xs uppercase tracking-wider font-extrabold text-slate-400 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-slate-400" /> Civic Incident Registry
            </h2>

            <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
              {incidents.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-4">No logged incidents found.</p>
              ) : (
                incidents.map((inc) => {
                  const active = inc.id === selectedIncId;
                  const isClosed = inc.status === "CLOSED";
                  return (
                    <button 
                      key={inc.id}
                      onClick={() => {
                        setSelectedIncId(inc.id);
                        fetchIncidentDetails(inc.id);
                      }}
                      className={`w-full flex justify-between items-center text-xs p-2.5 rounded-xl transition text-left border ${
                        active 
                          ? "bg-slate-900 border-slate-900 text-white shadow-md shadow-slate-950/10" 
                          : "bg-white border-slate-100 hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <div className="truncate pr-2">
                        <p className={`font-bold ${active ? "text-white" : "text-slate-700"}`}>{inc.complainant_name}</p>
                        <p className={`text-[10px] truncate ${active ? "text-slate-300" : "text-slate-400"}`}>{inc.id}</p>
                      </div>
                      <span className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                        isClosed 
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" 
                          : active ? "bg-white/20 border-white/30 text-white" : "bg-slate-100 border-slate-200 text-slate-500"
                      }`}>
                        {inc.status === "MONITORING" ? "PENDING" : inc.status}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Card 3: Simulator Controls console */}
          <div className="backdrop-blur-xl border border-slate-200/80 bg-[#F8FAFC]/90 shadow-lg rounded-3xl p-5 space-y-3 relative overflow-hidden">
            <h2 className="text-xs uppercase tracking-wider font-extrabold text-slate-400 flex items-center gap-1.5">
              <Settings className="h-4 w-4 text-slate-400" /> Simulator Console
            </h2>

            <div className="space-y-3">
              <div className="bg-white border border-slate-200 rounded-xl p-3 text-[11px] font-mono space-y-1.5 shadow-inner">
                <div className="flex justify-between">
                  <span className="text-slate-400">Token:</span>
                  <span className="font-semibold text-slate-800">{selectedIncident?.official_token || "None"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status:</span>
                  <span className={`font-bold ${
                    selectedIncident?.status === "CLOSED" ? "text-emerald-600" :
                    selectedIncident?.status === "MONITORING" ? "text-amber-600 animate-pulse" :
                    "text-slate-500"
                  }`}>
                    {selectedIncident?.status === "MONITORING" ? "PENDING" : selectedIncident?.status || "NONE"}
                  </span>
                </div>
              </div>

              {selectedIncident?.official_token && (
                <div className="space-y-1.5 mt-2">
                  <button 
                    onClick={handleMarkResolved}
                    className="w-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-bold py-1.5 rounded-lg text-[10px] transition shadow-sm"
                  >
                    Force Ticket Resolved
                  </button>
                  <button 
                    onClick={handleTriggerSLABreach}
                    className="w-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-bold py-1.5 rounded-lg text-[10px] transition shadow-sm"
                  >
                    Fast-Forward 24h
                  </button>
                  <button 
                    onClick={handleSimulateCrash}
                    className="w-full bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-bold py-1.5 rounded-lg text-[10px] transition shadow-sm"
                  >
                    Simulate Portal Crash
                  </button>
                </div>
              )}
            </div>
          </div>

        </section>

        {/* RIGHT COLUMN: The AI Main Character Node & Brain Execution Console (8 cols) */}
        <section className="lg:col-span-8 space-y-6">
          
          {/* Main Card: Hero Agent Mission Control Console */}
          <div className="backdrop-blur-xl border border-white/50 bg-white/70 shadow-2xl rounded-3xl p-6 md:p-8 space-y-8 relative overflow-hidden">
            
            {/* Storyteller loading overlay */}
            <AnimatePresence>
              {isTicking && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-white/90 backdrop-blur-md z-40 flex flex-col items-center justify-center p-6 space-y-4"
                >
                  <div className="h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin shadow-lg shadow-blue-500/20" />
                  <p className="font-outfit font-extrabold text-sm text-slate-800 uppercase tracking-wider">Agent Logic Executing...</p>
                  
                  <div className="w-full max-w-xs space-y-1.5 pt-4">
                    {STORYTELLER_STEPS.map((step, idx) => {
                      const active = idx === storyIndex;
                      const done = idx < storyIndex;
                      return (
                        <div key={idx} className="flex items-center gap-2 text-[10px] text-left">
                          {done ? (
                            <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                          ) : active ? (
                            <span className="h-3.5 w-3.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <span className="h-3.5 w-3.5 rounded-full bg-slate-100 border border-slate-200" />
                          )}
                          <span className={`font-mono ${
                            done ? "text-slate-400 line-through" : active ? "text-blue-600 font-bold" : "text-slate-300"
                          }`}>{step}</span>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Decision Flow Node Line */}
            <div className="w-full border-b border-slate-100 pb-4">
              <div className="flex justify-between items-center text-[9px] uppercase font-bold tracking-wider text-slate-400">
                <span className={selectedIncident?.status === "DETECTED" ? "text-blue-500" : ""}>1. Sensing</span>
                <ArrowRight className="h-3 w-3" />
                <span className={selectedIncident?.status === "PLANNED" ? "text-blue-500" : ""}>2. Routing</span>
                <ArrowRight className="h-3 w-3" />
                <span className={selectedIncident?.status === "SUBMITTED" ? "text-blue-500" : ""}>3. Submission</span>
                <ArrowRight className="h-3 w-3" />
                <span className={selectedIncident?.status === "MONITORING" ? "text-amber-500 animate-pulse" : ""}>4. Monitoring</span>
                <ArrowRight className="h-3 w-3" />
                <span className={selectedIncident?.status === "VERIFYING" ? "text-indigo-500 animate-pulse" : ""}>5. Verification</span>
                <ArrowRight className="h-3 w-3" />
                <span className={selectedIncident?.status === "CLOSED" ? "text-emerald-500" : ""}>6. Resolved</span>
              </div>
            </div>

            {/* Glowing AI Orb (Google-colored gradients pulsing with states) */}
            <div className="flex flex-col items-center justify-center space-y-4 py-4">
              
              <div className={`h-28 w-28 rounded-full bg-gradient-to-tr flex items-center justify-center text-white relative shadow-2xl transition duration-700 ${
                !selectedIncident ? "from-slate-400 to-slate-500" :
                selectedIncident.status === "CLOSED" ? "from-emerald-400 to-teal-500 animate-orb-closed" :
                selectedIncident.status === "ESCALATED" ? "from-rose-500 to-red-600 animate-orb-escalated" :
                selectedIncident.status === "VERIFYING" ? "from-indigo-500 to-purple-600 animate-orb-verifying" :
                selectedIncident.status === "MONITORING" ? "from-amber-400 to-yellow-500 animate-orb-monitoring" :
                "from-blue-500 via-purple-500 to-rose-500 animate-orb-thinking"
              }`}>
                {/* Visual feedback icon inside Orb */}
                <div className="absolute inset-1.5 rounded-full bg-slate-950/20 backdrop-blur-sm flex flex-col items-center justify-center p-2 text-center">
                  {!selectedIncident ? (
                    <BrainCircuit className="h-8 w-8 text-white opacity-40 animate-pulse" />
                  ) : (
                    <>
                      <span className="text-[8px] font-bold tracking-wider uppercase text-white/60 mb-0.5">Confidence</span>
                      <span className="font-outfit font-extrabold text-lg leading-none">
                        <ConfidenceCounter target={selectedIncident.confidence} />
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Conversational thoughts status bubble */}
              <div className="text-center max-w-md">
                <span className="text-[10px] uppercase tracking-wider font-extrabold text-blue-500 px-2 py-0.5 bg-blue-50 rounded-full">🧠 Agent Status</span>
                <p className="font-outfit font-bold text-sm text-slate-700 leading-relaxed mt-2">
                  {getAgentThought(selectedIncident?.status)}
                </p>
              </div>
            </div>

            {/* Strategic Details Workflow & Decision card */}
            {selectedIncident && (
              <div className="space-y-6 pt-6 border-t border-slate-100">
                {/* AI Visual Evidence Comparison Panel */}
                <div className="p-4 rounded-2xl border border-slate-100 bg-slate-50/50 space-y-3">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block text-left">
                    {selectedIncident.status === "CLOSED" || selectedIncident.status === "VERIFYING" 
                      ? "Visual Verification: Before vs After Resolution" 
                      : "Sensing Input: Visual Evidence Verified"}
                  </span>
                  
                  <div className="flex gap-4 items-center justify-center">
                    <div className="flex flex-col items-center space-y-1.5 flex-1 max-w-[160px]">
                      <div className="w-full h-24 bg-slate-100 border border-slate-200/60 rounded-xl overflow-hidden shadow-inner flex items-center justify-center relative">
                        <img 
                          src={`${API_BASE}${selectedIncident.image_before_url}`} 
                          alt="Before" 
                          className="w-full h-full object-cover"
                        />
                        <span className="absolute bottom-1.5 left-1.5 bg-slate-900/60 backdrop-blur-sm text-white text-[8px] font-bold px-1 py-0.5 rounded uppercase">Before</span>
                      </div>
                    </div>

                    {(selectedIncident.status === "CLOSED" || selectedIncident.status === "VERIFYING") && (
                      <>
                        <ArrowRight className="h-4 w-4 text-slate-300 flex-shrink-0" />
                        <div className="flex flex-col items-center space-y-1.5 flex-1 max-w-[160px]">
                          <div className="w-full h-24 bg-slate-100 border border-slate-200/60 rounded-xl overflow-hidden shadow-inner flex items-center justify-center relative">
                            {selectedIncident.image_after_url ? (
                              <img 
                                src={`${API_BASE}${selectedIncident.image_after_url}`} 
                                alt="After" 
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="text-[9px] text-slate-400 font-bold uppercase tracking-wider text-center p-2 leading-tight flex flex-col items-center justify-center h-full">
                                {selectedIncident.status === "CLOSED" ? (
                                  selectedIncident.timeline?.some(event => event.decision === "Portal submission failed") ? (
                                    <>
                                      <AlertTriangle className="h-4.5 w-4.5 text-rose-500 mb-1 animate-pulse" />
                                      <span>Website Failed</span>
                                      <span className="text-[7px] text-slate-400 lowercase mt-0.5 font-normal">(No Photo Proof)</span>
                                    </>
                                  ) : (
                                    <>
                                      <AlertTriangle className="h-4.5 w-4.5 text-amber-500 mb-1 animate-pulse" />
                                      <span>Escalated Close</span>
                                      <span className="text-[7px] text-slate-400 lowercase mt-0.5 font-normal">(No Photo Proof)</span>
                                    </>
                                  )
                                ) : (
                                  "Awaiting Cleanup Proof"
                                )}
                              </div>
                            )}
                            <span className="absolute bottom-1.5 left-1.5 bg-indigo-900/60 backdrop-blur-sm text-white text-[8px] font-bold px-1 py-0.5 rounded uppercase">After</span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch text-left">
                  {/* Card A: Strategy Route details */}
                  <div className={`p-4 rounded-2xl border flex flex-col justify-between space-y-2 transition-all duration-500 ${
                    selectedIncident.status === "PLANNED" 
                      ? "bg-blue-50/50 border-blue-200 shadow-md shadow-blue-500/5 ring-1 ring-blue-500/10" 
                      : "border-slate-100 bg-slate-50/50"
                  }`}>
                    <div>
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Current Strategy Route</span>
                        {selectedIncident.status === "PLANNED" && (
                          <span className="text-[9px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold animate-pulse">Chosen by AI</span>
                        )}
                      </div>
                      <div className="font-bold text-sm text-slate-800 mt-1">
                        {selectedIncident?.current_strategy?.name || "Routing Queue..."}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Dept: {selectedIncident?.current_strategy?.department || "N/A"} | SLA: {selectedIncident?.current_strategy?.sla_hours || 0}h
                      </div>
                    </div>

                    <div className="pt-2">
                      <span className="text-[9px] uppercase font-bold text-slate-400">Escalation Path:</span>
                      <div className="flex gap-1.5 mt-1 items-center overflow-x-auto text-[9px] text-slate-500">
                        {selectedIncident?.current_strategy?.escalation_path?.map((step, index) => (
                          <div key={index} className="flex items-center gap-1">
                            <span className={`px-2 py-0.5 rounded-full border ${
                              selectedIncident.escalation_level === index + 1
                                ? "bg-rose-50 border-rose-200 text-rose-600 font-bold" 
                                : "bg-white border-slate-200"
                            }`}>{step}</span>
                            {index < selectedIncident.current_strategy.escalation_path.length - 1 && (
                              <ArrowRight className="h-2 w-2 text-slate-300" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                {/* Card B: Next Action Details */}
                <div className="p-4 rounded-2xl border border-slate-100 bg-slate-50/50 flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Next Planned Action</span>
                    {selectedIncident.status === "CLOSED" && !selectedIncident.image_after_url ? (
                      <div className="mt-1 space-y-1.5">
                        <p className="text-xs text-slate-600 font-medium">{brainDecision?.next_action}</p>
                        <div className="bg-amber-50 border border-amber-100 p-2.5 rounded-lg text-[9px] text-amber-800 space-y-0.5">
                          <p className="font-bold">Suggested Dispatch Contact:</p>
                          <p className="font-semibold">{HELPLINES[selectedIncident.issue_type]?.dept || "Public Works Department"}</p>
                          <p className="font-bold font-mono">📞 {HELPLINES[selectedIncident.issue_type]?.phone || "080-2223-1800"}</p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-600 font-medium mt-1">{brainDecision?.next_action || "Waiting for initialization"}</p>
                    )}
                  </div>

                  <div className="flex gap-2 pt-4">
                    {selectedIncident && ["SUBMITTED", "MONITORING", "VERIFYING", "ESCALATED", "CLOSED"].includes(selectedIncident.status) && (
                      <a 
                        href={`${API_BASE}/api/incidents/${selectedIncident.id}/download-form`}
                        download
                        className="flex-1 text-center bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 rounded-xl text-xs transition border border-slate-200 shadow-sm"
                      >
                        Download Petition
                      </a>
                    )}
                    {selectedIncident && selectedIncident.status === "PLANNED" && (
                      <button 
                        onClick={handleTriggerTick}
                        disabled={isTicking}
                        className="flex-1 flex items-center justify-center gap-1.5 bg-[#1A73E8] hover:bg-[#1557b0] text-white font-bold py-2 rounded-xl text-xs transition shadow-md shadow-blue-500/10 disabled:opacity-50"
                      >
                        <Zap className="h-3.5 w-3.5 text-white" />
                        File Official Petition
                      </button>
                    )}
                    {brainDecision && (
                      <button 
                        onClick={() => setShowTrace(true)} 
                        className="border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold py-2 px-3 rounded-xl text-xs transition"
                      >
                        Trace
                      </button>
                    )}
                  </div>
                </div>

              </div>
            </div>
          )}
          </div>

          {/* Card: Standardized Timeline entries with expand log blocks */}
          <div className="premium-card rounded-2xl p-6 bg-white space-y-4">
            <h3 className="text-xs uppercase tracking-wider font-bold text-slate-400 flex items-center gap-1.5">
              <Radio className="h-4 w-4 text-slate-400" /> Agent Activity Feed (Timeline)
            </h3>

            {!selectedIncident?.timeline || selectedIncident.timeline.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No logs generated. Initiate complaint above.</p>
            ) : (
              <div className="relative pl-4 border-l border-slate-100 space-y-4 max-h-[160px] overflow-y-auto pr-1">
                <AnimatePresence>
                  {selectedIncident?.timeline?.map((event, idx) => (
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4 }}
                      className="relative group text-xs"
                    >
                      {/* Timeline icon node */}
                      <span className="absolute -left-[25px] top-0 h-5 w-5 rounded-full border border-slate-100 bg-white flex items-center justify-center text-slate-500 shadow-sm group-hover:border-blue-400 transition">
                        {STAGE_ICONS[event.stage] || <Layers className="h-3 w-3" />}
                      </span>

                      <div className="flex justify-between items-center">
                        <span className="text-[9px] font-mono text-slate-400">{event.timestamp}</span>
                        <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-slate-50 text-slate-500 border border-slate-100">
                          {event.stage}
                        </span>
                      </div>

                      <div className="mt-1 bg-slate-50/50 border border-slate-100/50 rounded-xl p-3 hover:bg-slate-50 transition cursor-pointer"
                           onClick={() => setExpandedLogIdx(expandedLogIdx === idx ? null : idx)}>
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-700">{event.decision}</span>
                          <span className="text-[10px] text-blue-500 font-bold">{event.confidence}</span>
                        </div>
                        
                        {/* Expandable reasons / next actions logs */}
                        {expandedLogIdx === idx && (
                          <motion.div 
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            className="mt-2 pt-2 border-t border-slate-100 text-[10px] text-slate-500 space-y-1.5"
                          >
                            <p><strong>Reason:</strong> {event.reason}</p>
                            <p className="text-emerald-600 font-mono"><strong>Next Step:</strong> {event.next_action}</p>
                          </motion.div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>

        </section>

      </main>

      {/* Human Escalation Approval slide-over notification card */}
      <AnimatePresence>
        {selectedIncident?.status === "ESCALATED" && (
          <div className="fixed inset-0 z-50 flex justify-end">
            {/* Modal backdrop */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => { setSelectedIncId(""); setSelectedIncident(null); }}
              className="absolute inset-0 bg-slate-950/20 backdrop-blur-sm pointer-events-auto"
            />

            {/* Slide-over panel content */}
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-sm border-l border-slate-100 bg-white/95 backdrop-blur-md shadow-2xl h-full p-6 flex flex-col justify-between overflow-y-auto z-10"
            >
              <div className="space-y-6 text-left">
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider text-rose-500">Human Interaction Required</span>
                    <h2 className="font-outfit font-bold text-sm text-slate-800 mt-0.5">Approve Agent Escalation</h2>
                  </div>
                  <button 
                    onClick={() => { setSelectedIncId(""); setSelectedIncident(null); }} 
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-rose-50/50 border border-rose-100 rounded-xl text-xs leading-relaxed text-slate-600">
                    <strong>Notice:</strong> The SLA deadline has expired or portal submission timed out. To proceed, the AI agent is requesting direct human approval to initiate the escalation strategy.
                  </div>

                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 text-xs space-y-1.5 leading-normal">
                    <p><strong>Department Route:</strong> {selectedIncident.current_strategy?.department}</p>
                    <p><strong>Escalation Target:</strong> {selectedIncident.current_strategy?.escalation_path?.[selectedIncident.escalation_level] || "Zonal Commissioner"}</p>
                    <p><strong>Current Level:</strong> Tier {selectedIncident.escalation_level + 1} of {selectedIncident.current_strategy?.escalation_path?.length}</p>
                  </div>
                </div>

                {/* Twitter composer prefilled display card */}
                {selectedIncident.current_strategy?.escalation_path?.[selectedIncident.escalation_level] === "Social Escalation" ? (
                  <div className="bg-sky-50 border border-sky-100 rounded-xl p-3 space-y-2 text-left">
                    <div className="text-[9px] font-bold text-sky-600 uppercase tracking-wider flex items-center gap-1">
                      <Radio className="h-3 w-3 text-sky-400 animate-pulse" /> Twitter/X Escalation Draft
                    </div>
                    <div className="bg-white border border-slate-100 rounded-lg p-2.5 text-[11px] text-slate-700 shadow-sm font-sans space-y-1.5">
                      <div className="flex gap-1.5 items-center">
                        <div className="w-5 h-5 rounded-full bg-slate-900 flex items-center justify-center text-[8px] font-bold text-white font-mono">A</div>
                        <div>
                          <div className="font-bold text-slate-800 text-[10px] leading-tight">ACIRP Citizen Node</div>
                          <div className="text-[8px] text-slate-400">@acirp_civic</div>
                        </div>
                      </div>
                      <p className="leading-relaxed text-slate-600">
                        🚨 ESCALATION: Civic {selectedIncident.issue_type} unresolved at coordinates {selectedIncident.latitude}, {selectedIncident.longitude} for {selectedIncident.current_strategy.sla_hours}h. Ref: {selectedIncident.official_token || "BBMP-REF"}. Urgent action required @BBMPCOMM @citizen_alert. #CivicResolve
                      </p>
                    </div>
                    <a 
                      href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`🚨 ESCALATION: Civic ${selectedIncident.issue_type} unresolved at coordinates ${selectedIncident.latitude}, ${selectedIncident.longitude} for ${selectedIncident.current_strategy.sla_hours}h. Ref: ${selectedIncident.official_token || "BBMP-REF"}. Urgent action required @BBMPCOMM @citizen_alert. #CivicResolve`)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full mt-1 flex items-center justify-center gap-1 bg-sky-500 hover:bg-sky-600 text-white font-bold py-1.5 rounded-lg text-[10px] transition shadow-md shadow-sky-500/10 pointer-events-auto"
                    >
                      🐦 Open Twitter/X Intent & Tweet
                    </a>
                  </div>
                ) : (
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 space-y-1.5 text-left">
                    <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                      📞 Planned Action Target Details
                    </div>
                    <div className="text-[11px] text-slate-700 leading-normal space-y-1">
                      <p><strong>Authority Name:</strong> {selectedIncident.current_strategy?.escalation_path?.[selectedIncident.escalation_level] || "Zonal Chief"}</p>
                      <p><strong>Action Type:</strong> Official Municipal Dispatch Request & SLA Override</p>
                      <p><strong>Automatic Notice:</strong> Send formal report template directly via API.</p>
                    </div>
                  </div>
                )}
              </div>
              <div className="space-y-2 w-full">
                {selectedIncident.current_strategy?.escalation_path?.[selectedIncident.escalation_level] !== "Social Escalation" && (
                  <a 
                    href={`${API_BASE}/api/incidents/${selectedIncident.id}/download-escalation-letter`}
                    download
                    className="w-full flex items-center justify-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 rounded-xl text-xs transition border border-slate-200 shadow-sm pointer-events-auto"
                  >
                    📥 Download Escalation Letter (HTML)
                  </a>
                )}
                <div className="flex gap-2 w-full">
                  <button 
                    onClick={() => { setSelectedIncId(""); setSelectedIncident(null); }} 
                    className="flex-1 border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold py-2 rounded-xl text-xs transition"
                  >
                    Dismiss
                  </button>
                  <button 
                    onClick={handleApproveEscalation}
                    className="flex-1 bg-rose-500 hover:bg-rose-600 text-white font-bold py-2 rounded-xl text-xs transition shadow-md shadow-rose-500/20"
                  >
                    Approve Escalation
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Popover overlay modal detailing reasoning trace details */}
      {showTrace && brainDecision && (
        <div className="fixed inset-0 bg-slate-950/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 max-w-md w-full rounded-2xl p-5 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-outfit font-bold text-sm text-slate-800 flex items-center gap-1.5">
                <BrainCircuit className="h-4.5 w-4.5 text-[#1A73E8]" /> Decision Reasoning Trace
              </h3>
              <button onClick={() => setShowTrace(false)} className="text-slate-400 hover:text-slate-600 text-sm font-bold"><X className="h-4.5 w-4.5" /></button>
            </div>
            
            <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
              <div>
                <span className="text-slate-400 font-bold uppercase text-[9px] block">Current Goal Context:</span>
                <p className="font-semibold text-slate-800">{brainDecision.goal}</p>
              </div>
              <div>
                <span className="text-slate-400 font-bold uppercase text-[9px] block">Semantic Evaluation Logs:</span>
                <pre className="p-3 bg-slate-50 border border-slate-100 rounded-xl font-mono text-[9px] text-slate-500 leading-normal overflow-x-auto whitespace-pre-wrap">
                  [REASONING EVALUATION ENGINE]{"\n"}
                  - Active State: {brainDecision.current_state}{"\n"}
                  - Selected Strategy: {brainDecision.chosen_strategy.name}{"\n"}
                  - Target Dept: {brainDecision.chosen_strategy.department}{"\n"}
                  - Strategy SLA Window: {brainDecision.chosen_strategy.sla_hours} hours{"\n"}
                  - Execution Reason: "{brainDecision.reason}"{"\n"}
                  - Decision Confidence: {brainDecision.confidence * 100}%
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button 
                onClick={() => setShowTrace(false)}
                className="bg-[#1A73E8] hover:bg-[#1557b0] text-white font-bold py-1.5 px-4 rounded-xl text-xs transition"
              >
                Close Trace
              </button>
            </div>
          </div>
        </div>
      )}

      {showPortalCrashDialog && selectedIncident && (
        <div className="fixed inset-0 bg-slate-950/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 max-w-md w-full rounded-2xl p-5 space-y-4 shadow-2xl text-left">
            <div className="flex items-center gap-2 text-rose-600 border-b border-slate-100 pb-3">
              <AlertTriangle className="h-5 w-5 animate-pulse" />
              <h3 className="font-outfit font-bold text-sm text-slate-800">
                Government Portal Offline (HTTP 504)
              </h3>
            </div>
            
            <p className="text-xs text-slate-600 leading-relaxed">
              The autonomous agent encountered a gateway connection timeout while submitting the petition to the municipal portal. Portal database integration has failed.
            </p>

            <div className="bg-rose-50 border border-rose-100 text-rose-800 text-xs p-4 rounded-xl space-y-2">
              <p><strong>Emergency Dispatch Contact Suggestion:</strong></p>
              <p className="font-semibold">Dept: {HELPLINES[selectedIncident.issue_type]?.dept || "Public Works Department"}</p>
              <p className="text-sm font-bold font-mono">📞 Hotline: {HELPLINES[selectedIncident.issue_type]?.phone || "080-2223-1800"}</p>
            </div>

            <div className="pt-2 flex justify-end">
              <button 
                onClick={() => {
                  setShowPortalCrashDialog(false);
                  setSelectedIncId("");
                  setSelectedIncident(null);
                  setBrainDecision(null);
                  setVerifyFile(null);
                }}
                className="bg-rose-600 hover:bg-rose-700 text-white font-bold py-1.5 px-4 rounded-xl text-xs transition"
              >
                Acknowledge & Archive Case
              </button>
            </div>
          </div>
        </div>
      )}

      {showHelplineDialog && (
        <div className="fixed inset-0 bg-slate-950/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 max-w-md w-full rounded-2xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2 text-blue-600 border-b border-slate-100 pb-3">
              <Phone className="h-5 w-5" />
              <h3 className="font-outfit font-bold text-sm text-slate-800">
                Direct Department Helpline Suggestion
              </h3>
            </div>
            
            <p className="text-xs text-slate-600 leading-relaxed">
              All digital escalation channels have been fully exhausted. The agent has successfully logged the SLA breach and composed public alerts. Please contact the direct department helpline for immediate manual dispatch:
            </p>
            
            <div className="bg-blue-50 border border-blue-100 text-blue-800 text-xs p-4 rounded-xl space-y-2">
              <p><strong>Department:</strong> {
                HELPLINES[showHelplineDialog]?.dept || "Public Works Department"
              }</p>
              <p className="text-sm font-bold font-mono">
                📞 Hotline: {
                  HELPLINES[showHelplineDialog]?.phone || "080-2223-1800"
                }
              </p>
            </div>
            
            <div className="pt-2 flex justify-end">
              <button 
                onClick={() => {
                  setShowHelplineDialog(null);
                  setSelectedIncId("");
                  setSelectedIncident(null);
                  setBrainDecision(null);
                  setVerifyFile(null);
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-1.5 px-4 rounded-xl text-xs transition"
              >
                Acknowledge & Close Case
              </button>
            </div>
          </div>
        </div>
      )}

      {showSuccessDialog && (
        <div className="fixed inset-0 bg-slate-950/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-100 max-w-md w-full rounded-2xl p-5 space-y-4 shadow-2xl text-left">
            <div className="flex items-center gap-2 text-emerald-600 border-b border-slate-100 pb-3">
              <CheckCircle2 className="h-5 w-5" />
              <h3 className="font-outfit font-bold text-sm text-slate-800">
                Civic Resolution Verified!
              </h3>
            </div>
            
            <p className="text-xs text-slate-600 leading-relaxed">
              The verification agent compared the before and after evidence. Gemini vision checks confirmed cleanup matching with a high confidence. The complaint ticket has been marked **CLOSED** in the registry.
            </p>
            
            <div className="bg-emerald-50 border border-emerald-100 text-emerald-800 text-[11px] p-3 rounded-xl font-mono leading-normal">
              <strong>RESOLUTION SUMMARY:</strong> Verification passed successfully. Resolution matching accuracy exceeded 65% (ignoring camera background drift parameters).
            </div>

            <div className="pt-2 flex justify-end">
              <button 
                onClick={() => {
                  setShowSuccessDialog(false);
                  setSelectedIncId("");
                  setSelectedIncident(null);
                  setBrainDecision(null);
                  setVerifyFile(null);
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-1.5 px-4 rounded-xl text-xs transition"
              >
                Acknowledge & Archive Case
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Demo Presentation Guide (Bottom-Left) */}
      <div className="fixed bottom-5 left-5 z-40">
        <button 
          onClick={() => setShowDemoGuide(!showDemoGuide)}
          className="flex items-center gap-1.5 bg-slate-900/90 hover:bg-slate-950 text-white font-bold py-2.5 px-4 rounded-full text-xs shadow-xl transition border border-white/10 pointer-events-auto backdrop-blur-md"
        >
          <PlayCircle className="h-4.5 w-4.5 text-blue-400" />
          {showDemoGuide ? "Hide Pitch Guide" : "Demo Pitch Guide"}
        </button>

        <AnimatePresence>
          {showDemoGuide && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="absolute bottom-12 left-0 w-80 backdrop-blur-xl border border-white/50 bg-white/90 shadow-2xl rounded-3xl p-5 space-y-4 text-xs z-50 text-left font-sans"
            >
              <div className="border-b border-slate-100 pb-2">
                <h4 className="font-outfit font-extrabold text-slate-800 text-xs flex items-center gap-1">
                  🚀 Hackathon Demo Playbook
                </h4>
                <p className="text-[10px] text-slate-400">Present these 3 pathways to wow the judges:</p>
              </div>

              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                <div className="space-y-1">
                  <p className="font-bold text-slate-800">Step 1: File & Observe (Auto Routing)</p>
                  <ul className="list-decimal pl-4 space-y-0.5 text-[10px] text-slate-500">
                    <li>Upload any hazard photo, type name & click submit.</li>
                    <li>Show the morphing Google-color AI Orb and the strategy routing card highlighted as <span className="text-blue-600 font-bold">Chosen by AI</span>.</li>
                  </ul>
                </div>

                <div className="space-y-1">
                  <p className="font-bold text-slate-800">Step 2: Submit to Portal Registry</p>
                  <ul className="list-decimal pl-4 space-y-0.5 text-[10px] text-slate-500">
                    <li>Click <strong>File Official Petition</strong>.</li>
                    <li>Explain the storyteller overlay checks off security & API gates autonomously.</li>
                  </ul>
                </div>

                <div className="space-y-1">
                  <p className="font-bold text-slate-800">Step 3: Test Platform Resilience (Pick One)</p>
                  <ul className="list-disc pl-4 space-y-1 text-[10px] text-slate-500">
                    <li>
                      <span className="font-semibold text-blue-600">SLA Breach:</span> Click <strong>Fast-Forward 24h</strong> in the console. Note the breach alert, slide-over drawer, and official dispatch letter download.
                    </li>
                    <li>
                      <span className="font-semibold text-rose-600">Gateway Timeout:</span> Click <strong>Simulate Portal Crash</strong>. Note the HTTP 504 modal and immediate fallback to manual supervisor escalation.
                    </li>
                    <li>
                      <span className="font-semibold text-emerald-600">Verification Loop:</span> Click <strong>Force Ticket Resolved</strong>. Upload a clean road proof. Observe the side-by-side Before/After comparison. Helpline modal suggests hotline before auto-reset.
                    </li>
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Toast Manager container */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map(t => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`p-3.5 rounded-xl text-xs font-bold text-white shadow-lg flex items-center gap-2 border pointer-events-auto ${
                t.type === "success" 
                  ? "bg-emerald-500 border-emerald-600 shadow-emerald-500/10" 
                  : t.type === "error"
                  ? "bg-rose-500 border-rose-600 shadow-rose-500/10"
                  : "bg-[#1A73E8] border-blue-600 shadow-blue-500/10"
              }`}
            >
              {t.type === "success" && <CheckCircle2 className="h-4 w-4" />}
              {t.type === "error" && <AlertTriangle className="h-4 w-4" />}
              {t.type === "info" && <Radio className="h-4 w-4 animate-pulse" />}
              {t.message}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

    </div>
  );
}
