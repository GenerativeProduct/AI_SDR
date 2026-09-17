import sqlite3
import json
from datetime import datetime
import os

DB_FILE = 'marketing_agent.db'
# Navigate to the parent directory to find the db if it exists there
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_FILE)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
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
    # Identity resolution fields — added to leads via migration
    for col, typedef in [
        ('membership_id', 'TEXT'),
        ('mobile_number', 'TEXT'),
        ('identity_confidence', "TEXT DEFAULT 'low'"),
        ('canonical_lead_id', 'INTEGER'),
        ('is_duplicate', "INTEGER DEFAULT 0"),
    ]:
        try:
            c.execute(f'ALTER TABLE leads ADD COLUMN {col} {typedef}')
        except Exception:
            pass  # column already exists

    # 2. Customer Profiles
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            name TEXT,
            title TEXT,
            company TEXT,
            linkedin_url TEXT,
            preferred_channel TEXT DEFAULT 'email',
            notes TEXT,
            consent_status TEXT DEFAULT 'pending',
            favourite_category TEXT,
            customer_journey TEXT DEFAULT 'awareness',
            urgency_score INTEGER DEFAULT 0,
            preferred_channels TEXT DEFAULT '["email"]',
            engagement_summary TEXT,
            last_interaction TEXT,
            customer_notes TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    # consent_status migration for existing customer_profiles rows
    try:
        c.execute("ALTER TABLE customer_profiles ADD COLUMN consent_status TEXT DEFAULT 'pending'")
    except Exception:
        pass
    # Customer 360 migrations for existing databases
    for col, typedef in [
        ('favourite_category', 'TEXT'),
        ('customer_journey', "TEXT DEFAULT 'awareness'"),
        ('urgency_score', 'INTEGER DEFAULT 0'),
        ('preferred_channels', "TEXT DEFAULT '[\"email\"]'"),
        ('engagement_summary', 'TEXT'),
        ('last_interaction', 'TEXT'),
        ('customer_notes', 'TEXT'),
    ]:
        try:
            c.execute(f'ALTER TABLE customer_profiles ADD COLUMN {col} {typedef}')
        except Exception:
            pass
    # 3. Events
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            visitor_id TEXT,
            action_type TEXT,
            metadata TEXT,
            created_at TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    # 4. Campaigns
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
    # 5. Hub Configurations
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # 6. Identity Signals — tracks all resolution match keys per lead
    c.execute('''
        CREATE TABLE IF NOT EXISTS identity_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            signal_type TEXT NOT NULL,
            signal_value TEXT NOT NULL,
            created_at TEXT,
            UNIQUE(signal_type, signal_value),
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')

    # Critical Production Indices
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_lead_id ON events(lead_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_visitor_id ON events(visitor_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_action_type ON events(action_type)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_campaigns_lead_id ON campaigns(lead_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_identity_signals_lead ON identity_signals(lead_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_leads_membership ON leads(membership_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_leads_mobile ON leads(mobile_number)')
    
    conn.commit()
    conn.close()

def _compute_identity_confidence(lead_id, conn):
    """Recalculates and persists identity_confidence for a lead based on matched signals."""
    c = conn.cursor()
    c.execute("SELECT signal_type FROM identity_signals WHERE lead_id = ?", (lead_id,))
    types = {r['signal_type'] for r in c.fetchall()}
    c.execute("SELECT visitor_id FROM events WHERE lead_id = ? AND visitor_id IS NOT NULL LIMIT 1", (lead_id,))
    has_cookie = c.fetchone() is not None

    matched = len(types)
    if has_cookie:
        matched += 1

    if matched >= 3:
        confidence = 'high'
    elif matched == 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    c.execute("UPDATE leads SET identity_confidence = ? WHERE id = ?", (confidence, lead_id))
    return confidence


def _upsert_identity_signal(lead_id, signal_type, signal_value, conn):
    """Registers a new identity signal, guarding against duplicate signal_value collisions."""
    if not signal_value:
        return
    c = conn.cursor()
    # Check if another lead already owns this signal value
    c.execute(
        "SELECT lead_id FROM identity_signals WHERE signal_type = ? AND signal_value = ?",
        (signal_type, signal_value)
    )
    existing = c.fetchone()
    if existing and existing['lead_id'] != lead_id:
        # Collision: mark current lead as duplicate of the canonical owner
        canonical_id = existing['lead_id']
        c.execute(
            "UPDATE leads SET is_duplicate = 1, canonical_lead_id = ? WHERE id = ? AND is_duplicate = 0",
            (canonical_id, lead_id)
        )
        return  # Do not re-register the signal under a different lead
    try:
        c.execute(
            "INSERT OR IGNORE INTO identity_signals (lead_id, signal_type, signal_value, created_at) VALUES (?, ?, ?, ?)",
            (lead_id, signal_type, signal_value, datetime.now().isoformat())
        )
    except Exception:
        pass


def _compute_engagement_summary(lead_id, conn):
    """Derives engagement_summary, last_interaction, and urgency_score from events and persists them."""
    c = conn.cursor()
    c.execute(
        "SELECT action_type, created_at FROM events WHERE lead_id = ? ORDER BY created_at DESC LIMIT 50",
        (lead_id,)
    )
    rows = c.fetchall()
    if not rows:
        return

    last_interaction = rows[0]['created_at']

    action_counts: dict = {}
    for r in rows:
        act = r['action_type']
        action_counts[act] = action_counts.get(act, 0) + 1

    total = len(rows)
    high_intent = sum(action_counts.get(a, 0) for a in ['book_demo_click', 'form_submit', 'user_identified'])
    mid_intent  = sum(action_counts.get(a, 0) for a in ['add_to_cart', 'cta_click'])
    low_intent  = sum(action_counts.get(a, 0) for a in ['video_click', 'video_play', 'page_view', 'session_resume'])

    # urgency_score: 0-100 derived from action mix
    raw = min(high_intent * 25 + mid_intent * 10 + low_intent * 2, 100)
    urgency_score = raw

    parts = []
    if high_intent:
        parts.append(f"{high_intent} high-intent action(s)")
    if mid_intent:
        parts.append(f"{mid_intent} mid-intent action(s)")
    if low_intent:
        parts.append(f"{low_intent} engagement action(s)")
    engagement_summary = f"{total} total events: " + ", ".join(parts) if parts else f"{total} events recorded"

    c.execute(
        "UPDATE customer_profiles SET engagement_summary = ?, last_interaction = ?, urgency_score = ? WHERE lead_id = ?",
        (engagement_summary, last_interaction, urgency_score, lead_id)
    )


def log_event(email, action_type, metadata_dict, visitor_id=None,
              membership_id=None, mobile_number=None):
    conn = get_db_connection()
    c = conn.cursor()

    # --- Identity stitching: look up by email, membership_id, or mobile_number ---
    lead_id = None

    if email:
        c.execute("SELECT id FROM leads WHERE email = ?", (email,))
        row = c.fetchone()
        if row:
            lead_id = row['id']

    if lead_id is None and membership_id:
        c.execute("SELECT id FROM leads WHERE membership_id = ?", (membership_id,))
        row = c.fetchone()
        if row:
            lead_id = row['id']
            # Back-fill email on this lead if we now know it
            if email:
                try:
                    c.execute("UPDATE leads SET email = ? WHERE id = ? AND (email IS NULL OR email = '')", (email, lead_id))
                except Exception:
                    pass

    if lead_id is None and mobile_number:
        c.execute("SELECT id FROM leads WHERE mobile_number = ?", (mobile_number,))
        row = c.fetchone()
        if row:
            lead_id = row['id']
            if email:
                try:
                    c.execute("UPDATE leads SET email = ? WHERE id = ? AND (email IS NULL OR email = '')", (email, lead_id))
                except Exception:
                    pass

    if lead_id is None:
        # New lead
        c.execute(
            "INSERT INTO leads (email, score, segment, membership_id, mobile_number, identity_confidence, created_at) "
            "VALUES (?, 1, 'bronze', ?, ?, 'low', ?)",
            (email, membership_id, mobile_number, datetime.now().isoformat())
        )
        lead_id = c.lastrowid
        c.execute("INSERT INTO customer_profiles (lead_id) VALUES (?)", (lead_id,))
    else:
        # Update any newly supplied identity fields
        if membership_id:
            c.execute("UPDATE leads SET membership_id = ? WHERE id = ? AND membership_id IS NULL", (membership_id, lead_id))
        if mobile_number:
            c.execute("UPDATE leads SET mobile_number = ? WHERE id = ? AND mobile_number IS NULL", (mobile_number, lead_id))

    # Register identity signals for collision/duplicate detection
    if email:
        _upsert_identity_signal(lead_id, 'email', email, conn)
    if membership_id:
        _upsert_identity_signal(lead_id, 'membership_id', membership_id, conn)
    if mobile_number:
        _upsert_identity_signal(lead_id, 'mobile_number', mobile_number, conn)

    # Recompute confidence
    _compute_identity_confidence(lead_id, conn)

    c.execute(
        "INSERT INTO events (lead_id, visitor_id, action_type, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
        (lead_id, visitor_id, action_type, json.dumps(metadata_dict), datetime.now().isoformat())
    )

    # Refresh Customer 360 computed fields
    _compute_engagement_summary(lead_id, conn)

    conn.commit()
    conn.close()
    return lead_id

def merge_visitor_data(visitor_id, lead_id):
    """Adopts historical anonymous events into the identified lead profile."""
    if not visitor_id:
        return
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Update all events with this visitor_id to point to the new lead_id
    c.execute("UPDATE events SET lead_id = ? WHERE visitor_id = ? AND lead_id != ?", 
              (lead_id, visitor_id, lead_id))

    # 2. Recompute identity confidence after cookie merge adds a new signal dimension
    _compute_identity_confidence(lead_id, conn)

    conn.commit()
    conn.close()
    
    # 3. Recalculate score after merge
    score_lead(lead_id)

def score_lead(lead_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT action_type FROM events WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
    events = c.fetchall()
    
    score = 0
    segment = 'bronze'
    for ev in events:
        act = ev['action_type']
        if act in ['book_demo_click', 'form_submit', 'user_identified']:
            score += 15
        elif act in ['add_to_cart', 'cta_click']:
            score += 10
        elif act in ['video_click', 'video_play', 'page_view', 'session_resume']:
            score += 2
        elif act == 'scroll_milestone':
            # Score based on depth
            try:
                meta = json.loads(ev['metadata'])
                depth = meta.get('percent', 0)
                if depth >= 75: score += 5
                elif depth >= 50: score += 2
            except: pass
            
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

def get_leads():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT l.*, p.name, p.title, p.company, p.linkedin_url, p.preferred_channel,
               p.notes, p.consent_status, p.favourite_category, p.customer_journey,
               p.urgency_score, p.preferred_channels, p.engagement_summary,
               p.last_interaction, p.customer_notes
        FROM leads l 
        LEFT JOIN customer_profiles p ON l.id = p.lead_id
        WHERE l.is_duplicate = 0 OR l.is_duplicate IS NULL
        ORDER BY l.score DESC
    """)
    leads = c.fetchall()
    conn.close()
    result = []
    for l in leads:
        row = dict(l)
        # Deserialise preferred_channels JSON list
        try:
            row['preferred_channels'] = json.loads(row['preferred_channels'] or '["email"]')
        except Exception:
            row['preferred_channels'] = ['email']
        result.append(row)
    return result

def get_lead(lead_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT l.*, p.name, p.title, p.company, p.linkedin_url, p.preferred_channel,
               p.notes, p.consent_status, p.favourite_category, p.customer_journey,
               p.urgency_score, p.preferred_channels, p.engagement_summary,
               p.last_interaction, p.customer_notes
        FROM leads l 
        LEFT JOIN customer_profiles p ON l.id = p.lead_id
        WHERE l.id = ?
    """, (lead_id,))
    lead = c.fetchone()
    if not lead:
        conn.close()
        return None
    result = dict(lead)
    # Deserialise preferred_channels JSON list
    try:
        result['preferred_channels'] = json.loads(result['preferred_channels'] or '["email"]')
    except Exception:
        result['preferred_channels'] = ['email']
    # Attach identity signals list
    c.execute("SELECT signal_type, signal_value, created_at FROM identity_signals WHERE lead_id = ?", (lead_id,))
    result['identity_signals'] = [dict(r) for r in c.fetchall()]
    conn.close()
    return result

def update_profile(lead_id, profile_dict):
    conn = get_db_connection()
    c = conn.cursor()

    # Serialise preferred_channels list → JSON string if supplied as a list
    preferred_channels = profile_dict.get('preferred_channels')
    if isinstance(preferred_channels, list):
        preferred_channels = json.dumps(preferred_channels)
    elif isinstance(preferred_channels, str):
        # Accept a raw JSON string or a bare channel name
        try:
            json.loads(preferred_channels)
        except Exception:
            preferred_channels = json.dumps([preferred_channels])

    c.execute("""
        UPDATE customer_profiles 
        SET name = ?, title = ?, company = ?, linkedin_url = ?, preferred_channel = ?,
            notes = ?, consent_status = ?, favourite_category = ?, customer_journey = ?,
            urgency_score = ?, preferred_channels = ?, customer_notes = ?
        WHERE lead_id = ?
    """, (
        profile_dict.get('name'),
        profile_dict.get('title'),
        profile_dict.get('company'),
        profile_dict.get('linkedin_url'),
        profile_dict.get('preferred_channel'),
        profile_dict.get('notes'),
        profile_dict.get('consent_status'),
        profile_dict.get('favourite_category'),
        profile_dict.get('customer_journey'),
        profile_dict.get('urgency_score'),
        preferred_channels,
        profile_dict.get('customer_notes'),
        lead_id
    ))

    # Persist identity resolution fields if supplied
    membership_id = profile_dict.get('membership_id')
    mobile_number = profile_dict.get('mobile_number')
    if membership_id:
        c.execute("UPDATE leads SET membership_id = ? WHERE id = ?", (membership_id, lead_id))
        _upsert_identity_signal(lead_id, 'membership_id', membership_id, conn)
    if mobile_number:
        c.execute("UPDATE leads SET mobile_number = ? WHERE id = ?", (mobile_number, lead_id))
        _upsert_identity_signal(lead_id, 'mobile_number', mobile_number, conn)
    if membership_id or mobile_number:
        _compute_identity_confidence(lead_id, conn)
    conn.commit()
    conn.close()

def get_lead_events(lead_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_lead_context(lead_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Profile
    c.execute("""
        SELECT l.*, p.name, p.title, p.company, p.notes, p.consent_status,
               p.favourite_category, p.customer_journey, p.urgency_score,
               p.preferred_channels, p.engagement_summary, p.last_interaction, p.customer_notes
        FROM leads l 
        LEFT JOIN customer_profiles p ON l.id = p.lead_id 
        WHERE l.id = ?
    """, (lead_id,))
    lead = c.fetchone()
    if not lead:
        conn.close()
        return None
    
    # Recent Events
    c.execute("SELECT action_type, metadata, created_at FROM events WHERE lead_id = ? ORDER BY created_at DESC LIMIT 8", (lead_id,))
    events = c.fetchall()
    conn.close()

    lead_dict = dict(lead)
    events_list = [dict(e) for e in events]
    
    context = f"Identity Profile: {lead_dict['name'] or lead_dict['email']}. "
    context += f"Role: {lead_dict['title'] or 'Expert'} at {lead_dict['company'] or 'Institutional Partner'}. "
    context += f"Classification: {lead_dict['segment'].upper()} (Trust Score: {lead_dict['score']}). "
    context += f"Identity Confidence: {lead_dict.get('identity_confidence', 'low').upper()}. "

    if lead_dict.get('customer_journey'):
        context += f"Journey Stage: {lead_dict['customer_journey']}. "
    if lead_dict.get('favourite_category'):
        context += f"Favourite Category: {lead_dict['favourite_category']}. "
    if lead_dict.get('urgency_score') is not None:
        context += f"Urgency Score: {lead_dict['urgency_score']}/100. "
    if lead_dict.get('engagement_summary'):
        context += f"Engagement: {lead_dict['engagement_summary']}. "
    if lead_dict.get('preferred_channels'):
        try:
            chs = json.loads(lead_dict['preferred_channels'])
            context += f"Preferred Channels: {', '.join(chs)}. "
        except Exception:
            pass
    if lead_dict.get('consent_status'):
        context += f"Consent: {lead_dict['consent_status']}. "
    if lead_dict['notes']:
        context += f"Institutional Knowledge: {lead_dict['notes']}. "
    if lead_dict.get('customer_notes'):
        context += f"Customer Notes: {lead_dict['customer_notes']}. "
    if events_list:
        ev_str = " -> ".join([f"[{e['action_type']} at {e['created_at']}]" for e in events_list])
        context += f"Operational History: {ev_str}."
    
    return context

def get_campaigns(lead_id=None):
    conn = get_db_connection()
    c = conn.cursor()
    if lead_id:
        c.execute("SELECT * FROM campaigns WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
    else:
        c.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_event_stats():
    conn = get_db_connection()
    c = conn.cursor()
    # Unique converted leads (form_submit)
    c.execute("SELECT COUNT(DISTINCT lead_id) FROM events WHERE action_type = 'form_submit'")
    converted = c.fetchone()[0]
    
    # Total unique leads
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    
    conversion_rate = (converted / total * 100) if total > 0 else 0
    
    # Active campaigns last 7 days
    c.execute("SELECT COUNT(*) FROM campaigns WHERE created_at > datetime('now', '-7 days')")
    active_campaigns = c.fetchone()[0]
    
    # AI Operations
    c.execute("SELECT COUNT(*) FROM events WHERE action_type = 'auto_agent_dispatch' OR action_type LIKE '%generate%'")
    ai_ops = c.fetchone()[0]
    
    # Tier Distribution
    c.execute("SELECT segment, COUNT(*) as count FROM leads GROUP BY segment")
    segs = {row['segment']: row['count'] for row in c.fetchall()}
    
    # Velocity Sparklines: Last 7 days historical trend for ALL metrics
    leads_velocity = []
    conversion_velocity = []
    campaign_velocity = []
    ai_velocity = []
    
    for i in range(6, -1, -1):
        # Leads
        c.execute("SELECT COUNT(*) FROM leads WHERE DATE(created_at) = DATE('now', '-' || ? || ' days')", (str(i),))
        leads_velocity.append(c.fetchone()[0])
        
        # Conversions
        c.execute("SELECT COUNT(DISTINCT lead_id) FROM events WHERE action_type = 'form_submit' AND DATE(created_at) = DATE('now', '-' || ? || ' days')", (str(i),))
        conversion_velocity.append(c.fetchone()[0])
        
        # Campaigns
        c.execute("SELECT COUNT(*) FROM campaigns WHERE DATE(created_at) = DATE('now', '-' || ? || ' days')", (str(i),))
        campaign_velocity.append(c.fetchone()[0])
        
        # AI Ops
        c.execute("SELECT COUNT(*) FROM events WHERE (action_type = 'auto_agent_dispatch' OR action_type LIKE '%generate%') AND DATE(created_at) = DATE('now', '-' || ? || ' days')", (str(i),))
        ai_velocity.append(c.fetchone()[0])
        
    conn.close()
    return {
        "conversion_rate": f"{conversion_rate:.1f}%",
        "active_campaigns": active_campaigns,
        "ai_responses": ai_ops,
        "segments": segs,
        "total_leads": total,
        "velocity": {
            "leads": leads_velocity,
            "conversions": conversion_velocity,
            "campaigns": campaign_velocity,
            "ai": ai_velocity
        }
    }
