import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

DB_FILE = 'marketing_agent.db'
# The DB lives next to the seed script (at the project root level)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def seed():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run the API first to initialize it.")
        return

    conn = get_db_connection()
    c = conn.cursor()

    print("🌱 Seeding high-fidelity historical data...")

    # Names for realism
    names = [
        "Alexander Pierce", "Elena Rodriguez", "Marcus Thorne", "Sarah Jenkins", 
        "David Chen", "Aisha Khan", "Julian Vane", "Sophie Laurent",
        "Thomas Wright", "Olivia Moore", "Nathan Scott", "Emma Wilson"
    ]
    companies = ["Vellux Corp", "Nexus Systems", "CloudScale", "Innovate AI", "Stellar Media", "Apex Solutions"]
    actions = ['page_view', 'video_play', 'cta_click', 'form_submit', 'auto_agent_dispatch']

    # 1. Clear existing data for a fresh start (Optional, but ensures fidelity)
    print("🧹 Clearing existing operational nodes...")
    c.execute("DELETE FROM events")
    c.execute("DELETE FROM campaigns")
    c.execute("DELETE FROM customer_profiles")
    c.execute("DELETE FROM leads")
    
    # 2. Generate Leads over 14 days
    lead_ids = []
    for i in range(25):
        name = random.choice(names)
        company = random.choice(companies)
        email = f"{name.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com"
        
        # Random spread over last 14 days
        days_ago = random.randint(0, 13)
        created_at = (datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))).isoformat()
        
        try:
            c.execute("INSERT INTO leads (email, score, segment, created_at) VALUES (?, ?, ?, ?)",
                      (email, 1, 'bronze', created_at))
            lead_id = c.lastrowid
            lead_ids.append(lead_id)
            c.execute("INSERT INTO customer_profiles (lead_id, name, company) VALUES (?, ?, ?)",
                      (lead_id, name, company))
        except sqlite3.IntegrityError:
            continue

    # 3. Generate Events for the leads to build score and velocity
    print("📡 Synthesizing event mesh...")
    for idx, lead_id in enumerate(lead_ids):
        # Different behaviors
        num_events = random.randint(5, 15)
        for _ in range(num_events):
            action = random.choice(actions)
            days_ago = random.randint(0, 10)
            created_at = (datetime.now() - timedelta(days=days_ago, minutes=random.randint(0, 500))).isoformat()
            
            c.execute("INSERT INTO events (lead_id, action_type, metadata, created_at) VALUES (?, ?, ?, ?)",
                      (lead_id, action, json.dumps({"source": "organic", "value": random.random()}), created_at))
            
            # If it's a campaign action, log a campaign record too
            if action == 'auto_agent_dispatch':
                c.execute("INSERT INTO campaigns (lead_id, channel, generated_content, sent_status, created_at) VALUES (?, ?, ?, ?, ?)",
                          (lead_id, 'auto_agent', "Personalized intelligence outreach.", 'sent', created_at))

    print("⚖️ Calibrating fidelity scores...")
    conn.commit()
    conn.close()

    # Trigger scoring via the scoring function (pseudo-call)
    # We need to import score_lead from database.py but easier to just do it here
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM leads")
    all_leads = c.fetchall()
    
    for (l_id,) in all_leads:
        c.execute("SELECT action_type FROM events WHERE lead_id = ?", (l_id,))
        evs = c.fetchall()
        score = 0
        for ev in evs:
            act = ev[0]
            if act in ['form_submit']: score += 15
            elif act in ['cta_click']: score += 10
            elif act in ['video_play', 'page_view']: score += 2
            elif act == 'auto_agent_dispatch': score += 5
        
        segment = 'bronze'
        if score >= 25: segment = 'platinum'
        elif score >= 15: segment = 'gold'
        elif score >= 5: segment = 'silver'
        
        c.execute("UPDATE leads SET score = ?, segment = ? WHERE id = ?", (score, segment, l_id))
    
    conn.commit()
    conn.close()
    print("✅ Mission Control synchronized with real historical data.")

if __name__ == "__main__":
    seed()
