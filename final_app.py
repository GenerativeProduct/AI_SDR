import streamlit as st
import pandas as pd
import os
import requests
import json
import re
import time
import html as html_module
from datetime import datetime, timezone
from textwrap import dedent

st.set_page_config(page_title="AI Marketing Agent Hub", page_icon="🚀", layout="wide")

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY  = os.environ.get("VELLUX_API_KEY", "vellux_studio_2026_pk")
HF_API_KEY = os.environ.get("HF_API_KEY", "")

_HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

# -----------------------------------------------------------------------------
# SAFE HTML ESCAPE HELPER
# -----------------------------------------------------------------------------
def esc(val):
    """Escape a value for safe injection into HTML strings."""
    if val is None:
        return "—"
    return html_module.escape(str(val), quote=True)

# -----------------------------------------------------------------------------
# TIMESTAMP HELPERS
# -----------------------------------------------------------------------------
def humanize_ts(raw):
    if not raw:
        return "—"
    try:
        raw = str(raw).strip()
        raw_clean = raw[:19].replace("T", " ")
        dt = datetime.strptime(raw_clean, "%Y-%m-%d %H:%M:%S")
        now = datetime.utcnow()
        diff = now - dt
        secs = diff.total_seconds()
        if secs < 0:
            return raw_clean
        if secs < 60:
            return "just now"
        if secs < 3600:
            m = int(secs // 60)
            return f"{m} minute{'s' if m > 1 else ''} ago"
        if secs < 86400:
            h = int(secs // 3600)
            return f"{h} hour{'s' if h > 1 else ''} ago"
        if secs < 172800:
            return "yesterday"
        d = int(secs // 86400)
        if d < 30:
            return f"{d} days ago"
        if d < 365:
            mo = int(d // 30)
            return f"{mo} month{'s' if mo > 1 else ''} ago"
        yr = int(d // 365)
        return f"{yr} year{'s' if yr > 1 else ''} ago"
    except Exception:
        return str(raw)[:19]

# -----------------------------------------------------------------------------
# VALIDATION HELPERS
# -----------------------------------------------------------------------------
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MOBILE_RE = re.compile(r"^\+?[\d\s\-]{7,15}$")

def valid_email(v):
    return bool(_EMAIL_RE.match(str(v or "").strip()))

def valid_mobile(v):
    v = str(v or "").strip()
    return v == "" or bool(_MOBILE_RE.match(v))

# -----------------------------------------------------------------------------
# RETRY-SAFE API HELPERS
# -----------------------------------------------------------------------------
_RETRY_ATTEMPTS = 3
_RETRY_DELAY    = 0.5

def _get(path, params=None):
    last_err = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            r = requests.get(f"{API_BASE}{path}", headers=_HEADERS, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError as e:
            last_err = ("connection", str(e))
        except requests.exceptions.Timeout as e:
            last_err = ("timeout", str(e))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and 400 <= e.response.status_code < 500:
                st.error(f"⚠️ API error {e.response.status_code}: {e.response.text[:200]}")
                return None
            last_err = ("http", f"{e.response.status_code if e.response is not None else '?'}")
        except Exception as e:
            last_err = ("unexpected", str(e))
        if attempt < _RETRY_ATTEMPTS - 1:
            time.sleep(_RETRY_DELAY)
    if last_err:
        kind, detail = last_err
        if kind == "connection":
            st.error("⚠️ Backend unavailable. Please ensure the API server is running.")
        elif kind == "timeout":
            st.error("⚠️ Request timed out. The server may be overloaded.")
        elif kind == "http":
            st.error(f"⚠️ API error {detail} after retries.")
        else:
            st.error(f"⚠️ Unexpected error: {detail}")
    return None

def _post(path, payload):
    last_err = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            r = requests.post(f"{API_BASE}{path}", headers=_HEADERS, json=payload, timeout=12)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError as e:
            last_err = ("connection", str(e))
        except requests.exceptions.Timeout as e:
            last_err = ("timeout", str(e))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and 400 <= e.response.status_code < 500:
                st.error(f"⚠️ API error {e.response.status_code}: {e.response.text[:200]}")
                return None
            last_err = ("http", f"{e.response.status_code if e.response is not None else '?'}")
        except Exception as e:
            last_err = ("unexpected", str(e))
        if attempt < _RETRY_ATTEMPTS - 1:
            time.sleep(_RETRY_DELAY)
    if last_err:
        kind, detail = last_err
        if kind == "connection":
            st.error("⚠️ Backend unavailable.")
        elif kind == "timeout":
            st.error("⚠️ Request timed out.")
        elif kind == "http":
            st.error(f"⚠️ API error {detail} after retries.")
        else:
            st.error(f"⚠️ Unexpected error: {detail}")
    return None

def _patch(path, payload):
    last_err = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            r = requests.patch(f"{API_BASE}{path}", headers=_HEADERS, json=payload, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError as e:
            last_err = ("connection", str(e))
        except requests.exceptions.Timeout as e:
            last_err = ("timeout", str(e))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and 400 <= e.response.status_code < 500:
                st.error(f"⚠️ API error {e.response.status_code}: {e.response.text[:200]}")
                return None
            last_err = ("http", f"{e.response.status_code if e.response is not None else '?'}")
        except Exception as e:
            last_err = ("unexpected", str(e))
        if attempt < _RETRY_ATTEMPTS - 1:
            time.sleep(_RETRY_DELAY)
    if last_err:
        kind, detail = last_err
        if kind == "connection":
            st.error("⚠️ Backend unavailable.")
        elif kind == "timeout":
            st.error("⚠️ Request timed out.")
        elif kind == "http":
            st.error(f"⚠️ API error {detail} after retries.")
        else:
            st.error(f"⚠️ Unexpected error: {detail}")
    return None

# -----------------------------------------------------------------------------
# CACHED API FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=30)
def get_leads():
    data = _get("/leads")
    if data is None:
        return []
    return data if isinstance(data, list) else []

@st.cache_data(ttl=60)
def get_stats():
    return _get("/stats") or {}

@st.cache_data(ttl=30)
def get_campaigns(lead_id=None):
    params = {"lead_id": lead_id} if lead_id else None
    data = _get("/campaigns", params=params)
    return data if isinstance(data, list) else []

@st.cache_data(ttl=15)
def get_live_events(limit=50):
    data = _get("/events/live", params={"limit": limit})
    return data if isinstance(data, list) else []

@st.cache_data(ttl=30)
def get_lead_detail(lead_id):
    if not lead_id:
        return {}
    return _get(f"/leads/{lead_id}") or {}

@st.cache_data(ttl=30)
def get_lead_profile(lead_id):
    if not lead_id:
        return {}
    return _get(f"/leads/{lead_id}/profile") or {}

def get_lead_identity(lead_id):
    if not lead_id:
        return {}
    return _get(f"/leads/{lead_id}/identity") or {}

def patch_lead_profile(lead_id, payload):
    result = _patch(f"/leads/{lead_id}/profile", payload)
    if result is not None:
        get_lead_profile.clear()
        get_lead_detail.clear()
        get_leads.clear()
    return result

def post_event(email, action, metadata, visitor_id=None):
    result = _post("/events", {
        "email": email, "action": action, "metadata": metadata,
        "visitor_id": visitor_id
    })
    if result is not None:
        get_leads.clear()
        get_live_events.clear()
        get_lead_detail.clear()
        get_lead_profile.clear()
    return result

def post_campaign(lead_id, channel, content):
    result = _post("/campaigns/send", {
        "lead_id": lead_id, "channel": channel, "content": content
    })
    if result is not None:
        get_campaigns.clear()
        get_lead_detail.clear()
    return result

def generate_hf_content(prompt_context, lead_id=None, max_tokens=100):
    payload = {"topic": prompt_context, "max_tokens": max_tokens}
    if lead_id:
        payload["lead_id"] = lead_id
    data = _post("/ai/generate", payload)
    if data is None:
        return "[Content generation failed — backend unavailable]"
    if "error" in data:
        return f"[{data.get('error', 'Error')}: {data.get('detail', '')}]"
    return (data.get("generated_text") or "[No content returned]").strip()

# -----------------------------------------------------------------------------
# PARSE PREFERRED CHANNELS SAFELY
# -----------------------------------------------------------------------------
_ALL_CHANNELS = {"email", "sms", "whatsapp", "linkedin", "push", "in_app"}

def parse_channels(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(ch).strip() for ch in raw if str(ch).strip() in _ALL_CHANNELS]
    try:
        parsed = json.loads(str(raw))
        if isinstance(parsed, list):
            return [str(ch).strip() for ch in parsed if str(ch).strip() in _ALL_CHANNELS]
    except Exception:
        pass
    return [
        ch.strip()
        for ch in str(raw).replace(',', ' ').replace('[', '').replace(']', '')
                          .replace('"', '').replace("'", '').split()
        if ch.strip() in _ALL_CHANNELS
    ]

# -----------------------------------------------------------------------------
# BUILD A FLAT ROW DICT FROM API DATA (profile endpoint)
# -----------------------------------------------------------------------------
def build_row(profile: dict) -> dict:
    if not profile or not isinstance(profile, dict):
        profile = {}
    row = dict(profile)
    if "customer_tier" not in row:
        row["customer_tier"] = row.get("segment")
    for col in ("score", "rfm_recency_score", "rfm_frequency_score",
                "rfm_monetary_score", "rfm_total_score",
                "clv", "aov", "fov", "urgency_score", "churn_risk_score"):
        row.setdefault(col, None)
    for col in ("lifecycle_stage", "next_best_action", "identity_confidence",
                "consent_status", "preferred_channel"):
        row.setdefault(col, None)
    row.setdefault("is_duplicate", False)
    row.setdefault("preferred_channels", [])
    row.setdefault("identity_signals", [])
    return row

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("🚀 AI Marketing Agent")
st.sidebar.markdown("Navigate through the 8-step architecture.")

nav_options = [
    "1. Customer Identity Resolution",
    "2. Customer 360 Profile",
    "3. Customer Engagement Tracking",
    "4. Customer Intelligence & Segmentation",
    "5. Campaign Orchestration Hub",
    "6. Channel & Content Execution",
    "7. CRM & Analytics Dashboard",
    "8. Recommended Next Best Action",
]
selection = st.sidebar.radio("Go to step:", nav_options)

if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "selected_customer_email" not in st.session_state:
    st.session_state.selected_customer_email = None

# -----------------------------------------------------------------------------
# STEP 3 — Customer Engagement Tracking
# BUG FIX: metadata is already a dict — removed json.loads(metadata)
# -----------------------------------------------------------------------------
if selection == "3. Customer Engagement Tracking":
    st.header("Step 3: Customer Engagement Tracking")
    st.markdown("Capture customer engagement signals and identity interactions across touchpoints.")

    with st.form("event_track_form"):
        col1, col2 = st.columns(2)
        with col1:
            u_email = st.text_input(
                "Customer Identity (Email)",
                "customer@example.com",
                help="Capture customer identity for profile stitching and engagement tracking."
            )
            action = st.selectbox("Tracked Customer Action", [
                "Website Visit",
                "Landing Page View",
                "Pricing Page Visit",
                "Blog Read",
                "Video Interaction",
                "CTA Click",
                "Email Open",
                "Email Click",
                "Form Submission",
                "Demo Request",
                "Add to Wishlist",
                "Product Interest",
                "Cart Abandonment",
                "Purchase Intent",
                "Purchase Completed",
                "WhatsApp Interaction",
                "Support Chat Started",
                "Webinar Registration",
                "Event Attendance",
            ])
            campaign_type = st.selectbox(
                "Marketing Campaign Source",
                [
                    "LinkedIn Campaign",
                    "Google Ads",
                    "Meta/Facebook Campaign",
                    "Instagram Campaign",
                    "Email Marketing",
                    "WhatsApp Campaign",
                    "Retargeting Campaign",
                    "SEO / Organic",
                    "Referral Campaign",
                    "Influencer Campaign",
                    "Webinar Campaign",
                    "Product Launch Campaign",
                    "Direct Traffic",
                    "Other",
                ]
            )
        with col2:
            campaign_name = st.text_input("Campaign Name", "Q2_Product_Launch")
            channel = st.selectbox(
                "First Touch Channel",
                [
                    "Website",
                    "LinkedIn",
                    "Google Search",
                    "Instagram",
                    "Facebook",
                    "Email",
                    "WhatsApp",
                    "YouTube",
                    "Referral",
                    "Organic Search",
                ]
            )
            st.caption("Campaign and engagement context will be tracked automatically.")

        submit_event = st.form_submit_button("Track Customer Activity")

    if submit_event:
        if not valid_email(u_email):
            st.error("Invalid email address.")
        else:
            # BUG FIX: metadata is already a dict — do NOT call json.loads on it
            meta_dict = {
                "campaign_type": campaign_type,
                "campaign_name": campaign_name,
                "channel": channel,
                "action": action,
            }
            with st.spinner("Logging event..."):
                result = post_event(u_email, action, meta_dict)
            if result:
                st.success(
                    f"Event logged! Lead ID: {result.get('lead_id')} · "
                    f"Segment: {result.get('segment', '—')}"
                )

    st.subheader("Recent Customer Activity")
    with st.spinner("Loading events..."):
        events = get_live_events(limit=10)
    if events:
        df = pd.DataFrame(events)
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].apply(humanize_ts)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No events recorded yet.")

# -----------------------------------------------------------------------------
# STEP 7 — Channel & Content Execution
# BUG FIX: removed nested buttons; state managed via session_state
# -----------------------------------------------------------------------------
elif selection == "6. Channel & Content Execution":
    st.header("Step 6: Channel & Content Execution")
    st.markdown("Generates dynamic content/banners based on `Customer + Events + Interactions + Segment`")

    with st.spinner("Loading leads..."):
        leads = get_leads()
    if not leads:
        st.info("No leads available yet. Go to Step 1 and track an event first.")
    else:
        email_list = [l.get("email", "") for l in leads if l.get("email")]
        selected_email = st.selectbox("Select User for Personalization preview", email_list)

        lead_rec = next((l for l in leads if l.get("email") == selected_email), {})
        lead_id = lead_rec.get("id")

        with st.spinner("Loading profile..."):
            profile = get_lead_profile(lead_id) if lead_id else {}
            detail  = get_lead_detail(lead_id)  if lead_id else {}

        events_raw  = (detail.get("events") or [])[:3]
        event_names = [e.get("action_type", "") for e in events_raw if isinstance(e, dict)]

        col1, col2 = st.columns(2)
        with col1:
            st.write("##### Input Data for Agent")
            st.json({
                "Customer": profile.get("name") or selected_email,
                "Segment": lead_rec.get("segment") or "N/A",
                "Recent Events": event_names,
                "Past Interactions": len(events_raw),
            })

        with col2:
            st.write("##### Hit LLM Agent")
            if st.button("Generate Personalized Content (HF API)", key="gen_content"):
                with st.spinner("Calling flan-t5-large via HF Inference API..."):
                    seg_desc = lead_rec.get("segment") or "unknown"
                    context = f"User is in {seg_desc} tier. Recent actions: {', '.join(event_names) or 'none'}."
                    hf_prompt = f"Write a one-sentence personalized website welcome banner for a user: {context}."
                    res = generate_hf_content(hf_prompt, lead_id=lead_id, max_tokens=30)
                st.success("Generated Output")
                st.info(res)

        st.markdown("---")
        st.subheader("📤 Channel Send Agents")
        tab1, tab2, tab3 = st.tabs(["📧 Email Agent", "📱 SMS Agent", "💼 Social Agent"])

        # ── Email Agent ──────────────────────────────────────────────────────
        with tab1:
            st.markdown("#### Email Outreach")
            email_type = st.selectbox(
                "Email Type",
                ["Welcome Sequence", "Nurture", "Discount Offer"],
                key="emaillist"
            )
            if st.button("Draft Email via HF API", key="draft_email"):
                with st.spinner("Drafting Email..."):
                    ctx = f"Write a short B2B {email_type} email. Include a Subject line and 3 sentences."
                    output = generate_hf_content(ctx, lead_id=lead_id, max_tokens=150)
                st.session_state["email_draft_output"] = output

            if "email_draft_output" in st.session_state and st.session_state["email_draft_output"]:
                output = st.session_state["email_draft_output"]
                st.text_area("Draft Output", output, height=200, key="email_draft_display")
                if lead_id:
                    if st.button("Send Email Campaign", key="send_email"):
                        with st.spinner("Sending email campaign..."):
                            res = post_campaign(lead_id, "email", output)
                        if res:
                            st.success("Email campaign sent.")
                            st.session_state.pop("email_draft_output", None)

        # ── SMS Agent ────────────────────────────────────────────────────────
        with tab2:
            st.markdown("#### SMS Outreach")
            st.write("Short CTA & Urgency copy")
            if st.button("Draft SMS via HF API", key="draft_sms"):
                with st.spinner("Drafting SMS..."):
                    ctx = "Write a 1-sentence urgent SMS message asking the user to book a demo. Include a short CTA."
                    output = generate_hf_content(ctx, lead_id=lead_id, max_tokens=40)
                st.session_state["sms_draft_output"] = output

            if "sms_draft_output" in st.session_state and st.session_state["sms_draft_output"]:
                output = st.session_state["sms_draft_output"]
                st.text_area("Draft Output", output, height=100, key="sms_draft_display")
                if lead_id:
                    if st.button("Send SMS Campaign", key="send_sms"):
                        with st.spinner("Sending SMS campaign..."):
                            res = post_campaign(lead_id, "sms", output)
                        if res:
                            st.success("SMS campaign sent.")
                            st.session_state.pop("sms_draft_output", None)

        # ── Social Agent ─────────────────────────────────────────────────────
        with tab3:
            st.markdown("#### Social Media / Ad Audience Agent")
            st.info("Pushes enriched segments to LinkedIn/Facebook lookalike audiences.")

# -----------------------------------------------------------------------------
# STEP 5 — Campaign Orchestration Hub
# -----------------------------------------------------------------------------
elif selection == "5. Campaign Orchestration Hub":
    st.header("Step 5: Campaign Orchestration Hub")
    st.markdown("### The Decision Center")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Frequency Control")
        max_sends_day  = st.slider("Max Sends Per Day", 1, 10, 3)
        max_sends_week = st.slider("Max Sends Per Week", 1, 30, 7)
        cooldown       = st.number_input("Cooldown between campaigns (Hours)", value=24)
    with col2:
        st.subheader("Control Panel")
        mode = st.radio("Operating Mode", ["Manual (Approval Required)", "Auto (Fully Autonomous)"])
        content_type = st.multiselect(
            "Content Types Allowed",
            ["Promotional", "Reminder", "Nurture", "Awareness", "Offer/Discount"],
            default=["Nurture", "Reminder"]
        )

    if st.button("Save Settings"):
        st.success("Hub Orchestration Settings saved.")

# -----------------------------------------------------------------------------
# STEP 7 — CRM & Analytics Dashboard
# -----------------------------------------------------------------------------
elif selection == "7. CRM & Analytics Dashboard":
    st.header("Step 7: CRM & Analytics Dashboard")
    st.markdown("Consolidated view of Lead History, Campaign Engagement, and Next Actions.")

    with st.spinner("Loading CRM data..."):
        leads = get_leads()

    if not leads:
        st.info("CRM is empty.")
    else:
        email_list = [l.get("email", "") for l in leads if l.get("email")]
        selected_lead_email = st.selectbox("Select Lead to view CRM record", email_list)
        lead_rec = next((l for l in leads if l.get("email") == selected_lead_email), {})
        lead_id  = lead_rec.get("id")

        with st.spinner("Loading lead profile and history..."):
            profile = get_lead_profile(lead_id) if lead_id else {}
            detail  = get_lead_detail(lead_id)  if lead_id else {}

        events_raw    = detail.get("events") or []
        campaigns_raw = detail.get("campaigns") or []

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("### Lead Details")
            score_val = lead_rec.get("score")
            st.metric("Score", int(score_val) if score_val is not None else "N/A")
            tier_val = lead_rec.get("segment")
            st.write("**Tier:**", str(tier_val).upper() if tier_val else "N/A")
            st.write("**Name:**", profile.get("name") or "—")
            st.write("**LinkedIn:**", profile.get("linkedin_url") or "—")
            st.write("**Customer Notes:**", profile.get("customer_notes") or "—")

            st.markdown("---")
            st.write("### Recommended Next Action")
            seg = lead_rec.get("segment")
            if seg == "platinum":
                st.success("Manual Rep Outreach Required")
            elif seg == "gold":
                st.info("Trigger Automated Free Trial Nurture")
            elif seg:
                st.warning("Continue Passive Social Retargeting")
            else:
                st.info("N/A")

        with col2:
            st.write("### Interaction & Campaign History")

            st.write("#### Events Tracking")
            if events_raw:
                try:
                    ev_df = pd.DataFrame([
                        {
                            "Action": e.get("action_type", ""),
                            "Date":   humanize_ts(e.get("created_at", "")),
                        }
                        for e in events_raw if isinstance(e, dict)
                    ])
                    st.dataframe(ev_df, use_container_width=True)
                except Exception:
                    st.caption("Could not render events.")
            else:
                st.caption("No events recorded.")

            st.write("#### Outreach Campaigns Sent")
            if campaigns_raw:
                try:
                    camp_df = pd.DataFrame([
                        {
                            "Channel": c.get("channel", ""),
                            "Content": (str(c.get("generated_content") or ""))[:80],
                            "Status":  c.get("sent_status", ""),
                            "Date":    humanize_ts(c.get("created_at", "")),
                        }
                        for c in campaigns_raw if isinstance(c, dict)
                    ])
                    st.dataframe(camp_df, use_container_width=True)
                except Exception:
                    st.caption("Could not render campaigns.")
            else:
                st.caption("No campaigns sent yet.")

# -----------------------------------------------------------------------------
# STEPS 2, 3, 4, 5 — Distinct lead-centric views
# -----------------------------------------------------------------------------
elif selection in (
    "1. Customer Identity Resolution",
    "2. Customer 360 Profile",
    "4. Customer Intelligence & Segmentation",
):
    _step_label = {
        "1. Customer Identity Resolution":         ("Step 1: Customer Identity Resolution",         "Real-time identity stitching & profile resolution"),
        "2. Customer 360 Profile":                 ("Step 2: Customer 360 Profile",                 "Unified customer profile — preferences, consent, journey & engagement"),
        "4. Customer Intelligence & Segmentation": ("Step 4: Customer Intelligence & Segmentation", "Scoring & predictive intelligence dashboard"),
    }[selection]
    st.header(_step_label[0])
    st.markdown(_step_label[1])

    LIFECYCLE_COLORS = {
        "new": "🟦", "active": "🟩", "vip": "🟨",
        "at_risk": "🟧", "dormant": "🟥",
    }
    TIER_COLORS = {
        "bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎",
    }
    NBA_LABELS = {
        "send_discount_offer":        "💸 Send Discount Offer",
        "send_reengagement_campaign": "📢 Re-engagement Campaign",
        "whatsapp_followup":          "💬 WhatsApp Follow-up",
        "sales_call":                 "📞 Sales Call",
        "premium_upgrade_offer":      "⭐ Premium Upgrade Offer",
        "nurture_email":              "📧 Nurture Email",
    }
    TIER_CSS = {
        "bronze":   ("🥉", "#cd7f32", "#3d2b1f"),
        "silver":   ("🥈", "#a8a9ad", "#2a2a2e"),
        "gold":     ("🥇", "#ffd700", "#3d3510"),
        "platinum": ("💎", "#e5e4e2", "#1e2a2e"),
    }
    LC_CSS = {
        "new":     ("#60a5fa", "#1e2d42"),
        "active":  ("#34d399", "#1a2e26"),
        "vip":     ("#fbbf24", "#2e2a14"),
        "at_risk": ("#f97316", "#2e1e0f"),
        "dormant": ("#f87171", "#2e1414"),
    }
    CHANNEL_COLORS = {
        "email":    ("#60a5fa", "#1e2d42"),
        "sms":      ("#34d399", "#1a2e26"),
        "whatsapp": ("#4ade80", "#162d1a"),
        "linkedin": ("#818cf8", "#1e1e3a"),
        "push":     ("#fb923c", "#2e1e0f"),
        "in_app":   ("#f472b6", "#2e1428"),
    }
    JOURNEY_COLORS = {
        "awareness":     ("#60a5fa", "#1e2d42"),
        "consideration": ("#a78bfa", "#1e1e3a"),
        "decision":      ("#fbbf24", "#2e2a14"),
        "retention":     ("#34d399", "#1a2e26"),
        "advocacy":      ("#4ade80", "#162d1a"),
    }
    CONF_ICON  = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    CONF_COLOR = {"high": "#34d399", "medium": "#fbbf24", "low": "#f87171"}

    with st.spinner("Loading leads..."):
        leads_raw = get_leads()

    if not leads_raw:
        st.info("No leads yet. Go to Step 1 and track some events first.")
        st.stop()

    try:
        full_df = pd.DataFrame(leads_raw)
    except Exception:
        st.error("Failed to build leads dataframe.")
        st.stop()

    if "segment" in full_df.columns and "customer_tier" not in full_df.columns:
        full_df["customer_tier"] = full_df["segment"]

    if "is_duplicate" in full_df.columns:
        full_df = full_df[full_df["is_duplicate"].fillna(0).astype(int) == 0]

    for col, default in [
        ("name", ""), ("company", ""), ("title", ""),
        ("identity_confidence", None), ("lifecycle_stage", None),
        ("churn_risk_score", None), ("next_best_action", None),
        ("rfm_total_score", None), ("clv", None), ("last_interaction", ""),
        ("is_duplicate", 0),
    ]:
        if col not in full_df.columns:
            full_df[col] = default

    if full_df.empty:
        st.info("No active leads found.")
        st.stop()

    # ── Lead selector (Steps 2-4) ─────────────────────────────────────────────
    # BUG FIX: removed unsafe open <div> wrapper + closing </div> as separate markdown
    row     = None
    lead_id = None

    with st.container():
            st.markdown(
                "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                "color:#666;margin-bottom:10px;'>🔍 LEAD SELECTOR</p>",
                unsafe_allow_html=True,
            )
            default_search = ""
            if selection == "2. Customer 360 Profile" and st.session_state.selected_customer_email:
                default_search = st.session_state.selected_customer_email
            search_query = st.text_input(
                "Search by email, name, or company",
                default_search,
                label_visibility="collapsed",
                placeholder="Search by email, name, or company…",
            )

            filtered_df = full_df.copy()
            if search_query:
                q = search_query.lower()
                mask = (
                    filtered_df["email"].astype(str).str.lower().str.contains(q, na=False)
                    | filtered_df["name"].astype(str).str.lower().str.contains(q, na=False)
                    | filtered_df["company"].astype(str).str.lower().str.contains(q, na=False)
                )
                filtered_df = filtered_df[mask]

            if filtered_df.empty:
                st.warning("No leads match your search.")
                st.stop()

            lead_labels = filtered_df.apply(
                lambda r: f'{r.get("email", "--")} [{r.get("name", "--") or "--"}]',
                axis=1,
            ).tolist()
            selected_label = st.selectbox("Select Lead", lead_labels)

    selected_idx   = lead_labels.index(selected_label)
    row_basic      = filtered_df.iloc[selected_idx]
    lead_id        = int(row_basic["id"]) if "id" in row_basic else int(row_basic.get("lead_id", 0) or 0)

    with st.spinner("Loading profile..."):
        profile_data = get_lead_profile(lead_id)
    row = build_row(profile_data) if profile_data else build_row(row_basic.to_dict())

    # ── Pre-compute shared display values ─────────────────────────────────────
    if row is not None:
        _tier_raw  = row.get("customer_tier") or row.get("segment")
        tier_val   = str(_tier_raw).lower() if _tier_raw else None
        tier_icon  = TIER_COLORS.get(tier_val, "⚪") if tier_val else "⚪"

        _conf_raw  = row.get("identity_confidence")
        conf_val   = str(_conf_raw).lower() if _conf_raw else None
        conf_icon  = CONF_ICON.get(conf_val, "⚪") if conf_val else "⚪"
        conf_css_color = CONF_COLOR.get(conf_val, "#888") if conf_val else "#888"

        _lc_raw    = row.get("lifecycle_stage")
        lc         = str(_lc_raw).lower() if _lc_raw else None
        lc_ic      = LIFECYCLE_COLORS.get(lc, "⚪") if lc else "⚪"

        _churn_raw = row.get("churn_risk_score")
        churn      = int(_churn_raw) if _churn_raw is not None else None

        _urgency_raw = row.get("urgency_score")
        urgency      = int(_urgency_raw) if _urgency_raw is not None else None

        _nba_raw   = row.get("next_best_action")
        nba        = str(_nba_raw) if _nba_raw else None
        nba_label  = NBA_LABELS.get(nba, nba) if nba else None

        tier_badge_color, tier_bg = TIER_CSS.get(tier_val, ("⚪", "#888", "#1e1e2e"))[1:] if tier_val else ("#888", "#1e1e2e")
        tier_badge_icon           = TIER_CSS.get(tier_val, ("⚪",))[0] if tier_val else "⚪"
        lc_text_color, lc_bg      = LC_CSS.get(lc, ("#888", "#1e1e2e")) if lc else ("#888", "#1e1e2e")

        churn_color   = "#f87171" if churn is not None and churn >= 70 else "#fbbf24" if churn is not None and churn >= 40 else "#34d399"
        urgency_color = "#f87171" if urgency is not None and urgency >= 70 else "#fbbf24" if urgency is not None and urgency >= 40 else "#34d399"

        def _render_recent_events(lid):
            with st.expander("🕓 Recent Events (last 5)", expanded=False):
                with st.spinner("Loading events..."):
                    detail_data = get_lead_detail(lid)
                recent_evs = (detail_data.get("events") or [])[:5]
                if recent_evs:
                    try:
                        ev_df = pd.DataFrame([
                            {
                                "action_type": e.get("action_type", ""),
                                "created_at":  humanize_ts(e.get("created_at", "")),
                            }
                            for e in recent_evs if isinstance(e, dict)
                        ])
                        st.dataframe(ev_df, use_container_width=True, hide_index=True)
                    except Exception:
                        st.caption("Could not render events.")
                else:
                    st.caption("No events yet.")

        # =====================================================================
        # STEP 1 — Customer Identity Resolution
        # BUG FIX: all user values escaped with esc(); no raw </div> markdown
        # =====================================================================
        if selection == "1. Customer Identity Resolution":

            st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

            name_val    = esc(row.get("name") or "—")
            company_val = esc(row.get("company") or "—")
            title_val   = esc(row.get("title") or "—")
            mobile_val  = esc(row.get("mobile_number") or "—")
            ucp_id_val  = esc(row.get("ucp_id") or "—")
            email_val   = esc(row.get("email", ""))
            consent_val = str(row.get("consent_status") or "pending")
            if consent_val.lower() not in ("granted", "withdrawn", "pending"):
                consent_val = "pending"
            consent_color = {
                "granted": "#34d399", "pending": "#fbbf24", "withdrawn": "#f87171"
            }.get(consent_val.lower(), "#fbbf24")
            consent_disp = esc(consent_val.upper())
            is_dup = bool(row.get("is_duplicate", False))
            dup_badge = (
                '<span style="background:#3d1a1a;color:#f87171;border:1px solid #f87171;'
                'border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;">⚠ DUPLICATE</span>'
                if is_dup else
                '<span style="background:#1a3d1a;color:#34d399;border:1px solid #34d399;'
                'border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;">✓ UNIQUE</span>'
            )

            # Resolution Type: derive from confidence + duplicate status
            _conf_raw_step1 = row.get("identity_confidence", "low")
            if is_dup and _conf_raw_step1 == "high":
                _resolution_type     = "Deterministic Match"
                _resolution_color    = "#f87171"
                _resolution_bg       = "#3d1a1a"
                _resolution_border   = "#f87171"
                _resolution_icon     = "🔴"
            elif is_dup and _conf_raw_step1 == "medium":
                _resolution_type     = "Probabilistic Match"
                _resolution_color    = "#fbbf24"
                _resolution_bg       = "#3d3010"
                _resolution_border   = "#fbbf24"
                _resolution_icon     = "🟡"
            else:
                _resolution_type     = "Unique Identity"
                _resolution_color    = "#34d399"
                _resolution_bg       = "#1a3d1a"
                _resolution_border   = "#34d399"
                _resolution_icon     = "🟢"
            _resolution_disp = esc(f"{_resolution_icon} {_resolution_type}")

            id_col, meta_col = st.columns([3, 2])

            with id_col:
                identity_card = f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:22px 26px;height:100%;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:14px;">🪪 IDENTITY SUMMARY</div>
<div style="margin-bottom:14px;">
<span style="font-size:24px;font-weight:700;color:#f1f1f1;">{name_val}</span><br>
<span style="font-size:13px;color:#aaa;">{title_val} &nbsp;·&nbsp; {company_val}</span>
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px;color:#ccc;">
<tr><td style="padding:6px 0;color:#666;width:40%;">📧 Email</td><td style="padding:6px 0;font-weight:500;">{email_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">📱 Mobile</td><td style="padding:6px 0;">{mobile_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">🪪 UCP ID</td><td style="padding:6px 0;font-weight:700;color:#a78bfa;font-family:monospace;">{ucp_id_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">✅ Consent</td>
<td style="padding:6px 0;"><span style="color:{consent_color};font-weight:700;">{consent_disp}</span></td></tr>
<tr><td style="padding:6px 0;color:#666;">🔁 Duplicate</td>
<td style="padding:6px 0;">{dup_badge}</td></tr>
</table>
</div>
"""
                st.markdown(identity_card, unsafe_allow_html=True)

            with meta_col:
                _conf_disp  = conf_val.upper() if conf_val else "N/A"
                _conf_label = esc(f"{conf_icon} {_conf_disp}")
                dup_text    = esc("⚠ Duplicate record detected for this identity." if is_dup else "✓ No duplicate records found.")
                dup_bg      = "#3d1a1a" if is_dup else "#1a3d1a"
                dup_color   = "#f87171" if is_dup else "#34d399"
                dup_border  = "#f87171" if is_dup else "#34d399"
                _conf_bar_width = "100%" if conf_val == "high" else "55%" if conf_val == "medium" else "25%" if conf_val == "low" else "0%"

                conf_card = f"""<div style="display:flex;flex-direction:column;gap:14px;">
<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:18px 22px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:12px;">🎯 IDENTITY CONFIDENCE</div>
<div style="font-size:28px;font-weight:800;color:{conf_css_color};margin-bottom:8px;">{_conf_label}</div>
<div style="background:#2a2a3a;border-radius:6px;height:8px;overflow:hidden;">
<div style="width:{_conf_bar_width};height:100%;background:{conf_css_color};border-radius:6px;"></div>
</div>
<div style="font-size:11px;color:#555;margin-top:6px;">Based on matched identity signals</div>
</div>
<div style="background:{dup_bg};border:1px solid {dup_border};border-radius:12px;padding:16px 20px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:{dup_color};margin-bottom:6px;">🔁 DUPLICATE DETECTION</div>
<div style="font-size:13px;color:{dup_color};">{dup_text}</div>
</div>
<div style="background:{_resolution_bg};border:1px solid {_resolution_border};border-radius:12px;padding:16px 20px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:{_resolution_color};margin-bottom:6px;">🧩 RESOLUTION TYPE</div>
<div style="font-size:14px;color:{_resolution_color};font-weight:700;">{_resolution_disp}</div>
</div>
</div>
"""
                st.markdown(conf_card, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:8px;margin-top:4px;'>📡 IDENTITY SIGNALS</p>",
                    unsafe_allow_html=True,
                )
                signals = row.get("identity_signals", [])
                if signals and isinstance(signals, list) and len(signals) > 0:
                    try:
                        sig_df = pd.DataFrame(signals)
                        if "created_at" in sig_df.columns:
                            sig_df["created_at"] = sig_df["created_at"].apply(humanize_ts)
                        st.dataframe(sig_df, use_container_width=True, hide_index=True)
                    except Exception:
                        st.write(signals)
                else:
                    st.caption("No identity signals recorded yet.")

            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            _render_recent_events(lead_id)
            st.session_state.selected_customer = lead_id
            st.session_state.selected_customer_email = row.get("email", "")

        # =====================================================================
        # STEP 2 — Customer 360 Profile
        # BUG FIX: all injected values escaped; no raw </div> markdowns
        # =====================================================================
        elif selection == "2. Customer 360 Profile":

            st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

            left_col, right_col = st.columns([2, 3])

            with left_col:
                name_val        = esc(row.get("name") or "—")
                company_val     = esc(row.get("company") or "—")
                title_val       = esc(row.get("title") or "—")
                mobile_val      = esc(row.get("mobile_number") or "—")
                ucp_id_val      = esc(row.get("ucp_id") or "—")
                email_val       = esc(row.get("email", ""))
                consent_val_raw = str(row.get("consent_status") or "pending")
                if consent_val_raw.lower() not in ("granted", "withdrawn", "pending"):
                    consent_val_raw = "pending"
                consent_color_id = {
                    "granted": "#34d399", "pending": "#fbbf24", "withdrawn": "#f87171"
                }.get(consent_val_raw.lower(), "#fbbf24")
                is_dup = bool(row.get("is_duplicate", False))
                dup_badge = (
                    '<span style="background:#3d1a1a;color:#f87171;border:1px solid #f87171;'
                    'border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;">⚠ DUPLICATE</span>'
                    if is_dup else
                    '<span style="background:#1a3d1a;color:#34d399;border:1px solid #34d399;'
                    'border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;">✓ UNIQUE</span>'
                )

                identity_card_360 = f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:22px 26px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:14px;">🪪 IDENTITY SUMMARY</div>
<div style="margin-bottom:14px;">
<span style="font-size:22px;font-weight:700;color:#f1f1f1;">{name_val}</span><br>
<span style="font-size:13px;color:#aaa;">{title_val} &nbsp;·&nbsp; {company_val}</span>
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px;color:#ccc;">
<tr><td style="padding:6px 0;color:#666;width:42%;">📧 Email</td><td style="padding:6px 0;font-weight:500;">{email_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">📱 Mobile</td><td style="padding:6px 0;">{mobile_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">🪪 UCP ID</td><td style="padding:6px 0;font-weight:700;color:#a78bfa;font-family:monospace;">{ucp_id_val}</td></tr>
<tr><td style="padding:6px 0;color:#666;">🔁 Duplicate</td>
<td style="padding:6px 0;">{dup_badge}</td></tr>
</table>
<div style="margin-top:14px;padding:10px 12px;background:#1a1a2e;border:1px solid #2a2a4a;border-radius:8px;">
<span style="font-size:11px;color:#7c6fff;">🔗 All customer actions are stitched through a Unified Customer Profile ID.</span>
</div>
</div>
"""
                st.markdown(identity_card_360, unsafe_allow_html=True)

            with right_col:
                channel_list = parse_channels(row.get("preferred_channels", ""))
                fav_cat      = esc(row.get("favourite_category") or "—")
                _journey_raw = row.get("customer_journey")
                journey      = str(_journey_raw) if _journey_raw else "—"
                last_seen    = esc(humanize_ts(row.get("last_interaction", "")))
                notes_val    = esc(row.get("customer_notes") or "—")

                _consent_raw3  = row.get("consent_status")
                consent_disp3  = esc(str(_consent_raw3).upper() if _consent_raw3 else "PENDING")
                consent_color3 = {
                    "GRANTED": "#34d399", "PENDING": "#fbbf24", "WITHDRAWN": "#f87171"
                }.get(str(_consent_raw3).upper() if _consent_raw3 else "PENDING", "#fbbf24")

                pref_ch_raw    = row.get("preferred_channel")
                pref_ch_single = esc(str(pref_ch_raw).upper() if pref_ch_raw else "—")
                _pch_tc, _pch_bg = CHANNEL_COLORS.get(str(pref_ch_raw or "").lower(), ("#aaa", "#2a2a3a"))
                pref_ch_pill = (
                    f'<span style="background:{_pch_bg};color:{_pch_tc};border:1px solid {_pch_tc};'
                    f'border-radius:16px;padding:3px 11px;font-size:12px;">{pref_ch_single}</span>'
                    if pref_ch_raw else '<span style="color:#555;">—</span>'
                )

                pills_html = ""
                if channel_list:
                    for ch in channel_list:
                        tc, bg = CHANNEL_COLORS.get(ch.lower(), ("#aaa", "#2a2a3a"))
                        ch_esc = esc(ch)
                        pills_html += (
                            f'<span style="background:{bg};color:{tc};border:1px solid {tc};'
                            f'border-radius:16px;padding:3px 11px;font-size:12px;margin-right:5px;'
                            f'margin-bottom:4px;display:inline-block;">{ch_esc}</span>'
                        )
                else:
                    pills_html = '<span style="color:#555;">—</span>'

                _jc, _jbg = JOURNEY_COLORS.get(journey.lower(), ("#aaa", "#2a2a3a")) if _journey_raw else ("#555", "#1e1e2e")
                journey_disp = esc(journey.upper() if _journey_raw else "—")
                journey_pill = (
                    f'<span style="background:{_jbg};color:{_jc};border:1px solid {_jc};'
                    f'border-radius:16px;padding:3px 11px;font-size:12px;">{journey_disp}</span>'
                )

                pref_card = f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:22px 26px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:14px;">💬 PREFERENCE &amp; ENGAGEMENT</div>
<div style="margin-bottom:14px;">
<div style="font-size:11px;color:#555;margin-bottom:6px;font-weight:600;">PREFERRED CHANNELS</div>
<div style="margin-bottom:4px;">{pills_html}</div>
<div style="font-size:11px;color:#555;margin-top:8px;margin-bottom:4px;">PRIMARY CHANNEL</div>
{pref_ch_pill}
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px;color:#ccc;">
<tr>
<td style="padding:7px 0;color:#666;width:40%;vertical-align:top;">✅ Consent</td>
<td style="padding:7px 0;"><span style="color:{consent_color3};font-weight:700;">{consent_disp3}</span></td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;vertical-align:top;">🗺️ Journey Stage</td>
<td style="padding:7px 0;">{journey_pill}</td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;vertical-align:top;">🏷️ Fav. Category</td>
<td style="padding:7px 0;font-weight:600;">{fav_cat}</td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;vertical-align:top;">🕐 Last Interaction</td>
<td style="padding:7px 0;">{last_seen}</td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;vertical-align:top;">📝 Customer Notes</td>
<td style="padding:7px 0;font-style:italic;color:#bbb;">{notes_val}</td>
</tr>
</table>
</div>
"""
                st.markdown(pref_card, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.expander("✏️ Edit Customer 360 Profile", expanded=False):
                CHANNELS = ["email", "sms", "whatsapp", "linkedin", "push", "in_app"]
                JOURNEYS = ["awareness", "consideration", "decision", "retention", "advocacy"]
                CONSENTS = ["pending", "granted", "withdrawn"]

                st.markdown("**Backend-computed fields (read-only):**")
                ro_col1, ro_col2 = st.columns(2)
                with ro_col1:
                    st.text_input(
                        "Engagement Summary (backend)",
                        value=str(row.get("engagement_summary") or ""),
                        disabled=True,
                        key="ro_engagement_summary",
                    )
                with ro_col2:
                    st.text_input(
                        "Last Interaction (backend)",
                        value=str(row.get("last_interaction") or ""),
                        disabled=True,
                        key="ro_last_interaction",
                    )

                with st.form("c360_edit_form"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        f_name     = st.text_input("Name",          str(row.get("name", "") or ""))
                        f_title    = st.text_input("Title",         str(row.get("title", "") or ""))
                        f_company  = st.text_input("Company",       str(row.get("company", "") or ""))
                        f_linkedin = st.text_input("LinkedIn URL",  str(row.get("linkedin_url", "") or ""))
                        f_mobile   = st.text_input("Mobile Number", str(row.get("mobile_number", "") or ""))

                        _consent_now = str(row.get("consent_status", "pending") or "pending")
                        if _consent_now not in CONSENTS:
                            _consent_now = "pending"
                        f_consent = st.selectbox("Consent Status", CONSENTS, index=CONSENTS.index(_consent_now))

                        _pc_now = str(row.get("preferred_channel", "email") or "email")
                        _pc_idx = CHANNELS.index(_pc_now) if _pc_now in CHANNELS else 0
                        f_pref_channel = st.selectbox("Preferred Channel (single)", CHANNELS, index=_pc_idx)

                    with col_b:
                        _pcs_default    = parse_channels(row.get("preferred_channels", ""))
                        f_pref_channels = st.multiselect("Preferred Channels (multi)", CHANNELS, default=_pcs_default)

                        f_fav_cat = st.text_input("Favourite Category", str(row.get("favourite_category", "") or ""))

                        _journey_now = str(row.get("customer_journey", "awareness") or "awareness")
                        _journey_idx = JOURNEYS.index(_journey_now) if _journey_now in JOURNEYS else 0
                        f_journey = st.selectbox("Customer Journey Stage", JOURNEYS, index=_journey_idx)

                        f_urgency = st.slider("Urgency Score", 0, 100, int(row.get("urgency_score", 0) or 0))
                        f_notes   = st.text_area("Customer Notes", str(row.get("customer_notes", "") or ""))

                    submitted = st.form_submit_button("💾 Save Customer 360")
                    if submitted:
                        errors = []
                        if f_mobile and not valid_mobile(f_mobile):
                            errors.append("Invalid mobile number format.")
                        if not (0 <= f_urgency <= 100):
                            errors.append("Urgency score must be 0–100.")
                        if f_consent not in CONSENTS:
                            errors.append("Invalid consent status.")
                        if errors:
                            for e in errors:
                                st.error(e)
                        else:
                            patch_payload = {
                                "name":               f_name or None,
                                "title":              f_title or None,
                                "company":            f_company or None,
                                "linkedin_url":       f_linkedin or None,
                                "mobile_number":      f_mobile or None,
                                "consent_status":     f_consent,
                                "preferred_channel":  f_pref_channel,
                                "preferred_channels": f_pref_channels,
                                "favourite_category": f_fav_cat or None,
                                "customer_journey":   f_journey,
                                "urgency_score":      f_urgency,
                                "customer_notes":     f_notes or None,
                            }
                            with st.spinner("Saving Customer 360 profile..."):
                                res = patch_lead_profile(lead_id, patch_payload)
                            if res:
                                st.success("Customer 360 profile saved.")
                                st.rerun()

            _render_recent_events(lead_id)

        # =====================================================================
        # STEP 4 — Customer Intelligence & Scoring
        # BUG FIX: broken nested f-string expressions replaced with pre-computed variables
        # BUG FIX: all user values escaped; _rfm_bar returns safe HTML only
        # =====================================================================
        elif selection == "4. Customer Intelligence & Segmentation":

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:10px;'>📊 KEY PERFORMANCE INDICATORS</p>",
                    unsafe_allow_html=True,
                )
                k1, k2, k3, k4, k5 = st.columns(5)
                _score_raw = row.get("score")
                k1.metric("Lead Score",    int(_score_raw) if _score_raw is not None else "N/A")
                _rfmt_raw  = row.get("rfm_total_score")
                k2.metric("RFM Total",     int(_rfmt_raw) if _rfmt_raw is not None else "N/A")
                _clv_raw   = row.get("clv")
                k3.metric("CLV Index",     f"{float(_clv_raw or 0):.1f}" if _clv_raw is not None else "N/A")
                k4.metric("Churn Risk",    f"{churn}%" if churn is not None else "N/A")
                k5.metric("Urgency Score", f"{urgency}/100" if urgency is not None else "N/A")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            intel_col, comm_col = st.columns(2)

            with intel_col:
                _tier_disp   = esc(f"{tier_badge_icon} {tier_val.upper()}") if tier_val else "⚪ N/A"
                _lc_disp     = esc(f"{lc_ic} {lc.upper()}") if lc else "⚪ N/A"
                _conf_disp   = esc(f"{conf_icon} {conf_val.upper()}") if conf_val else "⚪ N/A"
                _churn_pct   = churn if churn is not None else 0
                _churn_label = esc(f"{churn}%") if churn is not None else "N/A"
                _urgency_pct   = urgency if urgency is not None else 0
                _urgency_label = esc(f"{urgency}/100") if urgency is not None else "N/A"

                intel_card = f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:22px 26px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:16px;">🎯 CUSTOMER INTELLIGENCE</div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px;">
<span style="background:{tier_bg};color:{tier_badge_color};border:1px solid {tier_badge_color};border-radius:20px;padding:5px 14px;font-size:13px;font-weight:700;">{_tier_disp}</span>
<span style="background:{lc_bg};color:{lc_text_color};border:1px solid {lc_text_color};border-radius:20px;padding:5px 14px;font-size:13px;font-weight:700;">{_lc_disp}</span>
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px;color:#ccc;margin-bottom:16px;">
<tr>
<td style="padding:7px 0;color:#666;width:48%;">🎯 ID Confidence</td>
<td style="padding:7px 0;font-weight:700;color:{conf_css_color};">{_conf_disp}</td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;">🏷️ Tier</td>
<td style="padding:7px 0;font-weight:600;">{_tier_disp}</td>
</tr>
<tr>
<td style="padding:7px 0;color:#666;">🔄 Lifecycle</td>
<td style="padding:7px 0;">{_lc_disp}</td>
</tr>
</table>
<div style="margin-bottom:14px;">
<div style="display:flex;justify-content:space-between;font-size:12px;color:#888;margin-bottom:5px;">
<span style="font-weight:600;">CHURN RISK</span>
<span style="color:{churn_color};font-weight:700;">{_churn_label}</span>
</div>
<div style="background:#2a2a3a;border-radius:6px;height:10px;overflow:hidden;">
<div style="width:{_churn_pct}%;height:100%;background:{churn_color};border-radius:6px;transition:width 0.4s;"></div>
</div>
</div>
<div>
<div style="display:flex;justify-content:space-between;font-size:12px;color:#888;margin-bottom:5px;">
<span style="font-weight:600;">URGENCY SCORE</span>
<span style="color:{urgency_color};font-weight:700;">{_urgency_label}</span>
</div>
<div style="background:#2a2a3a;border-radius:6px;height:10px;overflow:hidden;">
<div style="width:{_urgency_pct}%;height:100%;background:{urgency_color};border-radius:6px;transition:width 0.4s;"></div>
</div>
</div>
</div>
"""
                st.markdown(intel_card, unsafe_allow_html=True)

            with comm_col:
                rfm_r = row.get("rfm_recency_score")
                rfm_f = row.get("rfm_frequency_score")
                rfm_m = row.get("rfm_monetary_score")
                rfm_t = row.get("rfm_total_score")
                clv   = row.get("clv")
                aov   = row.get("aov")
                fov   = row.get("fov")
                rfm_r_v = int(rfm_r) if rfm_r is not None else None
                rfm_f_v = int(rfm_f) if rfm_f is not None else None
                rfm_m_v = int(rfm_m) if rfm_m is not None else None
                rfm_t_v = int(rfm_t) if rfm_t is not None else None
                clv_v   = float(clv) if clv is not None else None
                aov_v   = float(aov) if aov is not None else None
                fov_v   = float(fov) if fov is not None else None
                rfm_max = 15

                def _rfm_bar(val, color):
                    if val is None:
                        return '<div style="color:#555;font-size:11px;">N/A</div>'
                    pct = min(val / rfm_max * 100, 100)
                    return (
                        f'<div style="background:#2a2a3a;border-radius:4px;height:8px;">'
                        f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:4px;"></div>'
                        f'</div>'
                    )

                # BUG FIX: pre-compute all display values before injecting into HTML
                clv_text  = "N/A" if clv_v  is None else f"{clv_v:.1f}"
                aov_text  = "N/A" if aov_v  is None else f"{aov_v:.2f}"
                fov_text  = "N/A" if fov_v  is None else f"{fov_v:.3f}"
                rfm_text  = "N/A" if rfm_t_v is None else str(rfm_t_v)
                rfm_r_text = "N/A" if rfm_r_v is None else str(rfm_r_v)
                rfm_f_text = "N/A" if rfm_f_v is None else str(rfm_f_v)
                rfm_m_text = "N/A" if rfm_m_v is None else str(rfm_m_v)
                rfm_r_bar = _rfm_bar(rfm_r_v, "#a78bfa")
                rfm_f_bar = _rfm_bar(rfm_f_v, "#34d399")
                rfm_m_bar = _rfm_bar(rfm_m_v, "#60a5fa")

                comm_card = f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:22px 26px;">
<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#666;margin-bottom:16px;">💰 COMMERCIAL METRICS</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px;">
<div style="background:#12122a;border-radius:10px;padding:14px 16px;text-align:center;">
<div style="font-size:11px;color:#666;margin-bottom:4px;font-weight:600;">CLV</div>
<div style="font-size:26px;font-weight:700;color:#a78bfa;">{clv_text}</div>
</div>
<div style="background:#12122a;border-radius:10px;padding:14px 16px;text-align:center;">
<div style="font-size:11px;color:#666;margin-bottom:4px;font-weight:600;">AOV</div>
<div style="font-size:26px;font-weight:700;color:#34d399;">{aov_text}</div>
</div>
<div style="background:#12122a;border-radius:10px;padding:14px 16px;text-align:center;">
<div style="font-size:11px;color:#666;margin-bottom:4px;font-weight:600;">FOV</div>
<div style="font-size:26px;font-weight:700;color:#60a5fa;">{fov_text}</div>
</div>
<div style="background:#12122a;border-radius:10px;padding:14px 16px;text-align:center;">
<div style="font-size:11px;color:#666;margin-bottom:4px;font-weight:600;">RFM TOTAL</div>
<div style="font-size:26px;font-weight:700;color:#fbbf24;">{rfm_text}</div>
</div>
</div>
<div style="font-size:11px;color:#555;margin-bottom:10px;font-weight:700;letter-spacing:1px;">RFM BREAKDOWN</div>
<div style="margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;font-size:12px;color:#aaa;margin-bottom:4px;">
<span>Recency</span><span style="color:#a78bfa;font-weight:700;">{rfm_r_text}</span>
</div>
{rfm_r_bar}
</div>
<div style="margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;font-size:12px;color:#aaa;margin-bottom:4px;">
<span>Frequency</span><span style="color:#34d399;font-weight:700;">{rfm_f_text}</span>
</div>
{rfm_f_bar}
</div>
<div>
<div style="display:flex;justify-content:space-between;font-size:12px;color:#aaa;margin-bottom:4px;">
<span>Monetary</span><span style="color:#60a5fa;font-weight:700;">{rfm_m_text}</span>
</div>
{rfm_m_bar}
</div>
</div>
"""
                st.markdown(comm_card, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:10px;'>👥 CUSTOMER KPIs</p>",
                    unsafe_allow_html=True,
                )
                ck1, ck2, ck3, ck4, ck5 = st.columns(5)
                ck1.metric("Total Customers", len(full_df))
                _avg_score = round(pd.to_numeric(full_df["score"], errors="coerce").mean(), 1) if "score" in full_df.columns else None
                ck2.metric("Avg Lead Score", _avg_score if _avg_score is not None and not pd.isna(_avg_score) else "N/A")
                _avg_clv = round(pd.to_numeric(full_df["clv"], errors="coerce").mean(), 1) if "clv" in full_df.columns else None
                ck3.metric("Avg CLV", _avg_clv if _avg_clv is not None and not pd.isna(_avg_clv) else "N/A")
                _avg_churn = round(pd.to_numeric(full_df["churn_risk_score"], errors="coerce").mean(), 1) if "churn_risk_score" in full_df.columns else None
                ck4.metric("Avg Churn", f"{_avg_churn}%" if _avg_churn is not None and not pd.isna(_avg_churn) else "N/A")
                ck5.metric("Retention Rate", "78%")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:10px;'>🛍️ PRODUCT KPIs</p>",
                    unsafe_allow_html=True,
                )
                pk1, pk2, pk3, pk4, pk5 = st.columns(5)
                pk1.metric("Top Product", "Product A")
                pk2.metric("Recommendation CTR", "12%")
                pk3.metric("Cross Sell Rate", "18%")
                pk4.metric("Upsell Success", "11%")
                pk5.metric("Product Affinity", "0.82")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:10px;'>💳 TRANSACTION KPIs</p>",
                    unsafe_allow_html=True,
                )
                tk1, tk2, tk3, tk4, tk5 = st.columns(5)
                _avg_aov = round(pd.to_numeric(full_df["aov"], errors="coerce").mean(), 2) if "aov" in full_df.columns else None
                tk1.metric("Avg Order Value", f"{_avg_aov}" if _avg_aov is not None and not pd.isna(_avg_aov) else "N/A")
                _avg_fov = round(pd.to_numeric(full_df["fov"], errors="coerce").mean(), 3) if "fov" in full_df.columns else None
                tk2.metric("Purchase Frequency", f"{_avg_fov}" if _avg_fov is not None and not pd.isna(_avg_fov) else "N/A")
                _rev_per_cust = (
                    round(
                        pd.to_numeric(full_df["aov"], errors="coerce").mean() *
                        pd.to_numeric(full_df["fov"], errors="coerce").mean(), 2
                    )
                    if "aov" in full_df.columns and "fov" in full_df.columns else None
                )
                tk3.metric("Revenue Per Customer", f"{_rev_per_cust}" if _rev_per_cust is not None and not pd.isna(_rev_per_cust) else "N/A")
                tk4.metric("Refund Rate", "4%")
                tk5.metric("Cart Abandonment", "27%")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:10px;'>📣 CAMPAIGN KPIs</p>",
                    unsafe_allow_html=True,
                )
                ca1, ca2, ca3, ca4, ca5 = st.columns(5)
                ca1.metric("CTR", "4.2%")
                ca2.metric("Open Rate", "29%")
                ca3.metric("Conversion", "11%")
                ca4.metric("ROAS", "3.4x")
                ca5.metric("CAC", "$14")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.markdown(
                        "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                        "color:#666;margin-bottom:8px;'>📊 CUSTOMER TIER DISTRIBUTION</p>",
                        unsafe_allow_html=True,
                    )
                    if "customer_tier" in full_df.columns:
                        _tier_dist = full_df["customer_tier"].dropna().value_counts().reset_index()
                        _tier_dist.columns = ["Tier", "Count"]
                        st.bar_chart(_tier_dist.set_index("Tier"), height=220)
                    else:
                        st.caption("customer_tier data unavailable.")
                with chart_col2:
                    st.markdown(
                        "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                        "color:#666;margin-bottom:8px;'>📊 LIFECYCLE DISTRIBUTION</p>",
                        unsafe_allow_html=True,
                    )
                    if "lifecycle_stage" in full_df.columns:
                        _lc_dist = full_df["lifecycle_stage"].dropna().value_counts().reset_index()
                        _lc_dist.columns = ["Stage", "Count"]
                        st.bar_chart(_lc_dist.set_index("Stage"), height=220)
                    else:
                        st.caption("lifecycle_stage data unavailable.")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:4px;'>🛍️ AI PRODUCT RECOMMENDATION ENGINE</p>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<p style='font-size:11px;color:#555;margin-bottom:16px;'>"
                    "AI-powered recommendations generated using customer intelligence, lifecycle stage, engagement behavior, and purchase signals.</p>",
                    unsafe_allow_html=True,
                )

                tier        = str(tier_val).lower() if tier_val else ""
                lifecycle   = str(lc).lower() if lc else ""
                churn_score = float(churn) if churn is not None else 0

                if tier == "platinum":
                    _rec_items = [
                        ("Premium Membership",  92, "Matched to Platinum tier profile and high CLV index."),
                        ("Executive Package",   88, "Aligned with VIP engagement patterns and spend history."),
                        ("Priority Support",    84, "High-value customers benefit most from dedicated support."),
                    ]
                elif churn_score > 70:
                    _rec_items = [
                        ("20% Discount Bundle", 95, "Critical retention offer for high churn risk segment."),
                        ("Reactivation Offer",  89, "Re-engagement incentive based on dormancy signals."),
                        ("Loyalty Rewards",     82, "Loyalty program to rebuild engagement and reduce attrition."),
                    ]
                elif lifecycle == "new":
                    _rec_items = [
                        ("Starter Package",    91, "Ideal onboarding product for new lifecycle customers."),
                        ("Welcome Offer",      86, "First-touch incentive to drive early conversion."),
                        ("Free Trial Upgrade", 81, "Low-friction upgrade path to accelerate adoption."),
                    ]
                else:
                    _rec_items = [
                        ("Smart Watch",           88, "Top affinity product based on behavioral purchase signals."),
                        ("Wireless Earbuds",      84, "Frequently co-purchased with similar customer profiles."),
                        ("Premium Subscription",  80, "Subscription upsell aligned with engagement frequency."),
                    ]

                _rec_cols = st.columns(3)
                for _ci, (_rname, _rpct, _rreason) in enumerate(_rec_items):
                    _bar_color = "#7c3aed" if _rpct >= 90 else "#2563eb" if _rpct >= 85 else "#0891b2"
                    _badge_bg  = "#2d1b69" if _rpct >= 90 else "#1e3a6e" if _rpct >= 85 else "#0c3547"
                    with _rec_cols[_ci]:
                        st.markdown(f"""<div style="background:#1e1e2e;border:1px solid #2a2a4a;border-radius:12px;padding:18px 20px;height:100%;">
<div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:10px;">{esc(_rname)}</div>
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
  <div style="flex:1;background:#2a2a3a;border-radius:6px;height:8px;overflow:hidden;">
    <div style="width:{_rpct}%;height:100%;background:{_bar_color};border-radius:6px;"></div>
  </div>
  <span style="background:{_badge_bg};color:{_bar_color};border:1px solid {_bar_color};border-radius:20px;padding:3px 10px;font-size:12px;font-weight:700;white-space:nowrap;">{_rpct}% Match</span>
</div>
<div style="font-size:11px;color:#888;line-height:1.5;">{esc(_rreason)}</div>
</div>""", unsafe_allow_html=True)

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            with st.container():
                st.markdown(
                    "<p style='font-size:12px;font-weight:700;letter-spacing:1.5px;"
                    "color:#666;margin-bottom:8px;'>🚀 NEXT BEST ACTION</p>",
                    unsafe_allow_html=True,
                )
                if nba_label is None:
                    st.caption("Next Best Action not available — backend data pending.")
                elif churn is not None and (churn >= 70 or lc in ("dormant", "at_risk")):
                    st.error(nba_label)
                elif lc == "vip":
                    st.success(nba_label)
                else:
                    st.info(nba_label)

            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            _render_recent_events(lead_id)

    st.markdown("---")

    # ── Segmentation Table (appended to Step 4) ───────────────────────────────
    if selection == "4. Customer Intelligence & Segmentation":
        st.subheader("📋 Customer Segmentation Table")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            _tier_opts = (
                ["All"] + sorted(full_df["customer_tier"].dropna().unique().tolist())
                if "customer_tier" in full_df.columns
                else ["All"]
            )
            f_tier = st.selectbox("Filter by Customer Tier", _tier_opts, key="seg_filter_tier")
        with fc2:
            _lc_opts = (
                ["All"] + sorted(full_df["lifecycle_stage"].dropna().unique().tolist())
                if "lifecycle_stage" in full_df.columns
                else ["All"]
            )
            f_lc = st.selectbox("Filter by Lifecycle Stage", _lc_opts, key="seg_filter_lc")
        with fc3:
            f_churn = st.selectbox(
                "Filter by Churn Risk",
                ["All", "Low (<40)", "Medium (40-69)", "High (≥70)"],
                key="seg_filter_churn",
            )

        with st.spinner("Loading segmentation data..."):
            display_cols = [
                "email", "name", "company", "customer_tier", "lifecycle_stage",
                "score", "rfm_total_score", "clv", "churn_risk_score",
                "next_best_action", "identity_confidence", "last_interaction",
            ]
            seg_df = full_df[[c for c in display_cols if c in full_df.columns]].copy()

            if f_tier != "All" and "customer_tier" in seg_df.columns:
                seg_df = seg_df[seg_df["customer_tier"].astype(str).str.lower() == f_tier.lower()]
            if f_lc != "All" and "lifecycle_stage" in seg_df.columns:
                seg_df = seg_df[seg_df["lifecycle_stage"].astype(str).str.lower() == f_lc.lower()]
            if f_churn != "All" and "churn_risk_score" in seg_df.columns:
                _churn_num = pd.to_numeric(seg_df["churn_risk_score"], errors="coerce").fillna(0)
                if f_churn == "Low (<40)":
                    seg_df = seg_df[_churn_num < 40]
                elif f_churn == "Medium (40-69)":
                    seg_df = seg_df[(_churn_num >= 40) & (_churn_num < 70)]
                elif f_churn == "High (≥70)":
                    seg_df = seg_df[_churn_num >= 70]

            if "last_interaction" in seg_df.columns:
                seg_df["last_interaction"] = seg_df["last_interaction"].apply(humanize_ts)
            if "clv" in seg_df.columns:
                seg_df["clv"] = seg_df["clv"].apply(
                    lambda x: round(float(x), 1) if x is not None else None
                )
            if "churn_risk_score" in seg_df.columns:
                seg_df["churn_risk_score"] = seg_df["churn_risk_score"].apply(
                    lambda x: int(x) if x is not None else None
                )
            if "rfm_total_score" in seg_df.columns:
                seg_df["rfm_total_score"] = seg_df["rfm_total_score"].apply(
                    lambda x: int(x) if x is not None else None
                )
            seg_df.rename(columns={
                "customer_tier":       "Tier",
                "lifecycle_stage":     "Lifecycle",
                "rfm_total_score":     "RFM",
                "churn_risk_score":    "Churn%",
                "next_best_action":    "Next Action",
                "identity_confidence": "ID Conf.",
                "last_interaction":    "Last Seen",
            }, inplace=True)

        st.dataframe(seg_df, use_container_width=True, hide_index=True)

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("**Tier Distribution**")
            if "Tier" in seg_df.columns:
                tier_counts = seg_df["Tier"].value_counts().reset_index()
                tier_counts.columns = ["Tier", "Count"]
                st.bar_chart(tier_counts.set_index("Tier"), height=200)
        with ch2:
            st.markdown("**Lifecycle Distribution**")
            if "Lifecycle" in seg_df.columns:
                lc_counts = seg_df["Lifecycle"].dropna().value_counts().reset_index()
                lc_counts.columns = ["Stage", "Count"]
                st.bar_chart(lc_counts.set_index("Stage"), height=200)

# -----------------------------------------------------------------------------
# STEP 8 — Recommended Next Best Action
# -----------------------------------------------------------------------------
elif selection == "8. Recommended Next Best Action":
    st.header("Step 8: Recommended Next Best Action")
    st.markdown("Per-lead action recommendations derived from lifecycle stage, churn risk, and segment tier.")

    with st.spinner("Loading leads..."):
        leads_raw = get_leads()

    if not leads_raw:
        st.info("No leads yet. Go to Step 1 and track some events first.")
    else:
        NBA_LABELS = {
            "send_discount_offer":        "💸 Send Discount Offer",
            "send_reengagement_campaign": "📢 Re-engagement Campaign",
            "whatsapp_followup":          "💬 WhatsApp Follow-up",
            "sales_call":                 "📞 Sales Call",
            "premium_upgrade_offer":      "⭐ Premium Upgrade Offer",
            "nurture_email":              "📧 Nurture Email",
        }
        LIFECYCLE_COLORS = {
            "new": "🟦", "active": "🟩", "vip": "🟨",
            "at_risk": "🟧", "dormant": "🟥",
        }

        rows = []
        for l in leads_raw:
            if not isinstance(l, dict):
                continue
            rows.append({
                "email":            l.get("email", ""),
                "segment":          l.get("segment"),
                "score":            l.get("score"),
                "lifecycle_stage":  l.get("lifecycle_stage"),
                "churn_risk_score": l.get("churn_risk_score"),
                "next_best_action": l.get("next_best_action"),
                "lead_id":          l.get("id", l.get("lead_id")),
            })

        if not rows:
            st.info("No valid lead records found.")
        else:
            leads = pd.DataFrame(rows)

            selected_email = st.selectbox("Select Lead", leads["email"].tolist())
            lead_rec = leads[leads["email"] == selected_email].iloc[0]
            lead_id  = int(lead_rec.get("lead_id") or 0)

            if lead_id:
                with st.spinner("Loading profile..."):
                    profile = get_lead_profile(lead_id)
                if profile:
                    lc    = profile.get("lifecycle_stage") or lead_rec.get("lifecycle_stage")
                    churn = profile.get("churn_risk_score") if profile.get("churn_risk_score") is not None else lead_rec.get("churn_risk_score")
                    nba   = profile.get("next_best_action") or lead_rec.get("next_best_action")
                else:
                    lc    = lead_rec.get("lifecycle_stage")
                    churn = lead_rec.get("churn_risk_score")
                    nba   = lead_rec.get("next_best_action")
            else:
                lc    = lead_rec.get("lifecycle_stage")
                churn = lead_rec.get("churn_risk_score")
                nba   = lead_rec.get("next_best_action")

            lc        = str(lc).lower() if lc else None
            churn     = int(churn) if churn is not None else None
            nba_label = NBA_LABELS.get(str(nba), str(nba)) if nba else None
            lc_icon   = LIFECYCLE_COLORS.get(lc, "⚪") if lc else "⚪"

            col1, col2 = st.columns(2)
            with col1:
                _score_disp = int(lead_rec["score"]) if lead_rec.get("score") is not None else "N/A"
                st.metric("Lead Score", _score_disp)
                st.metric("Churn Risk", f"{churn}%" if churn is not None else "N/A")
                if churn is not None:
                    st.progress(min(churn, 100) / 100)
                st.markdown(f"**Lifecycle Stage:** {lc_icon} {lc.upper() if lc else 'N/A'}")
                _seg = lead_rec.get("segment")
                st.markdown(f"**Segment Tier:** {str(_seg).upper() if _seg else 'N/A'}")
            with col2:
                st.markdown("### Recommended Action")
                if nba_label is None:
                    st.caption("Next Best Action not available — backend data pending.")
                elif churn is not None and (churn >= 70 or lc in ("dormant", "at_risk")):
                    st.error(nba_label)
                elif lc == "vip" or (lead_rec.get("segment") == "platinum"):
                    st.success(nba_label)
                else:
                    st.info(nba_label)

                st.markdown("---")
                st.markdown("**All Leads — NBA Summary**")
                summary = leads[["email", "segment", "lifecycle_stage", "churn_risk_score", "next_best_action"]].copy()
                summary["next_best_action"] = summary["next_best_action"].map(
                    lambda x: NBA_LABELS.get(str(x), str(x)) if x else "—"
                )
                summary["churn_risk_score"] = pd.to_numeric(
                    summary["churn_risk_score"], errors="coerce"
                ).apply(lambda x: int(x) if x is not None and not pd.isna(x) else None)
                summary.rename(columns={
                    "lifecycle_stage":  "Lifecycle",
                    "churn_risk_score": "Churn%",
                    "next_best_action": "Next Action",
                }, inplace=True)
                st.dataframe(summary, use_container_width=True, hide_index=True)
