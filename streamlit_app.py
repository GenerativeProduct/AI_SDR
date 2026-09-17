import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
import json
from datetime import datetime

st.set_page_config(page_title="AI Marketing Agent Hub", page_icon="🚀", layout="wide")

DB_FILE = 'marketing_agent.db'
HF_API_KEY = os.environ.get("HF_API_KEY", "")

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION
# -----------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 1. Leads
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            score INTEGER DEFAULT 1,
            segment TEXT DEFAULT 'bronze',
            created_at TEXT
        )
    ''')
    # 2. Customer Profiles (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            name TEXT,
            linkedin_url TEXT,
            preferred_channel TEXT DEFAULT 'email',
            notes TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    # 3. Events
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            action_type TEXT,
            metadata TEXT,
            created_at TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    # 4. Campaigns (Sent Messages)
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            channel TEXT,
            generated_content TEXT,
            sent_status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    # 5. Hub Configurations (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def log_event(email, action_type, metadata_dict):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT id FROM leads WHERE email = ?", (email,))
    lead = c.fetchone()
    if not lead:
        c.execute("INSERT INTO leads (email, score, segment, created_at) VALUES (?, 1, 'bronze', ?)", 
                  (email, datetime.now().isoformat()))
        lead_id = c.lastrowid
        # Also create empty profile
        c.execute("INSERT INTO customer_profiles (lead_id) VALUES (?)", (lead_id,))
    else:
        lead_id = lead['id']

    c.execute("INSERT INTO events (lead_id, action_type, metadata, created_at) VALUES (?, ?, ?, ?)",
              (lead_id, action_type, json.dumps(metadata_dict), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return lead_id

def score_lead(lead_id):
    conn = get_db()
    c = conn.cursor()
    # Sum event weights or last event logic
    c.execute("SELECT action_type FROM events WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
    events = c.fetchall()
    
    score = 0
    segment = 'bronze'
    for ev in events:
        act = ev['action_type']
        if act in ['book_demo_click', 'form_submit']:
            score += 15
        elif act in ['add_to_cart', 'cta_click']:
            score += 10
        elif act in ['video_click', 'page_view']:
            score += 2
            
    if score >= 25:
        segment = 'platinum'
    elif score >= 15:
        segment = 'gold'
    elif score >= 5:
        segment = 'silver'
        
    c.execute("UPDATE leads SET score = ?, segment = ? WHERE id = ?", (score, segment, lead_id))
    conn.commit()
    conn.close()
    return score, segment

def generate_hf_content(prompt_context, max_tokens=50):
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt_context,
        "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code != 200:
            return f"[HF Error {response.status_code}]: {response.text}"
        else:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            return str(result)
    except Exception as e:
        return f"[Connection Failed: {str(e)}]"
# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("🚀 AI Marketing Agent")
st.sidebar.markdown("Navigate through the 7-step architecture.")

nav_options = [
    "1. Event Tracking",
    "2. Personalization",
    "3. Lead Scoring",
    "4. Customer Profile + Segments",
    "5. Campaign Orchestration Hub",
    "6. Channel Agents",
    "7. CRM & Analytics"
]
selection = st.sidebar.radio("Go to step:", nav_options)

# -----------------------------------------------------------------------------
# UI SECTIONS
# -----------------------------------------------------------------------------

if selection == "1. Event Tracking":
    st.header("Step 1: Event Tracking")
    st.markdown("Simulate a user interacting with our landing page or product.")
    
    with st.form("event_track_form"):
        col1, col2 = st.columns(2)
        with col1:
            u_email = st.text_input("User Email", "visitor@example.com")
            action = st.selectbox("Action Performed", ["page_view", "video_click", "cta_click", "add_to_cart", "book_demo_click", "form_submit"])
        with col2:
            metadata = st.text_area("Metadata (JSON format)", '{"source": "linkedin_ad"}')
        submit_event = st.form_submit_button("Simulate Event")
        
    if submit_event:
        try:
            meta_dict = json.loads(metadata)
        except:
            meta_dict = {"raw": metadata}
            
        l_id = log_event(u_email, action, meta_dict)
        st.success(f"Event logged! Lead ID: {l_id}")
        
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM events ORDER BY created_at DESC LIMIT 10", conn)
    conn.close()
    st.subheader("Recent Events (Raw Stream)")
    st.dataframe(df, use_container_width=True)

elif selection == "2. Personalization":
    st.header("Step 2: Personalization Logic")
    st.markdown("Generates dynamic content/banners based on `Customer + Events + Interactions + Segment`")
    
    conn = get_db()
    leads = pd.read_sql_query("SELECT l.id, l.email, l.segment, p.name FROM leads l LEFT JOIN customer_profiles p ON l.id = p.lead_id", conn)
    conn.close()
    
    if len(leads) == 0:
        st.info("No leads available yet. Go to Step 1 and track an event first.")
    else:
        selected_email = st.selectbox("Select User for Personalization preview", leads['email'])
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM leads WHERE email=?", (selected_email,))
        lead = c.fetchone()
        c.execute("SELECT * FROM events WHERE lead_id=? ORDER BY created_at DESC LIMIT 3", (lead['id'],))
        events = c.fetchall()
        c.execute("SELECT * FROM customer_profiles WHERE lead_id=?", (lead['id'],))
        profile = c.fetchone()
        conn.close()
        
        event_names = [e['action_type'] for e in events]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("##### Input Data for Agent")
            st.json({
                "Customer": profile['name'] if profile and profile['name'] else selected_email,
                "Segment": lead['segment'],
                "Recent Events": event_names,
                "Past Interactions": len(events)
            })
            
        with col2:
            st.write("##### Hit LLM Agent")
            if st.button("Generate Personalized Content (HF API)"):
                with st.spinner("Calling flan-t5-large via HF Inference API..."):
                    context = f"User is in {lead['segment']} tier. Recent actions: {', '.join(event_names)}."
                    hf_prompt = f"Write a one-sentence personalized website welcome banner for a user: {context}."
                    res = generate_hf_content(hf_prompt, max_tokens=30)
                    st.success("Generated Output")
                    st.info(res)

elif selection == "3. Lead Scoring":
    st.header("Step 3: Lead Scoring Engine")
    st.markdown("Re-evaluates and assigns scores/tiers based on all historical behaviors.")
    
    conn = get_db()
    df = pd.read_sql_query("SELECT id, email, score, segment FROM leads", conn)
    conn.close()
    
    st.dataframe(df, use_container_width=True)
    
    if st.button("Run Global Scoring Batch Job"):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM leads")
        all_leads = c.fetchall()
        conn.close()
        
        for l in all_leads:
            score_lead(l['id'])
            
        st.success("Scoring updated for all profiles.")
        st.rerun()

elif selection == "4. Customer Profile + Segments":
    st.header("Step 4: Customer Profile Data Layer")
    st.markdown("Centralized 360 view sitting between scoring and orchestration.")
    
    conn = get_db()
    leads = pd.read_sql_query("SELECT id, email FROM leads", conn)
    if len(leads) > 0:
        lead_selection = st.selectbox("Select Lead to edit profile:", leads['email'])
        l_id = leads[leads['email'] == lead_selection].iloc[0]['id']
        
        c = conn.cursor()
        c.execute("SELECT * FROM customer_profiles WHERE lead_id=?", (int(l_id),))
        profile = c.fetchone()
        
        if profile is None:
            profile = {'name': '', 'linkedin_url': '', 'preferred_channel': 'email', 'notes': ''}
            
        with st.form("profile_form"):
            name = st.text_input("Name", profile['name'] if profile['name'] else "")
            linkedin_url = st.text_input("LinkedIn Profile URL", profile['linkedin_url'] if profile['linkedin_url'] else "")
            pref_chan = st.selectbox("Preferred Channel", ["email", "sms", "linkedin_dm"], index=0 if not profile['preferred_channel'] else ["email", "sms", "linkedin_dm"].index(profile['preferred_channel']))
            notes = st.text_area("Customer Notes", profile['notes'] if profile['notes'] else "")
            
            if st.form_submit_button("Save Profile"):
                c.execute('''UPDATE customer_profiles 
                             SET name=?, linkedin_url=?, preferred_channel=?, notes=? 
                             WHERE lead_id=?''', (name, linkedin_url, pref_chan, notes, l_id))
                conn.commit()
                st.success("Profile Updated")
        
        st.subheader("Segmentation Matrix Overview")
        seg_counts = pd.read_sql_query("SELECT segment, COUNT(*) as count FROM leads GROUP BY segment", conn)
        st.bar_chart(data=seg_counts, x="segment", y="count")
    else:
        st.info("No leads available.")
    conn.close()

elif selection == "5. Campaign Orchestration Hub":
    st.header("Step 5: Campaign Orchestration Hub")
    st.markdown("### The Decision Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Frequency Control")
        max_sends_day = st.slider("Max Sends Per Day", 1, 10, 3)
        max_sends_week = st.slider("Max Sends Per Week", 1, 30, 7)
        cooldown = st.number_input("Cooldown between campaigns (Hours)", value=24)
        
    with col2:
        st.subheader("Control Panel")
        mode = st.radio("Operating Mode", ["Manual (Approval Required)", "Auto (Fully Autonomous)"])
        content_type = st.multiselect("Content Types Allowed", ["Promotional", "Reminder", "Nurture", "Awareness", "Offer/Discount"], default=["Nurture", "Reminder"])
        
    if st.button("Save Settings"):
        st.success("Hub Orchestration Settings saved.")

elif selection == "6. Channel Agents":
    st.header("Step 6: Specialized Channel Agents")
    
    conn = get_db()
    leads = pd.read_sql_query("SELECT id, email FROM leads", conn)
    conn.close()
    
    if len(leads) == 0:
        st.warning("Needs leads to send campaigns.")
    else:
        target_email = st.selectbox("Target Email", leads['email'])
        target_id = leads[leads['email'] == target_email].iloc[0]['id']
        
        tab1, tab2, tab3 = st.tabs(["📧 Email Agent", "📱 SMS Agent", "💼 Social Agent"])
        
        with tab1:
            st.markdown("#### Email Outreach")
            email_type = st.selectbox("Email Type", ["Welcome Sequence", "Nurture", "Discount Offer"], key="emaillist")
            if st.button("Draft Email via HF API"):
                with st.spinner("Drafting Email..."):
                    ctx = f"Write a short B2B {email_type} email. Include a Subject line and 3 sentences."
                    output = generate_hf_content(ctx, 150)
                    st.text_area("Draft Output", output, height=200)
                    if st.button("Send Email Campaign", key="send_email"):
                        conn = get_db()
                        conn.execute("INSERT INTO campaigns (lead_id, channel, generated_content, sent_status, created_at) VALUES (?, ?, ?, 'sent', ?)", 
                                     (int(target_id), 'email', output, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        st.success("Email sent logged in DB.")

        with tab2:
            st.markdown("#### SMS Outreach")
            st.write("Short CTA & Urgency copy")
            if st.button("Draft SMS via HF API"):
                with st.spinner("Drafting SMS..."):
                    ctx = f"Write a 1-sentence urgent SMS message asking the user to book a demo. Include a short CTA."
                    output = generate_hf_content(ctx, 40)
                    st.text_area("Draft Output", output, height=100)
                    if st.button("Send SMS Campaign", key="send_sms"):
                        conn = get_db()
                        conn.execute("INSERT INTO campaigns (lead_id, channel, generated_content, sent_status, created_at) VALUES (?, ?, ?, 'sent', ?)", 
                                     (int(target_id), 'sms', output, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        st.success("SMS sent logged in DB.")
                        
        with tab3:
            st.markdown("#### Social Media / Ad Audience Agent")
            st.info("Pushes enriched segments to LinkedIn/Facebook lookalike audiences.")

elif selection == "7. CRM & Analytics":
    st.header("Step 7: CRM + Customer Details")
    st.markdown("Consolidated view of Lead History, Campaign Engagement, and Next Actions.")
    
    conn = get_db()
    leads = pd.read_sql_query("""
        SELECT l.id as lead_id, l.email, l.score, l.segment, 
               p.name, p.linkedin_url, p.notes
        FROM leads l
        LEFT JOIN customer_profiles p ON l.id = p.lead_id
    """, conn)
    
    if len(leads) > 0:
        selected_lead = st.selectbox("Select Lead to view CRM record", leads['email'])
        l_df = leads[leads['email'] == selected_lead].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("### Lead Details")
            st.metric("Score", l_df['score'])
            st.write("**Tier:**", l_df['segment'].upper())
            st.write("**Name:**", l_df['name'])
            st.write("**LinkedIn:**", l_df['linkedin_url'])
            st.write("**Customer Notes:**", l_df['notes'])
            
            st.markdown("---")
            st.write("### Recommended Next Action")
            if l_df['segment'] == 'platinum': st.success("Manual Rep Outreach Required")
            elif l_df['segment'] == 'gold': st.info("Trigger Automated Free Trial Nurture")
            else: st.warning("Continue Passive Social Retargeting")
            
        with col2:
            st.write("### Interaction & Campaign History")
            hist_events = pd.read_sql_query(f"SELECT action_type as Action, created_at as Date FROM events WHERE lead_id={l_df['lead_id']} ORDER BY created_at DESC", conn)
            hist_camp = pd.read_sql_query(f"SELECT channel, generated_content, sent_status, created_at as Date FROM campaigns WHERE lead_id={l_df['lead_id']} ORDER BY created_at DESC", conn)
            
            st.write("#### Events Tracking")
            st.dataframe(hist_events, use_container_width=True)
            
            st.write("#### Outreach Campaigns Sent")
            st.dataframe(hist_camp, use_container_width=True)
            
    else:
        st.info("CRM is empty.")
    
    conn.close()
