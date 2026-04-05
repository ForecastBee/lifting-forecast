"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   LIFTING OPERATIONS WEATHER FORECAST  v4.0  —  Land + Offshore Combined   ║
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
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Lifting Ops Forecast",
    page_icon="🐝️",
    layout="wide",
    initial_sidebar_state="expanded",
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
/* ── Hide Streamlit chrome (keep sidebar) ── */
#MainMenu, header, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: block !important; }
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
.box-warning { background:rgba(255,193,7,.1); border:1px solid #FFC107; border-radius:7px; padding:.6rem .8rem; margin:.3rem 0; font-size:.8rem; }

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

/* Mobile-first: location input appears first on small screens */
@media (max-width: 768px) {
    .page-title { font-size: 1.4rem; }
    .main .block-container { padding: 0.4rem 0.5rem; }
    .legend-strip { gap: 8px; font-size: 0.7rem; }
    .fc-table { font-size: 0.7rem; }
    .fc-table td { padding: 3px 3px; }
    .hide-mobile { display: none; }
    /* Reorder: location section should be visually first */
    div[data-testid="stVerticalBlock"] > div:first-child {
        order: -1;
    }
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
# DATA FETCH — LAND (ECMWF IFS 0.25° direct)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_ecmwf_land(lat: float, lon: float, hours: int = 168):
    """
    Fetch ECMWF IFS 0.25° directly from Open-Meteo.
    Uses list-of-tuples params so requests sends hourly=x&hourly=y correctly.
    """
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
        now = pd.Timestamp.now().floor("h")
        df = df[df["time"] >= now].reset_index(drop=True)
        return df, ["ECMWF IFS 0.25°"]
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None, []

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

        ws_h = ws * ((crane_h / 10) ** 0.11)
        wg_h = wg * ((crane_h / 10) ** 0.11)

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
    
    if mode == "offshore":
        header_html = header_html.replace('<th>Cloud</th>', '<th class="hide-mobile">Cloud</th>')
        header_html = header_html.replace('<th>Pressure</th>', '<th class="hide-mobile">Pressure</th>')
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
# INFO PAGE CONTENT
# ══════════════════════════════════════════════════════════════════════════════

def render_info_page():
    st.markdown('<div class="page-title" style="font-size:1.8rem;">About Windcast</div>', unsafe_allow_html=True)
    
    # About the Creator
    with st.expander("👤 About the Creator", expanded=True):
        st.markdown("""
        I built Windcast between jobs, out of sheer frustration with the weather forecasts I was getting on site.
        
        I'm a lifting supervisor — not a software engineer. I've stood on too many crane decks watching the wind pick up while some generic forecast told me it was fine. Or worse, cancelled a lift based on a number from a weather station 20 miles away that had nothing to do with the wind at boom height.
        
        My wife is a UX designer. She watched me mutter at spreadsheets and API docs for weeks, then one night she sat down with me and asked: *"What would actually help you make a decision?"*
        
        That conversation turned this from a scrappy script into a real app. She forced me to think about colours, layout, and what a tired lifting supervisor needs to see in three seconds, not three minutes.
        
        Six months later, it's grown beyond anything I expected. Real crane operators are using it. I've had messages from offshore guys saying it saved them a wasted trip. That's why I keep building it.
        
        **I'm not selling anything. I just want the forecast to be right for once.**
        """)
    
    # What It Does
    with st.expander("🎯 What It Does", expanded=True):
        st.markdown("""
        **One sentence:** Windcast gives you a crane-height wind forecast, colour-coded to BS 7121-1:2016, using the best free weather model on the planet.
        
        - **ECMWF IFS** — the same model used by national meteorological agencies worldwide. Not some simplified phone widget.
        - **Height correction** — adjusts 10m wind data to your actual crane hook height using power law (BS 7121-1:2016).
        - **Colour-coded Go/No-Go** — SAFE (blue ●), CAUTION (orange ⬡), STOP (purple Ⓧ). You'll know in half a second.
        - **LOLER-aware** — built for lifting supervisors, by a lifting supervisor. Not a software company.
        - **Land + Offshore** — with wave height, swell, and period for marine lifts.
        - **Completely free** — while the free API tier lasts. No ads, no data harvesting.
        """)
    
    # How To Use
    with st.expander("📋 How To Use", expanded=True):
        st.markdown("""
        1. **Enter your location** — UK postcode, place name, or decimal coordinates (e.g., `51.08 ; -1.29`). Press Enter or click Get Forecast.
        
        2. **Set your crane** — enter the hook height in metres. Choose terrain type (affects wind shear).
        
        3. **Read the table** — each row is one hour. The two wind columns show:
           - Left: 10m reference (what most forecasts give you)
           - Right: **Your crane height** (what actually matters)
        
        4. **Make the call** — the coloured symbol tells you the risk level at your hook height. Blue = go ahead but stay alert. Orange = caution, review your lift plan. Purple = STOP, do not lift.
        
        That's it. No login. No paywall. Just the forecast you actually need.
        """)
    
    # Colour Legend (duplicate for Info page)
    with st.expander("🎨 Colour Legend", expanded=True):
        render_legend()
        st.markdown("""
        **Risk thresholds (gust speed at crane height):**
        - **SAFE** (≤5.9 m/s / 11.5 knots / 13 mph) — normal operations with appropriate precautions
        - **CAUTION** (6–14 m/s / 12–27 knots / 13–31 mph) — increased vigilance, consider limiting lift parameters
        - **STOP** (>14 m/s / 27 knots / 31 mph) — do not lift per BS 7121-1:2016
        
        *These thresholds assume normal lifting conditions. Crane-specific limits and site procedures always take precedence.*
        """)
    
    # Where's The Catch
    with st.expander("💰 Where's The Catch?", expanded=True):
        st.markdown("""
        **No catch. But a few honest notes:**
        
        The free Open-Meteo API tier limits full ECMWF IFS data to the first 6 hours of the forecast. Beyond that, it falls back to a blend of models. I'm working on upgrading to a paid tier that gives full ECMWF for the entire 7-day forecast.
        
        **If you find Windcast useful and want to help:**
        
        [![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/yourusername)
        
        As soon as tips cover the monthly API cost (~$50), everyone on the email list gets notified and the full ECMWF forecast is unlocked for all users.
        
        **No pressure, no paywall, no tracking.** Just an honest request from one lifting supervisor to another.
        """)
    
    # Email signup placeholder
    with st.expander("📧 Get notified when full ECMWF is unlocked", expanded=False):
        st.markdown("""
        Drop your email here (no spam, ever — just one email when the paid API is live):
        """)
        email = st.text_input("Email address", key="info_email", placeholder="crane.op@example.com")
        if st.button("Notify Me", key="notify_btn"):
            st.success("Thanks! You'll hear from me when the full forecast is unlocked.")
            # In production, this would send to a mailing list
    
    # Version & Changelog
    with st.expander("📦 Version & Changelog", expanded=False):
        st.markdown("""
        **Current version: v4.0 — April 2026**
        
        **What's new:**
        - v4.0: Full info page, disclaimer checkbox, shareable location URLs, Ko-fi button, mobile layout improvements
        - v3.1: Added swell Hs, visibility, air and sea temperature, combined Go/No-Go across all parameters
        - v3.0: Offshore mode with wave height, period, and direction
        - v2.5: Height correction for terrain types (open/coastal, industrial, urban, woodland)
        - v2.0: BS 7121-1:2016 colour-coded risk levels
        - v1.0: Initial release — ECMWF IFS forecast for land operations
        """)
    
    # Feedback link
    st.markdown("---")
    st.markdown("📝 [Found an error or have a suggestion? Tell me](https://forms.google.com/your-feedback-form-url) — I read every message.")

# ══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER ACKNOWLEDGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def check_disclaimer_acknowledged():
    """Check if user has acknowledged the disclaimer. Show modal if not."""
    if "disclaimer_acknowledged" not in st.session_state:
        st.session_state.disclaimer_acknowledged = False
    
    if not st.session_state.disclaimer_acknowledged:
        with st.container():
            st.markdown('<div class="box-warning">', unsafe_allow_html=True)
            st.warning("⚠️ **LEGAL DISCLAIMER**")
            st.markdown("""
            This forecast is generated from public weather data and is for **planning purposes only**.
            
            Actual site conditions may differ significantly due to local topography, equipment, and microclimates.
            
            **I understand that:**  
            - This forecast does not replace a calibrated on-site anemometer  
            - I will verify conditions before commencing any lifting operation  
            - The lifting supervisor retains full Go/No-Go responsibility per BS 7121-1:2016 and LOLER 1998
            """)
            ack = st.checkbox("I acknowledge and agree to verify conditions with on-site equipment before lifting")
            if ack:
                if st.button("Continue to Forecast", type="primary"):
                    st.session_state.disclaimer_acknowledged = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()
    
    return True

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🐝️ Windcast")
        st.markdown("*Lifting Ops Weather*")
        st.markdown("---")
        
        # Ko-fi button
        st.markdown("""
        <div style="text-align: center; margin: 10px 0;">
            <a href="https://ko-fi.com/yourusername" target="_blank">
                <img src="https://cdn.ko-fi.com/cdn/kofi3.png?v=3" alt="Support on Ko-fi" 
                     style="height: 36px; border-radius: 8px;">
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick settings
        st.markdown("### ⚙️ Quick Settings")
        
        # Mode selector
        mode = st.radio("Operation Type", ["Land", "Offshore"], horizontal=True, key="sidebar_mode")
        st.session_state.mode = mode.lower()
        
        # Crane height
        crane_h = st.number_input("Crane height (m)", min_value=10, max_value=250,
                                  value=st.session_state.get("crane_h", 40), step=5,
                                  key="sidebar_crane")
        st.session_state.crane_h = crane_h
        
        # Wind units
        wind_unit = st.selectbox("Wind units", list(WIND_UNIT_FACTORS.keys()), 
                                key="sidebar_wind_unit")
        st.session_state.wind_unit = wind_unit
        
        # Temp units
        temp_unit = st.selectbox("Temperature", ["°C", "°F"], key="sidebar_temp_unit")
        st.session_state.temp_unit = temp_unit
        
        st.markdown("---")
        
        # Feedback link
        st.markdown("📝 [Report an error](https://forms.google.com/your-feedback-form-url)")
        
        # Debug expander (collapsed by default)
        with st.expander("⚙️ Advanced — Model Selection"):
            st.markdown("""
            **ECMWF IFS 0.25°** is the default and recommended model.
            
            It's the same model used by national meteorological agencies worldwide.
            
            No other models are currently enabled to ensure forecast consistency.
            """)
            st.info("Full ECMWF IFS forecast is active for the first 6 hours. Beyond that, Open-Meteo blends with other models.")
        
        st.markdown("---")
        st.caption("v4.0 | BS 7121-1:2016 | LOLER 1998")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Session defaults ──────────────────────────────────────────────────────
    for k, v in [("mode","land"),("crane_h",40),("lat",None),("lon",None),
                 ("loc_name",""),("fdays",1),("wind_unit","m/s"),
                 ("temp_unit","°C"),("terrain","Open / Coastal")]:
        if k not in st.session_state:
            st.session_state[k] = v
    
    # Read query params for location sharing
    query_params = st.query_params
    if "lat" in query_params and "lon" in query_params:
        try:
            lat_q = float(query_params["lat"])
            lon_q = float(query_params["lon"])
            if st.session_state.lat is None:
                st.session_state.lat = lat_q
                st.session_state.lon = lon_q
                st.session_state.loc_name = f"{lat_q:.4f}°N, {lon_q:.4f}°E"
        except (ValueError, TypeError):
            pass
    
    # Disclaimer check (must happen before any forecast loads)
    check_disclaimer_acknowledged()
    
    # Render sidebar
    render_sidebar()
    
    mode = st.session_state.mode
    wind_unit = st.session_state.wind_unit
    temp_unit = st.session_state.temp_unit
    crane_h = st.session_state.crane_h
    
    # ── Tabs for Forecast / Info ──────────────────────────────────────────────
    tab1, tab2 = st.tabs(["🌤️ Forecast", "ℹ️ Info"])
    
    with tab1:
        # ══════════════════════════════════════════════════════════════════════
        # PAGE TITLE
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="page-title">Lifting Ops Forecast</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # CONTROLS ROW (Location first on mobile)
        # ══════════════════════════════════════════════════════════════════════
        if mode == "land":
            c1,c2,c3,c4,c5,c6,c7 = st.columns([1.0, 3.2, 0.55, 1.7, 1.1, 0.8, 1.5])
        else:
            c1,c2,c3,c4,c5,c6 = st.columns([1.0, 3.2, 0.55, 1.1, 0.8, 1.5])

        with c1:
            crane_h_input = st.number_input("Crane height (m)", min_value=10, max_value=250,
                                       value=crane_h, step=5, key="crane_num")
            st.session_state.crane_h = crane_h_input

        with c2:
            search_val = st.text_input(
                "Location",
                value=st.session_state.loc_name if st.session_state.lat else "",
                placeholder="Postcode · Place name · lat ; lon",
                key="search_input",
            )
            st.markdown('<div class="coord-hint">Lat (°N) ; Lon (°E)</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
            save_btn = st.button("📌", use_container_width=True, key="save_btn", help="Save this site")

        if mode == "land":
            with c4:
                terrain = st.selectbox("Terrain type", list(TERRAIN.keys()), key="terrain",
                                       help="Affects wind shear height correction (~10–20%)")
                st.session_state.terrain = terrain
            with c5:
                wind_unit_sel = st.selectbox("Wind speed units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit_sel")
                st.session_state.wind_unit = wind_unit_sel
            with c6:
                temp_unit_sel = st.selectbox("Temp units", ["°C", "°F"], key="temp_unit_sel")
                st.session_state.temp_unit = temp_unit_sel
            with c7:
                st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
                fetch_btn = st.button("🌤️ Get Forecast", use_container_width=True,
                                       type="primary", key="fetch_btn")
        else:
            terrain = "Open / Coastal"
            with c4:
                wind_unit_sel = st.selectbox("Wind speed units", list(WIND_UNIT_FACTORS.keys()), key="wind_unit_sel")
                st.session_state.wind_unit = wind_unit_sel
            with c5:
                temp_unit_sel = st.selectbox("Temp units", ["°C", "°F"], key="temp_unit_sel")
                st.session_state.temp_unit = temp_unit_sel
            with c6:
                st.markdown('<div style="height:1.65rem"></div>', unsafe_allow_html=True)
                fetch_btn = st.button("🌤️ Get Forecast", use_container_width=True,
                                       type="primary", key="fetch_btn")

        st.markdown('<hr style="border-color:#222;margin:0.5rem 0 0 0;">', unsafe_allow_html=True)

        # ── Resolve location ──────────────────────────────────────────────────────
        lat = st.session_state.lat
        lon = st.session_state.lon
        loc_name = st.session_state.loc_name

        if search_val and (search_val != loc_name or lat is None):
            with st.spinner("Looking up location…"):
                lat_new, lon_new, name_new = parse_search(search_val)
            if lat_new:
                lat = lat_new; lon = lon_new; loc_name = name_new
                st.session_state.lat = lat; st.session_state.lon = lon
                st.session_state.loc_name = loc_name
                # Update URL query params for sharing
                st.query_params.update({"lat": f"{lat:.4f}", "lon": f"{lon:.4f}"})
            else:
                st.error("Location not found. Try a UK postcode, place name, or 'lat ; lon'.")
                st.stop()

        if save_btn and lat:
            save_location(loc_name[:40], lat, lon, crane_h, terrain)
            st.success(f"✅ Saved: {loc_name[:40]}")

        # ── Saved locations row ───────────────────────────────────────────────────
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
                # Update URL
                st.query_params.update({"lat": f"{loc['lat']:.4f}", "lon": f"{loc['lon']:.4f}"})
                st.rerun()

        # ── Fetch ─────────────────────────────────────────────────────────────────
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
            fetch_ecmwf_land.clear()
            fetch_offshore_wind.clear()
            fetch_offshore_marine.clear()
            for k in ["df_cache", "marine_cache", "fetch_time"]:
                st.session_state.pop(k, None)

        if fetch_btn or ("df_cache" not in st.session_state):
            if mode == "land":
                with st.spinner("Fetching ECMWF IFS forecast…"):
                    df, models_used = fetch_ecmwf_land(lat, lon, 168)
                if df is None or df.empty:
                    st.error("Failed to fetch forecast. Check your internet connection and try again.")
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

        df     = st.session_state.get("df_cache")
        marine = st.session_state.get("marine_cache")
        fetch_t = st.session_state.get("fetch_time", datetime.now(timezone.utc))

        if df is None or df.empty:
            st.error("No forecast data retrieved — check connection or try a different location.")
            st.stop()

        # ══════════════════════════════════════════════════════════════════════════
        # FORECAST SECTION HEADER
        # ══════════════════════════════════════════════════════════════════════════
        DAY_OPTIONS = {1: 24, 3: 72, 7: 168}
        forecast_hours = DAY_OPTIONS[st.session_state.fdays]

        hc = st.columns([1.4, 0.6, 0.6, 0.6, 3.5, 0.8, 0.8, 0.7, 0.7])

        with hc[0]:
            st.markdown('<div style="font-size:1.5rem;margin:0.5rem 0 0 0;">Forecast</div>',
                        unsafe_allow_html=True)

        for i, (days, hrs) in enumerate(DAY_OPTIONS.items()):
            with hc[i + 1]:
                label = f"{days} day" if days == 1 else f"{days} days"
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

        # ── Build table rows ──────────────────────────────────────────────────────
        if mode == "land":
            rows = build_land_table_html(df, crane_h, terrain, wind_unit, temp_unit, forecast_hours)
            hdr  = land_header(crane_h)
        else:
            rows = build_offshore_table_html(df, marine, crane_h, wind_unit, temp_unit, forecast_hours)
            hdr  = offshore_header(crane_h)

        # ── PDF download ──────────────────────────────────────────────────────────
        with hc[7]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            try:
                import weasyprint
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
                row_html_str = "\n".join(rows)
                table_html_full = (
                    f'<table><thead>{hdr}</thead>'
                    f'<tbody>{row_html_str}</tbody></td>'
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

        # ── Share button ──────────────────────────────────────────────────────────
        with hc[8]:
            st.markdown('<div style="margin-top:0.45rem">', unsafe_allow_html=True)
            share_url = f"?lat={lat:.4f}&lon={lon:.4f}"
            st.button("🔗 Share", use_container_width=True, key="share_btn",
                      help=f"Share this location: {lat:.4f}°N, {lon:.4f}°E")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Location + last updated line ──────────────────────────────────────────
        updated_str = fetch_t.strftime("%H:%M") if fetch_t else "--:--"
        mode_src = "ECMWF IFS 0.25°" if mode == "land" else "ECMWF Marine"
        st.markdown(
            f'<div class="info-line">Location: <b>{loc_name}</b> &nbsp;|&nbsp; '
            f'Last updated {updated_str}  ·  {mode_src}</div>',
            unsafe_allow_html=True
        )

        # ── Legend ────────────────────────────────────────────────────────────────
        render_legend()

        # ── Offshore special warnings ─────────────────────────────────────────────
        if mode == "offshore" and marine is not None and not marine.empty and len(marine) > 0:
            hs_now = safe_float(marine.iloc[0].get("hs"))
            if hs_now >= 2.5:
                wlvl  = "DANGER" if hs_now >= 4.0 else "CAUTION"
                bclass = "box-danger" if wlvl == "DANGER" else "box-caution"
                st.markdown(f'<div class="{bclass}">⚓ <b>Wave Height Warning:</b> Hs = {hs_now:.2f}m — {wlvl}. Review vessel motion limits.</div>',
                            unsafe_allow_html=True)

        # ── Forecast table — renders inline, page scrolls naturally ──────────────
        render_table(rows, hdr, mode)

        # ── Disclaimer ────────────────────────────────────────────────────────────
        st.markdown("""<div class="disclaimer">
⚠️ <b>FOR PLANNING PURPOSES ONLY.</b> Does not replace a calibrated on-site anemometer.
Lifting supervisor retains full Go / No-Go responsibility per <b>BS 7121-1:2016</b>,
<b>LOLER 1998</b>, <b>HSE PM55</b> and <b>IMCA LR006</b>.
Data: ECMWF IFS 0.25° via Open-Meteo (free tier). v4.0
</div>""", unsafe_allow_html=True)
    
    with tab2:
        render_info_page()


if __name__ == "__main__":
    main()
