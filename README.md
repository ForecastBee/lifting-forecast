Windcast v5.0 — Lifting Operations Weather Forecast
ECMWF IFS forecast, corrected to crane height per BS 7121, colour-coded for Go/No-Go.
Built by a lifting supervisor. Not a software company.

Streamlit App

Features
ECMWF IFS 0.25° — professional-grade global model via Open-Meteo (free tier)
BS 7121 height correction — power-law with terrain roughness factor
Go/No-Go colour coding — SAFE / CAUTION / STOP at crane height
Land + Offshore modes — offshore uses IMCA LR006 α = 0.11 correction
Optimal lift window — automatic calculation of next safe window in 72h
Sunrise/sunset — daylight bar in the NOW card
24h / 3h interval toggle — show every hour or 3-hourly snapshots
Rain intensity row tints — visual scan of precipitation intensity
Shareable URL — lat/lon/height/mode encoded in query params
PDF export — requires weasyprint (disabled on Streamlit Cloud free tier)
WhatsApp + Telegram share — deep links with forecast URL
Responsive design — desktop and mobile optimised
Deploy to Streamlit Cloud
Fork or push this repo to GitHub
Go to share.streamlit.io → New app
Set Main file path to windcast.py
Under Secrets, add: toml FEEDBACK_URL = "https://forms.gle/your-google-form-url"
Deploy
Run locally
bash pip install -r requirements.txt streamlit run windcast.py

Regulatory references
BS 7121-1:2016 — Safe use of cranes
LOLER 1998 — Lifting Operations and Lifting Equipment Regulations
HSE PM55 — Safe use of mobile cranes
IMCA LR006 — Guidance on the lifting of offshore cargo
NORSOK R-003 — Safe use of lifting equipment
Disclaimer
FOR PLANNING PURPOSES ONLY. This application does not replace a calibrated on-site anemometer. The lifting supervisor retains full Go/No-Go responsibility under BS 7121-1:2016, LOLER 1998, and HSE PM55.

Support
☕ Ko-fi — if Windcast has saved you a wasted mobilisation
