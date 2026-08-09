"""
ProvenTech AI Ticket Management Portal
Run: python -m streamlit run frontend.py
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ── Brand ─────────────────────────────────────────────────────────────────────
NAVY = "#032F57"
YELLOW = "#FFC400"
BG = "#F7F9FC"
CARD = "#FFFFFF"
TEXT = "#0F172A"

API_URL = "http://127.0.0.1:5000/predict"
REQUEST_TIMEOUT = 30

USER = {
    "name": "Alex Morgan",
    "first": "Alex",
    "role": "Support Engineer",
    "department": "IT Operations",
    "email": "alex.morgan@proventech.internal",
}

NAV_ITEMS = [
    ("Dashboard", "📊"),
    ("Raise Ticket", "🎫"),
    ("Ticket History", "📋"),
    ("AI Insights", "🤖"),
    ("Profile", "👤"),
    ("Logout", "🚪"),
]

PRIORITY_STYLES = {
    "High": {"bg": "#FEE2E2", "text": "#EF4444", "border": "#FECACA"},
    "Medium": {"bg": "#FEF3C7", "text": "#F59E0B", "border": "#FDE68A"},
    "Low": {"bg": "#DCFCE7", "text": "#22C55E", "border": "#BBF7D0"},
}

KPI_ACCENTS = {
    "total": YELLOW,
    "open": "#38BDF8",
    "high": "#EF4444",
    "resolved": "#22C55E",
}


def theme_palette(dark_mode: bool) -> dict[str, str]:
    if dark_mode:
        return {
            "bg": "#0B1220",
            "card": "#111827",
            "text": "#F1F5F9",
            "muted": "#94A3B8",
            "border": "#1E293B",
            "border_soft": "#334155",
            "input_bg": "#0F172A",
            "chip_bg": "#1E293B",
            "title": "#F8FAFC",
            "heading": "#E2E8F0",
            "footer_border": "#1E293B",
            "empty_border": "#475569",
            "row_border": "#1E293B",
            "focus_ring": "rgba(255,196,0,0.2)",
        }
    return {
        "bg": BG,
        "card": CARD,
        "text": TEXT,
        "muted": "#64748B",
        "border": "#E8EDF3",
        "border_soft": "#E2E8F0",
        "input_bg": "#FFFFFF",
        "chip_bg": BG,
        "title": NAVY,
        "heading": NAVY,
        "footer_border": "#E8EDF3",
        "empty_border": "#CBD5E1",
        "row_border": "#F1F5F9",
        "focus_ring": "rgba(3,47,87,0.14)",
    }


# ── Styles ────────────────────────────────────────────────────────────────────
def inject_styles(sidebar_open: bool = True, dark_mode: bool = False) -> None:
    t = theme_palette(dark_mode)
    sidebar_css = ""
    if not sidebar_open:
        sidebar_css = """
            section[data-testid="stSidebar"] {
                transform: translateX(-110%) !important;
                opacity: 0 !important;
                pointer-events: none !important;
                min-width: 0 !important;
                max-width: 0 !important;
                width: 0 !important;
            }
            section[data-testid="stSidebar"] > div {
                display: none !important;
            }
            [data-testid="stAppViewContainer"] {
                margin-left: 0 !important;
                padding-left: 1rem !important;
            }
            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
        """

    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
            .stApp {{ background: {t["bg"]}; }}
            [data-testid="stAppViewContainer"] {{ background: {t["bg"]}; }}
            #MainMenu, footer {{ visibility: hidden; height: 0; }}

            {sidebar_css}

            /* Keep Streamlit native sidebar collapse control visible when sidebar open */
            [data-testid="stSidebarCollapsedControl"] {{
                color: {NAVY} !important;
                z-index: 9999 !important;
            }}
            [data-testid="collapsedControl"] {{
                color: {NAVY} !important;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(12px); }}
                to   {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes slideUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to   {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes kpiIn {{
                from {{ opacity: 0; transform: translateY(16px) scale(0.97); }}
                to   {{ opacity: 1; transform: translateY(0) scale(1); }}
            }}
            @keyframes successIn {{
                from {{ opacity: 0; transform: translateY(-6px); }}
                to   {{ opacity: 1; transform: translateY(0); }}
            }}

            .fade-in {{ animation: fadeIn 0.5s ease both; }}
            .slide-up {{ animation: slideUp 0.55s ease both; }}
            .success-in {{ animation: successIn 0.4s ease both; }}
            .kpi-1 {{ animation: kpiIn 0.5s ease 0.04s both; }}
            .kpi-2 {{ animation: kpiIn 0.5s ease 0.10s both; }}
            .kpi-3 {{ animation: kpiIn 0.5s ease 0.16s both; }}
            .kpi-4 {{ animation: kpiIn 0.5s ease 0.22s both; }}
            .result-1 {{ animation: slideUp 0.5s ease 0.06s both; }}
            .result-2 {{ animation: slideUp 0.5s ease 0.14s both; }}
            .result-3 {{ animation: slideUp 0.5s ease 0.22s both; }}

            /* Sidebar */
            section[data-testid="stSidebar"] {{
                background: linear-gradient(185deg, {NAVY} 0%, #021E3A 100%) !important;
            }}
            section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.1); margin: 0.85rem 0; }}
            section[data-testid="stSidebar"] div.stButton > button {{
                background: transparent !important; color: #94A3B8 !important;
                border: none !important; text-align: left !important;
                padding: 0.72rem 1rem !important; border-radius: 10px !important;
                font-weight: 500 !important; font-size: 0.9rem !important;
                width: 100% !important; transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
                box-shadow: none !important;
            }}
            section[data-testid="stSidebar"] div.stButton > button:hover {{
                background: rgba(255,196,0,0.1) !important; color: #FFF !important;
                transform: translateX(4px);
            }}
            section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
                background: rgba(255,196,0,0.14) !important; color: {YELLOW} !important;
                border-left: 3px solid {YELLOW} !important; font-weight: 700 !important;
            }}

            .block-container {{ max-width: 1160px; padding-top: 0.75rem; padding-bottom: 2rem; }}

            /* Logo */
            .pt-logo {{ display: flex; align-items: center; gap: 0.7rem; padding: 1.5rem 1rem 1rem; }}
            .pt-logo-mark {{
                width: 40px; height: 40px; background: {YELLOW}; border-radius: 11px;
                display: flex; align-items: center; justify-content: center;
                font-weight: 900; color: {NAVY}; font-size: 1.15rem;
                box-shadow: 0 4px 12px rgba(255,196,0,0.28);
            }}
            .pt-logo-name {{ color: #FFF; font-weight: 800; font-size: 1.05rem; line-height: 1.2; }}
            .pt-logo-sub {{
                color: #64748B; font-size: 0.68rem; font-weight: 500;
                text-transform: uppercase; letter-spacing: 0.07em;
            }}

            /* Theme toggle in header */
            .theme-panel {{
                background: {t["chip_bg"]};
                border: 1px solid {t["border_soft"]};
                border-radius: 12px;
                padding: 0.55rem 0.65rem 0.5rem;
                text-align: center;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label) {{
                background: {t["chip_bg"]} !important;
                border-color: {t["border_soft"]} !important;
                border-radius: 12px !important;
                padding: 0.6rem 0.75rem 0.55rem !important;
                min-width: 155px;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label):hover {{
                border-color: {YELLOW} !important;
            }}
            .theme-control-label {{
                font-size: 0.68rem; font-weight: 700; color: {t["muted"]};
                text-transform: uppercase; letter-spacing: 0.08em;
                margin: 0 0 0.5rem; text-align: center;
            }}
            .theme-icon-wrap {{
                font-size: 1rem; text-align: center; line-height: 1.75rem;
                padding-top: 0.2rem; user-select: none;
            }}
            .theme-status {{
                font-size: 0.72rem; font-weight: 600; color: {t["muted"]};
                text-align: center; margin: 0.4rem 0 0; white-space: nowrap;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label) div[data-testid="stToggle"] {{
                display: flex !important; align-items: center !important;
                justify-content: center !important; margin: 0 !important; padding: 0 !important;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label) div[data-testid="stToggle"] label {{
                display: none !important; width: 0 !important; min-width: 0 !important;
                overflow: hidden !important; margin: 0 !important; padding: 0 !important;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label) div[data-testid="stToggle"] button[role="switch"] {{
                transition: background 0.25s ease !important;
                min-width: 2.85rem !important; min-height: 1.55rem !important;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.theme-control-label) div[data-testid="stToggle"] button[role="switch"][aria-checked="true"] {{
                background: {YELLOW} !important;
            }}
            .pt-header-block {{
                background: {t["card"]}; border: 1px solid {t["border"]};
                border-radius: 16px; padding: 1.1rem 1.25rem 1rem;
                margin-bottom: 1.75rem; box-shadow: 0 2px 12px rgba(3,47,87,0.05);
                animation: fadeIn 0.45s ease both;
            }}

            /* Header (legacy inner — kept for profile chip) */
            .profile-chip {{
                display: flex; align-items: center; gap: 0.75rem;
                background: {t["chip_bg"]}; border: 1px solid {t["border_soft"]}; border-radius: 12px;
                padding: 0.55rem 1rem 0.55rem 0.55rem;
                box-shadow: 0 2px 8px rgba(3,47,87,0.06);
                transition: box-shadow 0.28s ease, transform 0.28s ease;
            }}
            .profile-chip:hover {{
                box-shadow: 0 4px 16px rgba(3,47,87,0.1);
                transform: translateY(-1px);
            }}
            .profile-chip .avatar {{
                width: 44px; height: 44px; border-radius: 50%; background: {NAVY};
                color: {YELLOW}; display: flex; align-items: center; justify-content: center;
                font-weight: 700; font-size: 0.9rem; border: 2px solid {YELLOW}; flex-shrink: 0;
            }}
            .profile-chip .name {{ font-weight: 700; font-size: 0.88rem; color: {t["text"]}; line-height: 1.2; }}
            .profile-chip .role {{ font-size: 0.75rem; color: {t["muted"]}; margin-top: 0.1rem; }}

            /* Typography */
            .page-title {{
                font-size: 1.55rem; font-weight: 800; color: {t["title"]};
                margin: 0 0 0.35rem; animation: fadeIn 0.45s ease both;
            }}
            .page-sub {{
                font-size: 0.92rem; color: {t["muted"]}; margin: 0 0 1.75rem;
                font-weight: 400; animation: fadeIn 0.45s ease 0.05s both;
            }}
            .section-title {{
                font-size: 1.05rem; font-weight: 700; color: {t["heading"]}; margin: 0 0 0.25rem;
            }}
            .section-sub {{
                font-size: 0.88rem; color: {t["muted"]}; margin: 0 0 1rem;
            }}
            .section-label {{
                font-size: 0.92rem; font-weight: 700; color: {t["heading"]};
                margin: 0.75rem 0 0.5rem;
            }}
            .field-label {{
                font-size: 0.88rem; font-weight: 600; color: {t["text"]};
                margin: 0.25rem 0 0.35rem;
            }}

            /* KPI */
            .kpi {{
                background: {t["card"]}; border: 1px solid {t["border"]}; border-radius: 14px;
                padding: 1.35rem 1.4rem 1.25rem; box-shadow: 0 2px 10px rgba(3,47,87,0.05);
                transition: all 0.3s cubic-bezier(0.4,0,0.2,1); height: 100%;
                border-top: 3px solid var(--accent);
            }}
            .kpi:hover {{
                transform: translateY(-4px);
                box-shadow: 0 10px 28px rgba(3,47,87,0.1);
            }}
            .kpi-icon {{ font-size: 1.35rem; margin-bottom: 0.7rem; }}
            .kpi-val {{ font-size: 2rem; font-weight: 800; color: {t["title"]}; line-height: 1; margin-bottom: 0.3rem; }}
            .kpi-label {{
                font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.06em; color: {t["muted"]};
            }}

            /* Form area — no extra box wrapper */
            .raise-form-wrap {{
                animation: fadeIn 0.45s ease both;
            }}

            /* Result cards */
            .rc {{
                background: {t["card"]}; border: 1px solid {t["border"]}; border-radius: 14px;
                padding: 1.2rem 1.35rem; box-shadow: 0 2px 10px rgba(3,47,87,0.04); height: 100%;
                transition: transform 0.28s cubic-bezier(0.4,0,0.2,1),
                            box-shadow 0.28s cubic-bezier(0.4,0,0.2,1);
            }}
            .rc:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 22px rgba(3,47,87,0.09);
            }}
            .rc-label {{
                font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
                letter-spacing: 0.08em; color: {t["muted"]}; margin-bottom: 0.45rem;
            }}
            .rc-val {{ font-size: 1.05rem; font-weight: 700; color: {t["text"]}; word-break: break-word; }}
            .badge {{
                display: inline-flex; align-items: center; gap: 0.35rem;
                padding: 0.32rem 0.85rem; border-radius: 999px; font-size: 0.88rem; font-weight: 700;
            }}
            .badge-dot {{ width: 7px; height: 7px; border-radius: 50%; }}

            /* Empty state */
            .empty-state {{
                text-align: center; padding: 3.5rem 2rem;
                background: {t["card"]}; border: 1px dashed {t["empty_border"]}; border-radius: 16px;
                animation: fadeIn 0.5s ease both;
            }}
            .empty-state .icon {{ font-size: 2.75rem; margin-bottom: 0.75rem; }}
            .empty-state h3 {{ color: {t["title"]}; font-weight: 700; margin: 0 0 0.4rem; font-size: 1.1rem; }}
            .empty-state p {{ color: {t["muted"]}; font-size: 0.9rem; margin: 0; }}

            /* Profile card */
            .profile-card {{
                background: {t["card"]}; border: 1px solid {t["border"]}; border-radius: 16px;
                padding: 2.5rem 2rem; box-shadow: 0 4px 20px rgba(3,47,87,0.06);
                max-width: 520px; margin: 0 auto; text-align: center;
                animation: fadeIn 0.5s ease both;
            }}
            .profile-card .avatar-lg {{
                width: 80px; height: 80px; border-radius: 50%; background: {NAVY};
                color: {YELLOW}; display: flex; align-items: center; justify-content: center;
                font-weight: 800; font-size: 1.6rem; border: 3px solid {YELLOW};
                margin: 0 auto 1.25rem;
            }}
            .profile-card .pname {{ font-size: 1.35rem; font-weight: 800; color: {t["title"]}; margin: 0 0 0.2rem; }}
            .profile-card .prole {{ color: {t["muted"]}; font-size: 0.9rem; margin: 0 0 1.75rem; }}
            .profile-row {{
                display: flex; justify-content: space-between; align-items: center;
                padding: 0.75rem 0; border-top: 1px solid {t["row_border"]}; text-align: left;
            }}
            .profile-row .plabel {{ font-size: 0.82rem; font-weight: 600; color: {t["muted"]}; }}
            .profile-row .pval {{ font-size: 0.88rem; font-weight: 600; color: {t["text"]}; }}

            /* Footer */
            .pt-footer {{
                text-align: center; color: {t["muted"]}; font-size: 0.78rem;
                margin-top: 3rem; padding-top: 1.25rem; border-top: 1px solid {t["footer_border"]};
            }}

            /* Inputs */
            div[data-testid="stTextInput"] input,
            div[data-testid="stTextArea"] textarea {{
                background: {t["input_bg"]} !important; color: {t["text"]} !important;
                border: 1.5px solid {t["border_soft"]} !important; border-radius: 12px !important;
                padding: 0.8rem 1rem !important; font-size: 0.95rem !important;
                transition: border-color 0.2s, box-shadow 0.25s !important;
            }}
            div[data-testid="stTextInput"] input::placeholder,
            div[data-testid="stTextArea"] textarea::placeholder {{ color: #94A3B8 !important; opacity: 1 !important; }}
            div[data-testid="stTextInput"] input:focus,
            div[data-testid="stTextArea"] textarea:focus,
            div[data-testid="stDateInput"] input:focus {{
                border-color: {YELLOW if dark_mode else NAVY} !important;
                box-shadow: 0 0 0 4px {t["focus_ring"]} !important;
                outline: none !important;
            }}
            div[data-testid="stTextInput"] label,
            div[data-testid="stTextArea"] label,
            div[data-testid="stDateInput"] label {{
                color: {t["text"]} !important; font-weight: 600 !important; font-size: 0.9rem !important;
            }}
            div[data-testid="stDateInput"] input {{
                border-radius: 10px !important; border: 1.5px solid {t["border_soft"]} !important;
                background: {t["input_bg"]} !important; color: {t["text"]} !important;
                transition: border-color 0.2s, box-shadow 0.25s !important;
            }}

            /* General button hover */
            div[data-testid="stButton"] > button {{
                transition: all 0.26s cubic-bezier(0.4,0,0.2,1) !important;
            }}
            div[data-testid="stButton"] > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 14px rgba(3,47,87,0.12) !important;
            }}

            /* Deadline section */
            div[data-testid="stVerticalBlockBorderWrapper"] {{
                background: {t["card"]} !important;
                border: 1px solid {t["border"]} !important;
                border-radius: 12px !important;
                padding: 0.85rem 1rem 1rem !important;
                margin-bottom: 0.75rem !important;
                box-shadow: 0 2px 8px rgba(3,47,87,0.04);
                transition: border-color 0.25s, box-shadow 0.25s;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
                border-color: {YELLOW} !important;
                box-shadow: 0 4px 14px rgba(255,196,0,0.12);
            }}

            /* Sidebar toggle button */
            div[data-testid="stSidebar"] div[data-testid="stButton"] button.sidebar-toggle-btn {{
                background: rgba(255,196,0,0.12) !important;
                color: {YELLOW} !important;
                border: 1px solid rgba(255,196,0,0.25) !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                font-size: 0.82rem !important;
                text-align: center !important;
                padding: 0.55rem 0.75rem !important;
                margin-bottom: 0.5rem !important;
            }}
            div[data-testid="stSidebar"] div[data-testid="stButton"] button.sidebar-toggle-btn:hover {{
                background: rgba(255,196,0,0.22) !important;
                transform: none !important;
            }}
            button[data-testid="baseButton-secondary"][aria-label="Open sidebar"],
            button[kind="header"] {{
                color: {NAVY} !important;
            }}

            /* Main-area menu open button */
            div[data-testid="column"] > div > div[data-testid="stButton"] > button {{
                background: {NAVY} !important;
                color: {YELLOW} !important;
                border: none !important;
                border-radius: 10px !important;
                font-size: 1.2rem !important;
                font-weight: 700 !important;
                min-height: 44px !important;
                box-shadow: 0 2px 10px rgba(3,47,87,0.18) !important;
                transition: all 0.22s ease !important;
            }}
            div[data-testid="column"] > div > div[data-testid="stButton"] > button:hover {{
                background: #021E3A !important;
                transform: scale(1.06);
                box-shadow: 0 4px 16px rgba(3,47,87,0.28) !important;
            }}

            /* Submit button */
            div[data-testid="stFormSubmitButton"] button,
            div[data-testid="stButton"] > button[kind="primary"] {{
                background: {YELLOW} !important; color: {NAVY} !important;
                border: none !important; border-radius: 12px !important;
                padding: 0.9rem !important; font-weight: 800 !important; font-size: 1rem !important;
                box-shadow: 0 4px 16px rgba(255,196,0,0.32) !important;
                transition: all 0.28s cubic-bezier(0.4,0,0.2,1) !important; width: 100%;
            }}
            div[data-testid="stFormSubmitButton"] button:hover,
            div[data-testid="stButton"] > button[kind="primary"]:hover {{
                background: #E6B000 !important;
                box-shadow: 0 8px 24px rgba(255,196,0,0.42) !important;
                transform: scale(1.02);
            }}
            div[data-testid="stFormSubmitButton"] button:active,
            div[data-testid="stButton"] > button[kind="primary"]:active {{ transform: scale(0.98); }}

            div[data-testid="stAlert"] {{ border-radius: 12px; animation: successIn 0.4s ease both; }}
            div[data-testid="stDataFrame"] {{ border: 1px solid {t["border"]}; border-radius: 12px; overflow: hidden; }}
            div[data-testid="stMetric"] label {{ color: {t["muted"]} !important; }}
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ color: {t["text"]} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def init_state() -> None:
    defaults: dict[str, Any] = {
        "page": "Dashboard",
        "logged_in": True,
        "ticket_history": [],
        "latest_prediction": None,
        "prediction_error": None,
        "show_success": False,
        "ticket_id_date": "",
        "ticket_id_seq": 0,
        "last_active": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sidebar_open": True,
        "dark_mode": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def generate_ticket_id() -> str:
    today = datetime.now().strftime("%Y%m%d")
    if st.session_state.ticket_id_date != today:
        st.session_state.ticket_id_date = today
        st.session_state.ticket_id_seq = 0
    st.session_state.ticket_id_seq += 1
    return f"PT-{today}-{st.session_state.ticket_id_seq:03d}"


def parse_time_24h(value: str) -> time | None:
    value = value.strip()
    if re.fullmatch(r"\d{1,2}:\d{2}", value):
        try:
            parsed = datetime.strptime(value, "%H:%M")
            if parsed.hour > 23 or parsed.minute > 59:
                return None
            return parsed.time()
        except ValueError:
            return None
    return None


def normalize_time_24h(value: str) -> str | None:
    parsed = parse_time_24h(value)
    return parsed.strftime("%H:%M") if parsed else None


def format_time_24h(t: time) -> str:
    return t.strftime("%H:%M")


def priority_badge(priority: str) -> str:
    s = PRIORITY_STYLES.get(priority, {"bg": "#F1F5F9", "text": "#64748B", "border": "#E2E8F0"})
    return (
        f'<span class="badge" style="background:{s["bg"]};color:{s["text"]};'
        f'border:1px solid {s["border"]};">'
        f'<span class="badge-dot" style="background:{s["text"]};"></span>{priority}</span>'
    )


def rcard(label: str, value: str, anim: str = "") -> str:
    return f'<div class="rc {anim}"><div class="rc-label">{label}</div><div class="rc-val">{value}</div></div>'


def kpi_html(icon: str, label: str, val: int, accent: str, anim: str) -> str:
    return (
        f'<div class="kpi {anim}" style="--accent:{accent};">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-val">{val}</div>'
        f'<div class="kpi-label">{label}</div></div>'
    )


def build_payload(
    title: str,
    description: str,
    has_deadline: bool,
    dl_date: date | None,
    dl_time_str: str | None,
) -> str:
    text = f"{title.strip()}. {description.strip()}"
    if has_deadline and dl_date:
        ds = dl_date.strftime("%Y-%m-%d")
        if dl_time_str:
            text = f"{text} Need this resolved before {ds} {dl_time_str}."
        else:
            text = f"{text} Need this resolved before {ds}."
    return text


def call_api(ticket: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        resp = requests.post(
            API_URL,
            json={"ticket": ticket},
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.ConnectionError as e:
        return None, f"**Backend not reachable.** Run `python app.py` first.\n\n`{e}`"
    except requests.exceptions.Timeout as e:
        return None, f"**Request timeout** ({REQUEST_TIMEOUT}s).\n\n`{e}`"
    except requests.exceptions.RequestException as e:
        return None, f"**Request failed.**\n\n`{e}`"

    code = resp.status_code
    if not resp.text or not resp.text.strip():
        return None, f"**Empty response.** Status: `{code}`"

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError as e:
        return None, f"**Invalid JSON.** Status: `{code}`\n\n`{e}`"

    if not isinstance(data, dict):
        return None, f"**Unexpected format.** Status: `{code}`"

    if code >= 400:
        return None, f"**API error.** Status: `{code}`\n\n`{data.get('error', resp.text)}`"

    missing = [f for f in ("priority", "category", "department") if f not in data]
    if missing:
        return None, f"**Incomplete response.** Status: `{code}`. Missing: `{missing}`"

    data["_status_code"] = code
    return data, None


def kpi_stats() -> dict[str, int]:
    h = st.session_state.ticket_history
    return {
        "total": len(h),
        "open": sum(1 for t in h if t["Status"] == "Open"),
        "high": sum(1 for t in h if t["Priority"] == "High"),
        "resolved": sum(1 for t in h if t["Status"] == "Resolved"),
    }


def initials(name: str) -> str:
    return "".join(w[0] for w in name.split()[:2]).upper()


# ── Layout ────────────────────────────────────────────────────────────────────
def sidebar() -> None:
    st.markdown(
        f"""
        <div class="pt-logo">
            <div class="pt-logo-mark">P</div>
            <div>
                <div class="pt-logo-name">ProvenTech</div>
                <div class="pt-logo-sub">AI Ticket Portal</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("◀  Close Menu", key="close_sidebar", use_container_width=True):
        st.session_state.sidebar_open = False
        st.rerun()

    st.markdown("---")
    for name, icon in NAV_ITEMS:
        active = st.session_state.page == name
        if st.sidebar.button(
            f"{icon}  {name}",
            key=f"nav_{name}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.page = "Logout" if name == "Logout" else name
            st.session_state.logged_in = name != "Logout"
            st.rerun()


def render_theme_control() -> None:
    """Compact dark/light mode switch — icons + toggle only."""
    is_dark = st.session_state.dark_mode

    st.markdown('<p class="theme-control-label">Theme</p>', unsafe_allow_html=True)

    row = st.columns([0.28, 0.44, 0.28], gap="small")
    with row[0]:
        st.markdown('<div class="theme-icon-wrap">☀️</div>', unsafe_allow_html=True)
    with row[1]:
        toggled = st.toggle(
            "Dark mode",
            value=is_dark,
            key="theme_toggle",
            label_visibility="collapsed",
        )
    with row[2]:
        st.markdown('<div class="theme-icon-wrap">🌙</div>', unsafe_allow_html=True)

    status = "Dark mode" if toggled else "Light mode"
    st.markdown(f'<p class="theme-status">{status}</p>', unsafe_allow_html=True)

    if toggled != st.session_state.dark_mode:
        st.session_state.dark_mode = toggled
        st.rerun()


def render_menu_toggle() -> None:
    """Show open-sidebar button when sidebar is collapsed."""
    if not st.session_state.sidebar_open:
        if st.button("☰", key="open_sidebar", help="Open sidebar menu"):
            st.session_state.sidebar_open = True
            st.rerun()


def _render_header_inner() -> None:
    ini = initials(USER["name"])
    t = theme_palette(st.session_state.dark_mode)

    st.markdown('<div class="pt-header-block">', unsafe_allow_html=True)
    col_welcome, col_theme, col_profile = st.columns([0.46, 0.28, 0.26], gap="medium")

    with col_welcome:
        st.markdown(
            f"<h1 style='margin:0;font-size:1.35rem;font-weight:800;color:{t['text']};'>"
            f"Welcome back, {USER['first']} 👋</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:0.3rem 0 0;font-size:0.88rem;color:{t['muted']};'>"
            f"Manage and track AI-powered support tickets across ProvenTech</p>",
            unsafe_allow_html=True,
        )

    with col_theme:
        with st.container(border=True):
            render_theme_control()

    with col_profile:
        st.markdown(
            f"""
            <div class="profile-chip fade-in">
                <div class="avatar" title="{USER['name']}">{ini}</div>
                <div>
                    <div class="name">{USER['name']}</div>
                    <div class="role">{USER['role']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def header_bar() -> None:
    if not st.session_state.sidebar_open:
        menu_col, main_col = st.columns([0.045, 0.955], gap="small")
        with menu_col:
            render_menu_toggle()
        with main_col:
            _render_header_inner()
    else:
        _render_header_inner()


def footer() -> None:
    st.markdown(
        '<p class="pt-footer">Built for ProvenTech • AI-Powered Ticket Workflow Management</p>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<p class="page-title">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-sub">{subtitle}</p>', unsafe_allow_html=True)


# ── Pages ─────────────────────────────────────────────────────────────────────
def page_dashboard() -> None:
    page_header("Dashboard", "Overview of your support ticket activity.")
    s = kpi_stats()
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    cards = [
        ("🟨", "Total Tickets", s["total"], KPI_ACCENTS["total"], "kpi-1"),
        ("🟦", "Open Tickets", s["open"], KPI_ACCENTS["open"], "kpi-2"),
        ("🔴", "High Priority", s["high"], KPI_ACCENTS["high"], "kpi-3"),
        ("🟢", "Resolved Tickets", s["resolved"], KPI_ACCENTS["resolved"], "kpi-4"),
    ]
    for col, (icon, label, val, accent, anim) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(kpi_html(icon, label, val, accent, anim), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2 = st.columns(2, gap="medium")
    with a1:
        if st.button("➕  Raise New Ticket", use_container_width=True):
            st.session_state.page = "Raise Ticket"
            st.rerun()
    with a2:
        if st.button("📋  View Ticket History", use_container_width=True):
            st.session_state.page = "Ticket History"
            st.rerun()

    if st.session_state.ticket_history:
        st.markdown('<p class="section-title" style="margin-top:1.5rem;">Recent Tickets</p>', unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.ticket_history).iloc[::-1].head(5)
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_raise_ticket() -> None:
    st.markdown(
        """
        <div class="fade-in raise-form-wrap">
            <p class="section-title">Raise New Ticket</p>
            <p class="section-sub">Submit your issue and let ProvenTech AI classify it instantly.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    title = st.text_input("Ticket Title", placeholder="Login Access Issue", key="ticket_title")
    description = st.text_area(
        "Ticket Description",
        placeholder="Describe your issue in detail…",
        height=220,
        key="ticket_description",
    )

    st.markdown('<p class="section-label fade-in">Deadline (Optional)</p>', unsafe_allow_html=True)

    with st.container(border=True):
        dc1, dc2 = st.columns(2, gap="medium")
        with dc1:
            st.markdown('<p class="field-label">📅 Deadline Date</p>', unsafe_allow_html=True)
            dl_date = st.date_input(
                "Select Date",
                value=None,
                min_value=date.today(),
                label_visibility="collapsed",
                key="deadline_date",
            )
        with dc2:
            st.markdown('<p class="field-label">🕒 Deadline Time (24h)</p>', unsafe_allow_html=True)
            dl_time_str = st.text_input(
                "Select Time",
                placeholder="14:30",
                help="24-hour format only — e.g. 09:00, 14:30, 18:00. Leave blank if not needed.",
                label_visibility="collapsed",
                key="deadline_time",
            )

    submitted = st.button("Submit Ticket", use_container_width=True, type="primary", key="submit_ticket")

    if submitted:
        st.session_state.latest_prediction = None
        st.session_state.prediction_error = None
        st.session_state.show_success = False

        has_deadline = dl_date is not None or bool(dl_time_str and dl_time_str.strip())

        if not title or not title.strip():
            st.warning("Please enter ticket title")
        elif not description or not description.strip():
            st.warning("Please enter ticket description")
        elif has_deadline and dl_time_str and dl_time_str.strip() and not normalize_time_24h(dl_time_str):
            st.warning("Please enter time in 24-hour format (e.g. 14:30)")
        else:
            deadline_date = dl_date if dl_date is not None else (date.today() if has_deadline and dl_time_str else None)
            time_for_payload = normalize_time_24h(dl_time_str) if dl_time_str and dl_time_str.strip() else None
            payload = build_payload(title, description, has_deadline, deadline_date, time_for_payload)

            with st.spinner("Analyzing ticket..."):
                result, err = call_api(payload)

            if err:
                st.session_state.prediction_error = err
            elif result:
                tid = generate_ticket_id()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.last_active = datetime.now().strftime("%Y-%m-%d %H:%M")

                deadline_val = result.get("deadline_detected")
                if not deadline_val and has_deadline and deadline_date:
                    deadline_val = f"{deadline_date.strftime('%Y-%m-%d')} {time_for_payload or ''}".strip()

                record = {
                    "Ticket ID": tid,
                    "Title": title.strip(),
                    "Description": description.strip()[:80] + ("…" if len(description.strip()) > 80 else ""),
                    "Priority": result["priority"],
                    "Category": result["category"],
                    "Department": result["department"],
                    "Deadline": deadline_val or "—",
                    "Status": "Open",
                    "Created Date": ts,
                }
                st.session_state.ticket_history.append(record)
                st.session_state.latest_prediction = {
                    **result,
                    "ticket_id": tid,
                    "created_at": ts,
                    "deadline_display": deadline_val or "Not detected",
                }
                st.session_state.show_success = True

    if st.session_state.prediction_error:
        st.error(st.session_state.prediction_error)

    if st.session_state.show_success and st.session_state.latest_prediction:
        st.success("Prediction generated successfully")
        _render_results(st.session_state.latest_prediction)


def _render_results(p: dict[str, Any]) -> None:
    st.markdown('<p class="section-title" style="margin-top:1.75rem;">Prediction Results</p>', unsafe_allow_html=True)

    priority = str(p.get("priority", "—"))
    deadline = p.get("deadline_display", "Not detected")
    dl_html = (
        f'<span style="color:{NAVY};">{deadline}</span>'
        if deadline != "Not detected"
        else '<span style="color:#94A3B8;">Not detected</span>'
    )

    r1 = st.columns(3)
    fields_r1 = [
        ("Ticket ID", p.get("ticket_id", "—"), "result-1"),
        ("Priority", priority_badge(priority), "result-2"),
        ("Category", str(p.get("category", "—")), "result-3"),
    ]
    for col, (label, val, anim) in zip(r1, fields_r1):
        with col:
            st.markdown(rcard(label, val, anim), unsafe_allow_html=True)

    r2 = st.columns(3)
    fields_r2 = [
        ("Department", str(p.get("department", "—")), "result-1"),
        ("Deadline", dl_html, "result-2"),
        ("Created Timestamp", p.get("created_at", "—"), "result-3"),
    ]
    for col, (label, val, anim) in zip(r2, fields_r2):
        with col:
            st.markdown(rcard(label, val, anim), unsafe_allow_html=True)


def page_history() -> None:
    page_header("Ticket History", "All tickets submitted through the portal.")

    if not st.session_state.ticket_history:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📭</div>
                <h3>No tickets submitted yet</h3>
                <p>Once tickets are raised, they'll appear here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(st.session_state.ticket_history).iloc[::-1]
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_insights() -> None:
    page_header("AI Insights", "Analytics powered by your ticket data.")

    if not st.session_state.ticket_history:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📊</div>
                <h3>No data available yet</h3>
                <p>Submit tickets to unlock AI insights and trends.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(st.session_state.ticket_history)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Top Priority", df["Priority"].value_counts().idxmax())
    with m2:
        st.metric("Top Category", df["Category"].value_counts().idxmax())
    with m3:
        st.metric("Top Department", df["Department"].value_counts().idxmax())

    st.markdown('<p class="section-title" style="margin-top:1rem;">Priority Distribution</p>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.bar_chart(df["Priority"].value_counts(), color=YELLOW)
    with p2:
        st.altair_chart(_pie_chart(df["Priority"].value_counts(), "Priority"), use_container_width=True)

    st.markdown('<p class="section-title">Category Distribution</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(df["Category"].value_counts(), color=NAVY)
    with c2:
        st.altair_chart(_pie_chart(df["Category"].value_counts(), "Category"), use_container_width=True)

    st.markdown('<p class="section-title">Department Distribution</p>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.bar_chart(df["Department"].value_counts(), color="#38BDF8")
    with d2:
        st.altair_chart(_pie_chart(df["Department"].value_counts(), "Department"), use_container_width=True)

    st.markdown('<p class="section-title">Ticket Volume Trend</p>', unsafe_allow_html=True)
    st.altair_chart(_trend_chart(df), use_container_width=True)


def _pie_chart(series: pd.Series, title: str):
    import altair as alt

    chart_df = series.reset_index()
    chart_df.columns = ["label", "count"]
    palette = [NAVY, YELLOW, "#38BDF8", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
    return (
        alt.Chart(chart_df)
        .mark_arc(innerRadius=50, outerRadius=95)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("label:N", scale=alt.Scale(range=palette[: len(chart_df)]), legend=alt.Legend(title="")),
            tooltip=["label", "count"],
        )
        .properties(title=title, height=280)
        .configure_title(color=NAVY, fontSize=13, fontWeight="bold")
    )


def _trend_chart(df: pd.DataFrame):
    import altair as alt

    trend = df.copy()
    trend["date"] = pd.to_datetime(trend["Created Date"]).dt.date
    daily = trend.groupby("date").size().reset_index(name="tickets")
    daily["date"] = pd.to_datetime(daily["date"])

    return (
        alt.Chart(daily)
        .mark_line(point=True, color=NAVY, strokeWidth=2.5)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("tickets:Q", title="Tickets Submitted"),
            tooltip=["date:T", "tickets:Q"],
        )
        .properties(height=300)
        .configure_axis(labelColor=TEXT, titleColor=NAVY)
    )


def page_profile() -> None:
    page_header("Profile")
    ini = initials(USER["name"])
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="avatar-lg">{ini}</div>
            <p class="pname">{USER['name']}</p>
            <p class="prole">{USER['role']}</p>
            <div class="profile-row"><span class="plabel">Email</span><span class="pval">{USER['email']}</span></div>
            <div class="profile-row"><span class="plabel">Department</span><span class="pval">{USER['department']}</span></div>
            <div class="profile-row"><span class="plabel">Tickets Raised</span><span class="pval">{len(st.session_state.ticket_history)}</span></div>
            <div class="profile-row"><span class="plabel">Last Active</span><span class="pval">{st.session_state.last_active}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_logout() -> None:
    if not st.session_state.sidebar_open:
        render_menu_toggle()
        st.markdown("<br>", unsafe_allow_html=True)

    _, theme_col = st.columns([0.70, 0.30])
    with theme_col:
        with st.container(border=True):
            render_theme_control()

    st.markdown(
        f"""
        <div class="empty-state fade-in">
            <div class="icon">👋</div>
            <h3>Logged out</h3>
            <p>You have been signed out of the ProvenTech AI Ticket Portal.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Log back in", type="primary"):
        st.session_state.logged_in = True
        st.session_state.page = "Dashboard"
        st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="ProvenTech AI Ticket Portal",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    inject_styles(
        sidebar_open=st.session_state.sidebar_open,
        dark_mode=st.session_state.dark_mode,
    )

    with st.sidebar:
        if st.session_state.sidebar_open:
            sidebar()

    if st.session_state.page == "Logout" or not st.session_state.logged_in:
        page_logout()
        footer()
        return

    header_bar()

    routes = {
        "Dashboard": page_dashboard,
        "Raise Ticket": page_raise_ticket,
        "Ticket History": page_history,
        "AI Insights": page_insights,
        "Profile": page_profile,
    }
    routes.get(st.session_state.page, page_dashboard)()
    footer()


if __name__ == "__main__":
    main()
