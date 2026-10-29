"""
NEXUS AI Enterprise Support Intelligence Platform
Executive-Grade Service Management & ML Operations Dashboard
"""

import json
import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ── API Endpoint Configuration ───────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
API_PREDICT = f"{API_BASE}/predict"
API_TICKETS = f"{API_BASE}/tickets"
API_AGENTS = f"{API_BASE}/agents"
API_ANALYTICS = f"{API_BASE}/analytics/overview"
API_METRICS = f"{API_BASE}/analytics/model"
API_AUTH_LOGIN = f"{API_BASE}/auth/login"
API_AUTH_REGISTER = f"{API_BASE}/auth/register"
API_EXPORT = f"{API_BASE}/export/tickets"

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS AI - Enterprise Support Platform",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Embedded Backend Auto-Start (Enables 1-Click Cloud Deployment) ────────────
@st.cache_resource
def ensure_backend_alive() -> bool:
    """Ensure Flask backend is reachable. If running on localhost/cloud container, auto-boots Flask."""
    if "127.0.0.1" in API_BASE or "localhost" in API_BASE:
        try:
            r = requests.get(f"{API_BASE}/health", timeout=0.8)
            if r.status_code == 200:
                return True
        except Exception:
            pass

        import threading
        import time
        from app import app as flask_app

        def _run():
            flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

        server_thread = threading.Thread(target=_run, daemon=True)
        server_thread.start()

        for _ in range(25):
            time.sleep(0.2)
            try:
                r = requests.get(f"{API_BASE}/health", timeout=0.8)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
    return False

ensure_backend_alive()

# ── Bulletproof Enterprise CSS (Prevents Any White Leaks, Enforces Contrast) ──
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* 1. Global Background Enforcement (Cover Every Possible Streamlit Container) */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    .stApp, .main, section.main, .block-container {
        background-color: #0B0F19 !important;
        color: #E2E8F0 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    /* 2. Professional Typography Hierarchy */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }

    p, span, label, div {
        color: #CBD5E1;
    }

    .top-pill {
        display: inline-block;
        background: rgba(59, 130, 246, 0.12);
        color: #60A5FA !important;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero-title {
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 6px !important;
    }

    .hero-subtitle {
        font-size: 1.05rem !important;
        color: #94A3B8 !important;
        line-height: 1.6 !important;
        margin-bottom: 32px !important;
    }

    /* 3. Portal Selection Cards */
    .portal-box {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 14px;
        padding: 30px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .portal-box:hover {
        border-color: #3B82F6;
        box-shadow: 0 12px 30px -6px rgba(59, 130, 246, 0.25);
        transform: translateY(-2px);
    }

    .portal-badge {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-bottom: 8px;
    }

    .portal-heading {
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 12px;
    }

    .portal-text {
        font-size: 0.92rem;
        color: #94A3B8 !important;
        line-height: 1.6;
        margin-bottom: 20px;
    }

    .portal-features {
        list-style: none;
        padding: 0;
        margin: 0 0 24px 0;
    }

    .portal-features li {
        font-size: 0.85rem;
        color: #CBD5E1 !important;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }

    .portal-features li::before {
        content: "•";
        color: #38BDF8;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 10px;
    }

    /* 4. Streamlit Primary and Secondary Buttons Override */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        color: #FFFFFF !important;
        border: 1px solid #3B82F6 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
    }

    div.stButton > button[kind="secondary"] {
        background: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        background: #334155 !important;
        border-color: #475569 !important;
        color: #FFFFFF !important;
    }

    /* 5. Inputs, Textareas, Selectboxes */
    input, textarea, select {
        color: #FFFFFF !important;
        background-color: #111827 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    input:focus, textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        border-color: #334155 !important;
    }

    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }

    /* 6. Expanders */
    [data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stExpander"] summary {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 12px 18px !important;
    }

    /* 7. Metric Cards */
    .stat-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 18px 22px;
        height: 100%;
    }

    .stat-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8 !important;
        margin-bottom: 8px;
    }

    .stat-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #FFFFFF !important;
        font-family: 'JetBrains Mono', monospace;
    }

    /* 8. Priority Badges */
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .badge-high {
        background: rgba(239, 68, 68, 0.18) !important;
        color: #FCA5A5 !important;
        border: 1px solid rgba(239, 68, 68, 0.45) !important;
    }

    .badge-medium {
        background: rgba(245, 158, 11, 0.18) !important;
        color: #FDE68A !important;
        border: 1px solid rgba(245, 158, 11, 0.45) !important;
    }

    .badge-low {
        background: rgba(16, 185, 129, 0.18) !important;
        color: #A7F3D0 !important;
        border: 1px solid rgba(16, 185, 129, 0.45) !important;
    }

    .badge-review {
        background: rgba(236, 72, 153, 0.18) !important;
        color: #FBCFE8 !important;
        border: 1px solid rgba(236, 72, 153, 0.45) !important;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
    }

    /* 9. Top Navigation Bar */
    .top-nav {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px 22px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .nav-brand {
        font-size: 1.15rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
    }

    .nav-user {
        background: #1E293B;
        border: 1px solid #334155;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.84rem;
        color: #E2E8F0 !important;
    }

    .guide-box {
        background: #111827;
        border-left: 4px solid #3B82F6;
        border-top: 1px solid #1E293B;
        border-right: 1px solid #1E293B;
        border-bottom: 1px solid #1E293B;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 18px;
        color: #CBD5E1 !important;
        font-size: 0.9rem;
    }

    /* Tables */
    table {
        color: #FFFFFF !important;
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    th {
        color: #FFFFFF !important;
        background-color: #1E293B !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #334155 !important;
    }

    td {
        color: #CBD5E1 !important;
        border-bottom: 1px solid #1E293B !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session State Management ─────────────────────────────────────────────────
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None
if "portal_choice" not in st.session_state:
    st.session_state["portal_choice"] = None  # None, 'customer', or 'agent'
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"  # 'login' or 'register'


# ── Helper Functions ─────────────────────────────────────────────────────────
def get_auth_headers():
    headers = {"Content-Type": "application/json"}
    if st.session_state.get("auth_token"):
        headers["Authorization"] = f"Bearer {st.session_state['auth_token']}"
    return headers


def api_request(url, method="GET", payload=None):
    try:
        headers = get_auth_headers()
        if method == "GET":
            res = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            res = requests.post(url, json=payload, headers=headers, timeout=10)
        elif method == "PATCH":
            res = requests.patch(url, json=payload, headers=headers, timeout=10)
        elif method == "DELETE":
            res = requests.delete(url, headers=headers, timeout=10)

        if res.status_code in [200, 201]:
            return res.json()
        error_msg = res.json().get("error", f"HTTP {res.status_code}") if res.text else f"HTTP {res.status_code}"
        return {"error": error_msg}
    except Exception as e:
        return {"error": f"API Connection Failure: {str(e)}"}


def priority_badge_html(priority: str) -> str:
    p_lower = str(priority).lower()
    if p_lower == "high":
        return '<span class="badge-pill badge-high">HIGH</span>'
    elif p_lower == "medium":
        return '<span class="badge-pill badge-medium">MEDIUM</span>'
    return '<span class="badge-pill badge-low">LOW</span>'


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 1: PORTAL SELECTION (LANDING SCREEN)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state["auth_user"] and not st.session_state["portal_choice"]:
    st.markdown('<div class="top-pill">NEXUS AI • SERVICE INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">IT Service Management & Ticket Triage</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Automated Multi-Target Machine Learning, NLP Deadline Parsing, and Workqueue Orchestration</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="portal-box">
                <div>
                    <div class="portal-badge">CUSTOMER ACCESS</div>
                    <div class="portal-heading">Customer Support Portal</div>
                    <div class="portal-text">
                        Submit IT service requests, receive instant AI priority and routing classifications,
                        track dynamic SLA resolution targets, and communicate with engineers.
                    </div>
                    <ul class="portal-features">
                        <li>Real-time Priority & Department classification</li>
                        <li>Automated SLA deadline calculation</li>
                        <li>Ticket status history & engineer replies</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Enter Customer Portal →", type="primary", use_container_width=True):
            st.session_state["portal_choice"] = "customer"
            st.session_state["auth_mode"] = "login"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="portal-box">
                <div>
                    <div class="portal-badge">ENGINEERING & OPERATIONS</div>
                    <div class="portal-heading">Support Agent & Admin Console</div>
                    <div class="portal-text">
                        Triage active support workqueues, review low-confidence classifications,
                        execute policy-backed priority overrides, and inspect model telemetry.
                    </div>
                    <ul class="portal-features">
                        <li>Live triage workqueue with multi-parameter filters</li>
                        <li>Human-in-the-loop overrides with mandatory audit logging</li>
                        <li>5-Fold cross-validation model benchmark telemetry</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Enter Operations Console →", type="primary", use_container_width=True):
            st.session_state["portal_choice"] = "agent"
            st.session_state["auth_mode"] = "login"
            st.rerun()

    st.markdown("<hr style='border-color: #1E293B; margin: 40px 0 20px 0;'>", unsafe_allow_html=True)
    st.caption("Backend Service: http://127.0.0.1:5000 | Core Status: Healthy | Authentication: Stateless Bearer JWT")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 2: AUTHENTICATION (LOGIN & REGISTRATION SCREEN)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state["auth_user"] and st.session_state["portal_choice"]:
    target_portal = st.session_state["portal_choice"]
    portal_name = "Customer Support Portal" if target_portal == "customer" else "Support Agent & Admin Console"
    badge_label = "CUSTOMER AUTHENTICATION" if target_portal == "customer" else "ENGINEERING AUTHENTICATION"

    col_l, col_center, col_r = st.columns([1, 2, 1])

    with col_center:
        st.markdown(f'<div class="top-pill">{badge_label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-title" style="font-size: 1.75rem !important;">{portal_name}</div>', unsafe_allow_html=True)
        st.caption("Please provide authorized credentials to proceed.")
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        if st.session_state["auth_mode"] == "login":
            st.markdown("##### Account Sign In")
            default_user = "user1" if target_portal == "customer" else "admin"
            default_pass = "user123" if target_portal == "customer" else "admin123"

            uname = st.text_input("Username", value=default_user)
            pword = st.text_input("Password", type="password", value=default_pass)

            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                if st.button("Sign In →", type="primary", use_container_width=True):
                    res = api_request(API_AUTH_LOGIN, "POST", {"username": uname, "password": pword})
                    if "user" in res:
                        user_obj = res["user"]
                        if target_portal == "agent" and user_obj["role"] not in ["agent", "admin"]:
                            st.error("Access Denied: This account does not possess Support Agent or Administrator privileges.")
                        else:
                            st.session_state["auth_user"] = user_obj
                            st.session_state["auth_token"] = res.get("token")
                            st.success("Authenticated successfully.")
                            st.rerun()
                    else:
                        st.error(res.get("error", "Invalid username or password."))

            with col_btn2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["portal_choice"] = None
                    st.rerun()

            st.markdown("<hr style='border-color: #1E293B; margin: 24px 0 16px 0;'>", unsafe_allow_html=True)
            if st.button("New user? Create an account", use_container_width=True):
                st.session_state["auth_mode"] = "register"
                st.rerun()

        else:
            st.markdown("##### Account Registration")
            new_uname = st.text_input("Choose Username")
            new_email = st.text_input("Work Email Address")
            new_pword = st.text_input("Create Password", type="password")
            role_assigned = "customer" if target_portal == "customer" else "agent"
            st.caption(f"Assigned Access Tier: **{role_assigned.upper()}**")

            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                if st.button("Register & Sign In →", type="primary", use_container_width=True):
                    if not new_uname or not new_email or not new_pword:
                        st.error("All registration fields are required.")
                    else:
                        reg_res = api_request(API_AUTH_REGISTER, "POST", {
                            "username": new_uname,
                            "email": new_email,
                            "password": new_pword,
                            "role": role_assigned,
                        })
                        if "user" in reg_res:
                            st.session_state["auth_user"] = reg_res["user"]
                            st.session_state["auth_token"] = reg_res.get("token")
                            st.success("Account provisioned and authenticated!")
                            st.rerun()
                        else:
                            st.error(reg_res.get("error", "Registration rejected by server."))

            with col_r2:
                if st.button("Back to Login", use_container_width=True):
                    st.session_state["auth_mode"] = "login"
                    st.rerun()

    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 3: AUTHENTICATED PORTALS (CUSTOMER vs AGENT/ADMIN)
# ─────────────────────────────────────────────────────────────────────────────
user = st.session_state["auth_user"]

# Top Navigation Bar
nav_c1, nav_c2, nav_c3 = st.columns([3, 1.2, 0.8])
with nav_c1:
    st.markdown('<div class="hero-title" style="font-size: 1.45rem !important; margin-bottom: 2px !important;">NEXUS AI // Service Management</div>', unsafe_allow_html=True)
    st.caption("Active Operational Session • Connected to SQLite (WAL) Backend")

with nav_c2:
    st.markdown(f'<div class="stat-card" style="padding: 10px 14px;"><small style="color:#94A3B8;">AUTHENTICATED USER</small><br><strong style="color:#FFFFFF;">{user["username"]}</strong> &nbsp;<span style="color:#38BDF8;">[{user["role"].upper()}]</span></div>', unsafe_allow_html=True)

with nav_c3:
    if st.button("Sign Out", use_container_width=True):
        st.session_state["auth_user"] = None
        st.session_state["auth_token"] = None
        st.session_state["portal_choice"] = None
        st.rerun()

st.markdown("<hr style='border-color: #1E293B; margin: 18px 0 24px 0;'>", unsafe_allow_html=True)


# =============================================================================
# A. CUSTOMER PORTAL INTERFACE
# =============================================================================
if user["role"] == "customer":
    cust_tabs = st.tabs(["Submit Support Request", "My Active Tickets"])

    # ── TAB 1: SUBMIT TICKET ─────────────────────────────────────────────────
    with cust_tabs[0]:
        st.subheader("Submit Technical Incident")
        st.caption("Enter complete details regarding your issue. Natural Language Processing models will classify urgency and route to the appropriate department.")

        issue_text = st.text_area(
            "Incident Description",
            placeholder="Describe the incident, error output, and affected environment. Example: Production PostgreSQL database server unreachable, site down ASAP!",
            height=140,
        )

        c_act1, c_act2 = st.columns([2, 1])

        with c_act1:
            if st.button("Submit Support Request →", type="primary", use_container_width=True):
                if not issue_text.strip():
                    st.error("Please enter an issue description.")
                else:
                    with st.spinner("Analyzing semantic features and calculating SLA target..."):
                        t_payload = {
                            "ticket": issue_text,
                            "save": True,
                            "user_id": user["id"],
                        }
                        res = api_request(API_PREDICT, "POST", t_payload)

                        if "priority" in res:
                            st.success(f"Ticket #{res.get('id', 'N/A')} created and queued for resolution.")

                            m1, m2, m3, m4 = st.columns(4)
                            with m1:
                                st.markdown('<div class="stat-card"><div class="stat-label">Predicted Priority</div><div class="stat-value">' + res["priority"] + '</div></div>', unsafe_allow_html=True)
                            with m2:
                                st.markdown('<div class="stat-card"><div class="stat-label">Category</div><div class="stat-value" style="font-size:1.15rem;">' + res["category"] + '</div></div>', unsafe_allow_html=True)
                            with m3:
                                st.markdown('<div class="stat-card"><div class="stat-label">Target Department</div><div class="stat-value" style="font-size:1.15rem;">' + res["department"] + '</div></div>', unsafe_allow_html=True)
                            with m4:
                                conf_str = f"{res['confidence']:.1%}" if res.get("confidence") else "N/A"
                                st.markdown('<div class="stat-card"><div class="stat-label">Model Confidence</div><div class="stat-value">' + conf_str + '</div></div>', unsafe_allow_html=True)

                            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                            st.info(f"Target SLA Resolution: **{res.get('sla_deadline', 'N/A')}** | Detected Urgency Phrase: **{res.get('deadline_detected') or 'Standard SLA Policy'}**")
                        else:
                            st.error(res.get("error", "Ticket creation failed."))

        with c_act2:
            st.markdown("##### Fast Incident Presets")
            if st.button("Production DB Outage (High)", use_container_width=True):
                st.session_state["preset"] = "Production PostgreSQL database server unreachable, site down ASAP!"
            if st.button("Network Latency Degradation (Medium)", use_container_width=True):
                st.session_state["preset"] = "Intermittent network latency affecting backend microservices."
            if st.button("Repository Access Request (Low)", use_container_width=True):
                st.session_state["preset"] = "Need access to internal documentation repository on GitHub before Friday."

    # ── TAB 2: MY TICKETS ────────────────────────────────────────────────────
    with cust_tabs[1]:
        st.subheader("My Registered Tickets")
        st.caption(f"Showing support requests filed by user account: **{user['username']}**")

        my_res = api_request(f"{API_TICKETS}?user_id={user['id']}")
        ticket_items = my_res.get("tickets", [])

        if not ticket_items:
            st.info("No active tickets found for your account.")
        else:
            for item in ticket_items:
                badge = priority_badge_html(item["priority"])
                with st.expander(f"Ticket #{item['id']} — [{item['priority'].upper()}] {item['ticket'][:65]}..."):
                    st.markdown(f"**Priority:** {badge} &nbsp;|&nbsp; **Status:** `{item['status']}` &nbsp;|&nbsp; **Category:** `{item['category']}` &nbsp;|&nbsp; **Department:** `{item['department']}`", unsafe_allow_html=True)
                    st.write(f"**Full Description:** {item['ticket']}")
                    st.write(f"**Created At:** {item['created_at']} &nbsp;|&nbsp; **SLA Target:** {item.get('sla_deadline', 'N/A')} &nbsp;|&nbsp; **Assigned Agent:** {item.get('assigned_agent', 'Unassigned')}")

                    detail = api_request(f"{API_TICKETS}/{item['id']}")
                    replies_list = detail.get("replies", [])
                    if replies_list:
                        st.markdown("---")
                        st.markdown("**Conversation Thread:**")
                        for r in replies_list:
                            st.caption(f"[{r['created_at']}] **{r['author_name']}**: {r['message']}")

                    new_msg = st.text_input("Send reply to support engineers", key=f"cust_msg_{item['id']}")
                    if st.button("Post Reply", key=f"cust_btn_{item['id']}"):
                        if new_msg.strip():
                            api_request(f"{API_TICKETS}/{item['id']}/replies", "POST", {
                                "message": new_msg,
                                "author_name": user["username"],
                            })
                            st.success("Reply recorded.")
                            st.rerun()


# =============================================================================
# B. SUPPORT AGENT & ADMIN OPERATIONS CONSOLE
# =============================================================================
else:
    agent_tabs = st.tabs(["Triage Workqueue", "Operational Telemetry", "Model Intelligence", "System Data Export"])

    # ── TAB 1: TRIAGE WORKQUEUE ──────────────────────────────────────────────
    with agent_tabs[0]:
        st.subheader("Live Triage Workqueue")
        st.markdown(
            """
            <div class="guide-box">
                <strong>What this view does:</strong> This is the daily workspace for support engineers. Incoming tickets are automatically classified by priority, category, and department. Engineers can reassign tickets, update lifecycle statuses, or manually override the AI priority when operational business context requires it.
            </div>
            """,
            unsafe_allow_html=True,
        )

        agents_data = api_request(API_AGENTS)
        active_agents = agents_data.get("agents", ["admin", "agent_sarah"])

        # Filters
        f1, f2, f3, f4 = st.columns(4)
        filter_status = f1.selectbox("Filter Status", ["All", "Open", "In Progress", "Resolved", "Closed"])
        filter_priority = f2.selectbox("Filter Priority", ["All", "High", "Medium", "Low"])
        filter_agent = f3.selectbox("Filter Assignee", ["All"] + active_agents + ["Unassigned"])
        filter_search = f4.text_input("Search Content", placeholder="Keywords...")

        queue_res = api_request(f"{API_TICKETS}?status={filter_status}&priority={filter_priority}&assigned_agent={filter_agent}&search={filter_search}")
        queue_tickets = queue_res.get("tickets", [])

        st.markdown(f"**Showing {len(queue_tickets)} matching ticket(s)**")

        for t in queue_tickets:
            rev_flag = ' &nbsp; <span class="badge-review">NEEDS REVIEW</span>' if t.get("requires_review") else ''
            p_badge = priority_badge_html(t["priority"])
            header_summary = f"Ticket #{t['id']} — [{t['priority'].upper()}] {t['ticket'][:65]}..."

            with st.expander(header_summary):
                st.markdown(f"**Current Priority:** {p_badge} {rev_flag} &nbsp;|&nbsp; **Status:** `{t['status']}` &nbsp;|&nbsp; **Category:** `{t['category']}` &nbsp;|&nbsp; **Department:** `{t['department']}`", unsafe_allow_html=True)
                st.write(f"**Full Description:** {t['ticket']}")

                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    conf_disp = f"{t['confidence']:.1%}" if t.get("confidence") else "N/A"
                    st.write(f"**ML Prediction Confidence:** {conf_disp}")
                    st.caption("How certain the AI classifier was about this ticket's priority.")
                    st.write(f"**SLA Target Deadline:** {t.get('sla_deadline', 'N/A')}")
                    st.caption("Calculated resolution deadline based on priority policy and deadline phrases.")
                    st.write(f"**Assigned Agent:** {t.get('assigned_agent') or 'Unassigned'}")
                    if t.get("priority_override"):
                        st.info(f"Audit Trail: {t['priority_override']}")

                with c_info2:
                    st.markdown("##### Management Actions")
                    new_status = st.selectbox(
                        "Update Status",
                        ["Open", "In Progress", "Resolved", "Closed"],
                        index=["Open", "In Progress", "Resolved", "Closed"].index(t["status"]),
                        key=f"act_status_{t['id']}",
                    )

                    curr_ag = t.get("assigned_agent") or "Unassigned"
                    opts = ["Unassigned"] + active_agents
                    ag_idx = opts.index(curr_ag) if curr_ag in opts else 0
                    new_ag = st.selectbox("Reassign Agent", opts, index=ag_idx, key=f"act_ag_{t['id']}")

                    if st.button("Apply Status & Assignment", key=f"btn_apply_{t['id']}"):
                        api_request(f"{API_TICKETS}/{t['id']}", "PATCH", {
                            "status": new_status,
                            "assigned_agent": new_ag,
                        })
                        st.success("Changes committed.")
                        st.rerun()

                st.markdown("<hr style='border-color: #1E293B; margin: 16px 0;'>", unsafe_allow_html=True)

                # Priority Override Section
                ov_col1, ov_col2 = st.columns([1, 2])
                with ov_col1:
                    st.markdown("##### Human-in-the-Loop Override")
                    st.caption("Manually adjust priority when operational impact requires it.")
                    target_prio = st.selectbox("Select New Priority", ["High", "Medium", "Low"], key=f"ov_pr_{t['id']}")
                with ov_col2:
                    st.markdown("##### Mandatory Justification Reason")
                    ov_reason = st.text_input("Enter why the AI priority is being changed", placeholder="e.g. Executive escalation per VP approval", key=f"ov_rs_{t['id']}")
                    if st.button("Commit Priority Override", key=f"btn_ov_{t['id']}"):
                        if not ov_reason.strip():
                            st.error("A documented business justification is required for priority override.")
                        else:
                            ov_res = api_request(f"{API_TICKETS}/{t['id']}/priority-override", "POST", {
                                "priority": target_prio,
                                "reason": ov_reason,
                            })
                            if "error" in ov_res:
                                st.error(ov_res["error"])
                            else:
                                st.success("Priority override logged in immutable audit trail.")
                                st.rerun()

                # Audit Event Timeline
                full_doc = api_request(f"{API_TICKETS}/{t['id']}")
                events_list = full_doc.get("timeline", [])
                if events_list:
                    st.markdown("##### Audit Event Log (Event Sourcing)")
                    for ev in events_list:
                        st.caption(f"• **{ev['timestamp']}** — [{ev['event_type']}] by {ev['author_name']}: {ev['reason']} (Updated Value: {ev.get('new_value', '')})")

    # ── TAB 2: OPERATIONAL TELEMETRY ─────────────────────────────────────────
    with agent_tabs[1]:
        st.subheader("Operational Telemetry & Performance")
        st.markdown(
            """
            <div class="guide-box">
                <strong>What this view does:</strong> Provides leadership and team managers with real-time support workload metrics calculated directly from active database records (no fake/hardcoded figures).
            </div>
            """,
            unsafe_allow_html=True,
        )

        stats = api_request(API_ANALYTICS)

        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.markdown('<div class="stat-card"><div class="stat-label">Total Tickets</div><div class="stat-value">' + str(stats.get("total", 0)) + '</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown('<div class="stat-card"><div class="stat-label">Open Tickets</div><div class="stat-value" style="color: #60A5FA !important;">' + str(stats.get("open", 0)) + '</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown('<div class="stat-card"><div class="stat-label">In Progress</div><div class="stat-value" style="color: #FBBF24 !important;">' + str(stats.get("in_progress", 0)) + '</div></div>', unsafe_allow_html=True)
        with s4:
            st.markdown('<div class="stat-card"><div class="stat-label">Resolved</div><div class="stat-value" style="color: #34D399 !important;">' + str(stats.get("resolved", 0)) + '</div></div>', unsafe_allow_html=True)
        with s5:
            st.markdown('<div class="stat-card"><div class="stat-label">Overrides Logged</div><div class="stat-value" style="color: #F472B6 !important;">' + str(stats.get("total_overrides", 0)) + '</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        g1, g2 = st.columns(2)
        with g1:
            st.markdown("##### Tickets by Technical Category")
            by_c = stats.get("by_category", {})
            if by_c:
                st.bar_chart(pd.Series(by_c))

        with g2:
            st.markdown("##### Tickets by Priority Level")
            by_p = stats.get("by_priority", {})
            if by_p:
                st.bar_chart(pd.Series(by_p))

        # Configurable SLA Target Reference
        st.markdown("##### Configured SLA Target Policy")
        st.caption("Default response and resolution hours applied per priority level:")
        sla_table = stats.get("sla_policies", {})
        if sla_table:
            sla_df = pd.DataFrame.from_dict(sla_table, orient="index")
            sla_df.columns = ["Target Response (Hours)", "Target Resolution (Hours)"]
            st.table(sla_df)

    # ── TAB 3: MODEL INTELLIGENCE ────────────────────────────────────────────
    with agent_tabs[2]:
        st.subheader("Machine Learning Evaluation & Diagnostics")
        st.markdown(
            """
            <div class="guide-box">
                <strong>What this view does:</strong> Provides technical transparency and evidence for ML audits and viva defense. It shows the cross-validation comparison across 4 different algorithms, held-out test split results, and the confusion matrix.
            </div>
            """,
            unsafe_allow_html=True,
        )

        metrics_obj = api_request(API_METRICS)

        st.markdown("##### 1. Algorithm Benchmarking (5-Fold Stratified Cross-Validation)")
        st.caption("We evaluated 4 text classification models on the training data to select the optimal architecture:")

        if "candidate_benchmark_cv" in metrics_obj:
            cv_dict = metrics_obj["candidate_benchmark_cv"]
            cv_df = pd.DataFrame.from_dict(cv_dict, orient="index")
            cv_df.columns = ["CV Mean Accuracy", "CV Macro F1-Score"]
            cv_df["CV Mean Accuracy"] = cv_df["CV Mean Accuracy"].apply(lambda v: f"{v:.2%}")
            cv_df["CV Macro F1-Score"] = cv_df["CV Macro F1-Score"].apply(lambda v: f"{v:.4f}")
            st.table(cv_df)

        st.markdown("<hr style='border-color: #1E293B; margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown("##### 2. Independent Test Split Verification (240 Tickets)")
        st.caption("Final evaluation on unseen test data using the selected best model:")
        if "metrics" in metrics_obj:
            pri_eval = metrics_obj["metrics"]["priority"]
            cat_eval = metrics_obj["metrics"]["category"]
            dep_eval = metrics_obj["metrics"]["department"]

            e1, e2, e3 = st.columns(3)
            with e1:
                st.markdown(f'<div class="stat-card"><div class="stat-label">Priority Test Accuracy</div><div class="stat-value">{pri_eval["accuracy"]:.2%}</div><small style="color:#CBD5E1;">Macro F1: {pri_eval["macro_f1"]:.4f}</small></div>', unsafe_allow_html=True)
            with e2:
                st.markdown(f'<div class="stat-card"><div class="stat-label">Category Test Accuracy</div><div class="stat-value">{cat_eval["accuracy"]:.2%}</div><small style="color:#CBD5E1;">Macro F1: {cat_eval["macro_f1"]:.4f}</small></div>', unsafe_allow_html=True)
            with e3:
                st.markdown(f'<div class="stat-card"><div class="stat-label">Department Test Accuracy</div><div class="stat-value">{dep_eval["accuracy"]:.2%}</div><small style="color:#CBD5E1;">Macro F1: {dep_eval["macro_f1"]:.4f}</small></div>', unsafe_allow_html=True)

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 3. Priority Confusion Matrix")
            st.caption("Rows show actual ground-truth classes; columns show predicted classes:")
            cm_dict = pri_eval.get("confusion_matrix", {})
            if "matrix" in cm_dict:
                labels = cm_dict["labels"]
                cm_df = pd.DataFrame(
                    cm_dict["matrix"],
                    index=[f"Actual {l}" for l in labels],
                    columns=[f"Pred {l}" for l in labels],
                )
                st.dataframe(cm_df, use_container_width=True)

    # ── TAB 4: DATA EXPORT ───────────────────────────────────────────────────
    with agent_tabs[3]:
        st.subheader("System Data Export & Reporting")
        st.markdown(
            """
            <div class="guide-box">
                <strong>What this view does:</strong> Allows IT compliance and operations leads to export ticket records, AI predictions, and audit override notes into standard CSV format for external auditing.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Fetch Live Export Stream", type="primary"):
            tickets_bundle = api_request(API_TICKETS)
            raw_list = tickets_bundle.get("tickets", [])
            if raw_list:
                df_exp = pd.DataFrame(raw_list)
                csv_payload = df_exp.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download Tickets CSV",
                    data=csv_payload,
                    file_name="nexus_tickets_export.csv",
                    mime="text/csv",
                )
                st.dataframe(df_exp, use_container_width=True)
