"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   WINDCAST  v5.7  —  Lifting Operations Weather Forecast                    ║
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
KOFI_URL     = _secret("KOFI_URL", "https://ko-fi.com/windcast")

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700;800;900&family=Barlow:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;}
#MainMenu,header,footer{visibility:hidden;}
section[data-testid="stSidebar"]{display:none!important;}
button[data-testid="collapsedControl"]{display:none!important;}

:root{
--bg:#080f1f; --surface:#0e1729; --card:#141f35; --card-hi:#1b2844;
--rim:#1e2f4a; --muted:#2a3d5c; --accent:#3b82f6;
--safe:#22c55e; --warn:#f59e0b; --stop:#ef4444;
--txt:#e2eaff; --txt-dim:#7a90b8;
--font-h:'Barlow Condensed',sans-serif;
--font-b:'Barlow',sans-serif;
--font-m:'JetBrains Mono',monospace;
}

body,.stApp{background:var(--bg)!important;color:var(--txt)!important;font-family:var(--font-b);}
.main .block-container{padding:0!important;max-width:100%!important;}
.stApp >div{background:var(--bg)!important;}

/* ── Remove Streamlit default gaps ── */
div[data-testid="stVerticalBlock"] >div{gap:0!important;}
div[data-testid="stHorizontalBlock"]{gap:.5rem!important;}
.element-container{margin:0!important;padding:0!important;}
div[data-testid="stVerticalBlockBorderWrapper"]{padding:0!important;}

/* ════════════════════════════════════════════════════════════
   NAV BAR — logo rendered in HTML, buttons via Streamlit
   ════════════════════════════════════════════════════════════ */
.wc-nav-wrap{
background:rgba(14,23,41,.97);
backdrop-filter:blur(12px);
border-bottom:1px solid var(--rim);
position:sticky;top:0;z-index:100;
display:flex;align-items:center;
height:56px;padding:0 1rem;gap:.5rem;
}
.wc-logo{
font-family:var(--font-h);font-weight:900;font-size:1.4rem;
letter-spacing:.06em;display:flex;align-items:center;gap:.3rem;
flex-shrink:0;
}
.wc-logo .bolt{color:#fbbf24;}
.wc-logo .cast{color:var(--accent);}
.nav-spacer{flex:1;}
.wc-nav-sep{width:1px;height:20px;background:var(--rim);flex-shrink:0;}

/* Style ALL nav buttons via wrappers */
.nav-btn button{
background:transparent!important;
border:1px solid transparent!important;
border-radius:6px!important;
color:var(--txt-dim)!important;
font-family:var(--font-h)!important;
font-weight:700!important;font-size:.72rem!important;
letter-spacing:.08em!important;text-transform:uppercase!important;
padding:.28rem .85rem!important;
transition:all .15s!important;
height:auto!important;min-height:0!important;
white-space:nowrap!important;
}
.nav-btn button:hover{background:var(--card)!important;color:var(--txt)!important;}

/* Active forecast/info */
.nav-btn-active button{
background:rgba(59,130,246,.15)!important;
color:var(--accent)!important;
border-color:rgba(59,130,246,.3)!important;
}
/* Active sea */
.nav-btn-sea-active button{
background:rgba(239,68,68,.12)!important;
color:var(--stop)!important;
border-color:rgba(239,68,68,.25)!important;
}

/* ════════════════════════════════════════════════════════════
   MOBILE NAV — 2 rows of 2-way toggles, hidden on desktop
   ════════════════════════════════════════════════════════════ */
.wc-nav-mobile{
background:rgba(14,23,41,.97);
border-bottom:1px solid var(--rim);
padding:.45rem .75rem;
display:none;
flex-direction:column;
gap:.35rem;
}
.wc-nav-mobile-row{
display:flex;
gap:.35rem;
}
.wc-logo-mobile{
font-family:var(--font-h);font-weight:900;font-size:1.2rem;
letter-spacing:.06em;display:flex;align-items:center;gap:.3rem;
padding:.3rem 0 .1rem 0;
}
.wc-logo-mobile .bolt{color:#fbbf24;}
.wc-logo-mobile .cast{color:var(--accent);}

/* ════════════════════════════════════════════════════════════
   CONTROLS BAR
   ════════════════════════════════════════════════════════════ */
.wc-controls-bar{
background:var(--surface);
border-bottom:1px solid var(--rim);
padding:.6rem 1rem;
}

/* Search + GO integrated */
.search-row .stTextInput >div >div >input{
border-radius:6px 0 0 6px!important;
border-right:none!important;
background:var(--card)!important;
border-color:var(--rim)!important;
color:var(--txt)!important;
font-family:var(--font-b)!important;
font-size:.85rem!important;
padding:.45rem .75rem!important;
}
.search-row .stTextInput >div >div >input:focus{
border-color:var(--accent)!important;
box-shadow:0 0 0 2px rgba(59,130,246,.2)!important;
}
.go-btn button{
border-radius:0 6px 6px 0!important;
background:linear-gradient(135deg,#ef4444,#f97316)!important;
border:none!important;color:#fff!important;
font-family:var(--font-h)!important;font-weight:700!important;
font-size:.72rem!important;letter-spacing:.1em!important;
text-transform:uppercase!important;
padding:.45rem .85rem!important;height:auto!important;min-height:0!important;
}
.go-btn button:hover{
box-shadow:0 4px 12px rgba(239,68,68,.35)!important;
transform:translateY(-1px)!important;
}

/* Widget labels */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label{
font-family:var(--font-h)!important;font-weight:700!important;
font-size:.62rem!important;letter-spacing:.12em!important;
text-transform:uppercase!important;color:var(--txt-dim)!important;
margin-bottom:.15rem!important;
}
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] >div{
background:var(--card)!important;border-color:var(--rim)!important;
border-radius:6px!important;color:var(--txt)!important;
font-family:var(--font-b)!important;font-size:.85rem!important;
min-height:0!important;
}
/* Save pin button */
.pin-btn button{
background:var(--card)!important;border:1px solid var(--rim)!important;
border-radius:6px!important;color:var(--txt-dim)!important;
padding:.45rem!important;height:auto!important;min-height:0!important;
}
.pin-btn button:hover{border-color:var(--accent)!important;color:var(--accent)!important;}

/* ════════════════════════════════════════════════════════════
   SEGMENTED CONTROLS — st.radio(horizontal=True)
   ════════════════════════════════════════════════════════════ */
div[data-testid="stRadio"] >label{display:none!important;}
div[data-testid="stRadio"] >div[role="radiogroup"]{
display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
align-items:center!important;
background:var(--bg)!important;
border:1px solid var(--rim)!important;
border-radius:999px!important;
padding:3px!important;gap:2px!important;
width:fit-content!important;
}
div[data-testid="stRadio"] >div[role="radiogroup"] >label{
display:flex!important;align-items:center!important;justify-content:center!important;
border-radius:999px!important;padding:.25rem .9rem!important;margin:0!important;
font-family:var(--font-h)!important;font-weight:700!important;
font-size:.68rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;
color:var(--txt-dim)!important;cursor:pointer!important;
background:transparent!important;border:none!important;
user-select:none!important;white-space:nowrap!important;
transition:all .15s!important;
}
div[data-testid="stRadio"] >div[role="radiogroup"] >label >div:first-child{display:none!important;}
div[data-testid="stRadio"] >div[role="radiogroup"] >label:has(input:checked){
background:var(--accent)!important;color:#fff!important;
}

/* ════════════════════════════════════════════════════════════
   PDF / SHARE buttons
   ════════════════════════════════════════════════════════════ */
.pdf-btn button{
background:linear-gradient(135deg,#ef4444,#f97316)!important;
border:none!important;color:#fff!important;
font-family:var(--font-h)!important;font-weight:700!important;
font-size:.68rem!important;letter-spacing:.08em!important;
text-transform:uppercase!important;border-radius:6px!important;
padding:.28rem .75rem!important;height:auto!important;min-height:0!important;
}
.share-btn button{
background:var(--surface)!important;border:1px solid var(--rim)!important;
color:var(--txt-dim)!important;font-family:var(--font-h)!important;
font-weight:700!important;font-size:.68rem!important;letter-spacing:.08em!important;
text-transform:uppercase!important;border-radius:6px!important;
padding:.28rem .75rem!important;height:auto!important;min-height:0!important;
}
.share-btn button:hover{border-color:var(--accent)!important;color:var(--accent)!important;}

/* ════════════════════════════════════════════════════════════
   OPTIMAL WINDOW BANNER
   ════════════════════════════════════════════════════════════ */
.opt-banner{
background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.3);
border-radius:10px;padding:1rem 1.25rem;
display:flex;align-items:center;gap:1rem;
}
.opt-icon{width:2.5rem;height:2.5rem;border-radius:50%;background:rgba(34,197,94,.15);
display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0;}
.opt-title{font-family:var(--font-h);font-weight:900;font-size:.62rem;
letter-spacing:.15em;text-transform:uppercase;color:var(--safe);margin-bottom:.2rem;}
.opt-text{font-family:var(--font-h);font-weight:700;font-size:1.1rem;color:#fff;line-height:1.2;}
.opt-sub{font-size:.72rem;color:var(--txt-dim);margin-top:.2rem;}
.opt-badge-go{background:var(--safe);color:#000;padding:.3rem .85rem;border-radius:999px;
font-family:var(--font-h);font-weight:900;font-size:.7rem;letter-spacing:.08em;
text-transform:uppercase;flex-shrink:0;}
.opt-badge-nogo{background:var(--stop);color:#fff;padding:.3rem .85rem;border-radius:999px;
font-family:var(--font-h);font-weight:900;font-size:.7rem;letter-spacing:.08em;
text-transform:uppercase;flex-shrink:0;}

/* ════════════════════════════════════════════════════════════
   LEGEND
   ════════════════════════════════════════════════════════════ */
.legend-strip{background:var(--card);border:1px solid var(--rim);border-radius:8px;
padding:.6rem 1rem;display:flex;flex-wrap:wrap;align-items:center;gap:1rem;}
.legend-title{font-family:var(--font-h);font-weight:900;font-size:.58rem;
letter-spacing:.15em;text-transform:uppercase;color:var(--txt-dim);}
.legend-item{display:flex;align-items:center;gap:.45rem;
font-family:var(--font-h);font-weight:700;font-size:.72rem;}
.leg-dot{width:.72rem;height:.72rem;border-radius:50%;flex-shrink:0;}
.leg-safe{background:var(--safe);box-shadow:0 0 6px rgba(34,197,94,.5);}
.leg-warn{background:var(--warn);box-shadow:0 0 6px rgba(245,158,11,.5);}
.leg-stop{background:var(--stop);box-shadow:0 0 6px rgba(239,68,68,.5);}

/* ════════════════════════════════════════════════════════════
   TABLE
   ════════════════════════════════════════════════════════════ */
.table-wrap-outer{background:var(--card);border:1px solid var(--rim);border-radius:10px;overflow-x:auto;}
.wc-table{width:100%;border-collapse:collapse;font-family:var(--font-b);font-size:.82rem;min-width:700px;}
.wc-table thead tr{background:var(--surface);}
.wc-table thead th{padding:.75rem .7rem;text-align:center;
font-family:var(--font-h);font-weight:900;font-size:.62rem;
letter-spacing:.12em;text-transform:uppercase;color:var(--txt-dim);
white-space:nowrap;border-bottom:2px solid var(--rim);}
.wc-table thead th.th-crane{color:var(--accent);background:rgba(59,130,246,.08);
border-bottom:3px solid rgba(59,130,246,.4);}
.wc-table tbody tr{border-bottom:1px solid rgba(30,47,74,.5);transition:background .1s;}
.wc-table tbody tr:hover{background:rgba(59,130,246,.07);}
.wc-table tbody tr.day-break td{border-top:2px solid var(--rim);}
.wc-table td{padding:.75rem .7rem;text-align:center;vertical-align:middle;}
.td-time{font-family:var(--font-h);font-weight:700;font-size:.95rem;
color:var(--accent);text-align:left;white-space:nowrap;}
.td-wind{font-family:var(--font-m);font-weight:600;font-size:.8rem;line-height:1.7;}
.td-wind small{display:block;font-size:.68rem;opacity:.7;font-weight:400;}
.td-crane{background:rgba(59,130,246,.05);}
.td-safe{color:var(--safe);}.td-warn{color:var(--warn);}.td-stop{color:var(--stop);}
.td-dim{color:var(--txt-dim);}
.td-dir{font-family:var(--font-m);font-size:.78rem;color:var(--txt-dim);}
.rain-0{background:transparent;}.rain-1{background:rgba(59,130,246,.05);}
.rain-2{background:rgba(59,130,246,.11);}.rain-3{background:rgba(59,130,246,.2);}
.rain-4{background:rgba(30,64,175,.35);}
.temp-chip{display:inline-block;padding:.18rem .45rem;border-radius:5px;
font-family:var(--font-m);font-size:.75rem;font-weight:600;}
.sts-safe{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;border-radius:999px;
background:rgba(34,197,94,.13);border:1px solid rgba(34,197,94,.3);
color:var(--safe);font-family:var(--font-h);font-weight:700;font-size:.62rem;letter-spacing:.08em;}
.sts-warn{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;border-radius:999px;
background:rgba(245,158,11,.13);border:1px solid rgba(245,158,11,.3);
color:var(--warn);font-family:var(--font-h);font-weight:700;font-size:.62rem;letter-spacing:.08em;}
.sts-stop{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;border-radius:999px;
background:rgba(239,68,68,.13);border:1px solid rgba(239,68,68,.3);
color:var(--stop);font-family:var(--font-h);font-weight:700;font-size:.62rem;letter-spacing:.08em;}

/* ════════════════════════════════════════════════════════════
   TABLE CONTROLS ROW
   ════════════════════════════════════════════════════════════ */
.tbl-title-label{font-family:var(--font-h);font-weight:900;font-size:1.1rem;color:#fff;}
.tbl-meta-label{font-size:.72rem;color:var(--txt-dim);margin-top:.1rem;}

/* ════════════════════════════════════════════════════════════
   MISC
   ════════════════════════════════════════════════════════════ */
.wc-disclaimer{background:rgba(8,15,31,.8);border:1px solid var(--rim);border-radius:8px;
padding:.6rem .9rem;font-family:var(--font-b);font-size:.68rem;
color:var(--txt-dim);line-height:1.55;margin-top:.8rem;}
.box-info{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.3);
border-radius:8px;padding:.75rem 1rem;font-size:.85rem;color:var(--accent);}
.box-caution{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.4);
border-radius:8px;padding:.6rem .8rem;font-size:.82rem;color:var(--warn);}
.box-danger{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.4);
border-radius:8px;padding:.6rem .8rem;font-size:.82rem;color:var(--stop);}

/* ════════════════════════════════════════════════════════════
   MOBILE
   ════════════════════════════════════════════════════════════ */
@media(max-width:768px){
.wc-nav-wrap{height:52px;padding:0 .75rem;}
.wc-logo{font-size:1.15rem;}
.hide-mobile{display:none!important;}
.wc-table{font-size:.72rem;min-width:580px;}
.wc-table td{padding:.5rem .4rem;}
.td-time{font-size:.8rem;}
div[data-testid="stRadio"] >div[role="radiogroup"] >label{padding:.22rem .6rem!important;font-size:.62rem!important;}

/* On mobile: hide desktop nav, show mobile nav */
.wc-nav-wrap{display:none!important;}
.wc-nav-mobile{display:flex!important;}

/* Mobile pill toggle — each radio group fills full width */
.mob-nav div[data-testid="stRadio"] >div[role="radiogroup"]{
width:100%!important;
border-radius:8px!important;
}
.mob-nav div[data-testid="stRadio"] >div[role="radiogroup"] >label{
flex:1!important;
justify-content:center!important;
padding:.45rem .5rem!important;
font-size:.75rem!important;
border-radius:6px!important;
}
}
@media(max-width:480px){
.wc-nav-btn-text{display:none;}
}

/* ════════════════════════════════════════════════════════════
   INFO PAGE
   ════════════════════════════════════════════════════════════ */
.info-h{font-family:var(--font-h);font-weight:900;font-size:1rem;color:var(--accent);
border-bottom:1px solid var(--rim);padding-bottom:.35rem;margin-bottom:.65rem;}
.info-p{font-family:var(--font-b);font-size:.84rem;color:var(--txt-dim);line-height:1.65;margin-bottom:.5rem;}
.info-li{display:flex;gap:.5rem;font-family:var(--font-b);font-size:.82rem;
color:var(--txt-dim);line-height:1.55;margin-bottom:.28rem;}
.info-num{font-family:var(--font-h);font-weight:900;color:var(--accent);flex-shrink:0;min-width:1.2rem;}
.info-badge{display:inline-block;background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.3);
border-radius:5px;padding:.12rem .55rem;font-family:var(--font-m);font-size:.72rem;color:var(--accent);margin:.1rem .12rem;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
WIND_UNITS = {"m/s":(1.0,"m/s"),"knots":(1.9438,"kt"),"mph":(2.2369,"mph"),"km/h":(3.6,"km/h"),"Beaufort":(None,"Bft")}
TERRAIN = {
    "Open / Coastal":    {"alpha":0.14,"factor":1.00,"icon":"🌊"},
    "Industrial / Port": {"alpha":0.22,"factor":1.10,"icon":"🏭"},
    "Urban / City":      {"alpha":0.28,"factor":1.20,"icon":"🏙️"},
    "Woodland / Forest": {"alpha":0.20,"factor":1.15,"icon":"🌲"},
}
SAVED_FILE = "forecast_logs/saved_locations.json"
DUR_MAP  = {"1D":24,"3D":72,"7D":168,"MAX":168}
DUR_OPTS = list(DUR_MAP.keys())
RES_OPTS = ["24H","3H"]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def to_bft(ms):
    for i,t in enumerate([0.5,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,28.5,32.7]):
        if ms<t: return i
    return 12

def fmt_wind(ms,unit):
    if unit=="Beaufort": return f"{to_bft(ms)} Bft"
    f,l = WIND_UNITS[unit]; return f"{ms*f:.1f} {l}"

def risk_level(g):
    if g<=5.9: return "safe"
    if g<=14.0: return "warn"
    return "stop"

def risk_sym(l): return {"safe":"●","warn":"⬡","stop":"Ⓧ"}[l]
def risk_css(l): return {"safe":"td-safe","warn":"td-warn","stop":"td-stop"}[l]

def status_badge(l):
    label = {"safe":"SAFE","warn":"CAUTION","stop":"STOP"}[l]
    return f'<span class="sts-{l}">{label}</span>'

def dir_arrow(deg):
    try:
        d=float(deg)
        if np.isnan(d): return "—"
        return ["↓","↙","←","↖","↑","↗","→","↘"][int((d+22.5)/45)%8]
    except: return "—"

def apply_terrain(ws,tk,h):
    t=TERRAIN.get(tk,TERRAIN["Open / Coastal"])
    return ws*t["factor"]*((h/10)**t["alpha"])

def fmt_temp(c,unit):
    return f"{c*9/5+32:.0f}°F" if unit=="°F" else f"{c:.0f}°C"

def sf(val,default=0.0):
    try:
        if val is None or val is pd.NaT: return default
        f=float(val); return default if f!=f else f
    except: return default

def temp_col(t):
    if t<=-3: return "#1565C0","#fff"
    elif t<=0: return "#1976D2","#fff"
    elif t<=5: return "#42A5F5","#000"
    elif t<=10: return "#80DEEA","#000"
    elif t<=15: return "#fff176","#000"
    elif t<=20: return "#ffd54f","#000"
    elif t<=25: return "#ffb74d","#000"
    else: return "#ff8a65","#000"

def rain_cls(mm):
    if mm==0: return "rain-0"
    if mm<0.5: return "rain-1"
    if mm<2.0: return "rain-2"
    if mm<5.0: return "rain-3"
    return "rain-4"

def rain_lbl(mm):
    if mm==0: return "None"
    if mm<0.5: return "Light"
    if mm<2.0: return "Mod"
    if mm<5.0: return "Heavy"
    return "Extreme"

# ══════════════════════════════════════════════════════════════════════════════
# LOCATION
# ══════════════════════════════════════════════════════════════════════════════
def postcode_coords(pc):
    try:
        r=requests.get(f"https://api.postcodes.io/postcodes/{pc.replace(' ','')}",timeout=6)
        d=r.json()
        if d.get("status")==200:
            return d["result"]["latitude"],d["result"]["longitude"],f"{pc.upper()} ({d['result']['admin_district']})"
    except: pass
    return None,None,None

def place_coords(name):
    try:
        r=requests.get("https://nominatim.openstreetmap.org/search",
            params={"q":name,"format":"json","limit":1},
            headers={"User-Agent":"Windcast/5.7"},timeout=6)
        d=r.json()
        if d: return float(d[0]["lat"]),float(d[0]["lon"]),d[0].get("display_name"," ")[:70]
    except: pass
    return None,None,None

def parse_loc(q):
    q=q.strip()
    if not q: return None,None,None
    for sep in [";",","]:
        if sep in q:
            p=q.split(sep,1)
            try:
                la,lo=float(p[0].strip()),float(p[1].strip())
                if -90<=la<=90 and -180<=lo<=180: return la,lo,f"{la:.4f}°N, {lo:.4f}°E"
            except: pass
    if re.match(r'^[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s*\d[A-Za-z]{2}$',q):
        return postcode_coords(q)
    return place_coords(q)

def load_saved():
    try:
        os.makedirs("forecast_logs",exist_ok=True)
        if os.path.exists(SAVED_FILE):
            with open(SAVED_FILE) as f: return json.load(f)
    except: pass
    return []

def save_loc(name,lat,lon,crane_h,terrain):
    locs=load_saved()
    locs=[l for l in locs if l.get("name")!=name]
    locs.insert(0,{"name":name,"lat":lat,"lon":lon,"crane_h":crane_h,"terrain":terrain})
    try:
        with open(SAVED_FILE,"w") as f: json.dump(locs[:12],f,indent=2)
    except: pass

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_land(lat,lon,hours=168):
    params=[("latitude",lat),("longitude",lon),
        ("wind_speed_unit","ms"),("forecast_days",min(hours//24+1,7)),
        ("timezone","auto"),("models","ecmwf_ifs025"),
        ("hourly","wind_speed_10m"),("hourly","wind_gusts_10m"),
        ("hourly","wind_direction_10m"),("hourly","temperature_2m"),
        ("hourly","precipitation"),("hourly","cloud_cover"),
        ("hourly","surface_pressure"),("hourly","visibility"),
        ("hourly","relative_humidity_2m")]
    try:
        r=requests.get("https://api.open-meteo.com/v1/forecast",params=params,timeout=15)
        r.raise_for_status(); body=r.json()
        if body.get("error"): st.error(f"API: {body.get('reason')} "); return None
        h=body.get("hourly",{}); times=h.get("time",[])
        if not times: return None
        n=len(times)
        df=pd.DataFrame({
            "time":pd.to_datetime(times),
            "wind_speed":pd.to_numeric(h.get("wind_speed_10m",[np.nan]*n),errors="coerce"),
            "wind_gust":pd.to_numeric(h.get("wind_gusts_10m",[np.nan]*n),errors="coerce"),
            "wind_dir":pd.to_numeric(h.get("wind_direction_10m",[np.nan]*n),errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m",[np.nan]*n),errors="coerce"),
            "precip":pd.to_numeric(h.get("precipitation",[np.nan]*n),errors="coerce"),
            "cloud":pd.to_numeric(h.get("cloud_cover",[np.nan]*n),errors="coerce"),
            "pressure":pd.to_numeric(h.get("surface_pressure",[np.nan]*n),errors="coerce"),
        })
        return df[df["time"]>=pd.Timestamp.now().floor("h")].reset_index(drop=True)
    except Exception as e: st.error(f"Fetch error: {e} "); return None

@st.cache_data(ttl=1800)
def fetch_offshore_w(lat,lon,hours=168):
    try:
        r=requests.get("https://api.open-meteo.com/v1/forecast",params={
            "latitude":lat,"longitude":lon,
            "hourly":["wind_speed_10m","wind_gusts_10m","wind_direction_10m",
                "temperature_2m","cloud_cover","precipitation","pressure_msl"],
            "models":"ecmwf_ifs04","wind_speed_unit":"ms",
            "forecast_days":min(hours//24+1,7),"timezone":"UTC"},timeout=12)
        r.raise_for_status(); h=r.json().get("hourly",{}); times=h.get("time",[])
        if not times: return None
        n=len(times)
        df=pd.DataFrame({
            "time":pd.to_datetime(times),
            "wind_speed":pd.to_numeric(h.get("wind_speed_10m",[np.nan]*n),errors="coerce"),
            "wind_gust":pd.to_numeric(h.get("wind_gusts_10m",[np.nan]*n),errors="coerce"),
            "wind_dir":pd.to_numeric(h.get("wind_direction_10m",[np.nan]*n),errors="coerce"),
            "temperature":pd.to_numeric(h.get("temperature_2m",[np.nan]*n),errors="coerce"),
            "cloud":pd.to_numeric(h.get("cloud_cover",[np.nan]*n),errors="coerce"),
            "precip":pd.to_numeric(h.get("precipitation",[np.nan]*n),errors="coerce"),
            "pressure":pd.to_numeric(h.get("pressure_msl",[np.nan]*n),errors="coerce"),
        })
        return df[df["time"]>=pd.Timestamp.now().floor("h")].reset_index(drop=True)
    except Exception as e: st.error(f"Wind fetch: {e} "); return None

@st.cache_data(ttl=1800)
def fetch_marine(lat,lon,hours=168):
    try:
        r=requests.get("https://marine-api.open-meteo.com/v1/marine",params={
            "latitude":lat,"longitude":lon,
            "hourly":["wave_height","wave_period","wave_direction","swell_wave_height"],
            "forecast_days":min(hours//24+1,7),"timezone":"UTC"},timeout=12)
        r.raise_for_status(); h=r.json().get("hourly",{}); times=h.get("time",[])
        if not times: return None
        n=len(times)
        df=pd.DataFrame({
            "time":pd.to_datetime(times),
            "hs":pd.to_numeric(h.get("wave_height",[np.nan]*n),errors="coerce"),
            "wave_period":pd.to_numeric(h.get("wave_period",[np.nan]*n),errors="coerce"),
            "wave_dir":pd.to_numeric(h.get("wave_direction",[np.nan]*n),errors="coerce"),
            "swell_hs":pd.to_numeric(h.get("swell_wave_height",[np.nan]*n),errors="coerce"),
        })
        return df[df["time"]>=pd.Timestamp.now().floor("h")].reset_index(drop=True)
    except Exception as e: st.error(f"Marine fetch: {e} "); return None

# ══════════════════════════════════════════════════════════════════════════════
# TABLE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def wind_cells(ws10,wg10,wsh,wgh,unit):
    rl10=risk_level(wg10); rlH=risk_level(wgh)
    return (f'<td class="td-wind"><span class="{risk_css(rl10)}">{risk_sym(rl10)} {fmt_wind(wg10,unit)}</span>'
        f'<small class="td-dim">W {fmt_wind(ws10,unit)}</small></td>'
        f'<td class="td-wind td-crane"><span class="{risk_css(rlH)}">{risk_sym(rlH)} {fmt_wind(wgh,unit)}</span>'
        f'<small class="td-dim">W {fmt_wind(wsh,unit)}</small></td>')

def build_land_rows(df,crane_h,terrain,unit,tunit,hours,s3h=False):
    rows=[]; prev_day=None
    for _,row in df.head(hours).iterrows():
        ts=pd.to_datetime(row["time"])
        if s3h and ts.hour%3!=0: continue
        ws=sf(row.get("wind_speed")); wg=sf(row.get("wind_gust"))
        wsh=apply_terrain(ws,terrain,crane_h); wgh=apply_terrain(wg,terrain,crane_h)
        tmp=sf(row.get("temperature")); prc=sf(row.get("precip"))
        cld=sf(row.get("cloud")); prs=sf(row.get("pressure"),1013.0)
        wd=row.get("wind_dir",np.nan)
        try: wdf=float(wd) if not np.isnan(float(wd)) else np.nan
        except: wdf=np.nan
        day=ts.strftime("%Y-%m-%d"); db=" day-break" if day!=prev_day else ""; prev_day=day
        tc,tf=temp_col(tmp); dstr=f"{dir_arrow(wdf)} {wdf:.0f}°" if not np.isnan(wdf) else "—"
        rows.append(
            f'<tr class="{rain_cls(prc)}{db}">'
            f'<td class="td-time">{ts.strftime("%a %d %b %H:%M")}</td>'
            +wind_cells(ws,wg,wsh,wgh,unit)
            +f'<td class="td-dir">{dstr}</td>'
            +f'<td><span class="temp-chip" style="background:{tc};color:{tf};">{fmt_temp(tmp,tunit)}</span></td>'
            +f'<td class="td-dim" style="font-family:var(--font-m);font-size:.75rem;">{prc:.1f}mm<br><small>{rain_lbl(prc)}</small></td>'
            +f'<td class="td-dim hide-mobile">{cld:.0f}%</td>'
            +f'<td class="td-dim hide-mobile" style="font-family:var(--font-m);font-size:.75rem;">{prs:.0f} hPa</td>'
            +f'<td>{status_badge(risk_level(wgh))}</td></tr>'
        )
    return rows

def build_offshore_rows(wdf_data,mdf,crane_h,unit,tunit,hours,s3h=False):
    rows=[]; prev_day=None
    ml=len(mdf) if mdf is not None else 0
    for i in range(min(hours,len(wdf_data))):
        wr=wdf_data.iloc[i]; ts=pd.to_datetime(wr["time"])
        if s3h and ts.hour%3!=0: continue
        ws=sf(wr.get("wind_speed")); wg=sf(wr.get("wind_gust"))
        wsh=ws*((crane_h/10)**0.11); wgh=wg*((crane_h/10)**0.11)
        tmp=sf(wr.get("temperature")); prc=sf(wr.get("precip"))
        wd=wr.get("wind_dir",np.nan)
        try: wdf2=float(wd) if not np.isnan(float(wd)) else np.nan
        except: wdf2=np.nan
        hs=wp=wdw=sw="—"
        if mdf is not None and i<ml:
            m=mdf.iloc[i]
            hsf=sf(m.get("hs"),np.nan); wpf=sf(m.get("wave_period"),np.nan)
            wdwf=sf(m.get("wave_dir"),np.nan); swf=sf(m.get("swell_hs"),np.nan)
            hs=f"{hsf:.2f}m" if not np.isnan(hsf) else "—"
            wp=f"{wpf:.1f}s" if not np.isnan(wpf) else "—"
            wdw=f"{dir_arrow(wdwf)} {wdwf:.0f}°" if not np.isnan(wdwf) else "—"
            sw=f"{swf:.2f}m" if not np.isnan(swf) else "—"
        day=ts.strftime("%Y-%m-%d"); db=" day-break" if day!=prev_day else ""; prev_day=day
        tc,tf=temp_col(tmp); dstr=f"{dir_arrow(wdf2)} {wdf2:.0f}°" if not np.isnan(wdf2) else "—"
        rows.append(
            f'<tr class="{rain_cls(prc)}{db}">'
            f'<td class="td-time">{ts.strftime("%a %d %b %H:%M")}</td>'
            +wind_cells(ws,wg,wsh,wgh,unit)
            +f'<td class="td-dir">{dstr}</td>'
            +f'<td class="td-dim hide-mobile" style="font-family:var(--font-m)">{hs}</td>'
            +f'<td class="td-dim hide-mobile" style="font-family:var(--font-m)">{wp}</td>'
            +f'<td class="td-dir hide-mobile">{wdw}</td>'
            +f'<td class="td-dim hide-mobile" style="font-family:var(--font-m)">{sw}</td>'
            +f'<td><span class="temp-chip" style="background:{tc};color:{tf};">{fmt_temp(tmp,tunit)}</span></td>'
            +f'<td>{status_badge(risk_level(wgh))}</td></tr>'
        )
    return rows

def land_hdr(ch):
    return (f'<tr><th style="text-align:left;">Date & Time</th>'
        f'<th>Gust/Wind<br><small style="opacity:.6;">10m</small></th>'
        f'<th class="th-crane">Gust/Wind<br><small style="opacity:.8;">{ch}m ✦</small></th>'
        f'<th>Dir</th><th>Temp</th><th>Rain</th>'
        f'<th class="hide-mobile">Cloud</th><th class="hide-mobile">Press</th><th>Status</th></tr>')

def sea_hdr(ch):
    return (f'<tr><th style="text-align:left;">Date & Time</th>'
        f'<th>Gust/Wind<br><small style="opacity:.6;">10m</small></th>'
        f'<th class="th-crane">Gust/Wind<br><small style="opacity:.8;">{ch}m ✦</small></th>'
        f'<th>Dir</th><th class="hide-mobile">Hs (m)</th>'
        f'<th class="hide-mobile">Pd (s)</th><th class="hide-mobile">Wave Dir</th>'
        f'<th class="hide-mobile">Swell</th><th>Temp</th><th>Status</th></tr>')

def render_table(rows,hdr):
    st.markdown(
        f'<div class="table-wrap-outer"><table class="wc-table">'
        f'<thead>{hdr}</thead><tbody>{" ".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTIMAL WINDOW
# ══════════════════════════════════════════════════════════════════════════════
def render_optimal_window(df,crane_h,terrain,mode):
    if df is None or df.empty: return
    wins=[]; cur=None
    for _,row in df.head(72).iterrows():
        wg=sf(row.get("wind_gust"))
        wgh=apply_terrain(wg,terrain,crane_h) if mode=="land" else wg*((crane_h/10)**0.11)
        ts=pd.to_datetime(row["time"])
        if risk_level(wgh)=="safe":
            if cur is None: cur=ts
        else:
            if cur is not None: wins.append((cur,ts-pd.Timedelta(hours=1))); cur=None
    if cur is not None: wins.append((cur,df.iloc[-1]["time"]))
    if wins:
        s,e=wins[0]
        msg=f"Safe to lift {pd.to_datetime(s).strftime('%H:%M')}–{pd.to_datetime(e).strftime('%H:%M')} (next 72h window)"
        badge='<span class="opt-badge-go">GO</span>'
    else:
        msg="No safe window found in the next 72h. Review conditions."
        badge='<span class="opt-badge-nogo">NO-GO</span>'
    st.markdown(f"""
<div class="opt-banner">
 <div class="opt-icon">📅</div>
 <div style="flex:1;min-width:0;">
 <div class="opt-title">Optimal Lift Window</div>
 <div class="opt-text">{msg}</div>
 <div class="opt-sub">Crane {crane_h}m · Gust threshold ≤ 5.9 m/s</div>
 </div>{badge}
</div>""", unsafe_allow_html=True)

def render_legend():
    st.markdown("""
<div class="legend-strip">
 <span class="legend-title">Legend</span>
 <span class="legend-item"><span class="leg-dot leg-safe"></span><span style="color:var(--safe);">SAFE</span>  <span style="color:var(--txt-dim);font-weight:400;">≤ 5.9 m/s</span></span>
 <span class="legend-item"><span class="leg-dot leg-warn"></span><span style="color:var(--warn);">CAUTION</span>  <span style="color:var(--txt-dim);font-weight:400;">6–14 m/s</span></span>
 <span class="legend-item"><span class="leg-dot leg-stop"></span><span style="color:var(--stop);">STOP</span>  <span style="color:var(--txt-dim);font-weight:400;">&gt; 14 m/s</span></span>
 <span class="legend-item" style="margin-left:auto;font-weight:400;color:var(--txt-dim);font-size:.68rem;">Row tint = rain intensity</span>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INFO PAGE
# ══════════════════════════════════════════════════════════════════════════════
def render_info():
    st.markdown('<div style="padding:1.2rem 1.5rem;max-width:860px;">', unsafe_allow_html=True)
    st.markdown("""
<div style="margin-bottom:1.1rem;">
 <div class="info-h">👤 About the Creator</div>
 <p class="info-p">Built between jobs, out of sheer frustration. You know how it is on site — you're trying to make a Go/No-Go call, you check the weather, and what you get bears no resemblance to what the anemometer on the end of the jib is reading.</p>
 <p class="info-p">My wife — a UX designer — finally said: <em>"You clearly know what's wrong with these tools — so build a better one."</em> Six months later it's grown beyond what I expected.</p>
</div>
<div style="margin-bottom:1.1rem;">
 <div class="info-h">🎯 What It Does</div>
 <p class="info-p"><strong>ECMWF IFS forecast, corrected to your crane height per BS 7121, colour-coded for Go/No-Go. Built by a lifting supervisor, not a software company.</strong></p>
 <div class="info-li"><span class="info-num">✦</span><span>ECMWF IFS 0.25° — same model used by professional meteorological agencies worldwide</span></div>
 <div class="info-li"><span class="info-num">✦</span><span>BS 7121 height correction using power law, adjusted for terrain roughness</span></div>
 <div class="info-li"><span class="info-num">✦</span><span>Colour-coded Go/No-Go — SAFE ● CAUTION ⬡ STOP Ⓧ</span></div>
 <div class="info-li"><span class="info-num">✦</span><span>LOLER 1998 aware — built by an Appointed Person, not a software company</span></div>
 <div class="info-li"><span class="info-num">✦</span><span>Sea mode — Hs, swell, wave period, IMCA LR006 height correction (α = 0.11)</span></div>
</div>
<div style="margin-bottom:1.1rem;">
 <div class="info-h">📋 How To Use</div>
 <div class="info-li"><span class="info-num">1.</span><span>Enter your location in the search bar and press <strong>GO</strong> or hit Enter</span></div>
 <div class="info-li"><span class="info-num">2.</span><span>Set crane height. Switch <strong>Land / Sea</strong> from the nav bar top-right</span></div>
 <div class="info-li"><span class="info-num">3.</span><span>For Land: choose terrain type — drives the BS 7121 power-law height correction</span></div>
 <div class="info-li"><span class="info-num">4.</span><span>Read the ✦ crane-height column — gust at your working height, colour-coded</span></div>
 <div class="info-li"><span class="info-num">5.</span><span>Use <strong>1D / 3D / 7D / MAX</strong> and <strong>24H / 3H</strong> toggles to navigate the table</span></div>
 <div class="info-li"><span class="info-num">6.</span><span>Always verify with a calibrated on-site anemometer before any lifting operation</span></div>
</div>
<div style="margin-bottom:1.1rem;">
 <div class="info-h">🎨 Colour Legend</div>
 <div style="display:flex;flex-direction:column;gap:.6rem;margin-top:.3rem;">
 <div style="display:flex;align-items:center;gap:.8rem;">
 <span class="leg-dot leg-safe" style="width:.9rem;height:.9rem;flex-shrink:0;"></span>
 <div><div style="font-family:var(--font-h);font-weight:700;color:var(--safe);">SAFE — Gust ≤ 5.9 m/s (≤ 11.5 kt)</div>
 <div class="info-p" style="margin:0;">Proceed with lift plan.</div></div>
 </div>
 <div style="display:flex;align-items:center;gap:.8rem;">
 <span style="color:var(--warn);flex-shrink:0;font-size:1rem;">⬡</span>
 <div><div style="font-family:var(--font-h);font-weight:700;color:var(--warn);">CAUTION — 6–14 m/s</div>
 <div class="info-p" style="margin:0;">Enhanced monitoring. Review crane wind rating.</div></div>
 </div>
 <div style="display:flex;align-items:center;gap:.8rem;">
 <span style="color:var(--stop);flex-shrink:0;font-size:1rem;">Ⓧ</span>
 <div><div style="font-family:var(--font-h);font-weight:700;color:var(--stop);">STOP — &gt; 14 m/s</div>
 <div class="info-p" style="margin:0;">Do not commence lifting operations.</div></div>
 </div>
</div>
</div>
<div style="margin-bottom:1.1rem;">
 <div class="info-h">🪤 Where's The Catch?</div>
 <p class="info-p">Open-Meteo free tier — full ECMWF IFS resolution for 7 days, updated every 6 hours. This is not a replacement for your anemometer. It never will be.</p>
 <p class="info-p"><strong>Email list:</strong> Drop your email in the feedback form if you want to be notified when tips cover the paid ECMWF API. No spam — I'll contact everyone individually.</p>
</div>
<div style="margin-bottom:1.1rem;">
 <div class="info-h">📦 Changelog</div>
 <span class="info-badge">v5.7 — Current</span>
 <div style="margin-top:.5rem;display:flex;flex-direction:column;gap:.25rem;">
 <div class="info-li"><span class="info-num">▸</span><span><strong>v5.7 — Mobile Nav Fix:</strong> Proper 2-row pill toggles on mobile. Desktop nav hidden on screens &lt;768px.</span></div>
 <div class="info-li"><span class="info-num">▸</span><span><strong>v5.6 — April 2026:</strong> All buttons working via Streamlit session state. Integrated search + GO. Reduced whitespace. Share URL via copy box.</span></div>
 <div class="info-li"><span class="info-num">▸</span><span><strong>v5.5 — April 2026:</strong> Redesigned controls bar, cleaner table, rain intensity labels.</span></div>
 <div class="info-li"><span class="info-num">▸</span><span><strong>v5.2 — April 2026:</strong> Proper segmented controls via st.radio + CSS.</span></div>
 <div class="info-li"><span class="info-num">▸</span><span><strong>v5.1 — April 2026:</strong> Nav bar as single source of truth.</span></div>
 <div class="info-li"><span class="info-num">▸</span><span><strong>v3.1 — March 2026:</strong> Land and offshore merged. Combined Go/No-Go.</span></div>
</div>
</div>
""", unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: st.link_button("☕  Support Windcast on Ko-fi",KOFI_URL,use_container_width=True)
    with c2: st.link_button("📝  Found an error? Tell me here.",FEEDBACK_URL,use_container_width=True)
    st.markdown(f"""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006. Open-Meteo ECMWF IFS 0.25°. v5.7
</div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # ── Session state init ────────────────────────────────────────────────────
    defaults={
        "disclaimer_ack":True,
        "active_tab":"forecast",
        "mode":"land",
        "crane_h":40,
        "lat":None,"lon":None,"loc_name":"",
        "terrain":"Open / Coastal",
        "wc_dur":"1D",
        "wc_res":"24H",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v

    # URL params → session on first load (shareable links)
    params=st.query_params
    if st.session_state.lat is None and "lat" in params and "lon" in params:
        try:
            st.session_state.lat=float(params["lat"])
            st.session_state.lon=float(params["lon"])
            st.session_state.loc_name=f"{st.session_state.lat:.4f}°N, {st.session_state.lon:.4f}°E"
            if "h" in params: st.session_state.crane_h=max(10,min(250,int(params["h"])))
            if "mode" in params and params["mode"] in ("land","offshore"):
                st.session_state.mode=params["mode"]
        except: pass

    active_tab=st.session_state.active_tab
    mode=st.session_state.mode

    # ══════════════════════════════════════════════════════════════════════════
    # DESKTOP NAV — hidden on mobile via CSS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="wc-nav-wrap">', unsafe_allow_html=True)
    logo_col, sp, c_fc, c_inf, sep_col, c_land, c_sea = st.columns(
        [1.8, 3.5, 0.6, 0.5, 0.05, 0.55, 0.5])

    with logo_col:
        st.markdown('<div class="wc-logo"><span class="bolt">⚡</span> Wind<span class="cast">cast</span></div>',
                    unsafe_allow_html=True)

    with c_fc:
        fc_wrap = "nav-btn nav-btn-active" if active_tab=="forecast" else "nav-btn"
        st.markdown(f'<div class="{fc_wrap}">', unsafe_allow_html=True)
        if st.button("🌤 Forecast", key="nav_fc", use_container_width=True):
            st.session_state.active_tab="forecast"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_inf:
        inf_wrap = "nav-btn nav-btn-active" if active_tab=="info" else "nav-btn"
        st.markdown(f'<div class="{inf_wrap}">', unsafe_allow_html=True)
        if st.button("ℹ Info", key="nav_inf", use_container_width=True):
            st.session_state.active_tab="info"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with sep_col:
        st.markdown('<div class="wc-nav-sep" style="margin:auto;"></div>', unsafe_allow_html=True)

    with c_land:
        land_wrap = "nav-btn nav-btn-active" if mode=="land" else "nav-btn"
        st.markdown(f'<div class="{land_wrap}">', unsafe_allow_html=True)
        if st.button("🏗 Land", key="nav_land", use_container_width=True):
            if mode!="land":
                st.session_state.mode="land"
                for k in ["df_cache","marine_cache","fetch_time"]: st.session_state.pop(k,None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_sea:
        sea_wrap = "nav-btn nav-btn-sea-active" if mode=="offshore" else "nav-btn"
        st.markdown(f'<div class="{sea_wrap}">', unsafe_allow_html=True)
        if st.button("⚓ Sea", key="nav_sea", use_container_width=True):
            if mode!="offshore":
                st.session_state.mode="offshore"
                for k in ["df_cache","marine_cache","fetch_time"]: st.session_state.pop(k,None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MOBILE NAV — 2 rows of pill toggles (visible only on mobile via CSS)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="wc-nav-mobile">
      <div class="wc-logo-mobile"><span class="bolt">⚡</span> Wind<span class="cast">cast</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="mob-nav" style="background:rgba(14,23,41,.97);'
                'border-bottom:1px solid var(--rim);padding:.4rem .75rem .5rem .75rem;">'
                , unsafe_allow_html=True)

    # Row 1 — Forecast | Info
    tab_opts  = ["🌤 Forecast", "ℹ Info"]
    tab_idx   = 0 if active_tab=="forecast" else 1
    tab_sel   = st.radio("Page", tab_opts, index=tab_idx,
                         horizontal=True, key="mob_tab", label_visibility="collapsed")
    new_tab   = "forecast" if tab_sel==tab_opts[0] else "info"
    if new_tab != st.session_state.active_tab:
        st.session_state.active_tab = new_tab; st.rerun()

    # Row 2 — Land | Sea
    mode_opts = ["🏗 Land", "⚓ Sea"]
    mode_idx  = 0 if mode=="land" else 1
    mode_sel  = st.radio("Mode", mode_opts, index=mode_idx,
                         horizontal=True, key="mob_mode", label_visibility="collapsed")
    new_mode  = "land" if mode_sel==mode_opts[0] else "offshore"
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        for k in ["df_cache","marine_cache","fetch_time"]: st.session_state.pop(k,None)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    if not st.session_state.disclaimer_ack:
        st.markdown('<div style="padding:1.5rem;max-width:700px;">', unsafe_allow_html=True)
        st.warning(
            "⚠️ **Planning Tool — Regulatory Notice**\n\n"
            "Windcast provides forecast data for lift planning purposes only.  "
            "It does **not** replace a calibrated on-site anemometer.  "
            "The lifting supervisor remains solely responsible under  "
            "**BS 7121-1:2016**, **LOLER 1998**, and **HSE PM55**.")
        if st.checkbox(
            "I understand this is for planning purposes only.  "
            "I will verify with a calibrated on-site anemometer before commencing.",
            key="disc_cb"):
            st.session_state.disclaimer_ack=True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Route ─────────────────────────────────────────────────────────────────
    if active_tab=="info":
        render_info(); return

    # ══════════════════════════════════════════════════════════════════════════
    # FORECAST PAGE
    # ══════════════════════════════════════════════════════════════════════════
    terrain_keys=[k for k in TERRAIN.keys()]

    # ── Controls bar ──────────────────────────────────────────────────────────
    st.markdown('<div class="wc-controls-bar">', unsafe_allow_html=True)

    # Row 1: Location (with integrated GO) + Height + Terrain + Units + Temp + Pin
    if mode=="land":
        r1cols=st.columns([3.5, 0.55, 0.95, 2.0, 1.1, 0.75, 0.45])
        c_loc,c_go,c_h,c_ter,c_wu,c_tu,c_pin=r1cols
    else:
        r1cols=st.columns([3.5, 0.55, 0.95, 1.1, 0.75, 0.45])
        c_loc,c_go,c_h,c_wu,c_tu,c_pin=r1cols

    with c_loc:
        st.markdown('<div class="search-row">', unsafe_allow_html=True)
        search_val=st.text_input("Location",
            value=st.session_state.loc_name if st.session_state.lat else "",
            placeholder="Postcode · Place name · lat ; lon",
            key="search_input", label_visibility="visible")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_go:
        st.markdown('<div style="height:1.6rem;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="go-btn">', unsafe_allow_html=True)
        fetch_btn=st.button("GO 🔍", key="fetch_btn", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_h:
        crane_h=st.number_input("Height (m)", min_value=10, max_value=250,
                                 value=st.session_state.crane_h, step=5,
                                 key="crane_num")
        st.session_state.crane_h=crane_h

    terrain=st.session_state.terrain
    if mode=="land":
        with c_ter:
            terrain_disp=[f"{TERRAIN[t]['icon']} {t}" for t in terrain_keys]
            cur_idx=terrain_keys.index(st.session_state.terrain)
            tc=st.selectbox("Terrain", terrain_disp, index=cur_idx, key="terrain_sel")
            terrain=terrain_keys[terrain_disp.index(tc)]
            st.session_state.terrain=terrain

    with c_wu:
        wind_unit=st.selectbox("Wind Units", list(WIND_UNITS.keys()), key="wind_unit")
    with c_tu:
        temp_unit=st.selectbox("Temp", ["°C","°F"], key="temp_unit")
    with c_pin:
        st.markdown('<div style="height:1.6rem;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="pin-btn">', unsafe_allow_html=True)
        save_btn=st.button("📌", key="save_btn", help="Save this site", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Resolve location ──────────────────────────────────────────────────────
    lat=st.session_state.lat; lon=st.session_state.lon; loc_name=st.session_state.loc_name

    if search_val and (search_val!=loc_name or lat is None):
        with st.spinner("Looking up location…"):
            la,lo,nm=parse_loc(search_val)
        if la:
            lat=la; lon=lo; loc_name=nm
            st.session_state.lat=lat; st.session_state.lon=lon; st.session_state.loc_name=loc_name
        else:
            st.error("Location not found. Try a UK postcode, place name, or 'lat ; lon'."); return

    if save_btn and lat:
        save_loc(loc_name[:40],lat,lon,crane_h,terrain)
        st.toast(f"✅ Saved: {loc_name[:40]}")

    # Saved sites selector
    saved=load_saved()
    if saved:
        c_saved,_=st.columns([2,5])
        with c_saved:
            picked=st.selectbox("📍 Saved sites",["— select —"]+[l["name"] for l in saved], key="load_saved")
        if picked!="— select —":
            loc=next(l for l in saved if l["name"]==picked)
            st.session_state.lat=loc["lat"]; st.session_state.lon=loc["lon"]
            st.session_state.loc_name=loc["name"]; st.session_state.crane_h=loc.get("crane_h",crane_h)
            st.session_state.terrain=loc.get("terrain",terrain)
            for k in ["df_cache","marine_cache","fetch_time"]: st.session_state.pop(k,None)
            st.rerun()

    if lat is None:
        st.markdown('<div style="padding:.75rem 1rem;">', unsafe_allow_html=True)
        st.markdown("""<div class="box-info">
    👆 Enter a location and press <strong>GO</strong>. <br>
    UK postcodes (e.g. <code>RG12 1BE</code>), place names, or coordinates (<code>51.08 ; -1.29</code>).
     </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Fetch ─────────────────────────────────────────────────────────────────
    if fetch_btn:
        st.query_params.update({"lat":f"{lat:.4f}","lon":f"{lon:.4f}","h":str(crane_h),"mode":mode})
        fetch_land.clear(); fetch_offshore_w.clear(); fetch_marine.clear()
        for k in ["df_cache","marine_cache","fetch_time"]: st.session_state.pop(k,None)

    if fetch_btn or "df_cache" not in st.session_state:
        if mode=="land":
            with st.spinner("Fetching ECMWF IFS forecast…"):
                df=fetch_land(lat,lon,168)
            if df is None or df.empty:
                st.error("Weather model failed to respond."); return
            st.session_state.df_cache=df; st.session_state.marine_cache=None
        else:
            with st.spinner("Fetching ECMWF wind + Marine data…"):
                df=fetch_offshore_w(lat,lon,168); mdf=fetch_marine(lat,lon,168)
            if df is None or df.empty:
                st.error("Failed to fetch wind data."); return
            st.session_state.df_cache=df; st.session_state.marine_cache=mdf
        st.session_state.fetch_time=datetime.now(timezone.utc)

    df=st.session_state.get("df_cache")
    mdf=st.session_state.get("marine_cache")
    fetch_t=st.session_state.get("fetch_time",datetime.now(timezone.utc))
    if df is None or df.empty:
        st.error("No forecast data."); return

    # ── Main content area ─────────────────────────────────────────────────────
    st.markdown('<div style="padding:.75rem 1rem 0 1rem;">', unsafe_allow_html=True)

    render_optimal_window(df,crane_h,terrain,mode)
    st.markdown('<div style="margin-top:.5rem;">', unsafe_allow_html=True)
    render_legend()
    st.markdown('</div>', unsafe_allow_html=True)

    if mode=="offshore" and mdf is not None and not mdf.empty:
        hs_now=sf(mdf.iloc[0].get("hs"))
        if hs_now >=2.5:
            cls="box-danger" if hs_now >=4.0 else "box-caution"
            st.markdown(f'<div class="{cls}" style="margin-top:.5rem;">⚓ <strong>Wave Height Warning:</strong> Hs = {hs_now:.2f}m</div>',
                        unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE CONTROLS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div style="padding:.4rem 1rem 0 1rem;">', unsafe_allow_html=True)

    updated_str=fetch_t.strftime("%H:%M") if fetch_t else "--:--"
    mode_src="ECMWF IFS 0.25°" if mode=="land" else "ECMWF Marine"

    tc_label, tc_dur, tc_res, tc_pdf, tc_share = st.columns([3.5, 2.1, 1.15, 0.65, 0.7])

    with tc_label:
        st.markdown(
            f'<div class="tbl-title-label">Forecast</div>'
            f'<div class="tbl-meta-label">{loc_name[:42]} · {updated_str} UTC · {mode_src}</div>',
            unsafe_allow_html=True)

    with tc_dur:
        dur_sel=st.radio("Duration", DUR_OPTS,
                          index=DUR_OPTS.index(st.session_state.wc_dur),
                          horizontal=True, key="wc_dur", label_visibility="collapsed")
        forecast_hours=DUR_MAP[dur_sel]

    with tc_res:
        res_sel=st.radio("Resolution", RES_OPTS,
                          index=RES_OPTS.index(st.session_state.wc_res),
                          horizontal=True, key="wc_res", label_visibility="collapsed")
        show_3h=(res_sel=="3H")

    with tc_pdf:
        st.markdown('<div class="pdf-btn">', unsafe_allow_html=True)
        pdf_btn=st.button("📄 PDF", key="pdf_btn", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tc_share:
        st.markdown('<div class="share-btn">', unsafe_allow_html=True)
        share_btn=st.button("🔗 Share", key="share_btn", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Share URL box
    if share_btn and lat:
        share_url=f"https://windcast.streamlit.app/?lat={lat:.4f}&lon={lon:.4f}&h={crane_h}&mode={mode}"
        st.code(share_url, language=None)
        st.caption("Copy the link above to share this forecast location.")

    # PDF
    if pdf_btn:
        try:
            import weasyprint
            if mode=="land":
                rows_p=build_land_rows(df,crane_h,terrain,wind_unit,temp_unit,forecast_hours)
                hdr_p=land_hdr(crane_h)
            else:
                rows_p=build_offshore_rows(df,mdf,crane_h,wind_unit,temp_unit,forecast_hours)
                hdr_p=sea_hdr(crane_h)
            pdf_css="@page{margin:10mm;size:A4 landscape;}body{background:#080f1f;color:#e2eaff;font-family:Arial;font-size:8pt;}table{width:100%;border-collapse:collapse;}thead th{background:#0e1729;color:#7a90b8;padding:5px 4px;border-bottom:2px solid #1e2f4a;font-size:7pt;}td{padding:4px;text-align:center;}.td-time{color:#3b82f6;font-weight:bold;}.td-safe{color:#22c55e;}.td-warn{color:#f59e0b;}.td-stop{color:#ef4444;}"
            pdf_html=(f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{pdf_css}</style></head><body>'
                      f'<h3 style="color:#3b82f6">Windcast — {loc_name}</h3>'
                      f'<p style="color:#7a90b8;font-size:7pt">Crane {crane_h}m · {forecast_hours}h · {fetch_t.strftime("%Y-%m-%d %H:%M UTC")} · ECMWF IFS 0.25°</p>'
                      f'<table><thead>{hdr_p}</thead><tbody>{" ".join(rows_p)}</tbody></table>'
                      f'<p style="color:#555;font-size:6pt">FOR PLANNING PURPOSES ONLY · BS 7121-1:2016 · LOLER 1998 · HSE PM55</p>'
                      f'</body></html>')
            pdf_bytes=weasyprint.HTML(string=pdf_html).write_pdf()
            fname=f"windcast_{loc_name[:20].replace(' ','_')}_{fetch_t.strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("⬇️ Download PDF",data=pdf_bytes,file_name=fname,mime="application/pdf")
        except ImportError:
            st.info("Install `weasyprint` to enable PDF export: `pip install weasyprint`")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown('<div style="padding:.4rem 1rem 1rem 1rem;">', unsafe_allow_html=True)

    if mode=="land":
        rows=build_land_rows(df,crane_h,terrain,wind_unit,temp_unit,forecast_hours,show_3h)
        hdr=land_hdr(crane_h)
    else:
        rows=build_offshore_rows(df,mdf,crane_h,wind_unit,temp_unit,forecast_hours,show_3h)
        hdr=sea_hdr(crane_h)

    render_table(rows,hdr)

    st.markdown(f"""<div class="wc-disclaimer">
⚠️ <strong>FOR PLANNING PURPOSES ONLY.</strong> Does not replace a calibrated on-site anemometer.
BS 7121-1:2016 | LOLER 1998 | HSE PM55 | IMCA LR006. Open-Meteo ECMWF IFS 0.25°. v5.7
 · <a href="{FEEDBACK_URL}" target="_blank" style="color:var(--txt-dim);">📝 Found an error? Tell me here.</a>
</div>""", unsafe_allow_html=True)
    with st.expander("⚙️ Advanced — Model Information", expanded=False):
        st.markdown("**Current model:** ECMWF IFS 0.25° via Open-Meteo (free tier, 7-day, updated every 6h).")
        if df is not None and not df.empty: st.dataframe(df.head(4), hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__=="__main__":
    main()
