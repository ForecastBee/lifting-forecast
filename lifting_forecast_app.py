"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   WINDCAST — Precision Lifting Weather Forecast  v5.0                       ║
║   BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006                       ║
║   Source: ECMWF IFS 0.25° via Open-Meteo (free tier)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests, json, os, re
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import qrcode
from io import BytesIO
from suntime import Sun

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Windcast",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
if "disclaimer_ack" not in st.session_state:
    st.session_state.disclaimer_ack = False
for k, v in [("mode", "land"), ("crane_h", 40), ("lat", None), ("lon", None), 
             ("loc_name", ""), ("fdays", 1), ("wind_unit", "m/s"), ("temp_unit", "°C"), 
             ("terrain", "Open / Coastal"), ("theme", "system"), ("view_mode", "24h")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WIND_UNIT_FACTORS = {
    "m/s": (1.0, "m/s"),
    "knots": (1.9438, "kt"),
    "mph": (2.2369, "mph"),
    "km/h": (3.6, "km/h"),
    "Beaufort": (None, "Bft"),
}

TERRAIN = {
    "Open / Coastal": {"alpha": 0.14, "factor": 1.00, "icon": "🏖️"},
    "Industrial / Port": {"alpha": 0.22, "factor": 1.10, "icon": "🏭"},
    "Urban / City": {"alpha": 0.28, "factor": 1.20, "icon": "🏙️"},
    "Woodland / Forest": {"alpha": 0.20, "factor": 1.15, "icon": "🌲"},
}

# ══════════════════════════════════════════════════════════════════════════════
# RESPONSIVE CSS
# ══════════════════════════════════════════════════════════════════════════════
def get_css():
    return """
<style>
/* ── Base Reset ── */
#MainMenu, header, footer {visibility: hidden;}
section[data-testid="stSidebar"] {display: none !important;}
.main .block-container {padding: 0; max-width: 100%;}

/* ── Theme Support ── */
body.theme-light {background: #f8fafc; color: #1e293b;}
body.theme-dark {background: #0b1326; color: #dae2fd;}

/* ── Header ── */
.app-header {
    background: #131b2e;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2d3449;
    position: sticky;
    top: 0;
    z-index: 100;
}
.header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.header-nav {display: flex; gap: 1rem; align-items: center;}
.nav-link {
    background: none;
    border: none;
    color: #94a3b8;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    transition: all 0.2s;
}
.nav-link:hover {background: #31394d; color: #fff;}

/* ── Control Section ── */
.control-section {
    background: #171f33;
    padding: 1rem;
    margin: 1rem;
    border-radius: 0.75rem;
}

/* ── Search Container ── */
.search-container {position: relative; margin-bottom: 0.75rem;}
.search-input {
    width: 100%;
    background: #222a3d;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 3rem 0.75rem 1rem;
    color: #dae2fd;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
}
.search-btn {
    position: absolute;
    right: 0.25rem;
    top: 50%;
    transform: translateY(-50%);
    background: #ee9800;
    border: none;
    border-radius: 0.375rem;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}

/* ── Crane Widget ── */
.crane-widget {
    background: #222a3d;
    padding: 0.75rem 1rem;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}
.crane-label {
    font-size: 0.625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #c2c6d6;
}
.crane-slider {
    flex: 1;
    height: 0.375rem;
    background: #060e20;
    border-radius: 0.1875rem;
    outline: none;
}
.crane-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: #4d8eff;
    min-width: 2.5rem;
}

/* ── Toggle Rows ── */
.toggle-row {
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    scrollbar-width: none;
    margin-bottom: 0.5rem;
}
.toggle-row::-webkit-scrollbar {display: none;}
.toggle-group {
    background: #060e20;
    border-radius: 9999px;
    padding: 0.25rem;
    display: flex;
    flex: 1;
    min-width: 100px;
    height: 2.75rem;
    align-items: center;
}
.toggle-btn {
    flex: 1;
    border: none;
    background: transparent;
    color: #c2c6d6;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 9999px;
    cursor: pointer;
    transition: all 0.2s;
}
.toggle-btn.active {
    background: #4d8eff;
    color: #00285d;
}

/* ── NOW Card ── */
.now-card {
    background: #2d3449;
    padding: 1rem;
    border-radius: 0.75rem;
    margin: 1rem;
}
.now-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 1rem;
}
.now-title {
    font-size: 0.625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
}
.now-status {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #4ae176;
}
.now-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.now-stat {
    background: #060e20;
    padding: 0.75rem;
    border-radius: 0.5rem;
}
.now-stat-label {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #c2c6d6;
    margin-bottom: 0.25rem;
}
.now-stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 1.5rem;
    color: #4ae176;
}
.now-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.75rem;
    border-top: 1px solid #424754;
}

/* ── Optimal Window Banner ── */
.optimal-banner {
    background: rgba(74, 225, 118, 0.1);
    border: 1px solid rgba(74, 225, 118, 0.3);
    padding: 1rem;
    border-radius: 0.75rem;
    margin: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.optimal-icon {
    width: 2.5rem;
    height: 2.5rem;
    background: rgba(74, 225, 118, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.optimal-content {flex: 1;}
.optimal-label {
    font-size: 0.625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4ae176;
}
.optimal-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: #fff;
}

/* ── Forecast Container ── */
.forecast-container {
    background: #171f33;
    border-radius: 0.75rem;
    overflow: hidden;
    margin: 1rem;
}
.forecast-header-row {
    background: #31394d;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #424754;
}
.forecast-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.125rem;
    color: #fff;
}
.duration-toggles {
    display: flex;
    gap: 0.25rem;
    background: #060e20;
    padding: 0.25rem;
    border-radius: 9999px;
}
.duration-btn {
    padding: 0.375rem 0.75rem;
    border: none;
    background: transparent;
    color: #c2c6d6;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 9999px;
    cursor: pointer;
}
.duration-btn.active {
    background: #4d8eff;
    color: #00285d;
}

/* ── Forecast Table Header ── */
.table-header {
    display: grid;
    grid-template-columns: 3.5rem 1fr 1fr 2.5rem 2.5rem 2.5rem;
    padding: 0.5rem 1rem;
    background: #222a3d;
    font-size: 0.625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
    border-bottom: 1px solid #424754;
}

/* ── Forecast Rows ── */
.forecast-row {
    display: grid;
    grid-template-columns: 3.5rem 1fr 1fr 2.5rem 2.5rem 2.5rem;
    padding: 1rem;
    border-bottom: 1px solid #2d3449;
    background: #131b2e;
    align-items: center;
}
.forecast-row:nth-child(even) {background: #060e20;}
.forecast-row.caution {
    background: rgba(255, 185, 95, 0.1);
    border-left: 3px solid #ffb95f;
}
.forecast-row.stop {
    background: rgba(255, 180, 171, 0.1);
    border-left: 3px solid #ffb4ab;
}

.time-cell {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: #dae2fd;
}
.wind-cell {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
}
.wind-label {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #c2c6d6;
}
.wind-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 1rem;
}
.wind-value.safe {color: #4ae176;}
.wind-value.caution {color: #ffb95f;}
.wind-value.stop {color: #ffb4ab;}
.dir-cell, .temp-cell, .prec-cell {
    text-align: center;
    font-size: 0.75rem;
    font-weight: 700;
}
.status-indicator {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
    margin: 0 auto;
    box-shadow: 0 0 8px currentColor;
}
.status-safe {background: #4ae176; color: #4ae176;}
.status-caution {background: #ffb95f; color: #ffb95f;}
.status-stop {background: #ffb4ab; color: #ffb4ab;}

/* ── Legend Bar ── */
.legend-bar {
    background: #2d3449;
    padding: 1rem;
    border-radius: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem;
}
.legend-title {
    font-size: 0.625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
}
.legend-status {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
}
.legend-items {display: flex; gap: 1rem;}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.625rem;
    font-weight: 700;
}

/* ── Info Section ── */
.info-section {
    background: #171f33;
    padding: 1.5rem;
    border-radius: 0.75rem;
    margin: 1rem;
}
.info-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.125rem;
    color: #fff;
    margin-bottom: 1rem;
}
.info-content {
    color: #c2c6d6;
    line-height: 1.6;
}

/* ── Bottom Nav ── */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(19, 27, 46, 0.95);
    backdrop-filter: blur(12px);
    border-top: 1px solid #31394d;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 100;
}
.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
    padding: 0.5rem 1.5rem;
    border-radius: 9999px;
}
.nav-item.active {
    background: #3b82f6;
    color: white;
}
.nav-item:hover {color: #fff;}
.nav-label {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Export/Share Modal ── */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
}
.modal-content {
    background: #171f33;
    padding: 1.5rem;
    border-radius: 1rem;
    max-width: 90%;
    width: 400px;
}
.modal-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: #fff;
    margin-bottom: 1rem;
}
.modal-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: #222a3d;
    border-radius: 0.5rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
}
.modal-option:hover {background: #2d3449;}

/* ── Responsive ── */
@media (max-width: 768px) {
    .table-header, .forecast-row {
        grid-template-columns: 3rem 1fr 2rem 2rem 2rem;
    }
    .wind-cell {flex-direction: row; gap: 0.25rem; align-items: baseline;}
    .wind-label {display: none;}
    .now-grid {grid-template-columns: 1fr;}
    .legend-bar {flex-direction: column; gap: 1rem; align-items: flex-start;}
    .header-title {font-size: 1rem;}
}

@media (min-width: 769px) {
    .table-header, .forecast-row {
        grid-template-columns: 4rem 1.5fr 1.5fr 3rem 3rem 3rem 3rem;
    }
    .control-section {
        display: grid;
        grid-template-columns: 1fr 300px;
        gap: 1rem;
    }
}
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def fmt_wind(ms: float, unit: str) -> str:
    if unit == "Beaufort":
        thresholds = [0.5,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,28.5,32.7]
        for i, t in enumerate(thresholds):
            if ms < t: return f"{i}"
        return "12"
    factor, label = WIND_UNIT_FACTORS.get(unit, (1.0, "m/s"))
    return f"{ms * factor:.1f}"

def risk_status(gust_ms: float) -> tuple:
    if gust_ms <= 5.9:
        return "safe", "●", "#4ae176", "SAFE"
    elif gust_ms <= 14.0:
        return "caution", "⚠", "#ffb95f", "CAUTION"
    else:
        return "stop", "Ⓧ", "#ffb4ab", "STOP"

def direction_arrow(deg) -> str:
    try:
        d = float(deg)
        if np.isnan(d): return "—"
        arrows = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"]
        return arrows[int((d + 22.5) / 45) % 8]
    except:
        return "—"

def apply_terrain(ws_10m: float, terrain_key: str, height: float) -> float:
    t = TERRAIN.get(terrain_key, TERRAIN["Open / Coastal"])
    return ws_10m * t["factor"] * ((height / 10) ** t["alpha"])

def safe_float(val, default=0.0):
    try:
        if val is None or val is pd.NaT: return default
        f = float(val)
        return default if f != f else f
    except:
        return default

def get_weather_icon(cloud: float, precip: float) -> str:
    if precip > 2: return "🌧️"
    elif precip > 0: return "☁️"
    elif cloud > 70: return "☁️"
    elif cloud > 30: return "⛅"
    else: return "☀️"

def parse_location(query: str):
    """Parse location from search query"""
    q = query.strip()
    if not q:
        return None, None, None
    
    # Lat;Lon
    for sep in [";", ","]:
        if sep in q:
            parts = q.split(sep, 1)
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon, f"{lat:.2f}°N, {lon:.2f}°E"
            except:
                pass
    
    # UK Postcode
    if re.match(r'^[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s*\d[A-Za-z]{2}$', q):
        try:
            r = requests.get(f"https://api.postcodes.io/postcodes/{q.replace(' ','')}", timeout=6)
            d = r.json()
            if d.get("status") == 200:
                return (d["result"]["latitude"], d["result"]["longitude"],
                       f"{q.upper()} ({d['result']['admin_district']})")
        except:
            pass
    
    # Place name
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                        params={"q": q, "format": "json", "limit": 1},
                        headers={"User-Agent": "Windcast/5.0"}, timeout=6)
        d = r.json()
        if d:
            return float(d[0]["lat"]), float(d[0]["lon"]), d[0].get("display_name","")[:50]
    except:
        pass
    
    return None, None, None

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_forecast(lat: float, lon: float, hours: int = 168):
    url = "https://api.open-meteo.com/v1/forecast"
    params = [
        ("latitude", lat), ("longitude", lon),
        ("wind_speed_unit", "ms"), ("forecast_days", min(hours // 24 + 1, 7)),
        ("timezone", "auto"), ("models", "ecmwf_ifs025"),
        ("hourly", "wind_speed_10m"), ("hourly", "wind_gusts_10m"),
        ("hourly", "wind_direction_10m"), ("hourly", "temperature_2m"),
        ("hourly", "precipitation"), ("hourly", "cloud_cover"),
        ("hourly", "surface_pressure"),
    ]
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            return None
        
        h = body.get("hourly", {})
        times = h.get("time", [])
        n = len(times)
        
        df = pd.DataFrame({
            "time": pd.to_datetime(times),
            "wind_speed": pd.to_numeric(h.get("wind_speed_10m", [np.nan]*n), errors="coerce"),
            "wind_gust": pd.to_numeric(h.get("wind_gusts_10m", [np.nan]*n), errors="coerce"),
            "wind_dir": pd.to_numeric(h.get("wind_direction_10m", [np.nan]*n), errors="coerce"),
            "temperature": pd.to_numeric(h.get("temperature_2m", [np.nan]*n), errors="coerce"),
            "precip": pd.to_numeric(h.get("precipitation", [np.nan]*n), errors="coerce"),
            "cloud": pd.to_numeric(h.get("cloud_cover", [np.nan]*n), errors="coerce"),
            "pressure": pd.to_numeric(h.get("surface_pressure", [np.nan]*n), errors="coerce"),
        })
        
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # Inject CSS
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-header">
        <div class="header-title">
            <span style="color:#3b82f6">⚡</span>
            WINDCAST
        </div>
        <div class="header-nav">
            <button class="nav-link" onclick="document.getElementById('info-section').scrollIntoView({behavior:'smooth'})">Info</button>
            <button class="nav-link">Support</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── MOBILE CONTROLS ───────────────────────────────────────────────────────
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        search_val = st.text_input("Location", placeholder="LOCATION / POSTCODE", 
                                   label_visibility="collapsed", key="search_input")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Crane Height Widget
        st.markdown(f"""
        <div class="crane-widget">
            <span style="color:#4d8eff">📏</span>
            <span class="crane-label">Height</span>
            <input type="range" min="10" max="250" value="{st.session_state.crane_h}" 
                   class="crane-slider" id="craneSlider" step="10" onchange="location.reload()">
            <span class="crane-value">{st.session_state.crane_h}m</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # NOW Card
        st.markdown("""
        <div class="now-card">
            <div class="now-header">
                <div>
                    <div class="now-title">Live Status</div>
                    <div class="now-status">NOW</div>
                </div>
                <div style="color:#4ae176;font-weight:700">● SAFE</div>
            </div>
            <div class="now-grid">
                <div class="now-stat">
                    <div class="now-stat-label">Gust @10m</div>
                    <div class="now-stat-value">5.2</div>
                    <div style="font-size:0.75rem;color:#c2c6d6">m/s</div>
                </div>
                <div class="now-stat">
                    <div class="now-stat-label">Gust @40m</div>
                    <div class="now-stat-value" style="color:#ffb95f">7.1</div>
                    <div style="font-size:0.75rem;color:#c2c6d6">m/s</div>
                </div>
            </div>
            <div class="now-footer">
                <span>↙ 135°</span>
                <span>10°C</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Toggles Row 1: Land/Sea + Terrain
    st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
    
    # Land/Sea
    st.markdown('<div class="toggle-group">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏗️ LAND", key="land_btn", use_container_width=True, 
                    type="primary" if st.session_state.mode=="land" else "secondary"):
            st.session_state.mode = "land"
            st.rerun()
    with col2:
        if st.button("⚓ SEA", key="sea_btn", use_container_width=True,
                    type="primary" if st.session_state.mode=="offshore" else "secondary"):
            st.session_state.mode = "offshore"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Terrain
    st.markdown('<div class="toggle-group">', unsafe_allow_html=True)
    terrain_cols = st.columns(4)
    terrain_keys = list(TERRAIN.keys())
    for i, (tkey, tval) in enumerate(TERRAIN.items()):
        with terrain_cols[i]:
            btn_type = "primary" if st.session_state.terrain == tkey else "secondary"
            if st.button(f"{tval['icon']}", key=f"terrain_{i}", use_container_width=True, type=btn_type,
                        help=tkey):
                st.session_state.terrain = tkey
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Toggles Row 2: Duration + Units + View Mode
    st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
    
    # Duration
    st.markdown('<div class="toggle-group">', unsafe_allow_html=True)
    dur_cols = st.columns(3)
    for i, (days, label) in enumerate([(1, "1d"), (3, "3d"), (7, "7d")]):
        with dur_cols[i]:
            btn_type = "primary" if st.session_state.fdays == days else "secondary"
            if st.button(label, key=f"days_{days}", use_container_width=True, type=btn_type):
                st.session_state.fdays = days
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Units
    st.markdown('<div class="toggle-group">', unsafe_allow_html=True)
    unit_cols = st.columns(2)
    with unit_cols[0]:
        if st.button(st.session_state.wind_unit.upper(), key="unit_wind", use_container_width=True,
                    type="primary"):
            pass
    with unit_cols[1]:
        if st.button(st.session_state.temp_unit, key="unit_temp", use_container_width=True,
                    type="primary"):
            pass
    st.markdown('</div>', unsafe_allow_html=True)
    
    # View Mode (24h/3h)
    st.markdown('<div class="toggle-group" style="min-width:120px">', unsafe_allow_html=True)
    view_cols = st.columns(2)
    with view_cols[0]:
        if st.button("24h", key="view_24h", use_container_width=True,
                    type="primary" if st.session_state.view_mode=="24h" else "secondary"):
            st.session_state.view_mode = "24h"
            st.rerun()
    with view_cols[1]:
        if st.button("3h", key="view_3h", use_container_width=True,
                    type="primary" if st.session_state.view_mode=="3h" else "secondary"):
            st.session_state.view_mode = "3h"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── OPTIMAL WINDOW BANNER ─────────────────────────────────────────────────
    st.markdown("""
    <div class="optimal-banner">
        <div class="optimal-icon">📅</div>
        <div class="optimal-content">
            <div class="optimal-label">Optimal Lift Window</div>
            <div class="optimal-text">Safe to lift 09:00–13:00 — conditions deteriorate from 13:00</div>
        </div>
        <div style="background:#4ae176;color:#000;padding:0.25rem 0.75rem;border-radius:9999px;font-size:0.625rem;font-weight:800">ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── FETCH DATA ────────────────────────────────────────────────────────────
    if search_val and (not st.session_state.lat or search_val != st.session_state.loc_name):
        lat, lon, name = parse_location(search_val)
        if lat:
            st.session_state.lat, st.session_state.lon = lat, lon
            st.session_state.loc_name = name
            st.rerun()
        else:
            st.error("Location not found. Try UK postcode or coordinates.")
    
    # ── FORECAST TABLE ────────────────────────────────────────────────────────
    if st.session_state.lat:
        hours = st.session_state.fdays * 24
        df = fetch_forecast(st.session_state.lat, st.session_state.lon, hours)
        
        if df is not None and not df.empty:
            # Filter view mode
            if st.session_state.view_mode == "3h":
                df = df[df["time"].dt.hour % 3 == 0].reset_index(drop=True)
            
            st.markdown('<div class="forecast-container">', unsafe_allow_html=True)
            
            # Header with date and toggles
            date_str = datetime.now().strftime("%A %d %b %Y")
            st.markdown(f"""
            <div class="forecast-header-row">
                <div class="forecast-title">
                    <span>📅</span>
                    {date_str}
                </div>
                <div class="duration-toggles">
                    <button class="duration-btn {'active' if st.session_state.fdays==1 else ''}">1D</button>
                    <button class="duration-btn {'active' if st.session_state.fdays==3 else ''}">3D</button>
                    <button class="duration-btn {'active' if st.session_state.fdays==7 else ''}">7D</button>
                    <button class="duration-btn">MAX</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Table Header
            st.markdown("""
            <div class="table-header">
                <span>Time</span>
                <span>Gust/Wind @10m</span>
                <span>Gust/Wind @40m ✦</span>
                <span>Dir</span>
                <span>Temp</span>
                <span>Rain</span>
                <span>Cloud</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Forecast Rows
            crane_h = st.session_state.crane_h
            for _, row in df.head(24 if st.session_state.fdays == 1 else 72).iterrows():
                ts = pd.to_datetime(row["time"])
                ws = safe_float(row.get("wind_speed"))
                wg = safe_float(row.get("wind_gust"))
                wd = row.get("wind_dir", np.nan)
                tmp = safe_float(row.get("temperature"))
                prc = safe_float(row.get("precip"))
                cld = safe_float(row.get("cloud"))
                
                # Height correction
                if st.session_state.mode == "land":
                    wg_h = apply_terrain(wg, st.session_state.terrain, crane_h)
                else:
                    wg_h = wg * ((crane_h / 10) ** 0.11)
                
                status, symbol, color, label = risk_status(wg_h)
                time_str = ts.strftime("%H:%M")
                wind_10 = fmt_wind(ws, st.session_state.wind_unit)
                gust_10 = fmt_wind(wg, st.session_state.wind_unit)
                wind_h = fmt_wind(ws * ((crane_h/10)**0.14), st.session_state.wind_unit)
                gust_h = fmt_wind(wg_h, st.session_state.wind_unit)
                dir_arrow = direction_arrow(wd)
                weather_icon = get_weather_icon(cld, prc)
                
                row_class = f"forecast-row {status}" if status != "safe" else "forecast-row"
                
                st.markdown(f"""
                <div class="{row_class}">
                    <div class="time-cell">{time_str}</div>
                    <div class="wind-cell">
                        <span class="wind-label">@10m</span>
                        <span class="wind-value {status}">{gust_10} G / {wind_10} W</span>
                    </div>
                    <div class="wind-cell">
                        <span class="wind-label">@{crane_h}m ✦</span>
                        <span class="wind-value {status}">{gust_h} G / {wind_h} W</span>
                    </div>
                    <div class="dir-cell">{dir_arrow}</div>
                    <div class="temp-cell">{tmp:.0f}°</div>
                    <div class="prec-cell">{weather_icon} {prc:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Legend Bar
            st.markdown("""
            <div class="legend-bar">
                <div>
                    <div class="legend-title">Site Status</div>
                    <div class="legend-status" style="color:#4ae176">ALL LIFTS GO</div>
                </div>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="status-indicator status-safe"></div>
                        <span>SAFE ≤5.9</span>
                    </div>
                    <div class="legend-item">
                        <div class="status-indicator status-caution"></div>
                        <span>CAUTION 6–14</span>
                    </div>
                    <div class="legend-item">
                        <div class="status-indicator status-stop"></div>
                        <span>STOP >14 m/s</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ── INFO SECTION ──────────────────────────────────────────────────────────
    st.markdown('<div id="info-section" class="info-section">', unsafe_allow_html=True)
    st.markdown('<div class="info-title">📖 About Windcast</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-content">
    <p><strong>Built by lifting supervisors for lifting supervisors.</strong> Provides height-corrected wind forecasts based on ECMWF IFS 0.25° model data.</p>
    
    <h4 style="color:#fff;margin:1rem 0 0.5rem 0">🎯 What It Does</h4>
    <ul style="margin:0;padding-left:1.5rem">
        <li>ECMWF IFS 0.25° — professional-grade model</li>
        <li>BS 7121 height correction + terrain factor</li>
        <li>Colour-coded Go/No-Go thresholds</li>
        <li>Built by a lifting supervisor, not a software company</li>
    </ul>
    
    <h4 style="color:#fff;margin:1rem 0 0.5rem 0">📋 How To Use</h4>
    <ol style="margin:0;padding-left:1.5rem">
        <li>Enter your postcode, place name, or lat;lon</li>
        <li>Set crane height — use slider or tap +/−</li>
        <li>Read the ✦ crane height column — that's your Go/No-Go figure</li>
        <li>Always verify with your on-site anemometer before commencing</li>
    </ol>
    
    <h4 style="color:#fff;margin:1rem 0 0.5rem 0">🎨 Colour Legend</h4>
    <ul style="margin:0;padding-left:1.5rem">
        <li style="color:#4ae176"><strong>● SAFE</strong> — Gust ≤ 5.9 m/s — Proceed with lift plan</li>
        <li style="color:#ffb95f"><strong>⚠ CAUTION</strong> — Gust 6–14 m/s — Enhanced monitoring required</li>
        <li style="color:#ffb4ab"><strong>Ⓧ STOP</strong> — Gust > 14 m/s — Do not commence lifting operations</li>
    </ul>
    
    <p style="margin-top:1rem;padding:0.75rem;background:#222a3d;border-radius:0.5rem">
    <strong>⚠️ FOR PLANNING PURPOSES ONLY</strong> · BS 7121-1:2016 · LOLER 1998 · HSE PM55 · IMCA LR006
    </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── BOTTOM NAVIGATION ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="bottom-nav">
        <div class="nav-item active">
            <span>📊</span>
            <span class="nav-label">Forecast</span>
        </div>
        <div class="nav-item">
            <span>📥</span>
            <span class="nav-label">Export</span>
        </div>
        <div class="nav-item">
            <span>🔗</span>
            <span class="nav-label">Share</span>
        </div>
    </div>
    <div style="height:6rem"></div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
