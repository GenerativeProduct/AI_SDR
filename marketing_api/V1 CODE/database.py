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
    # Customer Scoring migrations — RFM, CLV, AOV, FOV
    for col, typedef in [
        ('rfm_recency_score',   'INTEGER DEFAULT 0'),
        ('rfm_frequency_score', 'INTEGER DEFAULT 0'),
        ('rfm_monetary_score',  'INTEGER DEFAULT 0'),
        ('rfm_total_score',     'INTEGER DEFAULT 0'),
        ('clv',                 'REAL DEFAULT 0.0'),
        ('aov',                 'REAL DEFAULT 0.0'),
        ('fov',                 'REAL DEFAULT 0.0'),
    ]:
        try:
            c.execute(f'ALTER TABLE customer_profiles ADD COLUMN {col} {typedef}')
        except Exception:
            pass
    # Lifecycle + Predictive Segmentation migrations
    for col, typedef in [
        ('lifecycle_stage',   "TEXT DEFAULT 'new'"),
        ('churn_risk_score',  'INTEGER DEFAULT 0'),
        ('next_best_action',  'TEXT'),
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

def _normalize_signal_value(signal_type, signal_value):
    v = str(signal_value or "").strip()
    if not v:
        return None
    if signal_type == "email":
        return v.lower()
    return v


def _prune_identity_signals(lead_id, conn):
    """Dedupe by (signal_type, signal_value); keep one value per type (prefer leads.*)."""
    c = conn.cursor()
    c.execute(
        "SELECT email, mobile_number, membership_id FROM leads WHERE id = ?",
        (lead_id,),
    )
    lead = c.fetchone()
    preferred = {}
    if lead:
        for col in ("email", "mobile_number", "membership_id"):
            if lead[col]:
                preferred[col] = _normalize_signal_value(col, lead[col])

    c.execute(
        "SELECT id, signal_type, signal_value FROM identity_signals WHERE lead_id = ? ORDER BY id",
        (lead_id,),
    )
    rows = list(c.fetchall())
    seen_tv = set()
    by_type = {}
    delete_ids = []

    for r in rows:
        stype = r["signal_type"]
        sval = _normalize_signal_value(stype, r["signal_value"])
        if not sval:
            delete_ids.append(r["id"])
            continue
        tv = (stype, sval)
        if tv in seen_tv:
            delete_ids.append(r["id"])
            continue
        seen_tv.add(tv)
        by_type.setdefault(stype, []).append((r["id"], sval))

    for stype, items in by_type.items():
        if len(items) <= 1:
            continue
        keep_id = None
        if stype in preferred:
            for sid, sval in items:
                if sval == preferred[stype]:
                    keep_id = sid
                    break
        if keep_id is None:
            keep_id = items[0][0]
        for sid, _ in items:
            if sid != keep_id:
                delete_ids.append(sid)

    for did in set(delete_ids):
        c.execute("DELETE FROM identity_signals WHERE id = ?", (did,))


def _sync_is_duplicate(lead_id, conn):
    c = conn.cursor()
    c.execute("SELECT canonical_lead_id FROM leads WHERE id = ?", (lead_id,))
    row = c.fetchone()
    is_dup = 1 if row and row["canonical_lead_id"] else 0
    c.execute("UPDATE leads SET is_duplicate = ? WHERE id = ?", (is_dup, lead_id))


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
    signal_value = _normalize_signal_value(signal_type, signal_value)
    if not signal_value:
        return
    c = conn.cursor()
    c.execute(
        "SELECT lead_id FROM identity_signals WHERE signal_type = ? AND signal_value = ?",
        (signal_type, signal_value),
    )
    existing = c.fetchone()
    if existing and existing["lead_id"] != lead_id:
        canonical_id = existing["lead_id"]
        c.execute(
            "UPDATE leads SET is_duplicate = 1, canonical_lead_id = ? WHERE id = ?",
            (canonical_id, lead_id),
        )
        _sync_is_duplicate(lead_id, conn)
        return
    c.execute(
        "SELECT signal_value FROM identity_signals WHERE lead_id = ? AND signal_type = ?",
        (lead_id, signal_type),
    )
    for row in c.fetchall():
        existing_val = _normalize_signal_value(signal_type, row["signal_value"])
        if existing_val and existing_val != signal_value:
            return
    try:
        c.execute(
            "INSERT OR IGNORE INTO identity_signals (lead_id, signal_type, signal_value, created_at) VALUES (?, ?, ?, ?)",
            (lead_id, signal_type, signal_value, datetime.now().isoformat()),
        )
    except Exception:
        pass
    _prune_identity_signals(lead_id, conn)
    _sync_is_duplicate(lead_id, conn)


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


def _compute_rfm_clv(lead_id, conn):
    """
    Computes RFM scores (1-5 each axis), CLV index, AOV, FOV and persists them.
    Also derives the customer tier (segment) from rfm_total_score and syncs leads.segment.

    Recency  — days since last event
    Frequency— total event count
    Monetary — high/mid-intent event count (conversion proxy)

    CLV  = rfm_total * frequency * 2.5   (dimensionless engagement index)
    AOV  = monetary_events / max(order_events, 1)
    FOV  = frequency / max(days_active, 1)
    """
    c = conn.cursor()

    # --- Recency ---
    c.execute("SELECT MAX(created_at) FROM events WHERE lead_id = ?", (lead_id,))
    row = c.fetchone()
    last_event_ts = row[0] if row and row[0] else None

    if last_event_ts:
        try:
            last_dt = datetime.fromisoformat(last_event_ts)
            days_since = max((datetime.now() - last_dt).days, 0)
        except Exception:
            days_since = 999
    else:
        days_since = 999

    if days_since <= 1:
        r_score = 5
    elif days_since <= 7:
        r_score = 4
    elif days_since <= 30:
        r_score = 3
    elif days_since <= 90:
        r_score = 2
    else:
        r_score = 1

    # --- Frequency ---
    c.execute("SELECT COUNT(*) FROM events WHERE lead_id = ?", (lead_id,))
    freq = c.fetchone()[0] or 0

    if freq >= 50:
        f_score = 5
    elif freq >= 20:
        f_score = 4
    elif freq >= 10:
        f_score = 3
    elif freq >= 4:
        f_score = 2
    else:
        f_score = 1

    # --- Monetary (high/mid-intent proxy) ---
    c.execute(
        "SELECT COUNT(*) FROM events WHERE lead_id = ? AND action_type IN "
        "('form_submit','book_demo_click','user_identified','add_to_cart','cta_click')",
        (lead_id,)
    )
    monetary_events = c.fetchone()[0] or 0

    if monetary_events >= 10:
        m_score = 5
    elif monetary_events >= 5:
        m_score = 4
    elif monetary_events >= 3:
        m_score = 3
    elif monetary_events >= 1:
        m_score = 2
    else:
        m_score = 1

    rfm_total = r_score + f_score + m_score  # 3–15

    # --- CLV index ---
    clv = round(rfm_total * freq * 2.5, 2)

    # --- AOV: monetary events / order-intent events ---
    c.execute(
        "SELECT COUNT(*) FROM events WHERE lead_id = ? AND action_type IN ('form_submit','add_to_cart')",
        (lead_id,)
    )
    order_events = c.fetchone()[0] or 0
    aov = round(monetary_events / max(order_events, 1), 2)

    # --- FOV: events per active day ---
    c.execute("SELECT MIN(created_at), MAX(created_at) FROM events WHERE lead_id = ?", (lead_id,))
    span_row = c.fetchone()
    try:
        first_dt = datetime.fromisoformat(span_row[0])
        last_dt2  = datetime.fromisoformat(span_row[1])
        days_active = max((last_dt2 - first_dt).days, 1)
    except Exception:
        days_active = 1
    fov = round(freq / days_active, 4)

    # --- Tier from rfm_total ---
    if rfm_total >= 13:
        rfm_segment = 'platinum'
    elif rfm_total >= 9:
        rfm_segment = 'gold'
    elif rfm_total >= 6:
        rfm_segment = 'silver'
    else:
        rfm_segment = 'bronze'

    c.execute(
        """UPDATE customer_profiles
           SET rfm_recency_score=?, rfm_frequency_score=?, rfm_monetary_score=?,
               rfm_total_score=?, clv=?, aov=?, fov=?
           WHERE lead_id=?""",
        (r_score, f_score, m_score, rfm_total, clv, aov, fov, lead_id)
    )
    # Sync tier to leads table
    c.execute("UPDATE leads SET segment=? WHERE id=?", (rfm_segment, lead_id))
    return r_score, f_score, m_score, rfm_total, clv, aov, fov, rfm_segment


def _compute_lifecycle_predictive(lead_id, conn):
    """
    Derives lifecycle_stage, churn_risk_score, and next_best_action from
    existing scoring/event/RFM signals and persists them to customer_profiles.

    lifecycle_stage values: new | active | vip | at_risk | dormant
    churn_risk_score: 0-100 (higher = more likely to churn)
    next_best_action: one of the defined action strings
    """
    c = conn.cursor()

    # Pull lead creation date and scoring fields
    c.execute(
        "SELECT l.score, l.segment, l.created_at, "
        "p.rfm_recency_score, p.rfm_frequency_score, p.rfm_monetary_score, "
        "p.rfm_total_score, p.clv, p.urgency_score, p.last_interaction "
        "FROM leads l LEFT JOIN customer_profiles p ON l.id = p.lead_id "
        "WHERE l.id = ?",
        (lead_id,)
    )
    row = c.fetchone()
    if not row:
        return

    score         = row['score'] or 0
    segment       = row['segment'] or 'bronze'
    created_at    = row['created_at'] or datetime.now().isoformat()
    r_score       = row['rfm_recency_score'] or 0
    f_score       = row['rfm_frequency_score'] or 0
    m_score       = row['rfm_monetary_score'] or 0
    rfm_total     = row['rfm_total_score'] or 0
    clv           = row['clv'] or 0.0
    urgency_score = row['urgency_score'] or 0
    last_iact     = row['last_interaction']

    # Days since account creation
    try:
        created_dt  = datetime.fromisoformat(created_at)
        days_old    = max((datetime.now() - created_dt).days, 0)
    except Exception:
        days_old = 0

    # Days since last interaction
    if last_iact:
        try:
            last_dt      = datetime.fromisoformat(last_iact)
            days_inactive = max((datetime.now() - last_dt).days, 0)
        except Exception:
            days_inactive = 999
    else:
        days_inactive = 999

    # Recent high-intent events in last 14 days
    c.execute(
        "SELECT COUNT(*) FROM events WHERE lead_id = ? "
        "AND action_type IN ('form_submit','book_demo_click','user_identified','add_to_cart','cta_click') "
        "AND created_at >= datetime('now', '-14 days')",
        (lead_id,)
    )
    recent_high_intent = c.fetchone()[0] or 0

    # Total events in last 30 days
    c.execute(
        "SELECT COUNT(*) FROM events WHERE lead_id = ? "
        "AND created_at >= datetime('now', '-30 days')",
        (lead_id,)
    )
    recent_total = c.fetchone()[0] or 0

    # ── Lifecycle Stage ──────────────────────────────────────────────────────
    if days_old <= 7 and f_score <= 2:
        lifecycle_stage = 'new'
    elif days_inactive >= 90:
        lifecycle_stage = 'dormant'
    elif days_inactive >= 30 and recent_total == 0:
        lifecycle_stage = 'at_risk'
    elif (segment in ('platinum', 'gold') and rfm_total >= 10 and clv >= 100):
        lifecycle_stage = 'vip'
    else:
        lifecycle_stage = 'active'

    # ── Churn Risk Score (0-100) ─────────────────────────────────────────────
    # Higher recency_score = more recent = lower churn risk
    recency_penalty  = max(0, (5 - r_score) * 12)   # 0-48 pts
    frequency_penalty= max(0, (5 - f_score) * 6)    # 0-24 pts
    monetary_penalty = max(0, (5 - m_score) * 5)    # 0-20 pts
    inactivity_bonus = min(days_inactive // 7, 8)   # 0-8 pts
    churn_risk_score = min(recency_penalty + frequency_penalty + monetary_penalty + inactivity_bonus, 100)

    # Dormant/at_risk floors
    if lifecycle_stage == 'dormant':
        churn_risk_score = max(churn_risk_score, 80)
    elif lifecycle_stage == 'at_risk':
        churn_risk_score = max(churn_risk_score, 55)
    elif lifecycle_stage == 'vip':
        churn_risk_score = min(churn_risk_score, 30)
    elif lifecycle_stage == 'new':
        churn_risk_score = min(churn_risk_score, 40)

    # ── Next Best Action ─────────────────────────────────────────────────────
    if lifecycle_stage == 'dormant':
        next_best_action = 'send_reengagement_campaign'
    elif lifecycle_stage == 'at_risk' and churn_risk_score >= 70:
        next_best_action = 'send_discount_offer'
    elif lifecycle_stage == 'at_risk':
        next_best_action = 'whatsapp_followup'
    elif lifecycle_stage == 'vip':
        next_best_action = 'sales_call'
    elif lifecycle_stage == 'new' and urgency_score >= 20:
        next_best_action = 'nurture_email'
    elif lifecycle_stage == 'active' and segment == 'gold' and recent_high_intent >= 2:
        next_best_action = 'premium_upgrade_offer'
    elif lifecycle_stage == 'active' and segment in ('silver', 'bronze'):
        next_best_action = 'nurture_email'
    elif lifecycle_stage == 'active' and recent_high_intent >= 1:
        next_best_action = 'sales_call'
    else:
        next_best_action = 'nurture_email'

    c.execute(
        """UPDATE customer_profiles
           SET lifecycle_stage=?, churn_risk_score=?, next_best_action=?
           WHERE lead_id=?""",
        (lifecycle_stage, churn_risk_score, next_best_action, lead_id)
    )
    return lifecycle_stage, churn_risk_score, next_best_action


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
    c.execute("SELECT action_type, metadata FROM events WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
    events = c.fetchall()

    score = 0
    for ev in events:
        act = ev['action_type']
        if act in ['book_demo_click', 'form_submit', 'user_identified']:
            score += 15
        elif act in ['add_to_cart', 'cta_click']:
            score += 10
        elif act in ['video_click', 'video_play', 'page_view', 'session_resume']:
            score += 2
        elif act == 'scroll_milestone':
            try:
                meta = json.loads(ev['metadata'])
                depth = meta.get('percent', 0)
                if depth >= 75:
                    score += 5
                elif depth >= 50:
                    score += 2
            except Exception:
                pass

    # RFM/CLV compute — also writes segment to leads
    _r, _f, _m, _rfm, _clv, _aov, _fov, segment = _compute_rfm_clv(lead_id, conn)

    # Lifecycle + Predictive compute
    _compute_lifecycle_predictive(lead_id, conn)

    c.execute("UPDATE leads SET score=? WHERE id=?", (score, lead_id))
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
               p.last_interaction, p.customer_notes,
               p.rfm_recency_score, p.rfm_frequency_score, p.rfm_monetary_score,
               p.rfm_total_score, p.clv, p.aov, p.fov,
               p.lifecycle_stage, p.churn_risk_score, p.next_best_action
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
               p.last_interaction, p.customer_notes,
               p.rfm_recency_score, p.rfm_frequency_score, p.rfm_monetary_score,
               p.rfm_total_score, p.clv, p.aov, p.fov,
               p.lifecycle_stage, p.churn_risk_score, p.next_best_action
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
    _prune_identity_signals(lead_id, conn)
    _sync_is_duplicate(lead_id, conn)
    c.execute(
        """SELECT signal_type, signal_value, MIN(created_at) AS created_at
           FROM identity_signals WHERE lead_id = ?
           GROUP BY signal_type, signal_value""",
        (lead_id,),
    )
    result["identity_signals"] = [dict(r) for r in c.fetchall()]
    result["is_duplicate"] = bool(
        c.execute("SELECT is_duplicate FROM leads WHERE id = ?", (lead_id,)).fetchone()["is_duplicate"]
    )
    conn.commit()
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
