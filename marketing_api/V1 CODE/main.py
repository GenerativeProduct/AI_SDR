from fastapi import FastAPI, HTTPException, Body, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Union
import os
import httpx
import json
from . import database as db
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="AI Marketing Agent API")

# Production Environment Config
HF_API_KEY = os.environ.get("HF_API_KEY", "")
VELLUX_MASTER_KEY = os.environ.get("VELLUX_API_KEY", "vellux_studio_2026_pk")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# Enable Secure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class EventCreate(BaseModel):
    email: str
    action: str
    metadata: Dict[str, Any]
    visitor_id: Optional[str] = None
    membership_id: Optional[str] = None
    mobile_number: Optional[str] = None
    identity_confidence: Optional[str] = None  # low | medium | high — caller hint; db recomputes authoritatively

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    preferred_channel: Optional[str] = "email"       # email | sms | whatsapp | linkedin | push
    notes: Optional[str] = None
    membership_id: Optional[str] = None
    mobile_number: Optional[str] = None
    consent_status: Optional[str] = None             # granted | withdrawn | pending
    # Customer 360 fields
    favourite_category: Optional[str] = None
    customer_journey: Optional[str] = None           # awareness | consideration | decision | retention | advocacy
    urgency_score: Optional[int] = None              # 0-100; auto-computed on events but manually overridable
    preferred_channels: Optional[Any] = None         # list or JSON string e.g. ["email","whatsapp"]
    customer_notes: Optional[str] = None

class WebhookPayload(BaseModel):
    id: str
    type: str
    actor: Dict[str, Any]
    visitor_id: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    membership_id: Optional[str] = None
    mobile_number: Optional[str] = None

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != VELLUX_MASTER_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key Configuration")
    return x_api_key

@app.on_event("startup")
def startup():
    db.init_db()

@app.get("/")
def read_root():
    return {"status": "AI Marketing Agent API is running", "autonomous": True}

@app.get("/leads", response_model=List[Dict[str, Any]])
def get_leads():
    return db.get_leads()

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead Identity Not Found")
    
    # Enrich with history
    campaigns = db.get_campaigns(lead_id)
    events = db.get_lead_events(lead_id)
    return {
        "profile": lead,
        "campaigns": campaigns,
        "events": events
    }

async def perform_autonomous_orchestration(lead_id: int, segment: str):
    """Triggered after scoring to check if an autonomous campaign is warranted."""
    if segment == 'platinum':
        conn = db.get_db_connection()
        existing = conn.execute("SELECT id FROM campaigns WHERE lead_id = ? AND channel = 'auto_agent'", (lead_id,)).fetchone()
        conn.close()
        
        if not existing:
            context = db.get_lead_context(lead_id)
            prompt = f"System Context: {context}. Mission: Generate a high-priority intro for a Platinum prospect. Goal: Set up a strategy call."
            
            API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 100, "temperature": 0.8}}
            
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(API_URL, headers=headers, json=payload, timeout=12.0)
                    data = res.json()
                    content = data[0]['generated_text'] if isinstance(data, list) else "Automated Agent Outreach Initiated."
                    
                    conn = db.get_db_connection()
                    conn.execute("INSERT INTO campaigns (lead_id, channel, generated_content, sent_status, created_at) VALUES (?, ?, ?, ?, ?)",
                                 (lead_id, 'auto_agent', content, 'dispatched', datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Autonomous orchestration failure: {e}")

@app.post("/events")
async def create_event(event: EventCreate, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    lead_id = db.log_event(
        event.email, event.action, event.metadata, event.visitor_id,
        membership_id=event.membership_id, mobile_number=event.mobile_number
    )
    
    # Identification Pulse
    if event.action in ['user_identified', 'form_submit']:
        db.merge_visitor_data(event.visitor_id, lead_id)
        
    score, segment = db.score_lead(lead_id)
    
    # Offload AI orchestration to background
    background_tasks.add_task(perform_autonomous_orchestration, lead_id, segment)
    
    return {"status": "success", "lead_id": lead_id, "segment": segment}

@app.post("/webhook")
async def handle_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """Generic webhook for external data ingestion."""
    email = payload.actor.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Actor email required for mesh identity")
    
    action = payload.type
    metadata = payload.content or {}
    
    lead_id = db.log_event(
        email, action, metadata, payload.visitor_id,
        membership_id=payload.membership_id or payload.actor.get("membership_id"),
        mobile_number=payload.mobile_number or payload.actor.get("mobile_number"),
    )
    
    # Identification Pulse
    if action in ['user_identified', 'form_submit']:
        db.merge_visitor_data(payload.visitor_id, lead_id)
        
    score, segment = db.score_lead(lead_id)
    
    # Offload AI orchestration
    background_tasks.add_task(perform_autonomous_orchestration, lead_id, segment)
    
    return {"status": "ingested", "lead_id": lead_id, "processing": "async_orchestration"}

@app.patch("/leads/{lead_id}/profile")
def update_profile(lead_id: int, profile: ProfileUpdate):
    db.update_profile(lead_id, profile.dict(exclude_unset=True))
    return {"status": "success", "detail": "Identity Mesh Synchronized"}

@app.get("")
def get_identity_resolution(lead_id: int):
    """Returns the identity resolution summary for a single lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead Identity Not Found")
    return {
        "lead_id": lead_id,
        "email": lead.get("email"),
        "membership_id": lead.get("membership_id"),
        "mobile_number": lead.get("mobile_number"),
        "identity_confidence": lead.get("identity_confidence", "low"),
        "is_duplicate": bool(lead.get("is_duplicate", 0)),
        "canonical_lead_id": lead.get("canonical_lead_id"),
        "identity_signals": lead.get("identity_signals", []),
    }

@app.get("/leads/{lead_id}/profile")
def get_customer_360(lead_id: int):
    """Returns the full Customer 360 profile for a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead Identity Not Found")
    return {
        "lead_id": lead_id,
        # Identity
        "email": lead.get("email"),
        "membership_id": lead.get("membership_id"),
        "mobile_number": lead.get("mobile_number"),
        "identity_confidence": lead.get("identity_confidence", "low"),
        "identity_signals": lead.get("identity_signals", []),
        # Firmographic
        "name": lead.get("name"),
        "title": lead.get("title"),
        "company": lead.get("company"),
        "linkedin_url": lead.get("linkedin_url"),
        # Consent & channel
        "consent_status": lead.get("consent_status", "pending"),
        "preferred_channel": lead.get("preferred_channel", "email"),
        "preferred_channels": lead.get("preferred_channels", ["email"]),
        # Customer 360
        "favourite_category": lead.get("favourite_category"),
        "customer_journey": lead.get("customer_journey", "awareness"),
        "urgency_score": lead.get("urgency_score", 0),
        "engagement_summary": lead.get("engagement_summary"),
        "last_interaction": lead.get("last_interaction"),
        "customer_notes": lead.get("customer_notes"),
        # Scoring
        "score": lead.get("score"),
        "segment": lead.get("segment"),
        # RFM
        "rfm_recency_score":   lead.get("rfm_recency_score", 0),
        "rfm_frequency_score": lead.get("rfm_frequency_score", 0),
        "rfm_monetary_score":  lead.get("rfm_monetary_score", 0),
        "rfm_total_score":     lead.get("rfm_total_score", 0),
        # Value metrics
        "clv": lead.get("clv", 0.0),
        "aov": lead.get("aov", 0.0),
        "fov": lead.get("fov", 0.0),
        # Lifecycle + Predictive
        "lifecycle_stage":   lead.get("lifecycle_stage", "new"),
        "churn_risk_score":  lead.get("churn_risk_score", 0),
        "next_best_action":  lead.get("next_best_action"),
    }

@app.post("/ai/generate")
async def generate_content(lead_id: Optional[int] = Body(None), topic: str = Body(..., embed=True), max_tokens: int = 150):
    prompt = f"Generate a {topic} message for marketing."
    
    if lead_id:
        context = db.get_lead_context(lead_id)
        if context:
            prompt = f"Detailed Context: {context}. Target Objective: {topic}. Output: Premium personalized copy."

    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7}}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=12.0)
            if response.status_code != 200:
                return {"error": f"Internal Cognitive Failure: {response.status_code}", "detail": response.text}
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                return {"generated_text": result[0]['generated_text'].strip()}
            return {"generated_text": str(result)}
        except Exception as e:
            return {"error": "Cognitive Mesh Connection Failed", "detail": str(e)}

@app.post("/campaigns/send")
def send_campaign(lead_id: int = Body(..., embed=True), channel: str = Body(..., embed=True), content: str = Body(..., embed=True)):
    conn = db.get_db_connection()
    conn.execute("INSERT INTO campaigns (lead_id, channel, generated_content, sent_status, created_at) VALUES (?, ?, ?, 'sent', ?)", 
                 (lead_id, channel, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/stats")
def get_stats():
    """Returns real-time aggregated metrics for the dashboard."""
    return db.get_event_stats()

@app.get("/campaigns")
def get_campaign_history(lead_id: Optional[int] = None):
    return db.get_campaigns(lead_id)

@app.get("/events/live")
def get_live_events(limit: int = 50):
    conn = db.get_db_connection()
    query = """
        SELECT e.*, l.email, l.score, l.segment, p.name 
        FROM events e
        JOIN leads l ON e.lead_id = l.id
        LEFT JOIN customer_profiles p ON l.id = p.lead_id
        ORDER BY e.created_at DESC
        LIMIT ?
    """
    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
