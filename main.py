# ============================================================================
# AI GUARDIAN: WOMEN'S SAFETY AGENT - ALL-IN-ONE (OFFLINE, RUNS ANYWHERE)
# Paste into a Kaggle/Colab notebook cell and run. No external API keys needed.
# ============================================================================

import os
import json
import datetime
import uuid
import asyncio
from typing import Dict, Any, List
from pathlib import Path

# -------------------------
# Setup folders
# -------------------------
Path('data').mkdir(exist_ok=True)
Path('logs').mkdir(exist_ok=True)

INCIDENT_LOG = "data/incident_log.jsonl"

print("🛡️ AI GUARDIAN - OFFLINE MODE")
print("=" * 70)

# -------------------------
# CELL: Tool Schemas (MCP-style)
# -------------------------
TOOL_SCHEMAS = {
    "save_user_profile": {
        "name": "save_user_profile",
        "title": "Save User Profile",
        "description": "Save user's name and emergency contact to session state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "emergency_contact": {"type": "string"}
            },
            "required": ["name", "emergency_contact"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {"status": {"type": "string"}, "message": {"type": "string"}}
        }
    },
    "trigger_emergency_alert": {
        "name": "trigger_emergency_alert",
        "title": "Trigger Emergency Alert",
        "description": "Activate emergency alert with location sharing and notifications",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threat_level": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "description": {"type": "string"}
            },
            "required": ["threat_level", "description"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "incident_id": {"type": "string"},
                "threat_level": {"type": "string"},
                "location": {"type": "string"},
                "maps_link": {"type": "string"},
                "notifications_sent": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    "get_safety_guidance": {
        "name": "get_safety_guidance",
        "title": "Get Safety Guidance",
        "description": "Provide situational safety advice and recommendations",
        "inputSchema": {
            "type": "object",
            "properties": {"situation": {"type": "string"}},
            "required": ["situation"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "situation": {"type": "string"},
                "guidance": {"type": "array", "items": {"type": "string"}},
                "message": {"type": "string"}
            }
        }
    }
}

print("✅ Tool schemas loaded (3 tools)")

# -------------------------
# CELL: Golden Dataset
# -------------------------
GOLDEN_DATASET = [
    {
        "scenario_id": "01",
        "name": "Profile Setup",
        "user_input": "Hi! My name is Priya and my emergency contact is +91-9876543210",
        "expected_tool": "save_user_profile",
        "expected_outcome": {"profile_saved": True, "name_stored": "Priya"},
        "threat_level": "NONE"
    },
    {
        "scenario_id": "02",
        "name": "Safety Guidance Request",
        "user_input": "I'm taking a late-night cab. What safety precautions should I take?",
        "expected_tool": "get_safety_guidance",
        "expected_outcome": {"guidance_provided": True},
        "threat_level": "NONE"
    },
    {
        "scenario_id": "03",
        "name": "Medium Threat - Being Followed",
        "user_input": "Someone has been following me for 3 blocks. I'm scared.",
        "expected_tool": "trigger_emergency_alert",
        "expected_outcome": {"alert_triggered": True, "threat_level": "MEDIUM"},
        "threat_level": "MEDIUM"
    },
    {
        "scenario_id": "04",
        "name": "High Threat Emergency",
        "user_input": "HELP ME! Someone trying to force me into a car at MG Road!",
        "expected_tool": "trigger_emergency_alert",
        "expected_outcome": {"alert_triggered": True, "threat_level": "HIGH"},
        "threat_level": "HIGH"
    }
]

print("✅ Golden dataset loaded (4 scenarios)")

# -------------------------
# CELL: Configuration & Services
# -------------------------
class GuardianConfig:
    TRIGGER_WORDS = ["help", "danger", "emergency", "sos", "unsafe", "help me"]
    HIGH_RISK_KEYWORDS = ['attack', 'force', 'kidnap', 'assault', 'stalking', 'follow', 'scared']
    INCIDENT_LOG = INCIDENT_LOG

config = GuardianConfig()

class LocationService:
    @staticmethod
    def get_current_location() -> Dict[str, Any]:
        loc = {
            "latitude": 19.0760,
            "longitude": 72.8777,
            "address": "Mumbai, Maharashtra, India",
            "timestamp": datetime.datetime.now().isoformat()
        }
        # save sample location
        try:
            with open("data/sample_location.json", "w") as f:
                json.dump(loc, f, indent=2)
        except Exception:
            pass
        return loc

    @staticmethod
    def get_google_maps_link(lat: float, lon: float) -> str:
        return f"https://www.google.com/maps?q={lat},{lon}"

class IncidentLogger:
    @staticmethod
    def log_incident(incident_data: Dict[str, Any]) -> None:
        incident_data['logged_at'] = datetime.datetime.now().isoformat()
        with open(config.INCIDENT_LOG, 'a') as f:
            f.write(json.dumps(incident_data) + "\n")

    @staticmethod
    def get_all_incidents() -> List[Dict]:
        incidents = []
        try:
            with open(config.INCIDENT_LOG, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        incidents.append(json.loads(line))
                    except Exception:
                        # skip malformed line
                        continue
        except FileNotFoundError:
            pass
        return incidents

print("✅ Services ready (Location, IncidentLogger)")

# -------------------------
# CELL: Danger Classifier (Rule-based + heuristic)
# -------------------------
class DangerClassifier:
    @staticmethod
    def classify_text(text: str) -> Dict[str, Any]:
        t = text.lower()
        # immediate triggers
        for trig in config.TRIGGER_WORDS:
            if trig in t:
                return {
                    "threat_level": "HIGH",
                    "confidence": 0.95,
                    "detected_trigger": trig,
                    "action": "IMMEDIATE_ALERT"
                }
        # keyword scoring
        score = sum(1 for kw in config.HIGH_RISK_KEYWORDS if kw in t)
        detected = [kw for kw in config.HIGH_RISK_KEYWORDS if kw in t]
        if score >= 2:
            return {"threat_level": "MEDIUM", "confidence": 0.75, "detected_keywords": detected, "action": "ALERT_CONTACTS"}
        if score == 1:
            return {"threat_level": "LOW", "confidence": 0.55, "detected_keywords": detected, "action": "MONITOR"}
        return {"threat_level": "NONE", "confidence": 0.98, "action": "CONTINUE"}

print("✅ DangerClassifier ready")

# -------------------------
# CELL: Offline LLM (Fallback) - Simple heuristics & templates
# -------------------------
def offline_llm(user_text: str) -> Dict[str, Any]:
    s = user_text.lower()
    # emergency detection
    for kw in ["help", "save", "attack", "force", "kidnap", "danger", "sos"]:
        if kw in s:
            return {"response": "I detected a possible emergency. Activating safety protocols.", "is_emergency": True}
    # profile detection
    if "my name is" in s and "emergency contact" in s:
        return {"response": "Profile noted. I have saved your details.", "is_emergency": False}
    # guidance triggers
    if "cab" in s or "ride" in s or "taxi" in s or "night" in s:
        return {"response": "Share your trip with someone, remain visible, and keep phone accessible.", "is_emergency": False}
    # default
    return {"response": "I'm here with you. Tell me more or say 'help' if you're in danger.", "is_emergency": False}

print("✅ Offline LLM ready")

# -------------------------
# CELL: Tools implementations (match TOOL_SCHEMAS)
# -------------------------
# Session-like state store (simple in-memory per-session dict)
SESSIONS: Dict[str, Dict[str, Any]] = {}

def ensure_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {"created_at": datetime.datetime.now().isoformat()}
    return SESSIONS[session_id]

def save_user_profile(tool_context: Dict[str, Any], name: str, emergency_contact: str) -> Dict[str, Any]:
    # tool_context is session dict
    tool_context["user:name"] = name
    tool_context["user:emergency_contact"] = emergency_contact
    return {"status": "success", "message": f"Profile saved for {name}"}

def trigger_emergency_alert(tool_context: Dict[str, Any], threat_level: str, description: str) -> Dict[str, Any]:
    location = LocationService.get_current_location()
    maps_link = LocationService.get_google_maps_link(location['latitude'], location['longitude'])
    incident_id = f"INC-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    incident = {
        "incident_id": incident_id,
        "threat_level": threat_level,
        "description": description,
        "location": location,
        "maps_link": maps_link,
        "user_name": tool_context.get("user:name", "Unknown"),
        "emergency_contact": tool_context.get("user:emergency_contact", "Not set"),
        "timestamp": datetime.datetime.now().isoformat()
    }
    IncidentLogger.log_incident(incident)
    notifications = ([
        f"SMS to {tool_context.get('user:emergency_contact','contact')}",
        "Email sent",
        "Police notified"
    ] if threat_level == "HIGH" else [
        f"SMS to {tool_context.get('user:emergency_contact','contact')}",
        "Community responders alerted"
    ])
    return {"status": "success", "incident_id": incident_id, "threat_level": threat_level,
            "location": location["address"], "maps_link": maps_link, "notifications_sent": notifications,
            "message": f"Alert activated: {incident_id}"}

def get_safety_guidance(tool_context: Dict[str, Any], situation: str) -> Dict[str, Any]:
    guidance_db = {
        "being_followed": ["Move to a populated area", "Call or text a friend", "Enter a public place"],
        "unsafe_transport": ["Share trip details", "Keep phone visible and charged", "Note vehicle number"],
        "harassment": ["Say 'NO' loudly", "Document messages", "Seek help"],
        "general": ["Stay calm", "Keep phone accessible", "Trust your instincts"]
    }
    sit = situation.lower()
    for key in guidance_db:
        if key in sit:
            g = guidance_db[key]
            return {"status": "success", "situation": situation, "guidance": g, "message": "Guidance provided"}
    return {"status": "success", "situation": situation, "guidance": guidance_db["general"], "message": "General guidance"}

print("✅ Tools implemented (save_user_profile, trigger_emergency_alert, get_safety_guidance)")

# -------------------------
# CELL: Chat / Orchestrator (simple)
# -------------------------
async def ai_guardian_chat(user_text: str, session_id: str = None):
    """
    Orchestrator that accepts user_text and session_id and:
     - runs offline LLM
     - classifies threat
     - calls tools as needed
     - returns result dict
    """
    if session_id is None:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    session = ensure_session(session_id)

    print("\n" + "="*70)
    print(f"👤 User ({session_id}): {user_text}")
    print("="*70 + "\n")

    # 1) LLM reasoning (offline)
    llm_out = offline_llm(user_text)
    # 2) If profile-ish message, parse and save
    lowered = user_text.lower()
    if "my name is" in lowered and "emergency contact" in lowered:
        # try to parse simple format: "My name is X and my emergency contact is Y"
        try:
            left = lowered.split("my name is", 1)[1]
            name_part = left.split("and")[0].strip()
            # get contact
            contact = lowered.split("emergency contact is", 1)[1].strip()
            name = name_part.title()
            save_res = save_user_profile(session, name, contact)
            print("🛡️ AI Guardian:", save_res["message"])
            return {"session_id": session_id, "action": "save_profile", "result": save_res}
        except Exception:
            # fallback to LLM reply
            print("🛡️ AI Guardian:", llm_out["response"])
            return {"session_id": session_id, "action": "reply", "result": llm_out}

    # 3) Classify for danger
    cls = DangerClassifier.classify_text(user_text)
    if cls["threat_level"] == "HIGH":
        # call emergency tool
        incident = trigger_emergency_alert(session, "HIGH", user_text)
        print("🚨 Emergency triggered:", incident["incident_id"])
        print("🛡️ AI Guardian: Emergency protocols activated. Help is on the way.")
        return {"session_id": session_id, "action": "emergency", "incident": incident}
    elif cls["threat_level"] == "MEDIUM":
        incident = trigger_emergency_alert(session, "MEDIUM", user_text)
        print("⚠️ Medium threat — incident logged:", incident["incident_id"])
        print("🛡️ AI Guardian: I've alerted your emergency contacts and logged the incident.")
        return {"session_id": session_id, "action": "alert_contacts", "incident": incident}
    elif cls["threat_level"] == "LOW":
        guidance = get_safety_guidance(session, user_text)
        print("🟡 Low-risk detected. Guidance:", guidance["guidance"])
        return {"session_id": session_id, "action": "guidance", "result": guidance}
    else:
        # no threat, reply with LLM response or suggestion
        print("🛡️ AI Guardian:", llm_out["response"])
        return {"session_id": session_id, "action": "reply", "result": llm_out}

print("✅ Orchestrator ready (ai_guardian_chat)")

# -------------------------
# CELL: Demo runner + Dashboard
# -------------------------
async def run_complete_demo():
    print("\n" + "="*70)
    print("🎬 AI GUARDIAN - DEMO RUN")
    print("="*70 + "\n")

    for scenario in GOLDEN_DATASET:
        print(f"📍 SCENARIO {scenario['scenario_id']}: {scenario['name']}")
        print("-" * 70)
        await ai_guardian_chat(scenario['user_input'], session_id=f"demo_{scenario['scenario_id']}")
        print("\n")

    # Dashboard
    incidents = IncidentLogger.get_all_incidents()
    print("\n" + "="*70)
    print("📊 INCIDENT DASHBOARD")
    print("="*70)
    print(f"Total Incidents: {len(incidents)}")
    if incidents:
        high = sum(1 for i in incidents if i.get('threat_level') == 'HIGH')
        medium = sum(1 for i in incidents if i.get('threat_level') == 'MEDIUM')
        low = sum(1 for i in incidents if i.get('threat_level') == 'LOW')
        print(f"  🔴 High: {high}   🟡 Medium: {medium}   🟢 Low: {low}\n")
        print("Recent Incidents:")
        for inc in incidents[-5:]:
            print(f" - {inc['incident_id']} | {inc['threat_level']} | {inc.get('user_name','Unknown')} | {inc.get('timestamp')}")
    else:
        print("No incidents logged yet.")

    print("\n" + "="*70)
    print("🎉 DEMO COMPLETE")
    print("="*70 + "\n")

# -------------------------
# CELL: Show tool schemas (human-readable)
# -------------------------
def print_tool_summaries():
    print("\n" + "="*70)
    print("🔧 TOOL SCHEMAS (MCP) SUMMARY")
    print("="*70)
    for name, schema in TOOL_SCHEMAS.items():
        print(f"\n• {schema['title']} (name: {name})")
        print(f"  Description: {schema['description']}")
        inputs = list(schema['inputSchema']['properties'].keys())
        outputs = list(schema['outputSchema']['properties'].keys())
        print(f"  Inputs: {inputs}")
        print(f"  Outputs: {outputs}")

# -------------------------
# RUN everything
# -------------------------
if __name__ == "__main__":
    await run_complete_demo()

    print_tool_summaries()

# ============================================================================
# End of notebook
# ============================================================================
