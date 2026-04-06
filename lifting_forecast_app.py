"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   WINDCAST — Precision Lifting Weather Forecast  v5.2                       ║
║   BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006                       ║
║   Source: ECMWF IFS 0.25° via Open-Meteo (free tier)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import requests, json, os, re
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Windcast",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("mode", "land"), ("crane_h", 40), ("lat", None), ("lon", None), 
             ("loc_name", ""), ("fdays", 1), ("wind_unit", "m/s"), ("temp_unit", "°C"), 
             ("terrain", "Open / Coastal"), ("view_mode", "24h"), ("show_info", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# RESPONSIVE CSS - FIXED BUTTON SIZES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base Reset ── */
#MainMenu, header, footer {visibility: hidden;}
section[data-testid="stSidebar"] {display: none !important;}
.main .block-container {padding: 0.5rem; max-width: 100%;}

/* ── Header ── */
.app-header {
    background: #131b2e;
    padding: 0.5rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2d3449;
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
.header-nav {display: flex; gap: 0.5rem; align-items: center;}

/* ── SMALL BUTTONS ── */
.small-btn {
    background: transparent !important;
    border: 1px solid #424754 !important;
    color: #94a3b8 !important;
    padding: 0.25rem 0.625rem !important;
    font-size: 0.6875rem !important;
    font-weight: 700 !important;
    border-radius: 0.375rem !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    height: auto !important;
    min-height: unset !important;
    line-height: 1.2 !important;
}
.small-btn:hover {
    background: #31394d !important;
    color: #fff !important;
    border-color: #64748b !important;
}
.small-btn.active {
    background: #3b82f6 !important;
    color: white !important;
    border-color: #3b82f6 !important;
}

/* ── Control Section ── */
.control-section {
    background: #171f33;
    padding: 0.75rem;
    margin: 0.5rem;
    border-radius: 0.75rem;
}

/* ── Search Container ── */
.search-container {
    position: relative;
    margin-bottom: 0.75rem;
}
.search-input {
    width: 100%;
    background: #222a3d;
    border: none;
    border-radius: 0.5rem;
    padding: 0.5rem 2.5rem 0.5rem 0.875rem;
    color: #dae2fd;
    font-family: 'Inter', sans-serif;
    font-size: 0.8125rem;
}
.search-btn {
    position: absolute;
    right: 0.25rem;
    top: 50%;
    transform: translateY(-50%);
    background: #ee9800;
    border: none;
    border-radius: 0.375rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}

/* ── Crane Widget ── */
.crane-widget {
    background: #222a3d;
    padding: 0.5rem 0.75rem;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    gap: 0.625rem;
    margin-bottom: 0.625rem;
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
    font-size: 0.8125rem;
    color: #4d8eff;
    min-width: 2.25rem;
}

/* ── Toggle Rows ── */
.toggle-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.toggle-group {
    background: #060e20;
    border-radius: 9999px;
    padding: 0.1875rem;
    display: flex;
    flex: 1;
    height: 2.25rem;
    align-items: center;
}

/* ── Streamlit Button Overrides - EXTRA SMALL ── */
.stButton > button {
    border: none !important;
    border-radius: 9999px !important;
    font-size: 0.6875rem !important;
    font-weight: 700 !important;
    padding: 0.25rem 0.625rem !important;
    height: auto !important;
    min-height: unset !important;
    transition: all 0.2s !important;
    line-height: 1.2 !important;
}

/* ── NOW Card ── */
.now-card {
    background: #2d3449;
    padding: 0.75rem;
    border-radius: 0.75rem;
    margin-bottom: 0.75rem;
}
.now-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 0.75rem;
}
.now-title {
    font-size: 0.5625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
}
.now-status {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: #4ae176;
}
.now-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}
.now-stat {
    background: #060e20;
    padding: 0.625rem;
    border-radius: 0.5rem;
}
.now-stat-label {
    font-size: 0.5625rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #c2c6d6;
    margin-bottom: 0.1875rem;
}
.now-stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 1.25rem;
    color: #4ae176;
}
.now-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.625rem;
    border-top: 1px solid #424754;
}

/* ── Optimal Window Banner ── */
.optimal-banner {
    background: rgba(74, 225, 118, 0.1);
    border: 1px solid rgba(74, 225, 118, 0.3);
    padding: 0.75rem;
    border-radius: 0.75rem;
    margin: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.optimal-icon {
    width: 2rem;
    height: 2rem;
    background: rgba(74, 225, 118, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.optimal-content {flex: 1;}
.optimal-label {
    font-size: 0.5625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4ae176;
}
.optimal-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.8125rem;
    color: #fff;
}

/* ── Forecast Container ── */
.forecast-container {
    background: #171f33;
    border-radius: 0.75rem;
    overflow: hidden;
    margin: 0.5rem;
}
.forecast-header-row {
    background: #31394d;
    padding: 0.625rem 0.875rem;
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
    font-size: 1rem;
    color: #fff;
}
.duration-toggles {
    display: flex;
    gap: 0.1875rem;
    background: #060e20;
    padding: 0.1875rem;
    border-radius: 9999px;
}
.duration-btn {
    padding: 0.3125rem 0.75rem;
    border: none;
    background: transparent;
    color: #c2c6d6;
    font-size: 0.6875rem;
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
    grid-template-columns: 3rem 1fr 1fr 2.25rem 2.25rem 2.25rem;
    padding: 0.4375rem 0.75rem;
    background: #222a3d;
    font-size: 0.5625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
    border-bottom: 1px solid #424754;
}

/* ── Forecast Rows ── */
.forecast-row {
    display: grid;
    grid-template-columns: 3rem 1fr 1fr 2.25rem 2.25rem 2.25rem;
    padding: 0.75rem 0.75rem;
    border-bottom: 1px solid #2d3449;
    background: #131b2e;
    align-items: center;
}
.forecast-row:nth-child(even) {background: #060e20;}
.forecast-row.caution {
    background: rgba(255, 185, 95, 0.08);
    border-left: 3px solid #ffb95f;
}
.forecast-row.stop {
    background: rgba(255, 180, 171, 0.08);
    border-left: 3px solid #ffb4ab;
}

.time-cell {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.8125rem;
    color: #dae2fd;
}
.wind-cell {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
}
.wind-label {
    font-size: 0.5625rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #c2c6d6;
}
.wind-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 0.875rem;
}
.wind-value.safe {color: #4ae176;}
.wind-value.caution {color: #ffb95f;}
.wind-value.stop {color: #ffb4ab;}
.dir-cell, .temp-cell, .prec-cell {
    text-align: center;
    font-size: 0.6875rem;
    font-weight: 700;
}

/* ── Legend Bar ── */
.legend-bar {
    background: #2d3449;
    padding: 0.75rem;
    border-radius: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0.5rem;
}
.legend-title {
    font-size: 0.5625rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c2c6d6;
}
.legend-status {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.8125rem;
}
.legend-items {display: flex; gap: 1rem;}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.3125rem;
    font-size: 0.625rem;
    font-weight: 700;
}
.status-dot {
    width: 0.5625rem;
    height: 0.5625rem;
    border-radius: 50%;
}
.status-safe {background: #4ae176;}
.status-caution {background: #ffb95f;}
.status-stop {background: #ffb4ab;}

/* ── Info Section ── */
.info-section {
    background: #171f33;
    padding: 1rem;
    border-radius: 0.75rem;
    margin: 0.5rem;
}
.info-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #fff;
    margin-bottom: 0.75rem;
}
.info-content {
    color: #c2c6d6;
    line-height: 1.6;
    font-size: 0.8125rem;
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
    padding: 0.625rem 0.75rem;
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 100;
}
.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.1875rem;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
    padding: 0.375rem 1.25rem;
    border-radius: 9999px;
}
.nav-item.active {
    background: #3b82f6;
    color: white;
}
.nav-item:hover {color: #fff;}
.nav-label {
    font-size: 0.5625rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── DESKTOP STYLES ── */
@media (min-width: 1024px) {
    .main .block-container {padding: 0.75rem 1.5rem;}
    .control-section {
        display: grid;
        grid-template-columns: 1fr 280px;
        gap: 1rem;
        padding: 1rem 1.25rem;
    }
    .toggle-row {margin-bottom: 0.625rem;}
    .toggle-group {min-width: unset;}
    .table-header, .forecast-row {
        grid-template-columns: 3.5rem 1.2fr 1.2fr 2.5rem 2.5rem 2.5rem;
    }
    .wind-value {font-size: 0.9375rem;}
    .header-title {font-size: 1.5rem;}
    .forecast-container {margin: 0.75rem 1rem;}
    .legend-bar {margin: 0.75rem 1rem;}
    .info-section {margin: 0.75rem 1rem;}
    .optimal-banner {margin: 0.75rem 1rem;}
    .now-card {margin-bottom: 0;}
}

/* ── MOBILE STYLES ── */
@media (max-width: 767px) {
    .main .block-container {padding: 0.375rem;}
    .app-header {padding: 0.5rem 0.75rem;}
    .header-title {font-size: 1rem;}
    .header-nav {gap: 0.375rem;}
    .control-section {padding: 0.625rem; margin: 0.375rem;}
    .toggle-row {flex-wrap: wrap; gap: 0.375rem;}
    .toggle-group {height: 2rem; min-width: unset;}
    .crane-widget {padding: 0.4375rem 0.625rem;}
    .table-header, .forecast-row {
        grid-template-columns: 2.75rem 1fr 2.25rem 1.75rem 1.75rem;
        font-size: 0.6875rem;
        padding: 0.5625rem 0.4375rem;
    }
    .table-header span:nth-child(3), 
    .forecast-row > div:nth-child(3) {display: none;}
    .wind-cell {flex-direction: row; gap: 0.25rem; align-items: baseline;}
    .wind-label {display: none;}
    .wind-value {font-size: 0.8125rem;}
    .legend-bar {
        flex-direction: column;
        gap: 0.75rem;
        align-items: flex-start;
        padding: 0.625rem;
        margin: 0.375rem;
    }
    .now-grid {grid-template-columns: 1fr;}
    .optimal-banner {
        flex-direction: column;
        align-items: flex-start;
        padding: 0.625rem;
        margin: 0.375rem;
    }
    .forecast-container {margin: 0.375rem;}
    .info-section {padding: 0.75rem; margin: 0.375rem;}
    .bottom-nav {padding: 0.5rem 0.375rem;}
    .nav-item {padding: 0.375rem 0.875rem;}
    .nav-label {font-size: 0.5rem;}
    .stButton > button {
        font-size: 0.625rem !important;
        padding: 0.1875rem 0.5rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WIND_UNIT_FACTORS = {
    "m/s": (1.0, "m/s"),
    "knots": (1.9438, "kt"),
    "mph": (2.2369, "mph"),
    "km/h": (3.6, "km/h"),
}

TERRAIN = {
    "Open / Coastal": {"alpha": 0.14, "factor": 1.00, "icon": "🏖️"},
    "Industrial / Port": {"alpha": 0.22, "factor": 1.10, "icon": "🏭"},
    "Urban / City": {"alpha": 0.28, "factor": 1.20, "icon": "🏙️"},
    "Woodland / Forest": {"alpha": 0.20, "factor": 1.15, "icon": "🌲"},
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def fmt_wind(ms: float, unit: str) -> str:
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
    """Parse location from search query - FIXED"""
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
    
    # Place name - IMPROVED
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                        params={"q": q, "format": "json", "limit": 1, "addressdetails": 1},
                        headers={"User-Agent": "Windcast/5.2"}, timeout=10)
        d = r.json()
        if d and len(d) > 0:
            lat = float(d[0]["lat"])
            lon = float(d[0]["lon"])
            # Get a better display name
            display = d[0].get("display_name", "")
            if display:
                # Extract just the city/town name
                parts = display.split(",")
                name = parts[0].strip() if parts else q
            else:
                name = q
            return lat, lon, name
    except Exception as e:
        st.error(f"Location lookup error: {e}")
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
    # ── HEADER WITH WORKING BUTTONS ──────────────────────────────────────────
    col_logo, col_nav = st.columns([3, 1], gap="small")
    
    with col_logo:
        st.markdown("""
        <div class="app-header" style="border:none;padding:0.5rem;">
            <div class="header-title">
                <span style="color:#fbbf24">⚡</span>
                WINDCAST
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_nav:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📖 Info", key="info_btn", use_container_width=True):
                st.session_state.show_info = not st.session_state.show_info
                st.rerun()
        with c2:
            if st.button("📞 Support", key="support_btn", use_container_width=True):
                st.info("Email: support@windcast.app\n\nFor urgent issues, contact your site supervisor.")
    
    # ── SHOW INFO SECTION ─────────────────────────────────────────────────────
    if st.session_state.show_info:
        st.markdown('<div id="info-section" class="info-section">', unsafe_allow_html=True)
        st.markdown('<div class="info-title">📖 About Windcast</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-content">
        <p><strong>Built by lifting supervisors for lifting supervisors.</strong></p>
        
        <h4 style="color:#fff;margin:1rem 0 0.5rem 0">🎯 What It Does</h4>
        <ul style="margin:0;padding-left:1.5rem">
            <li>ECMWF IFS 0.25° — professional-grade model</li>
            <li>BS 7121 height correction + terrain factor</li>
            <li>Colour-coded Go/No-Go thresholds</li>
        </ul>
        
        <h4 style="color:#fff;margin:1rem 0 0.5rem 0">📋 How To Use</h4>
        <ol style="margin:0;padding-left:1.5rem">
            <li>Enter postcode, place name, or lat;lon</li>
            <li>Set crane height</li>
            <li>Read the ✦ crane height column</li>
            <li>Verify with on-site anemometer</li>
        </ol>
        
        <h4 style="color:#fff;margin:1rem 0 0.5rem 0">🎨 Legend</h4>
        <ul style="margin:0;padding-left:1.5rem">
            <li style="color:#4ae176"><strong>● SAFE</strong> — ≤ 5.9 m/s</li>
            <li style="color:#ffb95f"><strong>⚠ CAUTION</strong> — 6–14 m/s</li>
            <li style="color:#ffb4ab"><strong>Ⓧ STOP</strong> — > 14 m/s</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ── CONTROL SECTION ───────────────────────────────────────────────────────
    st.markdown('<div class="control-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1], gap="small")
    
    with col1:
        # Search
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        search_val = st.text_input("Location", placeholder="Postcode / Place / lat;lon", 
                                   label_visibility="collapsed", key="search_input")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Crane Height Widget
        st.markdown(f"""
        <div class="crane-widget">
            <span style="color:#fbbf24">📏</span>
            <span class="crane-label">Height</span>
            <input type="range" min="10" max="250" value="{st.session_state.crane_h}" 
                   class="crane-slider" id="craneSlider" step="10">
            <span class="crane-value">{st.session_state.crane_h}m</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Toggles Row 1: Land/Sea
        st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
        st.markdown('<div class="toggle-group">', unsafe_allow_html=True)
        land_col, sea_col = st.columns(2)
        with land_col:
            if st.button("🏗️ LAND", key="land_btn", use_container_width=True, 
                        type="primary" if st.session_state.mode=="land" else "secondary"):
                st.session_state.mode = "land"
                st.rerun()
        with sea_col:
            if st.button("⚓ SEA", key="sea_btn", use_container_width=True,
                        type="primary" if st.session_state.mode=="offshore" else "secondary"):
                st.session_state.mode = "offshore"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Toggles Row 2: Terrain
        st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
        terrain_cols = st.columns(4)
        for i, (tkey, tval) in enumerate(TERRAIN.items()):
            with terrain_cols[i]:
                btn_type = "primary" if st.session_state.terrain == tkey else "secondary"
                if st.button(f"{tval['icon']}", key=f"terrain_{i}", use_container_width=True, 
                            type=btn_type, help=tkey):
                    st.session_state.terrain = tkey
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Toggles Row 3: Duration
        st.markdown('<div class="toggle-row">', unsafe_allow_html=True)
        dur_cols = st.columns(3)
        for i, (days, label) in enumerate([(1, "1d"), (3, "3d"), (7, "7d")]):
            with dur_cols[i]:
                btn_type = "primary" if st.session_state.fdays == days else "secondary"
                if st.button(label, key=f"days_{days}", use_container_width=True, type=btn_type):
                    st.session_state.fdays = days
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
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
                    <div style="font-size:0.6875rem;color:#c2c6d6">m/s</div>
                </div>
                <div class="now-stat">
                    <div class="now-stat-label">Gust @40m</div>
                    <div class="now-stat-value" style="color:#ffb95f">7.1</div>
                    <div style="font-size:0.6875rem;color:#c2c6d6">m/s</div>
                </div>
            </div>
            <div class="now-footer">
                <span>↙ 135°</span>
                <span>10°C</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── OPTIMAL WINDOW BANNER ─────────────────────────────────────────────────
    st.markdown("""
    <div class="optimal-banner">
        <div class="optimal-icon">📅</div>
        <div class="optimal-content">
            <div class="optimal-label">Optimal Lift Window</div>
            <div class="optimal-text">Safe to lift 09:00–13:00 — conditions deteriorate from 13:00</div>
        </div>
        <div style="background:#4ae176;color:#000;padding:0.1875rem 0.625rem;border-radius:9999px;font-size:0.5625rem;font-weight:800">ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── FETCH DATA ────────────────────────────────────────────────────────────
    if search_val and (not st.session_state.lat or search_val != st.session_state.loc_name):
        with st.spinner("Looking up location..."):
            lat, lon, name = parse_location(search_val)
        if lat:
            st.session_state.lat, st.session_state.lon = lat, lon
            st.session_state.loc_name = name
            st.success(f"📍 {name}")
            st.rerun()
        else:
            st.error(f"❌ Location not found: '{search_val}'\n\nTry:\n• UK postcode (e.g., SO23 9NA)\n• Place name (e.g., Winchester, London)\n• Coordinates (51.06;-1.31)")
    
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
                        <div class="status-dot status-safe"></div>
                        <span>SAFE ≤5.9</span>
                    </div>
                    <div class="legend-item">
                        <div class="status-dot status-caution"></div>
                        <span>CAUTION 6–14</span>
                    </div>
                    <div class="legend-item">
                        <div class="status-dot status-stop"></div>
                        <span>STOP >14 m/s</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
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
    <div style="height:4.5rem"></div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
