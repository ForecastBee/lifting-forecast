"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   WINDCAST  v5.4  —  Lifting Operations Weather Forecast                    ║
║   BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006 | NORSOK R-003       ║
║   Source: ECMWF IFS 0.25° via Open-Meteo (free tier)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests, json, os, re
import pandas as pd
import numpy as np
from datetime import datetime, timezone

st.set_page_config(
    page_title="Windcast | Lifting Ops Forecast",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def _secret(key, fallback=None):
    try: return st.secrets[key]
    except Exception: return fallback

FEEDBACK_URL = _secret("FEEDBACK_URL", "https://forms.gle/REPLACE_WITH_YOUR_FORM_URL")
KOFI_URL     = "https://ko-fi.com/windcast"

# ══════════════════════════════════════════════════════════════════════════════
# CSS — Matching the design mockups
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700;800;900&family=Barlow:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
#MainMenu, header, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }

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

body, .stApp { background: var(--bg) !important; color: var(--txt) !important; font-family: var(--font-b); }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
.stApp > div { background: var(--bg) !important; }

/* ══════════════════════════════════════════════════════════════════
   NAVIGATION BAR
══════════════════════════════════════════════════════════════════ */
.wc-nav {
  background: rgba(14, 23, 41, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--rim);
  padding: 0 1.5rem;
  height: 64px;
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
  font-size: 1.5rem;
  letter-spacing: .08em;
  color: #fff;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.wc-logo .bolt { color: #fbbf24; font-size: 1.8rem; }
.wc-logo .cast { color: var(--accent); }
.wc-nav-right { display: flex; align-items: center; gap: .5rem; }
.wc-nav-sep { width: 1px; height: 24px; background: var(--rim); margin: 0 .5rem; }
.wc-nav-btn {
  font-family: var(--font-h); font-weight: 700; font-size: .75rem;
  letter-spacing: .08em; text-transform: uppercase; padding: .4rem 1rem;
  border-radius: 6px; border: 1px solid transparent; cursor: pointer;
  background: transparent; color: var(--txt-dim); transition: all .15s;
  white-space: nowrap; text-decoration: none;
}
.wc-nav-btn:hover { background: var(--card); color: var(--txt); }
.wc-nav-btn.active-tab { background: rgba(59,130,246,.15); color: var(--accent); border-color: rgba(59,130,246,.3); }
.wc-nav-btn.active-land { background: rgba(59,130,246,.15); color: var(--accent); border-color: rgba(59,130,246,.3); }
.wc-nav-btn.active-sea { background: rgba(239,68,68,.12); color: var(--stop); border-color: rgba(239,68,68,.25); }

/* ══════════════════════════════════════════════════════════════════
   CONTROLS BAR
══════════════════════════════════════════════════════════════════ */
.wc-controls {
  background: var(--surface);
  border-bottom: 1px solid var(--rim);
  padding: 1rem 1.5rem;
}
.control-row { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
.control-group { display: flex; flex-direction: column; gap: .35rem; flex: 1; }
.control-label {
  font-family: var(--font-h); font-weight: 700; font-size: .65rem;
  letter-spacing: .12em; text-transform: uppercase; color: var(--txt-dim);
}
.control-input {
  background: var(--card); border: 1px solid var(--rim);
  border-radius: 6px; padding: .5rem .75rem;
  font-family: var(--font-b); font-size: .85rem; color: var(--txt);
  width: 100%;
}
.control-input:focus {
  outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(59,130,246,.2);
}
.btn-primary {
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  border: none; border-radius: 6px; padding: .5rem 1.25rem;
  font-family: var(--font-h); font-weight: 700; font-size: .75rem;
  letter-spacing: .08em; text-transform: uppercase; color: #fff;
  cursor: pointer; transition: all .15s;
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(239,68,68,.3); }

/* Terrain Selector - matching design */
.terrain-selector {
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 8px;
  padding: 0.5rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.terrain-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  background: transparent;
  border: none;
  font-family: var(--font-h);
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--txt-dim);
}
.terrain-option:hover {
  background: var(--surface);
}
.terrain-option.active {
  background: rgba(59,130,246,.2);
  color: var(--accent);
  border: 1px solid rgba(59,130,246,.3);
}

/* ══════════════════════════════════════════════════════════════════
   NOW CARD
══════════════════════════════════════════════════════════════════ */
.now-card {
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1rem;
}
.now-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 1rem;
}
.now-title {
  font-family: var(--font-h); font-weight: 900; font-size: .65rem;
  letter-spacing: .15em; text-transform: uppercase; color: var(--txt-dim);
}
.now-status {
  font-family: var(--font-h); font-weight: 900; font-size: 2rem;
  color: #fff; line-height: 1;
}
.now-metrics {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: .75rem;
  margin-bottom: 1rem;
}
.metric-box {
  background: var(--bg); border: 1px solid var(--rim);
  border-radius: 8px; padding: .75rem;
}
.metric-label {
  font-family: var(--font-h); font-weight: 700; font-size: .6rem;
  letter-spacing: .12em; text-transform: uppercase; color: var(--txt-dim);
  margin-bottom: .35rem;
}
.metric-value {
  font-family: var(--font-h); font-weight: 900; font-size: 1.75rem;
  line-height: 1;
}
.mv-safe { color: var(--safe); }
.mv-warn { color: var(--warn); }
.mv-stop { color: var(--stop); }
.mv-txt { color: var(--txt); }
.now-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: .75rem; border-top: 1px solid var(--rim);
  font-family: var(--font-m); font-size: .75rem; color: var(--txt-dim);
}

/* ══════════════════════════════════════════════════════════════════
   OPTIMAL WINDOW BANNER
══════════════════════════════════════════════════════════════════ */
.opt-banner {
  background: rgba(34,197,94,.08);
  border: 1px solid rgba(34,197,94,.3);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 1rem;
}
.opt-icon {
  width: 3rem; height: 3rem; border-radius: 50%;
  background: rgba(34,197,94,.15);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; flex-shrink: 0;
}
.opt-content { flex: 1; }
.opt-title {
  font-family: var(--font-h); font-weight: 900; font-size: .65rem;
  letter-spacing: .15em; text-transform: uppercase; color: var(--safe);
  margin-bottom: .25rem;
}
.opt-text {
  font-family: var(--font-h); font-weight: 700; font-size: 1.15rem;
  color: #fff; line-height: 1.2;
}
.opt-sub {
  font-size: .75rem; color: var(--txt-dim); margin-top: .25rem;
}
.opt-badge {
  background: var(--safe); color: #000;
  padding: .35rem .85rem; border-radius: 999px;
  font-family: var(--font-h); font-weight: 900; font-size: .7rem;
  letter-spacing: .08em; text-transform: uppercase;
}

/* ══════════════════════════════════════════════════════════════════
   LEGEND STRIP
══════════════════════════════════════════════════════════════════ */
.legend-strip {
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 10px;
  padding: .75rem 1rem;
  display: flex; flex-wrap: wrap; align-items: center; gap: 1.25rem;
  margin-bottom: 1rem;
}
.legend-title {
  font-family: var(--font-h); font-weight: 900; font-size: .6rem;
  letter-spacing: .15em; text-transform: uppercase; color: var(--txt-dim);
}
.legend-item {
  display: flex; align-items: center; gap: .5rem;
  font-family: var(--font-h); font-weight: 700; font-size: .75rem;
}
.legend-dot {
  width: .75rem; height: .75rem; border-radius: 50%; flex-shrink: 0;
}
.dot-safe { background: var(--safe); box-shadow: 0 0 8px rgba(34,197,94,.5); }
.dot-warn { background: var(--warn); box-shadow: 0 0 8px rgba(245,158,11,.5); }
.dot-stop { background: var(--stop); box-shadow: 0 0 8px rgba(239,68,68,.5); }

/* ══════════════════════════════════════════════════════════════════
   TABLE CONTROLS
══════════════════════════════════════════════════════════════════ */
.table-controls {
  display: flex; justify-content: space-between; align-items: center;
  padding: .75rem 0; margin-bottom: .5rem; flex-wrap: wrap; gap: 1rem;
}
.table-title {
  font-family: var(--font-h); font-weight: 900; font-size: 1.15rem;
  color: #fff;
}
.table-meta {
  font-size: .75rem; color: var(--txt-dim);
}
.segmented-control {
  display: flex; background: var(--bg); border: 1px solid var(--rim);
  border-radius: 999px; padding: 3px; gap: 2px;
}
.seg-btn {
  padding: .35rem 1rem; border-radius: 999px;
  font-family: var(--font-h); font-weight: 700; font-size: .7rem;
  letter-spacing: .08em; text-transform: uppercase;
  color: var(--txt-dim); border: none; cursor: pointer;
  background: transparent; transition: all .15s;
}
.seg-btn.active { background: var(--accent); color: #fff; }

/* ══════════════════════════════════════════════════════════════════
   FORECAST TABLE
══════════════════════════════════════════════════════════════════ */
.table-container {
  background: var(--card);
  border: 1px solid var(--rim);
  border-radius: 12px;
  overflow-x: auto;
  margin-top: 1rem;
}
.wc-table {
  width: 100%; border-collapse: collapse;
  font-family: var(--font-b); font-size: .85rem;
  min-width: 800px;
}
.wc-table thead tr {
  background: var(--surface);
}
.wc-table thead th {
  padding: .85rem .75rem; text-align: center;
  font-family: var(--font-h); font-weight: 900;
  font-size: .65rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--txt-dim);
  white-space: nowrap; border-bottom: 2px solid var(--rim);
}
.wc-table thead th.th-crane {
  color: var(--accent); background: rgba(59,130,246,.08);
  border-bottom: 3px solid rgba(59,130,246,.4);
}
.wc-table tbody tr {
  border-bottom: 1px solid rgba(30,47,74,.5);
  transition: background .1s;
}
.wc-table tbody tr:hover { background: rgba(59,130,246,.08); }
.wc-table tbody tr.day-break td { border-top: 2px solid var(--rim); }
.wc-table td {
  padding: .85rem .75rem; text-align: center; vertical-align: middle;
}
.td-time {
  font-family: var(--font-h); font-weight: 700; font-size: .95rem;
  color: var(--accent); text-align: left; white-space: nowrap;
}
.td-wind {
  font-family: var(--font-m); font-weight: 600; font-size: .85rem;
  line-height: 1.7;
}
.td-wind small {
  display: block; font-size: .7rem; opacity: .7; font-weight: 400;
}
.td-crane { background: rgba(59,130,246,.06); }
.td-safe { color: var(--safe); }
.td-warn { color: var(--warn); }
.td-stop { color: var(--stop); }
.td-dim { color: var(--txt-dim); }
.td-dir { font-family: var(--font-m); font-size: .8rem; color: var(--txt-dim); }
.rain-0 { background: transparent; }
.rain-1 { background: rgba(59,130,246,.06); }
.rain-2 { background: rgba(59,130,246,.12); }
.rain-3 { background: rgba(59,130,246,.2); }
.rain-4 { background: rgba(30,64,175,.35); }
.temp-badge {
  display: inline-block; padding: .25rem .5rem; border-radius: 6px;
  font-weight: 600; font-size: .8rem;
}

/* ══════════════════════════════════════════════════════════════════
   STATUS BADGES
══════════════════════════════════════════════════════════════════ */
.status-badge {
  display: inline-flex; align-items: center; gap: .35rem;
  padding: .25rem .65rem; border-radius: 999px;
  font-family: var(--font-h); font-weight: 700; font-size: .65rem;
  letter-spacing: .08em; text-transform: uppercase;
}
.sts-safe {
  background: rgba(34,197,94,.15); border: 1px solid rgba(34,197,94,.3);
  color: var(--safe);
}
.sts-warn {
  background: rgba(245,158,11,.15); border: 1px solid rgba(245,158,11,.3);
  color: var(--warn);
}
.sts-stop {
  background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3);
  color: var(--stop);
}

/* ══════════════════════════════════════════════════════════════════
   DISCLAIMER & INFO
══════════════════════════════════════════════════════════════════ */
.wc-disclaimer {
  background: rgba(8,15,31,.8);
  border: 1px solid var(--rim);
  border-radius: 8px;
  padding: .75rem 1rem;
  font-family: var(--font-b); font-size: .7rem;
  color: var(--txt-dim); line-height: 1.6;
  margin-top: 1rem;
}
.box-caution {
  background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.4);
  border-radius: 8px; padding: .75rem 1rem; font-size: .85rem; color: var(--warn);
}
.box-danger {
  background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.4);
  border-radius: 8px; padding: .75rem 1rem; font-size: .85rem; color: var(--stop);
}
.box-info {
  background: rgba(59,130,246,.1); border: 1px solid rgba(59,130,246,.3);
  border-radius: 8px; padding: .75rem 1rem; font-size: .85rem; color: var(--accent);
}

/* ══════════════════════════════════════════════════════════════════
   MOBILE RESPONSIVE
══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .wc-nav { padding: 0 1rem; height: 56px; }
  .wc-logo { font-size: 1.2rem; }
  .wc-logo .bolt { font-size: 1.4rem; }
  .wc-nav-btn { padding: .3rem .65rem; font-size: .65rem; }
  .hide-mobile { display: none !important; }
  .wc-table { font-size: .75rem; min-width: 650px; }
  .wc-table td { padding: .6rem .4rem; }
  .td-time { font-size: .8rem; }
  .control-row { flex-direction: column; align-items: stretch; }
  .control-group { width: 100%; }
  .table-controls { flex-direction: column; align-items: flex-start; }
  .segmented-control { width: 100%; justify-content: space-between; }
  .seg-btn { flex: 1; text-align: center; }
}
@media (max-width: 480px) {
  .td-time { font-size: .75rem; }
  .now-metrics { grid-template-columns: 1fr; }
  .opt-banner { flex-direction: column; text-align: center; }
}

/* ══════════════════════════════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
══════════════════════════════════════════════════════════════════ */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label {
  font-family: var(--font-h) !important; font-weight: 700 !important;
  font-size: .65rem !important; letter-spacing: .12em !important;
  text-transform: uppercase !important; color: var(--txt-dim) !important;
}
div[data-testid="stButton"] > button {
  font-family: var(--font-h) !important; font-weight: 700 !important;
  letter-spacing: .08em !important; text-transform: uppercase !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WIND_UNIT_FACTORS = {
    "m/s": (1.0, "m/s"), "knots": (1.9438, "kt"),
    "mph": (2.2369, "mph"), "km/h": (3.6, "km/h"), "Beaufort": (None, "Bft"),
}
TERRAIN = {
    "Open / Coastal":    {"alpha": 0.14, "factor": 1.00, "icon": "🌊"},
    "Industrial / Port": {"alpha": 0.22, "factor": 1.10, "icon": "🏭"},
    "Urban / City":      {"alpha": 0.28, "factor": 1.20, "icon": "🏙️"},
    "Woodland / Forest": {"alpha": 0.20, "factor": 1.15, "icon": "🌲"},
}
SAVED_LOCS_FILE = "forecast_logs/saved_locations.json"
DUR_MAP   = {"1D": 24, "3D": 72, "7D": 168, "MAX": 168}
DUR_OPTS  = list(DUR_MAP.keys())
RES_OPTS  = ["24H", "3H"]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def to_beaufort(ms):
    for i, t in enumerate([0.5,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,28.5,32.7]):
        if ms < t: return i
    return 12

def fmt_wind(ms, unit):
    if unit == "Beaufort": return f"{to_beaufort(ms)} Bft"
    factor, label = WIND_UNIT_FACTORS[unit]
    return f"{ms * factor:.1f} {label}"

def risk_level(gust_ms):
    if gust_ms <= 5.9:  return "safe"
    if gust_ms <= 14.0: return "warn"
    return "stop"

def risk_symbol(level):  return {"safe": "●", "warn": "⬡", "stop": "Ⓧ"}[level]
def risk_css(level):     return {"safe": "td-safe", "warn": "td-warn", "stop": "td-stop"}[level]

def status_badge(level):
    label = {"safe": "SAFE", "warn": "CAUTION", "stop": "STOP"}[level]
    return f'<span class="status-badge sts-{level}">{label}</span>'

def direction_arrow(deg):
    try:
        d = float(deg)
        if np.isnan(d): return "—"
        return ["↓","↙","←","↖","↑","↗","→","↘"][int((d + 22.5) / 45) % 8]
    except: return "—"

def apply_terrain(ws_10m, terrain_key, height):
    t = TERRAIN.get(terrain_key, TERRAIN["Open / Coastal"])
    return ws_10m * t["factor"] * ((height / 10) ** t["alpha"])

def fmt_temp(c, unit):
    return f"{c * 9/5 + 32:.0f}°F" if unit == "°F" else f"{c:.0f}°C"

def safe_float(val, default=0.0):
    try:
        if val is None or val is pd.NaT: return default
        f = float(val)
        return default if f != f else f
    except (TypeError, ValueError): return default

def temp_colour(t):
    if   t <= -3: return "#1565C0","#fff"
    elif t <=  0: return "#1976D2","#fff"
    elif t <=  5: return "#42A5F5","#000"
    elif t <= 10: return "#80DEEA","#000"
    elif t <= 15: return "#fff176","#000"
    elif t <= 20: return "#ffd54f","#000"
    elif t <= 25: return "#ffb74d","#000"
    else:         return "#ff8a65","#000"

def rain_row_class(mm):
    if mm == 0:   return "rain-0"
    if mm < 0.5:  return "rain-1"
    if mm < 2.0:  return "rain-2"
    if mm < 5.0:  return "rain-3"
    return "rain-4"

def rain_intensity(mm):
    if mm == 0: return "None"
    if mm < 0.5: return "Light"
    if mm < 2.0: return "Moderate"
    if mm < 5.0: return "Heavy"
    return "Extreme"

# ══════════════════════════════════════════════════════════════════════════════
# LOCATION
# ══════════════════════════════════════════════════════════════════════════════
def postcode_to_coords(pc):
    try:
        r = requests.get(f"https://api.postcodes.io/postcodes/{pc.replace(' ','')}", timeout=6)
        d = r.json()
        if d.get("status") == 200:
            return (d["result"]["latitude"], d["result"]["longitude"],
                    f"{pc.upper()} ({d['result']['admin_district']})")
    except Exception: pass
    return None, None, None

def place_to_coords(name):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": name, "format": "json", "limit": 1},
                         headers={"User-Agent": "Windcast/5.4"}, timeout=6)
        d = r.json()
        if d: return float(d[0]["lat"]), float(d[0]["lon"]), d[0].get("display_name","")[:70]
    except Exception: pass
    return None, None, None

def parse_search(query):
    q = query.strip()
    if not q: return None, None, None
    for sep in [";", ","]:
        if sep in q:
            parts = q.split(sep, 1)
            try:
                lat = float(parts[0].strip()); lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon, f"{lat:.4f}°N, {lon:.4f}°E"
            except ValueError: pass
    if re.match(r'^[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s*\d[A-Za-z]{2}$', q):
        return postcode_to_coords(q)
    return place_to_coords(q)

def load_saved():
    try:
        os.makedirs("forecast_logs", exist_ok=True)
        if os.path.exists(SAVED_LOCS_FILE):
            with open(SAVED_LOCS_FILE) as f: return json.load(f)
    except Exception: pass
    return []

def save_location(name, lat, lon, crane_h, terrain):
    locs = load_saved()
    locs = [l for l in locs if l.get("name") != name]
    locs.insert(0, {"name": name, "lat": lat, "lon": lon, "crane_h": crane_h, "terrain": terrain})
    try:
        with open(SAVED_LOCS_FILE, "w") as f: json.dump(locs[:12], f, indent=2)
    except Exception: pass

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_ecmwf_land(lat, lon, hours=168):
    url = "https://api.open-meteo.com/v1/forecast"
    params = [
        ("latitude", lat), ("longitude", lon),
        ("wind_speed_unit", "ms"), ("forecast_days", min(hours // 24 + 1, 7)),
        ("timezone", "auto"), ("models", "ecmwf_ifs025"),
        ("hourly", "wind_speed_10m"), ("hourly", "wind_gusts_10m"),
        ("hourly", "wind_direction_10m"), ("hourly", "temperature_2m"),
        ("hourly", "precipitation"), ("hourly", "cloud_cover"),
        ("hourly", "surface_pressure"), ("hourly", "visibility"),
        ("hourly", "relative_humidity_2m"),
    ]
    try:
        r = requests.get(url, params=params, timeout=15); r.raise_for_status()
        body = r.json()
        if body.get("error"):
            st.error(f"Open-Meteo: {body.get('reason', body)}"); return None, []
        h = body.get("hourly", {})
        times = h.get("time", [])
        if not times: return None, []
        n = len(times)
        df = pd.DataFrame({
            "time":       pd.to_datetime(times),
            "wind_speed": pd.to_numeric(h.get("wind_speed_10m",       [np.nan]*n), errors="coerce"),
            "wind_gust":  pd.to_numeric(h.get("wind_gusts_10m",       [np.nan]*n), errors="coerce"),
            "wind_dir":   pd.to_numeric(h.get("wind_direction_10m",   [np.nan]*n), errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m",       [np.nan]*n), errors="coerce"),
            "precip":     pd.to_numeric(h.get("precipitation",        [np.nan]*n), errors="coerce"),
            "cloud":      pd.to_numeric(h.get("cloud_cover",          [np.nan]*n), errors="coerce"),
            "pressure":   pd.to_numeric(h.get("surface_pressure",     [np.nan]*n), errors="coerce"),
            "visibility": pd.to_numeric(h.get("visibility",           [np.nan]*n), errors="coerce"),
            "humidity":   pd.to_numeric(h.get("relative_humidity_2m", [np.nan]*n), errors="coerce"),
        })
        df = df[df["time"] >= pd.Timestamp.now().floor("h")].reset_index(drop=True)
        return df, ["ECMWF IFS 0.25°"]
    except Exception as e:
        st.error(f"Fetch error: {e}"); return None, []

@st.cache_data(ttl=1800)
def fetch_offshore_wind(lat, lon, hours=168):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "hourly": ["wind_speed_10m","wind_gusts_10m","wind_direction_10m",
                       "temperature_2m","cloud_cover","precipitation","pressure_msl"],
            "models": "ecmwf_ifs04", "wind_speed_unit": "ms",
            "forecast_days": min(hours // 24 + 1, 7), "timezone": "UTC",
        }, timeout=12); r.raise_for_status()
        h = r.json().get("hourly", {}); times = h.get("time", [])
        if not times: return None
        n = len(times)
        df = pd.DataFrame({
            "time":       pd.to_datetime(times),
            "wind_speed": pd.to_numeric(h.get("wind_speed_10m",    [np.nan]*n), errors="coerce"),
            "wind_gust":  pd.to_numeric(h.get("wind_gusts_10m",    [np.nan]*n), errors="coerce"),
            "wind_dir":   pd.to_numeric(h.get("wind_direction_10m",[np.nan]*n), errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m",    [np.nan]*n), errors="coerce"),
            "cloud":      pd.to_numeric(h.get("cloud_cover",       [np.nan]*n), errors="coerce"),
            "precip":     pd.to_numeric(h.get("precipitation",     [np.nan]*n), errors="coerce"),
            "pressure":   pd.to_numeric(h.get("pressure_msl",      [np.nan]*n), errors="coerce"),
        })
        return df[df["time"] >= pd.Timestamp.now().floor("h")].reset_index(drop=True)
    except Exception as e:
        st.error(f"Wind fetch error: {e}"); return None

@st.cache_data(ttl=1800)
def fetch_offshore_marine(lat, lon, hours=168):
    try:
        r = requests.get("https://marine-api.open-meteo.com/v1/marine", params={
            "latitude": lat, "longitude": lon,
            "hourly": ["wave_height","wave_period","wave_direction",
                       "swell_wave_height","swell_wave_period","swell_wave_direction"],
            "forecast_days": min(hours // 24 + 1, 7), "timezone": "UTC",
        }, timeout=12); r.raise_for_status()
        h = r.json().get("hourly", {}); times = h.get("time", [])
        if not times: return None
        n = len(times)
        df = pd.DataFrame({
            "time":        pd.to_datetime(times),
            "hs":          pd.to_numeric(h.get("wave_height",          [np.nan]*n), errors="coerce"),
            "wave_period": pd.to_numeric(h.get("wave_period",          [np.nan]*n), errors="coerce"),
            "wave_dir":    pd.to_numeric(h.get("wave_direction",       [np.nan]*n), errors="coerce"),
            "swell_hs":    pd.to_numeric(h.get("swell_wave_height",    [np.nan]*n), errors="coerce"),
        })
        return df[df["time"] >= pd.Timestamp.now().floor("h")].reset_index(drop=True)
    except Exception as e:
        st.error(f"Marine fetch error: {e}"); return None

# ══════════════════════════════════════════════════════════════════════════════
# TABLE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def wind_cells(ws_10, wg_10, ws_h, wg_h, unit, crane_h):
    rl10 = risk_level(wg_10); rlH = risk_level(wg_h)
    return (
        f'<td class="td-wind"><span class="{risk_css(rl10)}">{risk_symbol(rl10)} {fmt_wind(wg_10,unit)}</span>'
        f'<small class="td-dim">W {fmt_wind(ws_10,unit)}</small></td>'
        f'<td class="td-wind td-crane"><span class="{risk_css(rlH)}">{risk_symbol(rlH)} {fmt_wind(wg_h,unit)}</span>'
        f'<small class="td-dim">W {fmt_wind(ws_h,unit)}</small></td>'
    )

def build_land_rows(df, crane_h, terrain, unit, temp_unit, hours, show_3h=False):
    rows = []; prev_day = None
    for _, row in df.head(hours).iterrows():
        ts = pd.to_datetime(row["time"])
        if show_3h and ts.hour % 3 != 0: continue
        ws = safe_float(row.get("wind_speed")); wg = safe_float(row.get("wind_gust"))
        ws_h = apply_terrain(ws, terrain, crane_h); wg_h = apply_terrain(wg, terrain, crane_h)
        tmp = safe_float(row.get("temperature")); prc = safe_float(row.get("precip"))
        cld = safe_float(row.get("cloud")); prs = safe_float(row.get("pressure"), 1013.0)
        wd  = row.get("wind_dir", np.nan)
        try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except: wd_f = np.nan
        day_str = ts.strftime("%Y-%m-%d"); db = " day-break" if day_str != prev_day else ""; prev_day = day_str
        tc, tf = temp_colour(tmp)
        rain_class = rain_row_class(prc)
        dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"
        
        rows.append(
            f'<tr class="{rain_class}{db}">'
            f'<td class="td-time">{ts.strftime("%a %d %b %H:%M")}</td>'
            + wind_cells(ws, wg, ws_h, wg_h, unit, crane_h)
            + f'<td class="td-dir">{dir_str}</td>'
            + f'<td class="temp-cell"><span class="temp-badge" style="background:{tc};color:{tf};">{fmt_temp(tmp,temp_unit)}</span></td>'
            + f'<td class="td-dim" style="font-family:var(--font-m);font-size:.75rem;">{prc:.1f}mm<br><small>{rain_intensity(prc)}</small></td>'
            + f'<td class="td-dim hide-mobile">{cld:.0f}%</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.75rem;">{prs:.0f} hPa</td>'
            + f'<td class="td-dim">{status_badge(risk_level(wg_h))}</td>'
            + '</tr>'
        )
    return rows

def build_offshore_rows(wind_df, marine_df, crane_h, unit, temp_unit, hours, show_3h=False):
    rows = []; prev_day = None
    ml = len(marine_df) if marine_df is not None else 0
    for i in range(min(hours, len(wind_df))):
        wrow = wind_df.iloc[i]; ts = pd.to_datetime(wrow["time"])
        if show_3h and ts.hour % 3 != 0: continue
        ws = safe_float(wrow.get("wind_speed")); wg = safe_float(wrow.get("wind_gust"))
        ws_h = ws * ((crane_h / 10) ** 0.11); wg_h = wg * ((crane_h / 10) ** 0.11)
        tmp = safe_float(wrow.get("temperature")); prc = safe_float(wrow.get("precip"))
        cld = safe_float(wrow.get("cloud")); prs = safe_float(wrow.get("pressure"), 1013.0)
        wd  = wrow.get("wind_dir", np.nan)
        try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except: wd_f = np.nan
        hs = wp = wd_w = sw = "—"
        if marine_df is not None and i < ml:
            m = marine_df.iloc[i]
            hs_f = safe_float(m.get("hs"), np.nan); wp_f = safe_float(m.get("wave_period"), np.nan)
            wdw_f= safe_float(m.get("wave_dir"), np.nan); sw_f = safe_float(m.get("swell_hs"), np.nan)
            hs   = f"{hs_f:.2f}m"  if not np.isnan(hs_f) else "—"
            wp   = f"{wp_f:.1f}s"  if not np.isnan(wp_f) else "—"
            wd_w = f"{direction_arrow(wdw_f)} {wdw_f:.0f}°" if not np.isnan(wdw_f) else "—"
            sw   = f"{sw_f:.2f}m"  if not np.isnan(sw_f) else "—"
        day_str = ts.strftime("%Y-%m-%d"); db = " day-break" if day_str != prev_day else ""; prev_day = day_str
        tc, tf = temp_colour(tmp)
        rain_class = rain_row_class(prc)
        dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"
        
        rows.append(
            f'<tr class="{rain_class}{db}">'
            f'<td class="td-time">{ts.strftime("%a %d %b %H:%M")}</td>'
            + wind_cells(ws, wg, ws_h, wg_h, unit, crane_h)
            + f'<td class="td-dir">{dir_str}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.75rem;">{hs}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.75rem;">{wp}</td>'
            + f'<td class="td-dir hide-mobile">{wd_w}</td>'
            + f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.75rem;">{sw}</td>'
            + f'<td class="temp-cell"><span class="temp-badge" style="background:{tc};color:{tf};">{fmt_temp(tmp,temp_unit)}</span></td>'
            + f'<td class="td-dim">{status_badge(risk_level(wg_h))}</td>'
            + '</tr>'
        )
    return rows

def land_header(crane_h):
    return (f'<tr><th style="text-align:left;">Date &amp; Time</th>'
            f'<th>Gust/Wind<br><small style="opacity:.6;">10m</small></th>'
            f'<th class="th-crane">Gust/Wind<br><small style="opacity:.8;">{crane_h}m ✦</small></th>'
            f'<th>Dir</th><th>Temp</th><th>Rain</th>'
            f'<th class="hide-mobile">Cloud</th><th class="hide-mobile">Press</th><th>Status</th></tr>')

def offshore_header(crane_h):
    return (f'<tr><th style="text-align:left;">Date &amp; Time</th>'
            f'<th>Gust/Wind<br><small style="opacity:.6;">10m</small></th>'
            f'<th class="th-crane">Gust/Wind<br><small style="opacity:.8;">{crane_h}m ✦</small></th>'
            f'<th>Dir</th>'
            f'<th class="hide-mobile">Hs (m)</th><th class="hide-mobile">Wave Pd</th>'
            f'<th class="hide-mobile">Wave Dir</th><th class="hide-mobile">Swell Hs</th>'
            f'<th>Temp</th><th>Status</th></tr>')

def render_table(rows, hdr):
    st.markdown(
        f'<div class="table-container"><table class="wc-table">'
        f'<thead>{hdr}</thead><tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# NOW CARD
# ══════════════════════════════════════════════════════════════════════════════
def render_now_card(df, crane_h, terrain, unit, mode):
    if df is None or df.empty: return
    row = df.iloc[0]
    ws  = safe_float(row.get("wind_speed")); wg = safe_float(row.get("wind_gust"))
    ws_h = apply_terrain(ws, terrain, crane_h) if mode=="land" else ws*((crane_h/10)**0.11)
    wg_h = apply_terrain(wg, terrain, crane_h) if mode=="land" else wg*((crane_h/10)**0.11)
    rl   = risk_level(wg_h); rl10 = risk_level(wg)
    tmp  = safe_float(row.get("temperature")); prs = safe_float(row.get("pressure"), 1013.0)
    wd   = row.get("wind_dir", np.nan)
    try: wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
    except: wd_f = np.nan
    dir_str = f"{direction_arrow(wd_f)} {wd_f:.0f}°" if not np.isnan(wd_f) else "—"
    lbl = {"safe": "SAFE", "warn": "CAUTION", "stop": "STOP"}[rl]
    
    st.markdown(f"""
<div class="now-card">
  <div class="now-header">
    <div>
      <div class="now-title">Live Status</div>
      <div class="now-status">NOW</div>
    </div>
    <span class="status-badge sts-{rl}">{lbl}</span>
  </div>
  <div class="now-metrics">
    <div class="metric-box">
      <div class="metric-label">Gust @10m</div>
      <div class="metric-value mv-{rl10}">{fmt_wind(wg,unit)}</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Gust @{crane_h}m ✦</div>
      <div class="metric-value mv-{rl}">{fmt_wind(wg_h,unit)}</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Wind @{crane_h}m ✦</div>
      <div class="metric-value mv-txt">{fmt_wind(ws_h,unit)}</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Direction</div>
      <div style="font-family:var(--font-m);font-weight:700;font-size:1.1rem;color:var(--accent);padding-top:.1rem;">{dir_str}</div>
    </div>
  </div>
  <div class="now-footer">
    <span>{fmt_temp(tmp,"°C")}</span><span>{prs:.0f} hPa</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTIMAL WINDOW
# ══════════════════════════════════════════════════════════════════════════════
def render_optimal_window(df, crane_h, terrain, mode):
    if df is None or df.empty: return
    windows = []; cur = None
    for _, row in df.head(72).iterrows():
        wg = safe_float(row.get("wind_gust"))
        wg_h = apply_terrain(wg,terrain,crane_h) if mode=="land" else wg*((crane_h/10)**0.11)
        ts = pd.to_datetime(row["time"])
        if risk_level(wg_h) == "safe":
            if cur is None: cur = ts
        else:
            if cur is not None: windows.append((cur, ts - pd.Timedelta(hours=1))); cur = None
    if cur is not None: windows.append((cur, df.iloc[-1]["time"]))
    if windows:
        s, e = windows[0]
        msg   = f"Safe to lift {pd.to_datetime(s).strftime('%H:%M')}–{pd.to_datetime(e).strftime('%H:%M')} (next 72h window)"
        badge = '<span class="opt-badge">GO</span>'
    else:
        msg   = "No safe window found in the next 72h. Review conditions."
        badge = '<span class="opt-badge" style="background:var(--stop);color:#fff;">NO-GO</span>'
    st.markdown(f"""
<div class="opt-banner">
  <div class="opt-icon">📅</div>
  <div class="opt-content">
    <div class="opt-title">Optimal Lift Window</div>
    <div class="opt-text">{msg}</div>
    <div class="opt-sub">Crane {crane_h}m · Gust threshold ≤ 5.9 m/s</div>
  </div>{badge}
</div>""", unsafe_allow_html=True)

def render_legend():
    st.markdown("""
<div class="legend-strip">
  <span class="legend-title">Legend</span>
  <span class="legend-item"><span class="legend-dot dot-safe"></span><span style="color:var(--safe);">SAFE</span> <span style="color:var(--txt-dim);font-weight:400;">≤ 5.9 m/s</span></span>
  <span class="legend-item"><span class="legend-dot dot-warn"></span><span style="color:var(--warn);">CAUTION</span> <span style="color:var(--txt-dim);font-weight:400;">6–14 m/s</span></span>
  <span class="legend-item"><span class="legend-dot dot-stop"></span><span style="color:var(--stop);">STOP</span> <span style="color:var(--txt-dim);font-weight:400;">&gt; 14 m/s</span></span>
  <span class="legend-item" style="margin-left:auto;"><span style="font-weight:400;color:var(--txt-dim);font-size:.7rem;">Row tint = rain intensity</span></span>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main():
    defaults = {
        "disclaimer_ack": False,
        "active_tab":     "forecast",
        "mode":           "land",
        "crane_h":        40,
        "lat":            None,
        "lon":            None,
        "loc_name":       "",
        "wc_dur":         "1D",
        "wc_res":         "24H",
        "terrain":        "Open / Coastal",
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

    # URL params → session state
    params = st.query_params
    if st.session_state.lat is None and "lat" in params and "lon" in params:
        try:
            st.session_state.lat      = float(params["lat"])
            st.session_state.lon      = float(params["lon"])
            st.session_state.loc_name = f"{st.session_state.lat:.4f}°N, {st.session_state.lon:.4f}°E"
            if "h"    in params: st.session_state.crane_h = max(10, min(250, int(params["h"])))
            if "mode" in params and params["mode"] in ("land","offshore"): st.session_state.mode = params["mode"]
        except Exception: pass

    active_tab = st.session_state.active_tab
    mode       = st.session_state.mode

    # ══ NAV BAR ═══════════════════════════════════════════════════════════════
    fc_cls   = "active-tab"  if active_tab == "forecast" else ""
    inf_cls  = "active-tab"  if active_tab == "info"     else ""
    land_cls = "active-land" if mode == "land"           else ""
    sea_cls  = "active-sea"  if mode == "offshore"       else ""

    st.markdown(f"""
<div class="wc-nav">
  <div class="wc-logo"><span class="bolt">⚡</span> Wind<span class="cast">cast</span></div>
  <div class="wc-nav-right">
    <button class="wc-nav-btn {fc_cls}" onclick="window.location.href='?tab=forecast&mode={mode}'">🌤️ Forecast</button>
    <button class="wc-nav-btn {inf_cls}" onclick="window.location.href='?tab=info&mode={mode}'">ℹ️ Info</button>
    <div class="wc-nav-sep"></div>
    <button class="wc-nav-btn {land_cls}" onclick="window.location.href='?tab={active_tab}&mode=land'">🏗️ Land</button>
    <button class="wc-nav-btn {sea_cls}"  onclick="window.location.href='?tab={active_tab}&mode=offshore'">⚓ Sea</button>
  </div>
</div>
""", unsafe_allow_html=True)

    # Apply URL-driven nav changes
    if "tab" in params:
        t = params["tab"]
        if t in ("forecast","info") and t != st.session_state.active_tab:
            st.session_state.active_tab = t; active_tab = t
    if "mode" in params:
        m = params["mode"]
        if m in ("land","offshore") and m != st.session_state.mode:
            st.session_state.mode = m; mode = m
            for k in ["df_cache","marine_cache","fetch_time"]:
                st.session_state.pop(k, None)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    if not st.session_state.disclaimer_ack:
        st.markdown('<div style="padding:2rem;max-width:700px;">', unsafe_allow_html=True)
        st.warning(
            "⚠️ **Planning Tool — Regulatory Notice**\n\n"
            "Windcast provides forecast data for lift planning purposes only. "
            "It does **not** replace a calibrated on-site anemometer. "
            "The lifting supervisor remains solely responsible for all Go/No-Go decisions "
            "under **BS 7121-1:2016**, **LOLER 1998**, and **HSE PM55**.")
        if st.checkbox(
            "I understand this forecast is for planning purposes only. "
            "I will verify with a calibrated on-site anemometer before any lifting operation.",
            key="disclaimer_checkbox"):
            st.session_state.disclaimer_ack = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if active_tab == "info":
        st.markdown('<div style="padding:2rem;max-width:900px;">', unsafe_allow_html=True)
        st.markdown("## ℹ️ About Windcast")
        st.markdown("""
Built between jobs, out of sheer frustration with inaccurate site wind forecasts. My wife — a UX designer — pushed me to make it a real app. Six months later, here it is.

### 🎯 What It Does
- **ECMWF IFS 0.25°** — professional-grade model
- **BS 7121 height correction** + terrain factor
- **Colour-coded Go/No-Go** — SAFE ● CAUTION ⬡ STOP Ⓧ
- Built by a lifting supervisor, not a software company

### 📋 How To Use
1. Enter your location — UK postcode, place name, or lat ; lon coordinates
2. Set crane height. Switch Land / Sea using the toggle in the nav bar
3. For Land: choose terrain type — drives the BS 7121 height correction
4. Click Get Forecast — hourly table loads, wind corrected to your crane height
5. Use the duration toggle (1D / 3D / 7D / MAX) and resolution toggle (24H / 3H)
6. Always verify with a calibrated on-site anemometer before any lifting operation

### 🎨 Colour Legend
- **● SAFE** — Gust ≤ 5.9 m/s — Proceed with lift plan
- **⬡ CAUTION** — 6–14 m/s — Enhanced monitoring. Review crane wind rating
- **Ⓧ STOP** — > 14 m/s — Do not commence lifting operations

### 🪤 Where's The Catch?
Open-Meteo free tier — full ECMWF IFS resolution for 7 days, updated every 6 hours. This is not a replacement for your anemometer. It never will be.
""")
        c1, c2 = st.columns(2)
        with c1: st.link_button("☕  Support Windcast on Ko-fi", KOFI_URL, use_container_width=True)
        with c2: st.link_button("📝  Found an error? Tell me here.", FEEDBACK_URL, use_container_width=True)
        st.markdown(f"""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006. Open-Meteo ECMWF IFS 0.25°. v5.4
</div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # FORECAST PAGE
    # ══════════════════════════════════════════════════════════════════════════
    terrain_keys  = list(TERRAIN.keys())

    # ── Controls bar ──────────────────────────────────────────────────────────
    st.markdown('<div class="wc-controls">', unsafe_allow_html=True)
    st.markdown('<div class="control-row">', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns([2.5, 0.8, 1.5, 0.8, 0.6, 0.8])

    with col1:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Location</div>', unsafe_allow_html=True)
        search_val = st.text_input("Location",
            value=st.session_state.loc_name if st.session_state.lat else "",
            placeholder="Postcode · Place name · lat ; lon",
            key="search_input", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Height (m)</div>', unsafe_allow_html=True)
        crane_h = st.number_input("Height", min_value=10, max_value=250,
                                   value=st.session_state.crane_h, step=5,
                                   key="crane_num", label_visibility="collapsed")
        st.session_state.crane_h = crane_h
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        if mode == "land":
            st.markdown('<div class="control-group">', unsafe_allow_html=True)
            st.markdown('<div class="control-label">Terrain</div>', unsafe_allow_html=True)
            # Custom terrain selector using selectbox with icons
            terrain_options = [f"{TERRAIN[t]['icon']} {t}" for t in terrain_keys]
            current_idx = terrain_keys.index(st.session_state.terrain)
            ter_choice = st.selectbox("Terrain", terrain_options, index=current_idx, key="terrain_sel", label_visibility="collapsed")
            terrain = terrain_keys[terrain_options.index(ter_choice)]
            st.session_state.terrain = terrain
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            terrain = "Open / Coastal"

    with col4:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Wind Units</div>', unsafe_allow_html=True)
        wind_unit = st.selectbox("Wind Units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Temp</div>', unsafe_allow_html=True)
        temp_unit = st.selectbox("Temp", ["°C","°F"], key="temp_unit", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with col6:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        save_btn = st.button("📌", key="save_btn", help="Save this site", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Second row for fetch button
    st.markdown('<div class="control-row" style="justify-content:flex-end;">', unsafe_allow_html=True)
    fetch_btn = st.button("🌤️ GET FORECAST", key="fetch_btn", use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Resolve location ──────────────────────────────────────────────────────
    lat = st.session_state.lat; lon = st.session_state.lon; loc_name = st.session_state.loc_name
    if search_val and (search_val != loc_name or lat is None):
        with st.spinner("Looking up location…"):
            lat_new, lon_new, name_new = parse_search(search_val)
        if lat_new:
            lat = lat_new; lon = lon_new; loc_name = name_new
            st.session_state.lat = lat; st.session_state.lon = lon; st.session_state.loc_name = loc_name
        else:
            st.error("Location not found. Try a UK postcode, place name, or 'lat ; lon'."); return

    if save_btn and lat:
        save_location(loc_name[:40], lat, lon, crane_h, terrain)
        st.success(f"✅ Saved: {loc_name[:40]}")

    saved = load_saved()
    if saved:
        picked = st.selectbox("📍 Load saved site", ["— select —"] + [l["name"] for l in saved], key="load_saved")
        if picked != "— select —":
            loc = next(l for l in saved if l["name"] == picked)
            st.session_state.lat = loc["lat"]; st.session_state.lon = loc["lon"]
            st.session_state.loc_name = loc["name"]; st.session_state.crane_h = loc.get("crane_h", crane_h)
            st.session_state.terrain = loc.get("terrain", terrain)
            st.rerun()

    if lat is None:
        st.markdown("""<div class="box-info" style="margin:1.5rem;">
        👆 Enter a location above and click <strong>Get Forecast</strong>.<br>
        UK postcodes (e.g. <code>RG12 1BE</code>), place names, or coordinates (<code>51.08 ; -1.29</code>).
        </div>""", unsafe_allow_html=True); return

    # ── Fetch ─────────────────────────────────────────────────────────────────
    if fetch_btn:
        st.query_params.update({"lat": f"{lat:.4f}", "lon": f"{lon:.4f}", "h": str(crane_h), "mode": mode})
        fetch_ecmwf_land.clear(); fetch_offshore_wind.clear(); fetch_offshore_marine.clear()
        for k in ["df_cache","marine_cache","fetch_time","models_used"]:
            st.session_state.pop(k, None)

    if fetch_btn or "df_cache" not in st.session_state:
        if mode == "land":
            with st.spinner("Fetching ECMWF IFS forecast…"):
                df, models_used = fetch_ecmwf_land(lat, lon, 168)
            if df is None or df.empty:
                st.error("Weather model failed to respond."); return
            st.session_state.df_cache = df; st.session_state.models_used = models_used
            st.session_state.marine_cache = None
        else:
            with st.spinner("Fetching ECMWF wind + Marine data…"):
                df = fetch_offshore_wind(lat, lon, 168); marine = fetch_offshore_marine(lat, lon, 168)
            if df is None or df.empty:
                st.error("Failed to fetch wind data."); return
            st.session_state.df_cache = df; st.session_state.marine_cache = marine
        st.session_state.fetch_time = datetime.now(timezone.utc)

    df      = st.session_state.get("df_cache")
    marine  = st.session_state.get("marine_cache")
    fetch_t = st.session_state.get("fetch_time", datetime.now(timezone.utc))
    if df is None or df.empty:
        st.error("No forecast data."); return

    # ── NOW card + optimal window + legend ────────────────────────────────────
    st.markdown('<div style="padding:1.5rem;">', unsafe_allow_html=True)
    
    col_now, col_right = st.columns([1, 2.5])
    with col_now:
        render_now_card(df, crane_h, terrain, wind_unit, mode)
    with col_right:
        render_optimal_window(df, crane_h, terrain, mode)
        render_legend()
        if mode == "offshore" and marine is not None and not marine.empty:
            hs_now = safe_float(marine.iloc[0].get("hs"))
            if hs_now >= 2.5:
                cls = "box-danger" if hs_now >= 4.0 else "box-caution"
                st.markdown(f'<div class="{cls}">⚓ <strong>Wave Height Warning:</strong> Hs = {hs_now:.2f}m</div>',
                            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Table controls ────────────────────────────────────────────────────────
    st.markdown('<div style="padding:0 1.5rem;">', unsafe_allow_html=True)
    
    updated_str = fetch_t.strftime("%H:%M") if fetch_t else "--:--"
    mode_src    = "ECMWF IFS 0.25°" if mode == "land" else "ECMWF Marine"
    
    # Handle duration/resolution from URL or session
    if "dur" in st.query_params:
        d = st.query_params["dur"]
        if d in DUR_OPTS: st.session_state.wc_dur = d
    if "res" in st.query_params:
        r = st.query_params["res"]
        if r in RES_OPTS: st.session_state.wc_res = r
    
    st.markdown(f"""
<div class="table-controls">
  <div>
    <div class="table-title">Forecast</div>
    <div class="table-meta">{loc_name[:40]} · {updated_str} UTC · {mode_src}</div>
  </div>
  <div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap;">
    <div class="segmented-control">
      <button class="seg-btn {'active' if st.session_state.wc_dur=='1D' else ''}" onclick="location.href='?dur=1D'">1D</button>
      <button class="seg-btn {'active' if st.session_state.wc_dur=='3D' else ''}" onclick="location.href='?dur=3D'">3D</button>
      <button class="seg-btn {'active' if st.session_state.wc_dur=='7D' else ''}" onclick="location.href='?dur=7D'">7D</button>
      <button class="seg-btn {'active' if st.session_state.wc_dur=='MAX' else ''}" onclick="location.href='?dur=MAX'">MAX</button>
    </div>
    <div class="segmented-control">
      <button class="seg-btn {'active' if st.session_state.wc_res=='24H' else ''}" onclick="location.href='?res=24H'">24H</button>
      <button class="seg-btn {'active' if st.session_state.wc_res=='3H' else ''}" onclick="location.href='?res=3H'">3H</button>
    </div>
    <button class="btn-primary" style="padding:.4rem .85rem;">📄 PDF</button>
    <button class="btn-primary" style="padding:.4rem .85rem;background:var(--surface);border:1px solid var(--rim);">🔗 Share</button>
  </div>
</div>
""", unsafe_allow_html=True)
    
    forecast_hours = DUR_MAP[st.session_state.wc_dur]
    show_3h = (st.session_state.wc_res == "3H")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Table ─────────────────────────────────────────────────────────────────
    if mode == "land":
        rows = build_land_rows(df, crane_h, terrain, wind_unit, temp_unit, forecast_hours, show_3h)
        hdr  = land_header(crane_h)
    else:
        rows = build_offshore_rows(df, marine, crane_h, wind_unit, temp_unit, forecast_hours, show_3h)
        hdr  = offshore_header(crane_h)

    st.markdown('<div style="padding:0 1.5rem 1.5rem 1.5rem;">', unsafe_allow_html=True)
    render_table(rows, hdr)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006. Open-Meteo ECMWF IFS 0.25°. v5.4
&nbsp;·&nbsp;<a href="{FEEDBACK_URL}" target="_blank" style="color:var(--txt-dim);">📝 Found an error? Tell me here.</a>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
