"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   LIFTING OPERATIONS WEATHER FORECAST  v3.1  —  Land + Offshore Combined   ║
║   BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006 | NORSOK R-003       ║
║   Source: ECMWF IFS 0.25° via Open-Meteo (free tier)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS (before secrets so st is available)
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import streamlit.components.v1 as components
import requests, json, os, re
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import pytz

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  — sidebar hidden by CSS, not initial_sidebar_state
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Lifting Ops Forecast",
    page_icon="🐝️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ══════════════════════════════════════════════════════════════════════════════
# API KEYS  — reads .streamlit/secrets.toml first, falls back to empty string
# secrets.toml format:
#   METOFFICE_API_KEY   = "your_key"
#   TOMORROW_IO_API_KEY = "your_key"
#   OPEN_METEO_API_KEY  = "your_key"   # omit line if using free tier
# ══════════════════════════════════════════════════════════════════════════════
def _secret(key, fallback=None):
    try:
        return st.secrets[key]
    except Exception:
        return fallback

METOFFICE_API_KEY   = _secret("METOFFICE_API_KEY",   "")
TOMORROW_IO_API_KEY = _secret("TOMORROW_IO_API_KEY",  "")
OPEN_METEO_API_KEY  = _secret("OPEN_METEO_API_KEY",   None)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Hide Streamlit chrome ── */
#MainMenu, header, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }
.main .block-container { padding: 0.8rem 1.2rem 1rem 1.2rem; max-width: 100%; }

/* ── Page title ── */
.page-title { font-size: 2rem; font-weight: 800; color: #fff; margin: 0 0 0.8rem 0; line-height: 1.1; }

/* ── Align button baseline with inputs: remove top label gap ── */
div[data-testid="stButton"] > button { margin-top: 0 !important; }
div[data-testid="column"]:has(.btn-align) button { margin-top: 1.65rem; }

/* ── Risk circle symbols ── */
.ci-safe    { color: #1E88E5; }
.ci-caution { color: #FB8C00; }
.ci-danger  { color: #8E24AA; }

/* ── Forecast tab buttons ── */
.tab-row { display:flex; gap:0; margin: 0.6rem 0 0.3rem 0; align-items:center; }
.tab-btn {
    background:#1a1a2e; color:#aaa; border:1px solid #333;
    padding: 4px 14px; font-size: 0.8rem; cursor:pointer;
    border-radius: 0;
}
.tab-btn:first-child { border-radius: 6px 0 0 6px; }
.tab-btn:last-child  { border-radius: 0 6px 6px 0; }
.tab-btn.active { background:#EF4444; color:#fff; border-color:#EF4444; font-weight:700; }

/* ── Land/Sea toggle ── */
.mode-toggle { display:flex; gap:0; }
.mode-btn {
    display:inline-flex; align-items:center; gap:5px;
    padding: 4px 14px; font-size: 0.8rem; font-weight:600;
    border: 1px solid #555; cursor:pointer; border-radius:0;
    background:#1a1a2e; color:#aaa;
}
.mode-btn:first-child { border-radius: 6px 0 0 6px; }
.mode-btn:last-child  { border-radius: 0 6px 6px 0; }
.mode-btn.active-land { background:#EF4444; color:#fff; border-color:#EF4444; }
.mode-btn.active-sea  { background:#EF4444; color:#fff; border-color:#EF4444; }

/* ── Info line ── */
.info-line { font-size:0.8rem; color:#90CAF9; margin: 0.15rem 0 0.3rem 0; }

/* ── Legend strip ── */
.legend-strip { display:flex; gap:14px; flex-wrap:wrap; font-size:0.78rem;
    margin:0.2rem 0 0.4rem 0; align-items:center; color:#ccc; }
.leg-item { display:flex; align-items:center; gap:4px; font-weight:600; }

/* ── Alert boxes ── */
.box-info    { background:rgba(21,101,192,.15); border:1px solid #1565C0; border-radius:7px; padding:.6rem .8rem; margin:.3rem 0; font-size:.8rem; }
.box-caution { background:rgba(230,81,0,.15);  border:1px solid #E65100; border-radius:7px; padding:.6rem .8rem; margin:.3rem 0; font-size:.8rem; }
.box-danger  { background:rgba(74,20,140,.15); border:1px solid #8E24AA; border-radius:7px; padding:.6rem .8rem; margin:.3rem 0; font-size:.8rem; }

/* ── Saved location pills ── */
.saved-pill { display:inline-block; background:#1a2a3a; border:1px solid #1565C0;
  border-radius:12px; padding:2px 10px; margin:2px 3px; font-size:0.72rem; color:#90CAF9; }

/* ── Disclaimer ── */
.disclaimer { background:#0d0d1a; border:1px solid #333; border-radius:5px;
  padding:.5rem; font-size:.68rem; color:#888; margin-top:0.8rem; }

/* ── coord hint ── */
.coord-hint { font-size: 0.68rem; color: #666; margin-top: 0.15rem; }

/* ── Table (rendered directly, no iframe) ── */
.table-wrap { overflow-x: auto; margin-top: 0.4rem; }
.fc-table { width:100%; border-collapse:collapse; font-size:0.8rem; font-family:system-ui,sans-serif; }
.fc-table thead tr th {
    background:#0f3460; color:#90CAF9; padding:8px 6px;
    text-align:center; white-space:nowrap;
    position:sticky; top:0; z-index:10;
    border-bottom:2px solid #1565C0; font-size:0.74rem;
}
.fc-table thead tr th.h10 { background:#0a2a50; color:#64B5F6; border-bottom:3px solid #1565C0; }
.fc-table thead tr th.hcr { background:#004d40; color:#80CBC4; border-bottom:3px solid #00796B; }
.fc-table tbody tr { border-bottom:1px solid #1a1a2e; color:#ddd; background:#0d0d1a; }
.fc-table tbody tr:hover { background:rgba(21,101,192,0.12); }
.fc-table tbody tr.day-break td { border-top:2px solid #1565C0 !important; }
.fc-table td { padding:5px 5px; text-align:center; vertical-align:middle; }
.fc-table td.time-col { white-space:nowrap; color:#90CAF9; font-weight:600; font-size:0.76rem; }
.fc-table td.h10 { background:rgba(10,42,80,0.55); }
.fc-table td.hcr { background:rgba(0,77,64,0.45); }
.fc-table td.wind-val { font-weight:600; font-size:0.82rem; padding:5px 8px; line-height:1.75; }
.fc-table .ci-safe    { color:#1E88E5; }
.fc-table .ci-caution { color:#FB8C00; }
.fc-table .ci-danger  { color:#8E24AA; }
.fc-table td.dir-cell { color:#aaa; font-size:0.85em; }
.fc-table td.temp-cell { border-radius:4px; padding:3px 5px; }
.fc-table td.cloud-cell { color:#bbb; }
.fc-table td.rain-cell { border-radius:4px; padding:3px 5px; }
.fc-table td.wave-cell { border-radius:5px; padding:4px 5px; }
.fc-table small { font-size:0.65em; opacity:0.85; display:block; }

/* Hide Cloud and Pressure on mobile */
@media (max-width: 768px) {
    .page-title { font-size: 1.4rem; }
    .main .block-container { padding: 0.4rem 0.5rem; }
    .tab-row { flex-wrap: wrap; }
    .legend-strip { gap: 8px; font-size: 0.7rem; }
    .fc-table { font-size: 0.7rem; }
    .fc-table td { padding: 3px 3px; }
    .hide-mobile { display: none; }
}
@media (max-width: 480px) {
    .page-title { font-size: 1.1rem; }
    .fc-table td.time-col { font-size: 0.65rem; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Wind speed conversion factors (from m/s)
WIND_UNIT_FACTORS = {
    "m/s":     (1.0,    "m/s"),
    "knots":   (1.9438, "kt"),
    "mph":     (2.2369, "mph"),
    "km/h":    (3.6,    "km/h"),
    "Beaufort": (None,  "Bft"),
}

# Site terrain — affects wind shear exponent (power law)
TERRAIN = {
    "Open / Coastal":   {"alpha": 0.14, "factor": 1.00, "label": "Open/Coastal"},
    "Industrial / Port":{"alpha": 0.22, "factor": 1.10, "label": "Industrial"},
    "Urban / City":     {"alpha": 0.28, "factor": 1.20, "label": "Urban/City"},
    "Woodland / Forest":{"alpha": 0.20, "factor": 1.15, "label": "Woodland"},
}

# Weather models
MODELS_LAND = {
    "ECMWF":        {"endpoint": "ecmwf_ifs04",   "weight": 0.40, "label": "ECMWF IFS"},
    "ICON":         {"endpoint": "icon_seamless",  "weight": 0.30, "label": "ICON"},
    "GFS":          {"endpoint": "gfs_global",     "weight": 0.20, "label": "GFS"},
    "MetOffice_UKV":{"endpoint": "ukmo_seamless",  "weight": 0.10, "label": "MetOffice UKV"},
}

SAVED_LOCS_FILE = "forecast_logs/saved_locations.json"

# ══════════════════════════════════════════════════════════════════════════════
# HELPER — WIND CONVERSION & RISK CIRCLES
# ══════════════════════════════════════════════════════════════════════════════

def to_beaufort(ms: float) -> int:
    thresholds = [0.5,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,28.5,32.7]
    for i, t in enumerate(thresholds):
        if ms < t:
            return i
    return 12

def fmt_wind(ms: float, unit: str) -> str:
    if unit == "Beaufort":
        return f"{to_beaufort(ms)} Bft"
    factor, label = WIND_UNIT_FACTORS[unit]
    return f"{ms * factor:.1f} {label}"

def risk_circle(gust_ms: float) -> tuple:
    """Returns (symbol, css_class, level_text) by gust in m/s."""
    if gust_ms <= 5.9:
        return "●",  "ci-safe",    "SAFE"
    elif gust_ms <= 14.0:
        return "⬡",  "ci-caution", "CAUTION"
    else:
        return "Ⓧ", "ci-danger",  "STOP"

def risk_banner_class(gust_ms: float) -> str:
    if gust_ms <= 5.9:   return "status-safe"
    elif gust_ms <= 14.0: return "status-caution"
    else:                 return "status-danger"

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
    if unit == "°F":
        return f"{c * 9/5 + 32:.1f}°F"
    return f"{c:.1f}°C"

def safe_float(val, default=0.0):
    """Convert NaT / NaN / None / str to float safely."""
    try:
        if val is None or val is pd.NaT: return default
        f = float(val)
        return default if f != f else f
    except (TypeError, ValueError):
        return default

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
                         headers={"User-Agent": "LiftingForecastApp/3.0"}, timeout=6)
        d = r.json()
        if d:
            return float(d[0]["lat"]), float(d[0]["lon"]), d[0].get("display_name","")[:70]
    except Exception:
        pass
    return None, None, None

def parse_search(query: str):
    """Auto-detect and resolve postcode / lat;lon / place name."""
    q = query.strip()
    if not q:
        return None, None, None

    # Lat ; Lon  (semicolon or comma with two numeric parts)
    for sep in [";", ","]:
        if sep in q:
            parts = q.split(sep, 1)
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon, f"{lat:.4f}°N, {lon:.4f}°E"
            except ValueError:
                pass

    # UK postcode pattern
    if re.match(r'^[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s*\d[A-Za-z]{2}$', q):
        return postcode_to_coords(q)

    # Place name (Nominatim)
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

def save_location(name: str, lat: float, lon: float, crane_h: int, terrain: str):
    locs = load_saved()
    # Remove duplicate by name
    locs = [l for l in locs if l.get("name") != name]
    locs.insert(0, {"name": name, "lat": lat, "lon": lon,
                    "crane_h": crane_h, "terrain": terrain})
    locs = locs[:12]   # keep last 12
    try:
        os.makedirs("forecast_logs", exist_ok=True)
        with open(SAVED_LOCS_FILE, "w") as f:
            json.dump(locs, f, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH — LAND (ECMWF IFS 0.25° direct — no blending)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_ecmwf_land(lat: float, lon: float, hours: int = 168):
    """
    Fetch ECMWF IFS 0.25° directly from Open-Meteo — no blending with weaker models.
    ECMWF IFS is the best freely available global model, used by Met agencies worldwide.
    Uses list-of-tuples params so requests sends hourly=x&hourly=y correctly.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = [
        ("latitude",        lat),
        ("longitude",       lon),
        ("wind_speed_unit", "ms"),
        ("forecast_days",   min(hours // 24 + 1, 7)),
        ("timezone",        "auto"),   # auto = local time at the coordinates
        ("models",          "ecmwf_ifs025"),   # 0.25° ECMWF IFS — best free global
        ("hourly",          "wind_speed_10m"),
        ("hourly",          "wind_gusts_10m"),
        ("hourly",          "wind_direction_10m"),
        ("hourly",          "temperature_2m"),
        ("hourly",          "precipitation"),
        ("hourly",          "cloud_cover"),
        ("hourly",          "surface_pressure"),
        ("hourly",          "visibility"),
        ("hourly",          "relative_humidity_2m"),
    ]
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            st.error(f"Open-Meteo error: {body.get('reason', body)}")
            return None, []
        h = body.get("hourly", {})
        times = h.get("time", [])
        if not times:
            return None, []
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
        # Filter to current hour onwards — naive comparison (API returns naive times)
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        return df, ["ECMWF IFS 0.25°"]
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None, []

# Alias so the rest of main() doesn't need changing
def fetch_consensus(lat: float, lon: float, hours: int):
    return fetch_ecmwf_land(lat, lon, hours)

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH — OFFSHORE (Open-Meteo Marine + Wind)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_offshore_wind(lat: float, lon: float, hours: int = 120):
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
        if not times:
            return None
        df = pd.DataFrame({
            "time":       pd.to_datetime(times),
            "wind_speed": pd.to_numeric(h.get("wind_speed_10m", [np.nan] * len(times)), errors="coerce"),
            "wind_gust":  pd.to_numeric(h.get("wind_gusts_10m", [np.nan] * len(times)), errors="coerce"),
            "wind_dir":   pd.to_numeric(h.get("wind_direction_10m", [np.nan] * len(times)), errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m", [np.nan] * len(times)), errors="coerce"),
            "cloud":      pd.to_numeric(h.get("cloud_cover", [np.nan] * len(times)), errors="coerce"),
            "precip":     pd.to_numeric(h.get("precipitation", [np.nan] * len(times)), errors="coerce"),
            "pressure":   pd.to_numeric(h.get("pressure_msl", [np.nan] * len(times)), errors="coerce"),
        })
        
        # Filter to current hour onwards
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Wind fetch error: {e}")
        return None

@st.cache_data(ttl=1800)
def fetch_offshore_marine(lat: float, lon: float, hours: int = 120):
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
        if not times:
            return None
        df = pd.DataFrame({
            "time":         pd.to_datetime(times),
            "hs":           pd.to_numeric(h.get("wave_height", [np.nan] * len(times)), errors="coerce"),
            "wave_period":  pd.to_numeric(h.get("wave_period", [np.nan] * len(times)), errors="coerce"),
            "wave_dir":     pd.to_numeric(h.get("wave_direction", [np.nan] * len(times)), errors="coerce"),
            "swell_hs":     pd.to_numeric(h.get("swell_wave_height", [np.nan] * len(times)), errors="coerce"),
            "swell_period": pd.to_numeric(h.get("swell_wave_period", [np.nan] * len(times)), errors="coerce"),
            "swell_dir":    pd.to_numeric(h.get("swell_wave_direction", [np.nan] * len(times)), errors="coerce"),
            "wind_wave_hs": pd.to_numeric(h.get("wind_wave_height", [np.nan] * len(times)), errors="coerce"),
        })
        
        # Filter to current hour onwards
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Marine fetch error: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# TABLE RENDERER — returns HTML string
# ══════════════════════════════════════════════════════════════════════════════

def _wind_cells(ws_10, wg_10, ws_h, wg_h, unit):
    """Return 2 <td> cells: one for 10m, one for crane height."""
    sym10, css10, _ = risk_circle(wg_10)
    symH,  cssH,  _ = risk_circle(wg_h)
    g10 = fmt_wind(wg_10, unit)
    w10 = fmt_wind(ws_10, unit)
    gH  = fmt_wind(wg_h,  unit)
    wH  = fmt_wind(ws_h,  unit)
    return (
        f'<td class="h10 wind-val">'
        f'<span class="{css10}">{sym10}</span> G {g10}<br>'
        f'<span style="color:#555;">○</span> W {w10}'
        f'</td>'
        f'<td class="hcr wind-val">'
        f'<span class="{cssH}">{symH}</span> G {gH}<br>'
        f'<span style="color:#555;">○</span> W {wH}'
        f'</td>'
    )

# Temperature colour palette
def _temp_colour(t: float) -> str:
    if   t <= -3: return "#1565C0","#fff"
    elif t <=  0: return "#1976D2","#fff"
    elif t <=  5: return "#42A5F5","#000"
    elif t <= 10: return "#80DEEA","#000"
    elif t <= 15: return "#FFF176","#000"
    elif t <= 20: return "#FFD54F","#000"
    elif t <= 25: return "#FFB74D","#000"
    else:         return "#FF8A65","#000"

def _rain_colour(r: float) -> str:
    if   r == 0:  return "#1a1a2e","#aaa"
    elif r < 0.5: return "#1565C0","#fff"
    elif r < 2:   return "#1976D2","#fff"
    elif r < 5:   return "#0D47A1","#fff"
    else:         return "#003060","#fff"

def _wave_colour(hs: float) -> tuple:
    """Returns (bg, fg, risk_css)"""
    if   hs < 0.5: return "#0D47A1","#fff","ci-safe"
    elif hs < 1.5: return "#1565C0","#fff","ci-safe"
    elif hs < 2.5: return "#E65100","#fff","ci-caution"
    elif hs < 4.0: return "#6A1B9A","#fff","ci-danger"
    else:          return "#38006b","#fff","ci-danger"

def build_land_table_html(df: pd.DataFrame, crane_h: int, terrain: str,
                           unit: str, temp_unit: str, hours: int) -> list:
    rows = []
    prev_day = None
    for _, row in df.head(hours).iterrows():
        ts  = pd.to_datetime(row["time"])
        ws  = safe_float(row.get("wind_speed"))
        wg  = safe_float(row.get("wind_gust"))
        wd  = row.get("wind_dir", np.nan)
        tmp = safe_float(row.get("temperature"))
        prc = safe_float(row.get("precip"))
        cld = safe_float(row.get("cloud"))
        prs = safe_float(row.get("pressure"), 1013.0)

        ws_h = apply_terrain(ws, terrain, crane_h)
        wg_h = apply_terrain(wg, terrain, crane_h)

        try:
            wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except:
            wd_f = np.nan

        # Merge date and time into one column
        datetime_str = ts.strftime("%a %d %b %H:%M")
        day_break = " class='day-break'" if ts.strftime("%Y-%m-%d") != prev_day else ""
        prev_day = ts.strftime("%Y-%m-%d")

        tc, tf = _temp_colour(tmp)
        rc, rf = _rain_colour(prc)

        dir_str = f"{direction_arrow(wd_f)}&thinsp;{wd_f:.0f}°" if not np.isnan(wd_f) else "—"

        row_html = (
            f"<tr{day_break}>"
            f"<td class='time-col'>{datetime_str}</td>"
            + _wind_cells(ws, wg, ws_h, wg_h, unit)
            + f"<td class='dir-cell'>{dir_str}</td>"
            + f"<td class='temp-cell' style='background:{tc};color:{tf};'>{fmt_temp(tmp, temp_unit)}</td>"
            + f"<td class='rain-cell' style='background:{rc};color:{rf};'>{prc:.1f}mm</td>"
            + f"<td class='cloud-cell'>{cld:.0f}%</td>"
            + f"<td style='color:#aaa;'>{prs:.0f}mb</td>"
            + "</tr>"
        )
        rows.append(row_html)
    return rows

def build_offshore_table_html(wind_df, marine_df, crane_h, unit, temp_unit, hours):
    rows = []
    prev_day = None
    n = min(hours, len(wind_df))
    marine_len = len(marine_df) if marine_df is not None else 0
    
    for i in range(n):
        wrow = wind_df.iloc[i]
        ts   = pd.to_datetime(wrow["time"])
        ws   = safe_float(wrow.get("wind_speed"))
        wg   = safe_float(wrow.get("wind_gust"))
        wd   = wrow.get("wind_dir", np.nan)
        tmp  = safe_float(wrow.get("temperature"))
        prc  = safe_float(wrow.get("precip"))
        cld  = safe_float(wrow.get("cloud"))
        prs  = safe_float(wrow.get("pressure"), 1013.0)

        # Height correction (offshore: alpha=0.11 per IMCA)
        ws_h = ws * ((crane_h / 10) ** 0.11)
        wg_h = wg * ((crane_h / 10) ** 0.11)

        # Marine data (if available)
        hs = wp = wd_wave = sw = "-"
        if marine_df is not None and i < marine_len:
            mrow   = marine_df.iloc[i]
            hs_f   = safe_float(mrow.get("hs"), float("nan"))
            wp_f   = safe_float(mrow.get("wave_period"), float("nan"))
            wdw_f  = safe_float(mrow.get("wave_dir"), float("nan"))
            sw_f   = safe_float(mrow.get("swell_hs"), float("nan"))
            hs     = f"{hs_f:.2f}m" if not np.isnan(hs_f) else "—"
            wp     = f"{wp_f:.1f}s"  if not np.isnan(wp_f) else "—"
            wd_wave= f"{direction_arrow(wdw_f)}&thinsp;{wdw_f:.0f}°" if not np.isnan(wdw_f) else "—"
            sw     = f"{sw_f:.2f}m"  if not np.isnan(sw_f) else "—"

            wbg,wfg,wcss = _wave_colour(safe_float(mrow.get("hs")))
        else:
            wbg,wfg,wcss = "#0D47A1","#fff","ci-safe"

        try:
            wd_f = float(wd) if not np.isnan(float(wd)) else np.nan
        except:
            wd_f = np.nan

        # Merge date and time into one column
        datetime_str = ts.strftime("%a %d %b %H:%M")
        day_break = " class='day-break'" if ts.strftime("%Y-%m-%d") != prev_day else ""
        prev_day = ts.strftime("%Y-%m-%d")

        tc, tf = _temp_colour(tmp)
        dir_str = f"{direction_arrow(wd_f)}&thinsp;{wd_f:.0f}°" if not np.isnan(wd_f) else "—"

        row_html = (
            f"<tr{day_break}>"
            f"<td class='time-col'>{datetime_str}</td>"
            + _wind_cells(ws, wg, ws_h, wg_h, unit)
            + f"<td class='dir-cell'>{dir_str}</td>"
            + f"<td class='wave-cell' style='background:{wbg};color:{wfg};'>{hs}</td>"
            + f"<td style='color:#88ccff;'>{wp}</td>"
            + f"<td class='dir-cell'>{wd_wave}</td>"
            + f"<td style='color:#66aaff;'>{sw}</td>"
            + f"<td class='temp-cell' style='background:{tc};color:{tf};'>{fmt_temp(tmp, temp_unit)}</td>"
            + f"<td class='cloud-cell'>{cld:.0f}%</td>"
            + f"<td style='color:#aaa;'>{prs:.0f}mb</td>"
            + "</tr>"
        )
        rows.append(row_html)
    return rows

def render_table(rows: list, header_html: str, mode: str):
    """Render forecast table directly as st.markdown — with mobile hiding."""
    row_html = "\n".join(rows)
    
    # Add hide-mobile class to cloud and pressure headers for offshore mode
    if mode == "offshore":
        header_html = header_html.replace('<th>Cloud</th>', '<th class="hide-mobile">Cloud</th>')
        header_html = header_html.replace('<th>Pressure</th>', '<th class="hide-mobile">Pressure</th>')
        # Also modify the table rows to hide those columns on mobile
        row_html = row_html.replace('<td class="cloud-cell">', '<td class="cloud-cell hide-mobile">')
        row_html = row_html.replace('<td style="color:#aaa;">', '<td class="hide-mobile" style="color:#aaa;">')
    
    html = (
        '<div class="table-wrap">'
        '<table class="fc-table">'
        f'<thead>{header_html}</thead>'
        f'<tbody>{row_html}</tbody>'
        '</table></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

def land_header(crane_h):
    return f"""<tr>
  <th>Date & Time</th>
  <th class="h10">Gust / Wind<br><span style="font-weight:400;font-size:0.68em;">at 10m height</span></th>
  <th class="hcr">Gust / Wind<br><span style="font-weight:400;font-size:0.68em;">at {crane_h}m height</span></th>
  <th>Dir</th>
  <th>Temp</th><th>Rain</th><th>Cloud</th><th>Pressure</th>
</tr>"""

def offshore_header(crane_h):
    return f"""<tr>
  <th>Date & Time</th>
  <th class="h10">Gust / Wind<br><span style="font-weight:400;font-size:0.68em;">at 10m height</span></th>
  <th class="hcr">Gust / Wind<br><span style="font-weight:400;font-size:0.68em;">at {crane_h}m height</span></th>
  <th>Dir</th>
  <th>Hs (m)</th><th>Wave Pd.</th><th>Wave Dir</th><th>Swell Hs</th>
  <th>Temp</th><th class="hide-mobile">Cloud</th><th class="hide-mobile">Pressure</th>
</tr>"""

# ══════════════════════════════════════════════════════════════════════════════
# STATUS BANNER
# ══════════════════════════════════════════════════════════════════════════════

def render_status_banner(current_row, crane_h, terrain, unit, mode):
    ws  = safe_float(current_row.get("wind_speed"))
    wg  = safe_float(current_row.get("wind_gust"))
    if mode == "land":
        ws_h = apply_terrain(ws, terrain, crane_h)
        wg_h = apply_terrain(wg, terrain, crane_h)
    else:
        ws_h = ws * ((crane_h / 10) ** 0.11)
        wg_h = wg * ((crane_h / 10) ** 0.11)

    sym, css, lvl = risk_circle(wg_h)
    gust_s = fmt_wind(wg_h, unit)
    wind_s = fmt_wind(ws_h, unit)

    st.markdown(
        f'<div class="box-info"><span class="{css}" style="font-size:1.3em;">{sym}</span>'
        f' &nbsp;{lvl} &nbsp;—&nbsp; Gust @{crane_h}m: <b>{gust_s}</b>'
        f' &nbsp;·&nbsp; Wind @{crane_h}m: {wind_s}</div>',
        unsafe_allow_html=True
    )
    return ws, wg, ws_h, wg_h

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════

def render_legend():
    st.markdown("""
<div class="legend-strip">
  <b>Legend:</b>
  <span class="leg-item"><span class="ci-safe" style="font-size:1.2em;">●</span>&nbsp;SAFE &nbsp;≤5.9 m/s</span>
  <span class="leg-item"><span class="ci-caution" style="font-size:1.1em;">⬡</span>&nbsp;CAUTION &nbsp;6–14 m/s</span>
  <span class="leg-item"><span class="ci-danger" style="font-size:1.1em;">Ⓧ</span>&nbsp;STOP &nbsp;&gt;14 m/s</span>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INFO TAB RENDERER
# ══════════════════════════════════════════════════════════════════════════════

FEEDBACK_URL = "https://forms.gle/REPLACE_WITH_YOUR_FORM_URL"
KOFI_URL     = "https://ko-fi.com/windcast"

def render_info_tab():
    st.markdown("""
<style>
.info-section { margin: 1.2rem 0 0.4rem 0; }
.info-section h3 { color: #90CAF9; font-size: 1.1rem; border-bottom: 1px solid #1565C0;
    padding-bottom: 0.3rem; margin-bottom: 0.6rem; }
.info-section p, .info-section li { color: #ccc; font-size: 0.88rem; line-height: 1.6; }
.info-section ul { padding-left: 1.2rem; }
.info-section ol { padding-left: 1.2rem; }
.info-section li { margin-bottom: 0.3rem; }
.info-badge { display:inline-block; background:#1a2a3a; border:1px solid #1565C0;
    border-radius:5px; padding:3px 9px; font-size:0.78rem; color:#90CAF9; margin:2px 3px; }
</style>
""", unsafe_allow_html=True)

    # ── About the Creator ──────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>👤 About the Creator</h3>
<p>
I built Windcast between jobs, out of sheer frustration.
</p>
<p>
You know how it is on site — you're trying to make a Go/No-Go call, you check the weather, and XCWeather gives you something that bears no resemblance to what the anemometer on the hook block is reading.
I'd been complaining about this for years, but it was my wife (a UX designer) who finally said: <em>"You clearly know what's wrong with these tools — so build a better one."</em>
</p>
<p>
I had no idea it would turn into this. What started as a quick Python script I used for my own lift plans has, six months later, grown into something I'm genuinely proud of. The accuracy against real site conditions has been consistent enough that I've stopped second-guessing it. That's when I knew it was worth sharing.
</p>
<p>
If you work in cranes, MEWPs, or marine lifting — this was built by someone who's sat in the same chair you're sitting in. I hope it helps.
</p>
</div>""", unsafe_allow_html=True)

    # ── What It Does ──────────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>🎯 What It Does</h3>
<p><strong>Windcast gives lifting supervisors an accurate, height-corrected wind forecast — colour-coded for Go/No-Go — built to BS 7121 standards, not generic weather websites.</strong></p>
<ul>
<li>🌍 <strong>ECMWF IFS 0.25°</strong> — the same model used by professional meteorological agencies worldwide</li>
<li>📐 <strong>BS 7121 height correction</strong> — wind speed calculated at your actual crane height using the power law, adjusted for terrain roughness</li>
<li>🟢🟡🔴 <strong>Colour-coded Go/No-Go</strong> — safe, caution, and stop thresholds displayed at a glance</li>
<li>⚖️ <strong>LOLER-aware</strong> — built with the Lifting Operations and Lifting Equipment Regulations 1998 in mind</li>
<li>🧰 <strong>Built by a lifting supervisor</strong> — not a software company. The assumptions, thresholds, and corrections are based on site experience, not guesswork</li>
<li>⚓ <strong>Offshore mode</strong> — includes wave height (Hs), swell, wave period, and IMCA LR006 height correction (α = 0.11)</li>
</ul>
</div>""", unsafe_allow_html=True)

    # ── How To Use ────────────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>📋 How To Use</h3>
<ol>
<li><strong>Enter your location</strong> — type a UK postcode (e.g. <code>SE1 7PB</code>), a place name, or latitude/longitude separated by a semicolon (<code>51.50 ; -0.12</code>). The app will resolve the location automatically.</li>
<li><strong>Set crane height and terrain</strong> — enter the maximum hook height in metres. Choose the terrain type that best describes your site (open, industrial, urban, or woodland). This drives the BS 7121 power-law correction.</li>
<li><strong>Click Get Forecast</strong> — the table loads with hourly wind speeds and gusts at both 10m reference height and your crane height.</li>
<li><strong>Read the colour-coded table</strong> — each row is an hour. The risk symbol in the crane-height column tells you the status at a glance. Green circle = safe, amber hexagon = caution, red Ⓧ = stop work.</li>
<li><strong>Use the Go/No-Go column for your lift plan</strong> — this is planning data, not a substitute for your on-site anemometer. Always verify with a calibrated instrument before commencing.</li>
</ol>
<p>Switch between <strong>Land</strong> and <strong>Sea</strong> modes using the toggle in the forecast header. Use the day buttons (1 / 3 / 7) to extend or narrow the forecast window.</p>
</div>""", unsafe_allow_html=True)

    # ── Colour Legend ─────────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>🎨 Colour Legend</h3>
<p>Wind risk is assessed by <strong>gust speed at crane height</strong>, corrected for terrain:</p>
</div>""", unsafe_allow_html=True)
    st.markdown("""
<div class="legend-strip" style="margin:0.5rem 0 0.8rem 0; font-size:0.85rem; gap:18px;">
  <span class="leg-item"><span class="ci-safe" style="font-size:1.4em;">●</span>&nbsp;<strong>SAFE</strong> — Gust ≤ 5.9 m/s (≤ 11.5 kt). Proceed with lift plan.</span>
  <span class="leg-item"><span class="ci-caution" style="font-size:1.3em;">⬡</span>&nbsp;<strong>CAUTION</strong> — Gust 6–14 m/s (11.6–27 kt). Enhanced monitoring required. Review lift plan against crane wind rating.</span>
  <span class="leg-item"><span class="ci-danger" style="font-size:1.3em;">Ⓧ</span>&nbsp;<strong>STOP</strong> — Gust > 14 m/s (> 27 kt). Do not commence lifting operations.</span>
</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="info-section">
<p style="font-size:0.78rem; color:#888;">Thresholds are based on BS 7121-1:2016 and HSE PM55 general guidance. Your specific crane manual may impose lower limits — always apply the more conservative figure.</p>
</div>""", unsafe_allow_html=True)

    # ── Where's The Catch ─────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>🪤 Where's The Catch?</h3>
<p>
There isn't a hidden one, but here's the honest picture:
</p>
<ul>
<li><strong>Free API limitation:</strong> The Open-Meteo free tier gives full ECMWF IFS resolution for the first 7 days, but the raw ECMWF data is updated every 6 hours. The free tier doesn't include the commercial ECMWF API with real-time sub-hourly updates. For planning purposes — which is what this is for — that's absolutely fine.</li>
<li><strong>This is not a replacement for your anemometer.</strong> It never will be. It's a planning tool, not a real-time measurement instrument.</li>
<li><strong>Funding:</strong> Running this costs time and, if I move to a paid API tier, money. If Windcast has saved you a wasted mobilisation or helped you make a better call, a small Ko-fi tip helps keep it online and improving.</li>
</ul>
<p><strong>Email list:</strong> If you'd like to be notified personally the moment tips cover the cost of the paid ECMWF API (which would unlock more frequent forecast updates), drop your email in the feedback form and mention it. I'll contact everyone individually — no mailing list software, no spam.</p>
</div>""", unsafe_allow_html=True)

    # Ko-fi button
    st.markdown(f"""
<div style="margin: 0.8rem 0;">
<a href="{KOFI_URL}" target="_blank" style="
    display: inline-flex; align-items: center; gap: 8px;
    background: #FF5E5B; color: #fff; font-weight: 700; font-size: 0.9rem;
    padding: 9px 18px; border-radius: 7px; text-decoration: none;
    box-shadow: 0 2px 6px rgba(255,94,91,0.4);">
    ☕ Support Windcast on Ko-fi
</a>
</div>""", unsafe_allow_html=True)

    # ── Version & Changelog ────────────────────────────────────────────────────
    st.markdown("""<div class="info-section">
<h3>📦 Version & Changelog</h3>
<p><span class="info-badge">v4.0 — Current</span></p>
<ul>
<li><strong>v4.0 — April 2026:</strong> Added tabs (Forecast / Info), disclaimer acknowledgement, shareable URL, Ko-fi support, feedback link, mobile-first location input, advanced model selection expander.</li>
<li><strong>v3.1 — March 2026:</strong> Merged land and offshore into single app. Added combined Go/No-Go across all parameters.</li>
<li><strong>v2.1 — February 2026:</strong> Added swell Hs, visibility, air and sea temperature. Switched to ECMWF-only model (removed blended consensus) for safety-critical accuracy.</li>
<li><strong>v1.0 — October 2025:</strong> Initial release. ECMWF + ICON + GFS consensus, BS 7121 height correction, colour-coded wind table.</li>
</ul>
</div>""", unsafe_allow_html=True)

    # ── Feedback ──────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="margin-top: 1.5rem; padding: 0.6rem 0.8rem; background: #0d0d1a;
    border: 1px solid #333; border-radius: 5px; font-size: 0.8rem; color: #888;">
📝 <a href="{FEEDBACK_URL}" target="_blank" style="color:#90CAF9;">Found an error or want to suggest something? Tell me here.</a>
</div>""", unsafe_allow_html=True)

    # Regulatory footer
    st.markdown("""<div class="disclaimer" style="margin-top: 1rem;">
⚠️ <b>FOR PLANNING PURPOSES ONLY.</b> Does not replace a calibrated on-site anemometer.
Lifting supervisor retains full Go / No-Go responsibility per <b>BS 7121-1:2016</b>,
<b>LOLER 1998</b>, <b>HSE PM55</b> and <b>IMCA LR006</b>.
Data: ECMWF IFS 0.25° via Open-Meteo (free tier). v4.0
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Session defaults — disclaimer_ack MUST be first to avoid KeyError ─────
    if "disclaimer_ack" not in st.session_state:
        st.session_state["disclaimer_ack"] = False
    for k, v in [("mode","land"),("crane_h",40),("lat",None),("lon",None),("loc_name",""),("fdays",1)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Read shareable URL params on first load ────────────────────────────────
    params = st.query_params
    if st.session_state.lat is None and "lat" in params and "lon" in params:
        try:
            st.session_state.lat      = float(params["lat"])
            st.session_state.lon      = float(params["lon"])
            st.session_state.loc_name = f"{st.session_state.lat:.4f}°N, {st.session_state.lon:.4f}°E"
            if "h" in params:
                st.session_state.crane_h = max(10, min(250, int(params["h"])))
            if "mode" in params and params["mode"] in ("land","offshore"):
                st.session_state.mode = params["mode"]
        except Exception:
            pass

    mode = st.session_state.mode

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE TITLE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="page-title">Lifting Ops Forecast</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # DISCLAIMER — shown once per session before any forecast content loads
    # ══════════════════════════════════════════════════════════════════════════
    if not st.session_state.disclaimer_ack:
        st.warning(
            "⚠️ **Planning Tool — Regulatory Notice**\n\n"
            "Windcast provides forecast data for lift planning purposes only. "
            "It does **not** replace a calibrated on-site anemometer. "
            "The lifting supervisor remains solely responsible for all Go/No-Go decisions "
            "under **BS 7121-1:2016**, **LOLER 1998**, and **HSE PM55**. "
            "Always verify conditions with a calibrated instrument before commencing any lifting operation."
        )
        ack = st.checkbox(
            "I understand this forecast is for planning purposes only. "
            "I will verify conditions with a calibrated on-site anemometer before commencing any lifting operation.",
            key="disclaimer_checkbox",
        )
        if ack:
            st.session_state.disclaimer_ack = True
            st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # TOP-LEVEL TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab_forecast, tab_info = st.tabs(["🌤️ Forecast", "ℹ️ Info"])

    # ══════════════════════════════════════════════════════════════════════════
    # FORECAST TAB
    # ══════════════════════════════════════════════════════════════════════════
    with tab_forecast:

        # ── Controls row — location FIRST so it stacks on top on mobile ───────
        # Row A: Location (wide) | Save pin | Fetch button
        if mode == "land":
            ra = st.columns([3.2, 0.55, 1.0, 1.7, 1.1, 0.8, 1.5])
        else:
            ra = st.columns([3.2, 0.55, 1.0, 1.1, 0.8, 1.5])

        with ra[0]:
            search_val = st.text_input(
                "Location",
                value=st.session_state.loc_name if st.session_state.lat else "",
                placeholder="Postcode · Place name · lat ; lon",
                key="search_input",
            )
            st.markdown('<div class="coord-hint">Lat (°N) ; Lon (°E) — or enter UK postcode / place name</div>',
                        unsafe_allow_html=True)

        with ra[1]:
            st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
            save_btn = st.button("📌", use_container_width=True, key="save_btn", help="Save this site")

        with ra[2]:
            crane_h = st.number_input("Height (m)", min_value=10, max_value=250,
                                       value=st.session_state.crane_h, step=5, key="crane_num")
            st.session_state.crane_h = crane_h

        if mode == "land":
            with ra[3]:
                terrain = st.selectbox("Terrain type", list(TERRAIN.keys()), key="terrain",
                                       help="Affects wind shear height correction (~10–20%)")
            with ra[4]:
                wind_unit = st.selectbox("Wind units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit")
            with ra[5]:
                temp_unit = st.selectbox("Temp", ["°C", "°F"], key="temp_unit")
            with ra[6]:
                st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
                fetch_btn = st.button("🌤️ Get Forecast", use_container_width=True,
                                       type="primary", key="fetch_btn")
        else:
            terrain = "Open / Coastal"
            with ra[3]:
                wind_unit = st.selectbox("Wind units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit")
            with ra[4]:
                temp_unit = st.selectbox("Temp", ["°C", "°F"], key="temp_unit")
            with ra[5]:
                st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
                fetch_btn = st.button("🌤️ Get Forecast", use_container_width=True,
                                       type="primary", key="fetch_btn")

        st.markdown('<hr style="border-color:#222;margin:0.5rem 0 0 0;">', unsafe_allow_html=True)

        # ── Resolve location ──────────────────────────────────────────────────
        lat      = st.session_state.lat
        lon      = st.session_state.lon
        loc_name = st.session_state.loc_name

        if search_val and (search_val != loc_name or lat is None):
            with st.spinner("Looking up location…"):
                lat_new, lon_new, name_new = parse_search(search_val)
            if lat_new:
                lat = lat_new; lon = lon_new; loc_name = name_new
                st.session_state.lat      = lat
                st.session_state.lon      = lon
                st.session_state.loc_name = loc_name
            else:
                st.error("Location not found. Try a UK postcode, place name, or 'lat ; lon'.")
                st.stop()

        if save_btn and lat:
            save_location(loc_name[:40], lat, lon, crane_h, terrain)
            st.success(f"✅ Saved: {loc_name[:40]}")

        # ── Saved locations row ───────────────────────────────────────────────
        saved = load_saved()
        if saved:
            saved_names = [l["name"] for l in saved]
            picked = st.selectbox("📍 Load saved site", ["— select —"] + saved_names,
                                  key="load_saved", label_visibility="visible")
            if picked != "— select —":
                loc = next(l for l in saved if l["name"] == picked)
                st.session_state.lat      = loc["lat"]
                st.session_state.lon      = loc["lon"]
                st.session_state.loc_name = loc["name"]
                st.session_state.crane_h  = loc.get("crane_h", crane_h)

        # ── Fetch ─────────────────────────────────────────────────────────────
        if lat is None:
            st.markdown(
                '<div class="box-info" style="margin-top:1rem;">👆 Enter a location above and click <b>Get Forecast</b>.<br>'
                'Supports UK postcodes (e.g. <code>RG12 1BE</code>), place names, or coordinates (<code>51.08 ; -1.29</code>).</div>',
                unsafe_allow_html=True
            )
            st.stop()

        if lat is None or lon is None:
            st.error("No location set.")
            st.stop()

        if fetch_btn:
            # Update shareable URL query params
            st.query_params.update({"lat": f"{lat:.4f}", "lon": f"{lon:.4f}",
                                    "h": str(crane_h), "mode": mode})
            # Clear cached data so fresh fetch happens
            fetch_ecmwf_land.clear()
            fetch_offshore_wind.clear()
            fetch_offshore_marine.clear()
            for k in ["df_cache", "marine_cache", "fetch_time"]:
                st.session_state.pop(k, None)

        if fetch_btn or ("df_cache" not in st.session_state):
            if mode == "land":
                with st.spinner("Fetching ECMWF IFS forecast…"):
                    df, models_used = fetch_consensus(lat, lon, 168)
                if df is None or df.empty:
                    st.error("All weather models failed to respond. Check your internet connection and try again.")
                    st.stop()
                st.session_state.df_cache      = df
                st.session_state.models_used   = models_used
                st.session_state.marine_cache  = None
            else:
                with st.spinner("Fetching ECMWF wind + Open-Meteo Marine data…"):
                    df     = fetch_offshore_wind(lat, lon, 168)
                    marine = fetch_offshore_marine(lat, lon, 168)
                if df is None or df.empty:
                    st.error("Failed to fetch wind data. Check connection and try again.")
                    st.stop()
                st.session_state.df_cache     = df
                st.session_state.marine_cache = marine
            st.session_state.fetch_time = datetime.now(timezone.utc)

        df      = st.session_state.get("df_cache")
        marine  = st.session_state.get("marine_cache")
        fetch_t = st.session_state.get("fetch_time", datetime.now(timezone.utc))

        if df is None or df.empty:
            st.error("No forecast data retrieved — check connection or try a different location.")
            st.stop()

        # ══════════════════════════════════════════════════════════════════════
        # FORECAST SECTION HEADER
        # ══════════════════════════════════════════════════════════════════════
        DAY_OPTIONS = {1: 24, 3: 72, 7: 168}
        forecast_hours = DAY_OPTIONS[st.session_state.fdays]

        hc = st.columns([1.4, 0.6, 0.6, 0.6, 3.5, 0.8, 0.8, 0.7, 0.7])

        with hc[0]:
            st.markdown('<div class="page-title" style="font-size:1.5rem;margin:0.5rem 0 0 0;">Forecast</div>',
                        unsafe_allow_html=True)

        for i, (days, hrs) in enumerate(DAY_OPTIONS.items()):
            with hc[i + 1]:
                label    = f"{days} day" if days == 1 else f"{days} days"
                btn_type = "primary" if st.session_state.fdays == days else "secondary"
                st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
                if st.button(label, key=f"day_{days}", type=btn_type, use_container_width=True):
                    st.session_state.fdays = days
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with hc[5]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            land_type = "primary" if mode == "land" else "secondary"
            if st.button("🐝️Land", key="toggle_land", type=land_type, use_container_width=True):
                if mode != "land":
                    st.session_state.mode = "land"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with hc[6]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            sea_type = "primary" if mode == "offshore" else "secondary"
            if st.button("🪸 Sea", key="toggle_sea", type=sea_type, use_container_width=True):
                if mode != "offshore":
                    st.session_state.mode = "offshore"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Build table rows ──────────────────────────────────────────────────
        if mode == "land":
            rows = build_land_table_html(df, crane_h, terrain, wind_unit, temp_unit, forecast_hours)
            hdr  = land_header(crane_h)
        else:
            rows = build_offshore_table_html(df, marine, crane_h, wind_unit, temp_unit, forecast_hours)
            hdr  = offshore_header(crane_h)

        # ── PDF download ──────────────────────────────────────────────────────
        with hc[7]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            try:
                import weasyprint, io
                pdf_css_extra = """
                @page { margin:10mm; size:A4 landscape; }
                body { background:#0d0d1a; color:#ddd; font-family:Arial,sans-serif; font-size:8pt; }
                table { width:100%; border-collapse:collapse; }
                thead th { background:#0f3460; color:#90CAF9; padding:5px 4px;
                           border-bottom:2px solid #1565C0; font-size:7.5pt; }
                thead th.h10 { background:#0a2a50; color:#64B5F6; }
                thead th.hcr { background:#004d40; color:#80CBC4; }
                tbody tr { border-bottom:1px solid #222; }
                td { padding:4px 4px; text-align:center; vertical-align:middle; }
                td.time-col { color:#90CAF9; font-weight:bold; }
                td.h10 { background:#0a2a50; }
                td.hcr { background:#004d40; }
                .ci-safe { color:#1E88E5; } .ci-caution { color:#FB8C00; } .ci-danger { color:#8E24AA; }
                """
                row_html_str   = "\n".join(rows)
                table_html_full = (
                    f'<table><thead>{hdr}</thead>'
                    f'<tbody>{row_html_str}</tbody></table>'
                )
                pdf_html = f"""<!DOCTYPE html><html><head>
                <meta charset="utf-8">
                <style>{pdf_css_extra}</style></head>
                <body>
                <h3 style="color:#90CAF9;margin-bottom:4px;">Lifting Ops Forecast — {loc_name}</h3>
                <p style="color:#888;font-size:7pt;margin:0 0 6px 0;">
                Crane {crane_h}m · {forecast_hours}h forecast · Generated {fetch_t.strftime("%Y-%m-%d %H:%M UTC")}
                · {"ECMWF IFS 0.25°" if mode=="land" else "ECMWF Marine"}
                </p>
                {table_html_full}
                <p style="color:#666;font-size:6pt;margin-top:6px;">
                FOR PLANNING PURPOSES ONLY. BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006
                </p>
                </body></html>"""
                pdf_bytes = weasyprint.HTML(string=pdf_html).write_pdf()
                fname = f"lifting_forecast_{loc_name[:20].replace(' ','_')}_{fetch_t.strftime('%Y%m%d_%H%M')}.pdf"
                st.download_button("📄 PDF", data=pdf_bytes, file_name=fname,
                                   mime="application/pdf", use_container_width=True)
            except ImportError:
                st.button("📄 PDF", disabled=True, use_container_width=True,
                          help="Install weasyprint to enable PDF export")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Share button ──────────────────────────────────────────────────────
        with hc[8]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            st.button("🔗 Share", use_container_width=True, key="share_btn",
                      help=f"URL updated with lat/lon — copy from address bar: {lat:.4f}°N, {lon:.4f}°E")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Location + last updated line ──────────────────────────────────────
        updated_str = fetch_t.strftime("%H:%M") if fetch_t else "--:--"
        mode_src    = "ECMWF IFS 0.25°" if mode == "land" else "ECMWF Marine"
        st.markdown(
            f'<div class="info-line">Location: <b>{loc_name}</b> &nbsp;|&nbsp; '
            f'Last updated {updated_str}  ·  {mode_src}</div>',
            unsafe_allow_html=True
        )

        # ── Legend ────────────────────────────────────────────────────────────
        render_legend()

        # ── Offshore special warnings ─────────────────────────────────────────
        if mode == "offshore" and marine is not None and not marine.empty and len(marine) > 0:
            hs_now = safe_float(marine.iloc[0].get("hs"))
            if hs_now >= 2.5:
                wlvl   = "DANGER" if hs_now >= 4.0 else "CAUTION"
                bclass = "box-danger" if wlvl == "DANGER" else "box-caution"
                st.markdown(
                    f'<div class="{bclass}">⚓ <b>Wave Height Warning:</b> Hs = {hs_now:.2f}m — {wlvl}. '
                    f'Review vessel motion limits.</div>',
                    unsafe_allow_html=True
                )

        # ── Forecast table ────────────────────────────────────────────────────
        render_table(rows, hdr, mode)

        # ── Regulatory disclaimer footer ──────────────────────────────────────
        st.markdown("""<div class="disclaimer">
⚠️ <b>FOR PLANNING PURPOSES ONLY.</b> Does not replace a calibrated on-site anemometer.
Lifting supervisor retains full Go / No-Go responsibility per <b>BS 7121-1:2016</b>,
<b>LOLER 1998</b>, <b>HSE PM55</b> and <b>IMCA LR006</b>.
Data: ECMWF IFS 0.25° via Open-Meteo (free tier). v4.0
</div>""", unsafe_allow_html=True)

        # ── Feedback link ─────────────────────────────────────────────────────
        st.markdown(
            f'<div style="margin-top:0.5rem; font-size:0.78rem; color:#555;">'
            f'📝 <a href="{FEEDBACK_URL}" target="_blank" style="color:#666;">Found an error? Tell me.</a>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── Advanced: Model Selection — collapsed at the very bottom ──────────
        models_used = st.session_state.get("models_used", ["ECMWF Marine" if mode == "offshore" else "?"])
        with st.expander("⚙️ Advanced — Model Selection", expanded=False):
            st.markdown("""
**Current model:** ECMWF IFS 0.25° (single-model, direct from Open-Meteo)

Windcast uses ECMWF IFS exclusively — no blending with lower-resolution models.
ECMWF is the highest-accuracy freely available global model and is used as the reference
standard by meteorological agencies worldwide.

Earlier versions blended ECMWF, ICON, GFS and MetOffice UKV with weighted consensus.
After six months of site validation, the single-ECMWF approach consistently outperformed blending.
The blended option may return in a future release as a toggle for advanced users.
""")
            st.write(f"**Active models this session:** {models_used}")
            if df is not None and not df.empty:
                first = df.iloc[0]
                st.write({c: round(float(first[c]), 2) if pd.notna(first.get(c)) else "NaN"
                          for c in ["wind_speed", "wind_gust", "temperature", "pressure", "cloud", "precip"]
                          if c in df.columns})
                st.dataframe(df.head(4))

    # ══════════════════════════════════════════════════════════════════════════
    # INFO TAB
    # ══════════════════════════════════════════════════════════════════════════
    with tab_info:
        render_info_tab()


if __name__ == "__main__":
    main()
