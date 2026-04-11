"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   WINDCAST  v5.0  —  Lifting Operations Weather Forecast                    ║
║   BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006 | NORSOK R-003       ║
║   Source: ECMWF IFS 0.25° via Open-Meteo (free tier)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests, json, os, re
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import pytz

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Windcast | Lifting Ops Forecast",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECRETS
# ══════════════════════════════════════════════════════════════════════════════
def _secret(key, fallback=None):
    try:
        return st.secrets[key]
    except Exception:
        return fallback

OPEN_METEO_API_KEY = _secret("OPEN_METEO_API_KEY", None)
FEEDBACK_URL = _secret("FEEDBACK_URL", "https://forms.gle/REPLACE_WITH_YOUR_FORM_URL")
KOFI_URL     = "https://ko-fi.com/windcast"

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Responsive Design System
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700;800;900&family=Barlow:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
#MainMenu, header, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }

/* ── Design tokens ── */
:root {
  --bg:       #080f1f;
  --surface:  #0e1729;
  --card:     #141f35;
  --card-hi:  #1b2844;
  --rim:      #1e2f4a;
  --muted:    #2a3d5c;
  --accent:   #3b82f6;
  --safe:     #22c55e;
  --warn:     #f59e0b;
  --stop:     #ef4444;
  --txt:      #e2eaff;
  --txt-dim:  #7a90b8;
  --font-h:   'Barlow Condensed', sans-serif;
  --font-b:   'Barlow', sans-serif;
  --font-m:   'JetBrains Mono', monospace;
}

/* ── Page & Streamlit container ── */
body, .stApp { background: var(--bg) !important; color: var(--txt) !important; font-family: var(--font-b); }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
.stApp > div { background: var(--bg) !important; }

/* ── Top nav bar ── */
.wc-nav {
  background: var(--surface);
  border-bottom: 1px solid var(--rim);
  padding: 0 1.5rem;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.wc-logo {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: 1.25rem;
  letter-spacing: .12em;
  color: #fff;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.wc-logo span { color: var(--accent); }
.wc-nav-links {
  display: flex;
  gap: .25rem;
  align-items: center;
}
.wc-nav-link {
  font-family: var(--font-h);
  font-weight: 600;
  font-size: .75rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--txt-dim);
  padding: .35rem .75rem;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  background: transparent;
  transition: background .15s, color .15s;
}
.wc-nav-link:hover  { background: var(--card); color: var(--txt); }
.wc-nav-link.active { background: rgba(59,130,246,.12); color: var(--accent);
  border: 1px solid rgba(59,130,246,.25); }
.wc-nav-sep { width: 1px; height: 18px; background: var(--rim); margin: 0 .25rem; }

/* ── Controls bar ── */
.wc-controls {
  background: var(--surface);
  border-bottom: 1px solid var(--rim);
  padding: .6rem 1.5rem;
}

/* ── Card ── */
.wc-card {
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 12px;
  padding: 1rem;
}
.wc-card-hi { background: var(--card-hi); }

/* ── Section label ── */
.sec-label {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: .6rem;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--txt-dim);
  margin-bottom: .35rem;
  display: block;
}

/* ── Pill badge ── */
.pill {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  padding: .2rem .7rem;
  border-radius: 999px;
  font-family: var(--font-h);
  font-weight: 700;
  font-size: .62rem;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.pill-safe   { background: rgba(34,197,94,.12);  border: 1px solid rgba(34,197,94,.3);  color: var(--safe); }
.pill-warn   { background: rgba(245,158,11,.12); border: 1px solid rgba(245,158,11,.3); color: var(--warn); }
.pill-stop   { background: rgba(239,68,68,.12);  border: 1px solid rgba(239,68,68,.3);  color: var(--stop); }
.pill-info   { background: rgba(59,130,246,.12); border: 1px solid rgba(59,130,246,.3); color: var(--accent); }
.dot { width: .45rem; height: .45rem; border-radius: 50%; display: inline-block; }
.dot-safe { background: var(--safe); animation: pulse-safe 2s infinite; }
.dot-warn { background: var(--warn); }
.dot-stop { background: var(--stop); }

@keyframes pulse-safe {
  0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,.5); }
  50%      { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
}

/* ── Metric block ── */
.metric-block {
  background: var(--bg);
  border: 1px solid var(--rim);
  border-radius: 8px;
  padding: .6rem .75rem;
}
.metric-label {
  font-family: var(--font-h);
  font-weight: 700;
  font-size: .58rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--txt-dim);
  margin-bottom: .15rem;
}
.metric-val {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: 1.6rem;
  line-height: 1;
}
.metric-unit {
  font-family: var(--font-m);
  font-size: .65rem;
  color: var(--txt-dim);
  margin-left: .15rem;
}
.mv-safe { color: var(--safe); }
.mv-warn { color: var(--warn); }
.mv-stop { color: var(--stop); }
.mv-txt  { color: var(--txt); }

/* ── Sunrise bar ── */
.sun-bar {
  height: 4px;
  background: var(--muted);
  border-radius: 4px;
  overflow: hidden;
  margin-top: .4rem;
}
.sun-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #f59e0b, #3b82f6, #f97316);
}

/* ── Optimal window ── */
.opt-window {
  background: rgba(34,197,94,.05);
  border: 1px solid rgba(34,197,94,.25);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.opt-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(34,197,94,.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}
.opt-title {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: .6rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--safe);
}
.opt-text {
  font-family: var(--font-h);
  font-weight: 700;
  font-size: 1.05rem;
  color: #fff;
  margin-top: .1rem;
}
.opt-sub {
  font-size: .7rem;
  color: var(--txt-dim);
  margin-top: .1rem;
}

/* ── Legend strip ── */
.legend-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: .7rem 1rem;
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 10px;
}
.leg-item {
  display: flex;
  align-items: center;
  gap: .4rem;
  font-family: var(--font-h);
  font-weight: 700;
  font-size: .72rem;
  letter-spacing: .05em;
}
.leg-dot {
  width: .7rem; height: .7rem;
  border-radius: 50%;
  flex-shrink: 0;
}
.leg-dot-safe { background: var(--safe); box-shadow: 0 0 6px rgba(34,197,94,.5); }
.leg-dot-warn { background: var(--warn); box-shadow: 0 0 6px rgba(245,158,11,.5); }
.leg-dot-stop { background: var(--stop); box-shadow: 0 0 6px rgba(239,68,68,.5); }

/* ── Forecast table ── */
.wc-table-wrap { overflow-x: auto; }
.wc-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-b);
  font-size: .8rem;
}
.wc-table thead tr {
  background: var(--surface);
}
.wc-table thead th {
  padding: .7rem .8rem;
  text-align: center;
  font-family: var(--font-h);
  font-weight: 900;
  font-size: .58rem;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: var(--txt-dim);
  white-space: nowrap;
  border-bottom: 1px solid var(--rim);
}
.wc-table thead th.th-crane {
  color: var(--accent);
  background: rgba(59,130,246,.05);
  border-bottom: 2px solid rgba(59,130,246,.3);
}
.wc-table tbody tr {
  border-bottom: 1px solid rgba(30,47,74,.5);
  transition: background .1s;
}
.wc-table tbody tr:hover { background: rgba(59,130,246,.06); }
.wc-table tbody tr.day-break td { border-top: 2px solid var(--rim); }
.wc-table td {
  padding: .65rem .8rem;
  text-align: center;
  vertical-align: middle;
}
.td-time {
  font-family: var(--font-h);
  font-weight: 700;
  font-size: 1rem;
  color: var(--accent);
  text-align: left;
  white-space: nowrap;
}
.td-wind {
  font-family: var(--font-m);
  font-weight: 600;
  font-size: .78rem;
  line-height: 1.6;
}
.td-wind small {
  display: block;
  font-size: .62rem;
  opacity: .7;
  font-weight: 400;
}
.td-crane { background: rgba(59,130,246,.04); }
.td-safe  { color: var(--safe); }
.td-warn  { color: var(--warn); }
.td-stop  { color: var(--stop); }
.td-dim   { color: var(--txt-dim); }
.td-dir   { font-family: var(--font-m); font-size: .75rem; color: var(--txt-dim); }

/* Rain row tints */
.rain-0 { background: transparent; }
.rain-1 { background: rgba(59,130,246,.04); }
.rain-2 { background: rgba(59,130,246,.1); }
.rain-3 { background: rgba(59,130,246,.2); }
.rain-4 { background: rgba(30,64,175,.35); }

/* ── Status badge in table ── */
.sts-safe { display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .55rem;
  border-radius:999px;background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);
  color:var(--safe);font-family:var(--font-h);font-weight:700;font-size:.6rem;letter-spacing:.1em; }
.sts-warn { display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .55rem;
  border-radius:999px;background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.25);
  color:var(--warn);font-family:var(--font-h);font-weight:700;font-size:.6rem;letter-spacing:.1em; }
.sts-stop { display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .55rem;
  border-radius:999px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.25);
  color:var(--stop);font-family:var(--font-h);font-weight:700;font-size:.6rem;letter-spacing:.1em; }

/* ── Table section header ── */
.tbl-header {
  background: var(--card-hi);
  border-bottom: 1px solid var(--rim);
  padding: .6rem 1rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .6rem;
}
.tbl-date {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: 1.15rem;
  color: #fff;
  letter-spacing: .03em;
}

/* ── Toggle pills ── */
.tog {
  display: flex;
  background: var(--bg);
  border: 1px solid var(--rim);
  border-radius: 999px;
  padding: 2px;
  gap: 2px;
}
.tog-btn {
  padding: .22rem .75rem;
  border-radius: 999px;
  font-family: var(--font-h);
  font-weight: 700;
  font-size: .62rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--txt-dim);
  border: none;
  cursor: pointer;
  background: transparent;
  transition: background .15s, color .15s;
}
.tog-btn.on { background: var(--accent); color: #fff; }

/* ── Disclaimer ── */
.wc-disclaimer {
  background: rgba(8,15,31,.8);
  border: 1px solid var(--rim);
  border-radius: 8px;
  padding: .55rem .8rem;
  font-family: var(--font-b);
  font-size: .65rem;
  color: var(--txt-dim);
  line-height: 1.5;
  margin-top: .8rem;
}

/* ── Info section ── */
.info-section { margin-bottom: 1.2rem; }
.info-h {
  font-family: var(--font-h);
  font-weight: 900;
  font-size: 1rem;
  letter-spacing: .05em;
  color: var(--accent);
  border-bottom: 1px solid var(--rim);
  padding-bottom: .4rem;
  margin-bottom: .7rem;
}
.info-p {
  font-family: var(--font-b);
  font-size: .84rem;
  color: var(--txt-dim);
  line-height: 1.65;
  margin-bottom: .5rem;
}
.info-li {
  display: flex;
  gap: .5rem;
  font-family: var(--font-b);
  font-size: .82rem;
  color: var(--txt-dim);
  line-height: 1.55;
  margin-bottom: .3rem;
}
.info-num {
  font-family: var(--font-h);
  font-weight: 900;
  color: var(--accent);
  flex-shrink: 0;
  min-width: 1.2rem;
}
.info-badge {
  display: inline-block;
  background: rgba(59,130,246,.1);
  border: 1px solid rgba(59,130,246,.3);
  border-radius: 5px;
  padding: .15rem .6rem;
  font-family: var(--font-m);
  font-size: .72rem;
  color: var(--accent);
  margin: .1rem .15rem;
}

/* ── Kofi button ── */
.kofi-btn {
  display: inline-flex;
  align-items: center;
  gap: .5rem;
  background: #FF5E5B;
  color: #fff !important;
  font-family: var(--font-h);
  font-weight: 700;
  font-size: .85rem;
  letter-spacing: .08em;
  padding: .65rem 1.4rem;
  border-radius: 10px;
  text-decoration: none !important;
  margin: .6rem 0;
  transition: background .15s;
}
.kofi-btn:hover { background: #e54e4b; }

/* ── Wave alert ── */
.box-caution { background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.4);
  border-radius:8px; padding:.6rem .8rem; font-size:.8rem; color:var(--warn); }
.box-danger  { background:rgba(239,68,68,.1);  border:1px solid rgba(239,68,68,.4);
  border-radius:8px; padding:.6rem .8rem; font-size:.8rem; color:var(--stop); }
.box-info    { background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,.3);
  border-radius:8px; padding:.6rem .8rem; font-size:.8rem; color:var(--accent); }

/* ── Temp colour chips ── */
.tc { border-radius: 5px; padding: .12rem .4rem; font-family:var(--font-m); font-size:.72rem; font-weight:600; }

/* ── Mobile tweaks ── */
@media (max-width: 768px) {
  .wc-nav { padding: 0 .75rem; }
  .wc-controls { padding: .5rem .75rem; }
  .hide-mobile { display: none !important; }
  .wc-table { font-size: .72rem; }
  .wc-table td { padding: .5rem .4rem; }
  .td-time { font-size: .85rem; }
  .metric-val { font-size: 1.3rem; }
}
@media (max-width: 480px) {
  .td-time { font-size: .75rem; }
}

/* ── Streamlit widget overrides ── */
div[data-testid="stButton"] > button {
  font-family: var(--font-h) !important;
  font-weight: 700 !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
}
div[data-testid="stTabs"] [role="tab"] {
  font-family: var(--font-h) !important;
  font-weight: 700 !important;
  letter-spacing: .1em !important;
  font-size: .8rem !important;
}
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label {
  font-family: var(--font-h) !important;
  font-weight: 700 !important;
  font-size: .65rem !important;
  letter-spacing: .15em !important;
  text-transform: uppercase !important;
  color: var(--txt-dim) !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WIND_UNIT_FACTORS = {
    "m/s":      (1.0,    "m/s"),
    "knots":    (1.9438, "kt"),
    "mph":      (2.2369, "mph"),
    "km/h":     (3.6,    "km/h"),
    "Beaufort": (None,   "Bft"),
}

TERRAIN = {
    "Open / Coastal":    {"alpha": 0.14, "factor": 1.00, "label": "Open/Coastal",   "icon": "🌊"},
    "Industrial / Port": {"alpha": 0.22, "factor": 1.10, "label": "Industrial",     "icon": "🏭"},
    "Urban / City":      {"alpha": 0.28, "factor": 1.20, "label": "Urban/City",     "icon": "🏙️"},
    "Woodland / Forest": {"alpha": 0.20, "factor": 1.15, "label": "Woodland",       "icon": "🌲"},
}

SAVED_LOCS_FILE = "forecast_logs/saved_locations.json"

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def to_beaufort(ms: float) -> int:
    for i, t in enumerate([0.5,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,28.5,32.7]):
        if ms < t: return i
    return 12

def fmt_wind(ms: float, unit: str) -> str:
    if unit == "Beaufort": return f"{to_beaufort(ms)} Bft"
    factor, label = WIND_UNIT_FACTORS[unit]
    return f"{ms * factor:.1f} {label}"

def risk_level(gust_ms: float) -> str:
    if gust_ms <= 5.9:  return "safe"
    if gust_ms <= 14.0: return "warn"
    return "stop"

def risk_symbol(level: str) -> str:
    return {"safe": "●", "warn": "⬡", "stop": "Ⓧ"}[level]

def risk_css(level: str) -> str:
    return {"safe": "td-safe", "warn": "td-warn", "stop": "td-stop"}[level]

def status_badge(level: str) -> str:
    dot = f'<span class="dot dot-{level}"></span>'
    label = {"safe": "SAFE", "warn": "CAUTION", "stop": "STOP"}[level]
    return f'<span class="sts-{level}">{dot} {label}</span>'

def direction_arrow(deg) -> str:
    try:
        d = float(deg)
        if np.isnan(d): return "—"
        return ["↓","↙","←","↖","↑","↗","→","↘"][int((d + 22.5) / 45) % 8]
    except:
        return "—"

def apply_terrain(ws_10m: float, terrain_key: str, height: float) -> float:
    t = TERRAIN.get(terrain_key, TERRAIN["Open / Coastal"])
    return ws_10m * t["factor"] * ((height / 10) ** t["alpha"])

def fmt_temp(c: float, unit: str) -> str:
    if unit == "°F": return f"{c * 9/5 + 32:.0f}°F"
    return f"{c:.0f}°C"

def safe_float(val, default=0.0):
    try:
        if val is None or val is pd.NaT: return default
        f = float(val)
        return default if f != f else f
    except (TypeError, ValueError):
        return default

def temp_colour(t: float) -> tuple:
    if   t <= -3: return "#1565C0","#fff"
    elif t <=  0: return "#1976D2","#fff"
    elif t <=  5: return "#42A5F5","#000"
    elif t <= 10: return "#80DEEA","#000"
    elif t <= 15: return "#fff176","#000"
    elif t <= 20: return "#ffd54f","#000"
    elif t <= 25: return "#ffb74d","#000"
    else:         return "#ff8a65","#000"

def rain_row_class(mm: float) -> str:
    if mm == 0:   return "rain-0"
    if mm < 0.5:  return "rain-1"
    if mm < 2.0:  return "rain-2"
    if mm < 5.0:  return "rain-3"
    return "rain-4"

# ══════════════════════════════════════════════════════════════════════════════
# LOCATION UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def postcode_to_coords(pc: str):
    try:
        r = requests.get(f"https://api.postcodes.io/postcodes/{pc.replace(' ','')}", timeout=6)
        d = r.json()
        if d.get("status") == 200:
            return (d["result"]["latitude"], d["result"]["longitude"],
                    f"{pc.upper()} ({d['result']['admin_district']})")
    except Exception:
        pass
    return None, None, None

def place_to_coords(name: str):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": name, "format": "json", "limit": 1},
                         headers={"User-Agent": "Windcast/5.0"}, timeout=6)
        d = r.json()
        if d:
            return float(d[0]["lat"]), float(d[0]["lon"]), d[0].get("display_name","")[:70]
    except Exception:
        pass
    return None, None, None

def parse_search(query: str):
    q = query.strip()
    if not q: return None, None, None
    for sep in [";", ","]:
        if sep in q:
            parts = q.split(sep, 1)
            try:
                lat = float(parts[0].strip()); lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon, f"{lat:.4f}°N, {lon:.4f}°E"
            except ValueError:
                pass
    if re.match(r'^[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s*\d[A-Za-z]{2}$', q):
        return postcode_to_coords(q)
    return place_to_coords(q)

def load_saved() -> list:
    try:
        os.makedirs("forecast_logs", exist_ok=True)
        if os.path.exists(SAVED_LOCS_FILE):
            with open(SAVED_LOCS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_location(name, lat, lon, crane_h, terrain):
    locs = load_saved()
    locs = [l for l in locs if l.get("name") != name]
    locs.insert(0, {"name": name, "lat": lat, "lon": lon, "crane_h": crane_h, "terrain": terrain})
    locs = locs[:12]
    try:
        os.makedirs("forecast_logs", exist_ok=True)
        with open(SAVED_LOCS_FILE, "w") as f:
            json.dump(locs, f, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH — LAND
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_ecmwf_land(lat: float, lon: float, hours: int = 168):
    url = "https://api.open-meteo.com/v1/forecast"
    params = [
        ("latitude",        lat),
        ("longitude",       lon),
        ("wind_speed_unit", "ms"),
        ("forecast_days",   min(hours // 24 + 1, 7)),
        ("timezone",        "auto"),
        ("models",          "ecmwf_ifs025"),
        ("hourly",          "wind_speed_10m"),
        ("hourly",          "wind_gusts_10m"),
        ("hourly",          "wind_direction_10m"),
        ("hourly",          "temperature_2m"),
        ("hourly",          "precipitation"),
        ("hourly",          "cloud_cover"),
        ("hourly",          "surface_pressure"),
        ("hourly",          "visibility"),
        ("hourly",          "relative_humidity_2m"),
        ("daily",           "sunrise"),
        ("daily",           "sunset"),
    ]
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            st.error(f"Open-Meteo: {body.get('reason', body)}")
            return None, [], None, None
        h = body.get("hourly", {})
        d = body.get("daily",  {})
        times = h.get("time", [])
        if not times:
            return None, [], None, None
        n = len(times)
        df = pd.DataFrame({
            "time":        pd.to_datetime(times),
            "wind_speed":  pd.to_numeric(h.get("wind_speed_10m",       [np.nan]*n), errors="coerce"),
            "wind_gust":   pd.to_numeric(h.get("wind_gusts_10m",       [np.nan]*n), errors="coerce"),
            "wind_dir":    pd.to_numeric(h.get("wind_direction_10m",   [np.nan]*n), errors="coerce"),
            "temperature": pd.to_numeric(h.get("temperature_2m",       [np.nan]*n), errors="coerce"),
            "precip":      pd.to_numeric(h.get("precipitation",        [np.nan]*n), errors="coerce"),
            "cloud":       pd.to_numeric(h.get("cloud_cover",          [np.nan]*n), errors="coerce"),
            "pressure":    pd.to_numeric(h.get("surface_pressure",     [np.nan]*n), errors="coerce"),
            "visibility":  pd.to_numeric(h.get("visibility",           [np.nan]*n), errors="coerce"),
            "humidity":    pd.to_numeric(h.get("relative_humidity_2m", [np.nan]*n), errors="coerce"),
        })
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        sunrise = d.get("sunrise",  [None])[0]
        sunset  = d.get("sunset",   [None])[0]
        return df, ["ECMWF IFS 0.25°"], sunrise, sunset
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None, [], None, None

def fetch_consensus(lat, lon, hours):
    return fetch_ecmwf_land(lat, lon, hours)

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH — OFFSHORE
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_offshore_wind(lat: float, lon: float, hours: int = 168):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["wind_speed_10m","wind_gusts_10m","wind_direction_10m",
                   "temperature_2m","cloud_cover","precipitation","pressure_msl"],
        "models": "ecmwf_ifs04",
        "wind_speed_unit": "ms",
        "forecast_days": min(hours // 24 + 1, 7),
        "timezone": "UTC",
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        h = r.json().get("hourly", {})
        times = h.get("time", [])
        if not times: return None
        df = pd.DataFrame({
            "time":       pd.to_datetime(times),
            "wind_speed": pd.to_numeric(h.get("wind_speed_10m",    [np.nan]*len(times)), errors="coerce"),
            "wind_gust":  pd.to_numeric(h.get("wind_gusts_10m",    [np.nan]*len(times)), errors="coerce"),
            "wind_dir":   pd.to_numeric(h.get("wind_direction_10m",[np.nan]*len(times)), errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m",    [np.nan]*len(times)), errors="coerce"),
            "cloud":      pd.to_numeric(h.get("cloud_cover",       [np.nan]*len(times)), errors="coerce"),
            "precip":     pd.to_numeric(h.get("precipitation",     [np.nan]*len(times)), errors="coerce"),
            "pressure":   pd.to_numeric(h.get("pressure_msl",      [np.nan]*len(times)), errors="coerce"),
        })
        now = pd.Timestamp.now().floor("h")
        return df[df["time"] >= now].reset_index(drop=True)
    except Exception as e:
        st.error(f"Wind fetch error: {e}")
        return None

@st.cache_data(ttl=1800)
def fetch_offshore_marine(lat: float, lon: float, hours: int = 168):
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["wave_height","wave_period","wave_direction",
                   "swell_wave_height","swell_wave_period","swell_wave_direction",
                   "wind_wave_height"],
        "forecast_days": min(hours // 24 + 1, 7),
        "timezone": "UTC",
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        h = r.json().get("hourly", {})
        times = h.get("time", [])
        if not times: return None
        df = pd.DataFrame({
            "time":         pd.to_datetime(times),
            "hs":           pd.to_numeric(h.get("wave_height",          [np.nan]*len(times)), errors="coerce"),
            "wave_period":  pd.to_numeric(h.get("wave_period",          [np.nan]*len(times)), errors="coerce"),
            "wave_dir":     pd.to_numeric(h.get("wave_direction",       [np.nan]*len(times)), errors="coerce"),
            "swell_hs":     pd.to_numeric(h.get("swell_wave_height",    [np.nan]*len(times)), errors="coerce"),
            "swell_period": pd.to_numeric(h.get("swell_wave_period",    [np.nan]*len(times)), errors="coerce"),
            "swell_dir":    pd.to_numeric(h.get("swell_wave_direction", [np.nan]*len(times)), errors="coerce"),
        })
        now = pd.Timestamp.now().floor("h")
        return df[df["time"] >= now].reset_index(drop=True)
    except Exception as e:
        st.error(f"Marine fetch error: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# TABLE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def wind_cells(ws_10, wg_10, ws_h, wg_h, unit, crane_h):
    rl10 = risk_level(wg_10); rlH = risk_level(wg_h)
    g10 = fmt_wind(wg_10, unit); w10 = fmt_wind(ws_10, unit)
    gH  = fmt_wind(wg_h,  unit); wH  = fmt_wind(ws_h,  unit)
    return (
        f'<td class="td-wind"><span class="{risk_css(rl10)}">{risk_symbol(rl10)} {g10}</span>'
        f'<small class="td-dim">W {w10}</small></td>'
        f'<td class="td-wind td-crane"><span class="{risk_css(rlH)}">{risk_symbol(rlH)} {gH}</span>'
        f'<small class="td-dim">W {wH}</small></td>'
    )

def build_land_rows(df, crane_h, terrain, unit, temp_unit, hours, show_3h=False):
    rows = []; prev_day = None
    for _, row in df.head(hours).iterrows():
        ts  = pd.to_datetime(row["time"])
        # 3h filter: only 00/03/06/09/12/15/18/21
        if show_3h and ts.hour % 3 != 0:
            continue
        ws  = safe_float(row.get("wind_speed"))
        wg  = safe_float(row.get("wind_gust"))
        wd  = row.get("wind_dir", np.nan)
        tmp = safe_float(row.get("temperature"))
        prc = safe_float(row.get("precip"))
        cld = safe_float(row.get("cloud"))
        prs = safe_float(row.get("pressure"), 1013.0)
        ws_h = apply_terrain(ws, terrain, crane_h)
        wg_h = apply_terrain(wg, terrain, crane_h)
        try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except: wd_f = np.nan
        dt_str   = ts.strftime("%a %d %b %H:%M")
        day_str  = ts.strftime("%Y-%m-%d")
        db_class = " day-break" if day_str != prev_day else ""
        prev_day = day_str
        rc  = rain_row_class(prc)
        tc, tf = temp_colour(tmp)
        rlH = risk_level(wg_h)
        dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"
        rows.append(
            f'<tr class="{rc}{db_class}">'
            f'<td class="td-time">{dt_str}</td>'
            + wind_cells(ws, wg, ws_h, wg_h, unit, crane_h)
            + f'<td class="td-dir">{dir_str}</td>'
            + f'<td><span class="tc" style="background:{tc};color:{tf};">{fmt_temp(tmp, temp_unit)}</span></td>'
            + f'<td class="td-dim" style="font-family:var(--font-m);font-size:.72rem;">{prc:.1f}mm</td>'
            + f'<td class="td-dim hide-mobile">{cld:.0f}%</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.72rem;">{prs:.0f}</td>'
            + f'<td>{status_badge(rlH)}</td>'
            + '</tr>'
        )
    return rows

def build_offshore_rows(wind_df, marine_df, crane_h, unit, temp_unit, hours, show_3h=False):
    rows = []; prev_day = None
    n = min(hours, len(wind_df))
    ml = len(marine_df) if marine_df is not None else 0
    for i in range(n):
        wrow = wind_df.iloc[i]
        ts   = pd.to_datetime(wrow["time"])
        if show_3h and ts.hour % 3 != 0:
            continue
        ws = safe_float(wrow.get("wind_speed")); wg = safe_float(wrow.get("wind_gust"))
        wd = wrow.get("wind_dir", np.nan);       tmp = safe_float(wrow.get("temperature"))
        prc = safe_float(wrow.get("precip"))
        ws_h = ws * ((crane_h / 10) ** 0.11)
        wg_h = wg * ((crane_h / 10) ** 0.11)
        hs = wp = wd_w = sw = "—"
        if marine_df is not None and i < ml:
            m = marine_df.iloc[i]
            hs_f = safe_float(m.get("hs"), np.nan); wp_f = safe_float(m.get("wave_period"), np.nan)
            wdw_f= safe_float(m.get("wave_dir"), np.nan); sw_f = safe_float(m.get("swell_hs"), np.nan)
            hs   = f"{hs_f:.2f}m"  if not np.isnan(hs_f) else "—"
            wp   = f"{wp_f:.1f}s"  if not np.isnan(wp_f) else "—"
            wd_w = f"{direction_arrow(wdw_f)} {wdw_f:.0f}°" if not np.isnan(wdw_f) else "—"
            sw   = f"{sw_f:.2f}m"  if not np.isnan(sw_f) else "—"
        try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except: wd_f = np.nan
        dt_str  = ts.strftime("%a %d %b %H:%M")
        day_str = ts.strftime("%Y-%m-%d")
        db_class= " day-break" if day_str != prev_day else ""
        prev_day= day_str
        rc = rain_row_class(prc)
        tc, tf = temp_colour(tmp)
        rlH= risk_level(wg_h)
        dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"
        rows.append(
            f'<tr class="{rc}{db_class}">'
            f'<td class="td-time">{dt_str}</td>'
            + wind_cells(ws, wg, ws_h, wg_h, unit, crane_h)
            + f'<td class="td-dir">{dir_str}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.72rem;">{hs}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.72rem;">{wp}</td>'
            + f'<td class="td-dir hide-mobile">{wd_w}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.72rem;">{sw}</td>'
            + f'<td><span class="tc" style="background:{tc};color:{tf};">{fmt_temp(tmp, temp_unit)}</span></td>'
            + f'<td>{status_badge(rlH)}</td>'
            + '</tr>'
        )
    return rows

def land_header(crane_h):
    return f"""<tr>
  <th style="text-align:left;">Date &amp; Time</th>
  <th>Gust / Wind<br><small style="font-weight:400;opacity:.6;">at 10m</small></th>
  <th class="th-crane">Gust / Wind<br><small style="font-weight:400;opacity:.8;">at {crane_h}m ✦</small></th>
  <th>Dir</th><th>Temp</th><th>Rain</th>
  <th class="hide-mobile">Cloud</th>
  <th class="hide-mobile">Press (hPa)</th>
  <th>Status</th>
</tr>"""

def offshore_header(crane_h):
    return f"""<tr>
  <th style="text-align:left;">Date &amp; Time</th>
  <th>Gust / Wind<br><small style="font-weight:400;opacity:.6;">at 10m</small></th>
  <th class="th-crane">Gust / Wind<br><small style="font-weight:400;opacity:.8;">at {crane_h}m ✦</small></th>
  <th>Dir</th>
  <th class="hide-mobile">Hs (m)</th>
  <th class="hide-mobile">Wave Pd</th>
  <th class="hide-mobile">Wave Dir</th>
  <th class="hide-mobile">Swell Hs</th>
  <th>Temp</th><th>Status</th>
</tr>"""

def render_table(rows, hdr):
    body = "\n".join(rows)
    st.markdown(
        f'<div class="wc-table-wrap"><table class="wc-table">'
        f'<thead>{hdr}</thead><tbody>{body}</tbody></table></div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# NOW CARD
# ══════════════════════════════════════════════════════════════════════════════
def render_now_card(df, crane_h, terrain, unit, mode, sunrise=None, sunset=None):
    if df is None or df.empty: return
    row = df.iloc[0]
    ws  = safe_float(row.get("wind_speed"))
    wg  = safe_float(row.get("wind_gust"))
    if mode == "land":
        ws_h = apply_terrain(ws, terrain, crane_h)
        wg_h = apply_terrain(wg, terrain, crane_h)
    else:
        ws_h = ws * ((crane_h / 10) ** 0.11)
        wg_h = wg * ((crane_h / 10) ** 0.11)
    rl   = risk_level(wg_h)
    tmp  = safe_float(row.get("temperature"))
    prs  = safe_float(row.get("pressure"), 1013.0)
    wd   = row.get("wind_dir", np.nan)
    try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
    except: wd_f = np.nan
    dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"

    pill_html = f'<span class="pill pill-{rl}"><span class="dot dot-{rl}"></span> {{"safe":"SAFE","warn":"CAUTION","stop":"STOP"}}["{rl}"]</span>'
    lbl = {"safe": "SAFE", "warn": "CAUTION", "stop": "STOP"}[rl]

    # Sunrise/sunset progress
    sun_html = ""
    if sunrise and sunset:
        try:
            sr = datetime.fromisoformat(sunrise); ss = datetime.fromisoformat(sunset)
            now_dt = datetime.now()
            daylight = (ss - sr).total_seconds()
            elapsed  = max(0, min(daylight, (now_dt - sr).total_seconds()))
            pct = int(elapsed / daylight * 100) if daylight > 0 else 0
            sr_fmt = sr.strftime("%H:%M"); ss_fmt = ss.strftime("%H:%M")
            hrs = int(daylight // 3600); mins = int((daylight % 3600) // 60)
            sun_html = f"""
<div class="metric-block" style="margin-top:.6rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem;">
    <div style="display:flex;align-items:center;gap:.5rem;">
      <span style="font-size:.9rem;">🌅</span>
      <div>
        <div class="metric-label">Sunrise</div>
        <div style="font-family:var(--font-m);font-weight:600;font-size:.85rem;color:var(--txt);">{sr_fmt}</div>
      </div>
    </div>
    <div style="text-align:center;">
      <div class="metric-label">Daylight</div>
      <div style="font-family:var(--font-m);font-weight:700;font-size:.85rem;color:var(--accent);">{hrs}h {mins}m</div>
    </div>
    <div style="display:flex;align-items:center;gap:.5rem;">
      <div style="text-align:right;">
        <div class="metric-label">Sunset</div>
        <div style="font-family:var(--font-m);font-weight:600;font-size:.85rem;color:var(--txt);">{ss_fmt}</div>
      </div>
      <span style="font-size:.9rem;">🌇</span>
    </div>
  </div>
  <div class="sun-bar"><div class="sun-fill" style="width:{pct}%"></div></div>
</div>"""
        except Exception:
            pass

    gust_h_str = fmt_wind(wg_h, unit)
    wind_h_str = fmt_wind(ws_h, unit)
    gust_10_str= fmt_wind(wg, unit)
    wind_10_str= fmt_wind(ws, unit)

    st.markdown(f"""
<div class="wc-card" style="height:100%;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.8rem;">
    <div>
      <span class="sec-label">Live Status</span>
      <div style="font-family:var(--font-h);font-weight:900;font-size:1.8rem;color:#fff;line-height:1;">NOW</div>
    </div>
    <span class="pill pill-{rl}"><span class="dot dot-{rl}"></span> {lbl}</span>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:.5rem;">
    <div class="metric-block">
      <div class="metric-label">Gust @10m</div>
      <div class="metric-val {{"safe":"mv-safe","warn":"mv-warn","stop":"mv-stop"}}["{risk_level(wg)}"]">{gust_10_str}</div>
    </div>
    <div class="metric-block">
      <div class="metric-label">Gust @{crane_h}m ✦</div>
      <div class="metric-val mv-{rl}">{gust_h_str}</div>
    </div>
    <div class="metric-block">
      <div class="metric-label">Wind @{crane_h}m ✦</div>
      <div class="metric-val mv-txt">{wind_h_str}</div>
    </div>
    <div class="metric-block">
      <div class="metric-label">Direction</div>
      <div style="font-family:var(--font-m);font-weight:700;font-size:1rem;color:var(--accent);padding-top:.1rem;">{dir_str}</div>
    </div>
  </div>

  <div style="display:flex;justify-content:space-between;padding:.4rem 0;border-top:1px solid var(--rim);font-family:var(--font-m);font-size:.72rem;color:var(--txt-dim);">
    <span>{fmt_temp(tmp,"°C")}</span>
    <span>{prs:.0f} hPa</span>
  </div>
  {sun_html}
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTIMAL WINDOW
# ══════════════════════════════════════════════════════════════════════════════
def render_optimal_window(df, crane_h, terrain, mode):
    if df is None or df.empty: return
    safe_windows = []
    current_start = None
    for _, row in df.head(72).iterrows():
        wg = safe_float(row.get("wind_gust"))
        wg_h = (apply_terrain(wg, terrain, crane_h) if mode == "land"
                else wg * ((crane_h / 10) ** 0.11))
        ts = pd.to_datetime(row["time"])
        if risk_level(wg_h) == "safe":
            if current_start is None: current_start = ts
        else:
            if current_start is not None:
                safe_windows.append((current_start, ts - pd.Timedelta(hours=1)))
                current_start = None
    if current_start is not None:
        safe_windows.append((current_start, df.iloc[-1]["time"]))

    if safe_windows:
        s, e = safe_windows[0]
        s_str = pd.to_datetime(s).strftime("%H:%M")
        e_str = pd.to_datetime(e).strftime("%H:%M")
        msg = f"Safe to lift {s_str}–{e_str} (next 72h window)"
        badge = '<span class="pill pill-safe">GO</span>'
    else:
        msg = "No safe window found in the next 72h. Review conditions."
        badge = '<span class="pill pill-stop">NO-GO</span>'

    st.markdown(f"""
<div class="opt-window" style="margin-bottom:.8rem;">
  <div class="opt-icon">📅</div>
  <div style="flex:1;min-width:0;">
    <div class="opt-title">Optimal Lift Window</div>
    <div class="opt-text">{msg}</div>
    <div class="opt-sub">Crane height {crane_h}m · Gust threshold ≤ 5.9 m/s</div>
  </div>
  {badge}
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════
def render_legend():
    st.markdown("""
<div class="legend-strip">
  <span style="font-family:var(--font-h);font-weight:900;font-size:.6rem;letter-spacing:.18em;color:var(--txt-dim);text-transform:uppercase;">Legend</span>
  <span class="leg-item"><span class="leg-dot leg-dot-safe"></span><span style="color:var(--safe);">SAFE</span> <span style="color:var(--txt-dim);font-weight:400;">≤ 5.9 m/s</span></span>
  <span class="leg-item"><span class="leg-dot leg-dot-warn"></span><span style="color:var(--warn);">CAUTION</span> <span style="color:var(--txt-dim);font-weight:400;">6–14 m/s</span></span>
  <span class="leg-item"><span class="leg-dot leg-dot-stop"></span><span style="color:var(--stop);">STOP</span> <span style="color:var(--txt-dim);font-weight:400;">&gt; 14 m/s</span></span>
  <span class="leg-item" style="margin-left:auto;">
    <span style="font-weight:400;color:var(--txt-dim);font-size:.68rem;">Row tint = rain intensity</span>
  </span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INFO TAB
# ══════════════════════════════════════════════════════════════════════════════
def render_info_tab():
    st.markdown("""
<div class="info-section">
  <div class="info-h">👤 About the Creator</div>
  <p class="info-p">Built between jobs, out of sheer frustration. You know how it is on site — you're trying to make a Go/No-Go call, you check the weather, and XCWeather gives you something that bears no resemblance to what the anemometer on the hook block is reading.</p>
  <p class="info-p">My wife — a UX designer — finally said: <em>"You clearly know what's wrong with these tools — so build a better one."</em> Six months later it's grown beyond what I expected. The accuracy against real site conditions has been consistent enough that I've stopped second-guessing it.</p>
</div>

<div class="info-section">
  <div class="info-h">🎯 What It Does</div>
  <p class="info-p"><strong>ECMWF IFS forecast, corrected to your crane height per BS 7121, colour-coded for Go/No-Go. Built by a lifting supervisor, not a software company.</strong></p>
  <div class="info-li"><span class="info-num">✦</span><span>ECMWF IFS 0.25° — same model used by professional meteorological agencies worldwide</span></div>
  <div class="info-li"><span class="info-num">✦</span><span>BS 7121 height correction using power law, adjusted for terrain roughness</span></div>
  <div class="info-li"><span class="info-num">✦</span><span>Colour-coded Go/No-Go with safe / caution / stop thresholds</span></div>
  <div class="info-li"><span class="info-num">✦</span><span>LOLER 1998 aware — built by an Appointed Person, not a software company</span></div>
  <div class="info-li"><span class="info-num">✦</span><span>Offshore mode — Hs, swell, wave period, IMCA LR006 height correction (α = 0.11)</span></div>
</div>

<div class="info-section">
  <div class="info-h">📋 How To Use</div>
  <div class="info-li"><span class="info-num">1.</span><span>Enter your location — UK postcode (e.g. <code style="background:rgba(59,130,246,.1);padding:1px 5px;border-radius:4px;font-family:var(--font-m);font-size:.8rem;">SE1 7PB</code>), place name, or lat; lon</span></div>
  <div class="info-li"><span class="info-num">2.</span><span>Set crane height using the +/− widget. Choose terrain type — this drives the BS 7121 power-law correction</span></div>
  <div class="info-li"><span class="info-num">3.</span><span>Click Get Forecast — the table loads with hourly speeds at 10m reference and your crane height</span></div>
  <div class="info-li"><span class="info-num">4.</span><span>Read the ✦ crane height column — SAFE ● / CAUTION ⬡ / STOP Ⓧ</span></div>
  <div class="info-li"><span class="info-num">5.</span><span>Always verify with a calibrated on-site anemometer before commencing any lifting operation</span></div>
</div>

<div class="info-section">
  <div class="info-h">🎨 Colour Legend</div>
  <div style="display:flex;flex-direction:column;gap:.7rem;margin-top:.3rem;">
    <div style="display:flex;align-items:center;gap:.8rem;">
      <span class="leg-dot leg-dot-safe" style="width:.9rem;height:.9rem;flex-shrink:0;"></span>
      <div><div style="font-family:var(--font-h);font-weight:700;color:var(--safe);">SAFE — Gust ≤ 5.9 m/s (≤ 11.5 kt)</div>
      <div class="info-p" style="margin:0;">Proceed with lift plan.</div></div>
    </div>
    <div style="display:flex;align-items:center;gap:.8rem;">
      <span style="color:var(--warn);font-size:1rem;flex-shrink:0;">⬡</span>
      <div><div style="font-family:var(--font-h);font-weight:700;color:var(--warn);">CAUTION — Gust 6–14 m/s (11.6–27 kt)</div>
      <div class="info-p" style="margin:0;">Enhanced monitoring. Review lift plan against crane wind rating.</div></div>
    </div>
    <div style="display:flex;align-items:center;gap:.8rem;">
      <span style="color:var(--stop);font-size:1rem;flex-shrink:0;">Ⓧ</span>
      <div><div style="font-family:var(--font-h);font-weight:700;color:var(--stop);">STOP — Gust &gt; 14 m/s (&gt; 27 kt)</div>
      <div class="info-p" style="margin:0;">Do not commence lifting operations.</div></div>
    </div>
  </div>
  <p class="info-p" style="margin-top:.8rem;font-size:.72rem;">Row background tint indicates rain intensity — clear / light / moderate / heavy / very heavy.</p>
</div>

<div class="info-section">
  <div class="info-h">🪤 Where's The Catch?</div>
  <p class="info-p">Open-Meteo free tier — full ECMWF IFS resolution for 7 days, updated every 6 hours. For lift planning purposes that is absolutely fine.</p>
  <p class="info-p">This is not a replacement for your anemometer. It never will be.</p>
  <p class="info-p"><strong>Email list:</strong> If you'd like to be notified personally when tips cover the cost of the paid ECMWF API, drop your email in the feedback form. No mailing list software, no spam — I'll contact everyone individually.</p>
</div>

<div class="info-section">
  <div class="info-h">📦 Version &amp; Changelog</div>
  <span class="info-badge">v5.0 — Current</span>
  <div style="margin-top:.6rem;display:flex;flex-direction:column;gap:.3rem;">
    <div class="info-li"><span class="info-num">▸</span><span><strong>v5.0 — April 2026:</strong> New design system (Barlow Condensed / JetBrains Mono), responsive desktop+mobile, rain row tints, optimal window calculator, sunrise/sunset bar, 24h/3h toggle, Export &amp; Share modal.</span></div>
    <div class="info-li"><span class="info-num">▸</span><span><strong>v4.0 — April 2026:</strong> Added Forecast/Info tabs, disclaimer, shareable URL, Ko-fi, feedback link.</span></div>
    <div class="info-li"><span class="info-num">▸</span><span><strong>v3.1 — March 2026:</strong> Merged land and offshore. Combined Go/No-Go across all parameters.</span></div>
    <div class="info-li"><span class="info-num">▸</span><span><strong>v2.1 — Feb 2026:</strong> Added swell Hs, visibility, sea temp. ECMWF-only (dropped blended consensus).</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.link_button("☕  Support Windcast on Ko-fi", KOFI_URL, use_container_width=True)
    with col2:
        st.link_button("📝  Found an error? Tell me here.", FEEDBACK_URL, use_container_width=True)

    st.markdown("""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
Lifting supervisor retains full Go/No-Go responsibility per <strong>BS 7121-1:2016</strong>,
<strong>LOLER 1998</strong>, <strong>HSE PM55</strong> and <strong>IMCA LR006</strong>.
Data: ECMWF IFS 0.25° via Open-Meteo (free tier). v5.0
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FORECAST TAB — wrapped in function so st.stop() → return keeps Info alive
# ══════════════════════════════════════════════════════════════════════════════
def _forecast_tab(mode):
    terrain_keys = list(TERRAIN.keys())
    terrain_icons = [f"{TERRAIN[k]['icon']} {k}" for k in terrain_keys]

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<div class="wc-controls">', unsafe_allow_html=True)

    if mode == "land":
        c_loc, c_save, c_h, c_ter, c_wu, c_tu, c_btn = st.columns([3.5, 0.45, 1.0, 2.0, 1.2, 0.8, 1.5])
    else:
        c_loc, c_save, c_h, c_wu, c_tu, c_btn = st.columns([3.5, 0.45, 1.0, 1.2, 0.8, 1.5])

    with c_loc:
        search_val = st.text_input("Location",
            value=st.session_state.loc_name if st.session_state.lat else "",
            placeholder="Postcode · Place name · lat ; lon",
            key="search_input")

    with c_save:
        st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
        save_btn = st.button("📌", key="save_btn", help="Save this site", use_container_width=True)

    with c_h:
        crane_h = st.number_input("Height (m)", min_value=10, max_value=250,
                                   value=st.session_state.crane_h, step=5, key="crane_num")
        st.session_state.crane_h = crane_h

    if mode == "land":
        with c_ter:
            ter_choice = st.selectbox("Terrain",
                terrain_icons, key="terrain_sel",
                help="Affects BS 7121 wind shear height correction")
            terrain = terrain_keys[terrain_icons.index(ter_choice)]
        with c_wu:
            wind_unit = st.selectbox("Wind units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit")
        with c_tu:
            temp_unit = st.selectbox("Temp", ["°C","°F"], key="temp_unit")
        with c_btn:
            st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
            fetch_btn = st.button("🌤️ Get Forecast", type="primary",
                                   use_container_width=True, key="fetch_btn")
    else:
        terrain = "Open / Coastal"
        with c_wu:
            wind_unit = st.selectbox("Wind units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit")
        with c_tu:
            temp_unit = st.selectbox("Temp", ["°C","°F"], key="temp_unit")
        with c_btn:
            st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
            fetch_btn = st.button("🌤️ Get Forecast", type="primary",
                                   use_container_width=True, key="fetch_btn")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Resolve location ──────────────────────────────────────────────────────
    lat = st.session_state.lat; lon = st.session_state.lon
    loc_name = st.session_state.loc_name

    if search_val and (search_val != loc_name or lat is None):
        with st.spinner("Looking up location…"):
            lat_new, lon_new, name_new = parse_search(search_val)
        if lat_new:
            lat = lat_new; lon = lon_new; loc_name = name_new
            st.session_state.lat = lat; st.session_state.lon = lon
            st.session_state.loc_name = loc_name
        else:
            st.error("Location not found. Try a UK postcode, place name, or 'lat ; lon'.")
            return

    if save_btn and lat:
        save_location(loc_name[:40], lat, lon, crane_h, terrain)
        st.success(f"✅ Saved: {loc_name[:40]}")

    saved = load_saved()
    if saved:
        saved_names = [l["name"] for l in saved]
        picked = st.selectbox("📍 Load saved site", ["— select —"] + saved_names,
                              key="load_saved", label_visibility="visible")
        if picked != "— select —":
            loc = next(l for l in saved if l["name"] == picked)
            st.session_state.lat = loc["lat"]; st.session_state.lon = loc["lon"]
            st.session_state.loc_name = loc["name"]
            st.session_state.crane_h = loc.get("crane_h", crane_h)

    if lat is None:
        st.markdown("""<div class="box-info" style="margin:1rem 1.5rem;">
        👆 Enter a location above and click <strong>Get Forecast</strong>.<br>
        Supports UK postcodes (e.g. <code>RG12 1BE</code>), place names, or coordinates (<code>51.08 ; -1.29</code>).
        </div>""", unsafe_allow_html=True)
        return

    if fetch_btn:
        st.query_params.update({"lat": f"{lat:.4f}", "lon": f"{lon:.4f}",
                                "h": str(crane_h), "mode": mode})
        fetch_ecmwf_land.clear(); fetch_offshore_wind.clear(); fetch_offshore_marine.clear()
        for k in ["df_cache","marine_cache","fetch_time","sunrise","sunset"]:
            st.session_state.pop(k, None)

    DAY_OPTIONS = {1: 24, 3: 72, 7: 168}

    if fetch_btn or "df_cache" not in st.session_state:
        if mode == "land":
            with st.spinner("Fetching ECMWF IFS forecast…"):
                df, models_used, sunrise, sunset = fetch_consensus(lat, lon, 168)
            if df is None or df.empty:
                st.error("Weather model failed to respond. Check connection and try again.")
                return
            st.session_state.df_cache     = df
            st.session_state.models_used  = models_used
            st.session_state.marine_cache = None
            st.session_state.sunrise      = sunrise
            st.session_state.sunset       = sunset
        else:
            with st.spinner("Fetching ECMWF wind + Marine data…"):
                df = fetch_offshore_wind(lat, lon, 168)
                marine = fetch_offshore_marine(lat, lon, 168)
            if df is None or df.empty:
                st.error("Failed to fetch wind data. Check connection and try again.")
                return
            st.session_state.df_cache     = df
            st.session_state.marine_cache = marine
            st.session_state.sunrise = st.session_state.sunset = None
        st.session_state.fetch_time = datetime.now(timezone.utc)

    df      = st.session_state.get("df_cache")
    marine  = st.session_state.get("marine_cache")
    fetch_t = st.session_state.get("fetch_time", datetime.now(timezone.utc))
    sunrise = st.session_state.get("sunrise")
    sunset  = st.session_state.get("sunset")

    if df is None or df.empty:
        st.error("No forecast data. Check connection or try a different location.")
        return

    forecast_hours = DAY_OPTIONS[st.session_state.fdays]

    # ── Main layout: NOW card + Optimal + Legend ──────────────────────────────
    st.markdown('<div style="padding:0.8rem 1.5rem 0 1.5rem;">', unsafe_allow_html=True)

    col_now, col_right = st.columns([1, 3])
    with col_now:
        render_now_card(df, crane_h, terrain, wind_unit, mode, sunrise, sunset)
    with col_right:
        render_optimal_window(df, crane_h, terrain, mode)
        render_legend()

        # ── Offshore wave warning ─────────────────────────────────────────────
        if mode == "offshore" and marine is not None and not marine.empty:
            hs_now = safe_float(marine.iloc[0].get("hs"))
            if hs_now >= 2.5:
                cls = "box-danger" if hs_now >= 4.0 else "box-caution"
                lvl = "DANGER" if hs_now >= 4.0 else "CAUTION"
                st.markdown(f'<div class="{cls}">⚓ <strong>Wave Height Warning:</strong> '
                            f'Hs = {hs_now:.2f}m — {lvl}. Review vessel motion limits.</div>',
                            unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Forecast table section ────────────────────────────────────────────────
    st.markdown('<div style="padding:.6rem 1.5rem 0 1.5rem;">', unsafe_allow_html=True)

    # Table header row with day buttons + 24h/3h + Land/Sea + info
    hcols = st.columns([2.5, 0.55, 0.55, 0.55, 0.55, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7])

    with hcols[0]:
        updated_str = fetch_t.strftime("%H:%M") if fetch_t else "--:--"
        mode_src = "ECMWF IFS 0.25°" if mode == "land" else "ECMWF Marine"
        st.markdown(
            f'<div style="font-family:var(--font-h);font-weight:900;font-size:1.1rem;color:#fff;padding-top:.4rem;">'
            f'Forecast &nbsp;<span style="font-size:.7rem;font-weight:400;color:var(--txt-dim);">'
            f'{loc_name[:40]} · {updated_str} UTC · {mode_src}</span></div>',
            unsafe_allow_html=True)

    for i, (days, hrs) in enumerate(DAY_OPTIONS.items()):
        with hcols[i + 1]:
            lbl = f"{days}d"
            btype = "primary" if st.session_state.fdays == days else "secondary"
            st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
            if st.button(lbl, key=f"day_{days}", type=btype, use_container_width=True):
                st.session_state.fdays = days; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with hcols[4]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        if st.button("Max", key="day_max",
                     type="primary" if st.session_state.fdays == 7 else "secondary",
                     use_container_width=True):
            st.session_state.fdays = 7; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[5]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        if st.button("24h", key="btn_24h",
                     type="primary" if not st.session_state.get("show_3h") else "secondary",
                     use_container_width=True):
            st.session_state.show_3h = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[6]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        if st.button("3h", key="btn_3h",
                     type="primary" if st.session_state.get("show_3h") else "secondary",
                     use_container_width=True):
            st.session_state.show_3h = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[7]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        land_t = "primary" if mode == "land" else "secondary"
        if st.button("🏗️ Land", key="toggle_land", type=land_t, use_container_width=True):
            if mode != "land": st.session_state.mode = "land"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[8]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        sea_t = "primary" if mode == "offshore" else "secondary"
        if st.button("⚓ Sea", key="toggle_sea", type=sea_t, use_container_width=True):
            if mode != "offshore": st.session_state.mode = "offshore"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[9]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        # PDF export
        try:
            import weasyprint
            if mode == "land":
                rows_pdf = build_land_rows(df, crane_h, terrain, wind_unit, temp_unit, forecast_hours)
                hdr_pdf  = land_header(crane_h)
            else:
                rows_pdf = build_offshore_rows(df, marine, crane_h, wind_unit, temp_unit, forecast_hours)
                hdr_pdf  = offshore_header(crane_h)
            body_pdf = "\n".join(rows_pdf)
            pdf_css  = """
@page { margin:10mm; size:A4 landscape; }
body { background:#080f1f; color:#e2eaff; font-family:Arial,sans-serif; font-size:8pt; }
table { width:100%; border-collapse:collapse; }
thead th { background:#0e1729; color:#7a90b8; padding:5px 4px; border-bottom:2px solid #1e2f4a; font-size:7pt; }
thead th.th-crane { color:#3b82f6; }
tbody tr { border-bottom:1px solid #1e2f4a; }
td { padding:4px; text-align:center; }
.td-time { color:#3b82f6; font-weight:bold; }
.td-safe { color:#22c55e; } .td-warn { color:#f59e0b; } .td-stop { color:#ef4444; }
"""
            pdf_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{pdf_css}</style></head><body>
<h3 style="color:#3b82f6;margin-bottom:4px;">Windcast — {loc_name}</h3>
<p style="color:#7a90b8;font-size:7pt;margin:0 0 6px 0;">Crane {crane_h}m · {forecast_hours}h · {fetch_t.strftime('%Y-%m-%d %H:%M UTC')} · ECMWF IFS 0.25°</p>
<table><thead>{hdr_pdf}</thead><tbody>{body_pdf}</tbody></table>
<p style="color:#555;font-size:6pt;margin-top:6px;">FOR PLANNING PURPOSES ONLY · BS 7121-1:2016 · LOLER 1998 · HSE PM55 · IMCA LR006</p>
</body></html>"""
            pdf_bytes = weasyprint.HTML(string=pdf_html).write_pdf()
            fname = f"windcast_{loc_name[:20].replace(' ','_')}_{fetch_t.strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("📄 PDF", data=pdf_bytes, file_name=fname,
                               mime="application/pdf", use_container_width=True)
        except ImportError:
            st.button("📄 PDF", disabled=True, use_container_width=True,
                      help="Install weasyprint for PDF export")
        st.markdown('</div>', unsafe_allow_html=True)

    with hcols[10]:
        st.markdown('<div style="margin-top:.3rem;">', unsafe_allow_html=True)
        share_url = f"https://windcast.streamlit.app/?lat={lat:.4f}&lon={lon:.4f}&h={crane_h}&mode={mode}"
        whatsapp  = f"https://api.whatsapp.com/send?text=Windcast+forecast+{share_url}"
        telegram  = f"https://t.me/share/url?url={share_url}&text=Windcast+lifting+forecast"
        st.button("🔗 Share", use_container_width=True, key="share_btn",
                  help=f"Copy link: {share_url}\nWhatsApp: {whatsapp}\nTelegram: {telegram}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Build and render table ─────────────────────────────────────────────────
    show_3h = st.session_state.get("show_3h", False)
    if mode == "land":
        rows = build_land_rows(df, crane_h, terrain, wind_unit, temp_unit, forecast_hours, show_3h)
        hdr  = land_header(crane_h)
    else:
        rows = build_offshore_rows(df, marine, crane_h, wind_unit, temp_unit, forecast_hours, show_3h)
        hdr  = offshore_header(crane_h)

    # Table wrapper card
    st.markdown('<div style="background:var(--card);border:1px solid var(--rim);border-radius:12px;overflow:hidden;margin-top:.5rem;">', unsafe_allow_html=True)
    render_table(rows, hdr)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
Lifting supervisor retains full Go/No-Go responsibility per <strong>BS 7121-1:2016</strong>,
<strong>LOLER 1998</strong>, <strong>HSE PM55</strong> and <strong>IMCA LR006</strong>.
Data: ECMWF IFS 0.25° via Open-Meteo (free tier). v5.0
</div>""", unsafe_allow_html=True)

    st.markdown(
        f'<div style="margin-top:.4rem;font-size:.7rem;color:var(--txt-dim);">'
        f'📝 <a href="{FEEDBACK_URL}" target="_blank" style="color:var(--txt-dim);">Found an error? Tell me here.</a>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Advanced model info ──────────────────────────────────────────────────
    models_used = st.session_state.get("models_used", ["ECMWF IFS 0.25°"])
    with st.expander("⚙️ Advanced — Model Selection", expanded=False):
        st.markdown(f"""
**Current model:** ECMWF IFS 0.25° (single-model, direct from Open-Meteo)

Windcast uses ECMWF IFS exclusively. It is the highest-accuracy freely available global model, used as the reference standard by meteorological agencies worldwide.

**Active this session:** {models_used}
""")
        if df is not None and not df.empty:
            st.dataframe(df.head(4))

    st.markdown('</div>', unsafe_allow_html=True)  # close padding div


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # ── Session state init ────────────────────────────────────────────────────
    if "disclaimer_ack" not in st.session_state:
        st.session_state["disclaimer_ack"] = False
    for k, v in [("mode","land"),("crane_h",40),("lat",None),("lon",None),
                  ("loc_name",""),("fdays",1),("show_3h",False)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Read shareable URL params ─────────────────────────────────────────────
    params = st.query_params
    if st.session_state.lat is None and "lat" in params and "lon" in params:
        try:
            st.session_state.lat      = float(params["lat"])
            st.session_state.lon      = float(params["lon"])
            st.session_state.loc_name = f"{st.session_state.lat:.4f}°N, {st.session_state.lon:.4f}°E"
            if "h"    in params: st.session_state.crane_h = max(10, min(250, int(params["h"])))
            if "mode" in params and params["mode"] in ("land","offshore"):
                st.session_state.mode = params["mode"]
        except Exception:
            pass

    mode = st.session_state.mode

    # ── TOP NAV ───────────────────────────────────────────────────────────────
    st.markdown(f"""
<div class="wc-nav">
  <div class="wc-logo">
    <span>⚡</span> Wind<span>cast</span>
  </div>
  <div class="wc-nav-links">
    <a href="?tab=forecast" class="wc-nav-link {'active' if st.session_state.get('active_tab','forecast')=='forecast' else ''}">🌤️ Forecast</a>
    <a href="?tab=info"     class="wc-nav-link {'active' if st.session_state.get('active_tab','forecast')=='info'     else ''}">ℹ️ Info</a>
    <div class="wc-nav-sep"></div>
    <span class="wc-nav-link" style="cursor:default;opacity:.5;">🏗️ Land / ⚓ Sea</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── DISCLAIMER ────────────────────────────────────────────────────────────
    if not st.session_state.disclaimer_ack:
        st.markdown('<div style="padding:1.5rem;">', unsafe_allow_html=True)
        st.warning(
            "⚠️ **Planning Tool — Regulatory Notice**\n\n"
            "Windcast provides forecast data for lift planning purposes only. "
            "It does **not** replace a calibrated on-site anemometer. "
            "The lifting supervisor remains solely responsible for all Go/No-Go decisions "
            "under **BS 7121-1:2016**, **LOLER 1998**, and **HSE PM55**."
        )
        if st.checkbox(
            "I understand this forecast is for planning purposes only. "
            "I will verify conditions with a calibrated on-site anemometer before commencing.",
            key="disclaimer_checkbox"):
            st.session_state.disclaimer_ack = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab_forecast, tab_info = st.tabs(["🌤️ Forecast", "ℹ️ Info"])

    with tab_forecast:
        st.session_state["active_tab"] = "forecast"
        _forecast_tab(mode)

    with tab_info:
        st.session_state["active_tab"] = "info"
        st.markdown('<div style="padding:1rem 1.5rem;">', unsafe_allow_html=True)
        render_info_tab()
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
