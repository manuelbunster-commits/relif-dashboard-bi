"""Funciones compartidas entre páginas del dashboard — versión v2 (diseño mejorado)."""

import base64
import math
import os
from datetime import date, timedelta, datetime
import pytz
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

RELIF_EXECUTE_URL = (
    "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app"
    "/admin/db/execute"
)

STATUS_COLORS = {
    "rejected_by_bank": "#ef4444",
    "sent_to_bank":     "#22c55e",
    "created":          "#3b82f6",
}

STATUS_LABELS = {
    "rejected_by_bank": "Rechazada",
    "sent_to_bank":     "Enviada",
    "created":          "Creada",
}

SCROLL_ANIM = """
<style>
.scroll-animate {
    opacity: 0;
    transform: translateY(28px);
    transition: opacity 0.55s ease-out, transform 0.55s ease-out;
}
.scroll-animate.in-view {
    opacity: 1;
    transform: translateY(0);
}
</style>
<script>
(function() {
    const SEL = [
        '[data-testid="stPlotlyChart"]',
        '[data-testid="stDataFrame"]',
        '[data-testid="stDataFrameResizable"]',
    ].join(',');

    const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('in-view');
                io.unobserve(e.target);
            }
        });
    }, { threshold: 0.05, rootMargin: '0px 0px -30px 0px' });

    function attach(el) {
        if (el.dataset.scrollBound) return;
        el.dataset.scrollBound = '1';
        el.classList.add('scroll-animate');
        io.observe(el);
    }

    // Observe elements added dynamically by Streamlit
    const mo = new MutationObserver(() => {
        document.querySelectorAll(SEL).forEach(attach);
    });

    setTimeout(() => {
        document.querySelectorAll(SEL).forEach(attach);
        mo.observe(document.body, { childList: true, subtree: true });
    }, 300);
})();
</script>
"""

CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Fondo gris muy suave para que las cards blancas "floten" */
.stApp, section.main { background: #f1f5f9 !important; }

.block-container {
    padding-top: 0 !important;
    padding-left: 2rem;
    padding-right: 2rem;
    animation: pageLoad 0.5s ease-out;
    max-width: 1200px;
}
@keyframes pageLoad {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Métricas nativas ── */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04);
}
[data-testid="metric-container"] label {
    font-size: 0.7rem !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}

/* ── Ocultar navegación nativa de Streamlit ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Alinear columnas del sidebar verticalmente ── */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    align-items: center !important;
}

/* ── st.page_link en sidebar: sin fondo azul, estilo link limpio ── */
[data-testid="stSidebar"] [data-testid="stPageLink"],
[data-testid="stSidebar"] [data-testid="stPageLink"] > div,
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    color: #cbd5e1 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    border-radius: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] a:focus {
    background: transparent !important;
    background-color: transparent !important;
    color: #f1f5f9 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    transform: translateY(-1px) !important;
}

/* ── Sidebar colapsado: pastilla con "R" de Relif ── */
[data-testid="stSidebarCollapsedControl"] {
    width: 48px !important;
    height: 48px !important;
    background: linear-gradient(135deg, #0f172a, #1e293b) !important;
    border-radius: 0 12px 12px 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 3px 0 12px rgba(0,0,0,0.2) !important;
    border: none !important;
    top: 18px !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}
[data-testid="stSidebarCollapsedControl"]:hover {
    background: linear-gradient(135deg, #1e293b, #334155) !important;
}
[data-testid="stSidebarCollapsedControl"] svg {
    display: none !important;
}
[data-testid="stSidebarCollapsedControl"]::after {
    content: "R";
    color: #f1f5f9;
    font-family: 'Inter', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
}

hr { border: none !important; border-top: 1px solid #e2e8f0 !important; margin: 1.5rem 0 !important; }

/* ── Filtros de fecha sticky ── */
section.main .block-container [data-testid="stHorizontalBlock"]:first-of-type {
    position: sticky !important;
    top: 0 !important;
    z-index: 100 !important;
    background: white !important;
    padding: 8px 0 10px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
    border-radius: 0 0 12px 12px !important;
    margin-bottom: 0.5rem !important;
}

/* ── KPI Cards ── */
.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.3rem 1.4rem 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 8px 28px rgba(0,0,0,0.07);
}
.kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.green::before  { background: linear-gradient(90deg,#22c55e,#4ade80); }
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#f87171); }
.kpi-card.purple::before { background: linear-gradient(90deg,#8b5cf6,#a78bfa); }
.kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    display: block;
    line-height: 1;
}
.kpi-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: #94a3b8; margin-bottom: 0.25rem; }
.kpi-value {
    font-size: 2.1rem; font-weight: 800; color: #0f172a; line-height: 1.05;
    letter-spacing: -0.02em;
    animation: countUp 0.6s ease-out;
}
@keyframes countUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.kpi-delta { font-size: 0.75rem; font-weight: 500; margin-top: 0.3rem; }
.kpi-delta.up      { color: #22c55e; }
.kpi-delta.down    { color: #ef4444; }
.kpi-delta.neutral { color: #94a3b8; }

/* ── Chart cards — envuelve automáticamente los gráficos Plotly ── */
[data-testid="stPlotlyChart"] {
    background: white !important;
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.05) !important;
    padding: 0.8rem 0.8rem 0 !important;
    overflow: hidden !important;
}

/* ── DataFrame cards ── */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
    background: white !important;
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.05) !important;
    overflow: hidden !important;
}

/* ── Tabla de detalle con badges ── */
.detail-table { width:100%; border-collapse:collapse; font-size:0.82rem; }
.detail-table th {
    background:#f8fafc; color:#64748b; font-size:0.65rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.07em;
    padding:0.7rem 1rem; border-bottom:1px solid #e2e8f0; text-align:left;
}
.detail-table td { padding:0.65rem 1rem; border-bottom:1px solid #f1f5f9; color:#0f172a; vertical-align:middle; }
.detail-table tr:last-child td { border-bottom:none; }
.detail-table tr:hover td { background:#f8fafc; }
.status-badge {
    display:inline-block; padding:3px 10px; border-radius:999px;
    font-size:0.72rem; font-weight:600; line-height:1.4;
}

/* ── Alert banner ── */
.alert-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    color: #991b1b;
    font-weight: 500;
}
.alert-banner.warning {
    background: #fffbeb;
    border-color: #fde68a;
    border-left-color: #f59e0b;
    color: #92400e;
}

.last-updated { font-size: 0.72rem; color: #94a3b8; text-align: right; margin-bottom: 1rem; }

h1 {
    font-weight: 700 !important;
    font-size: 1.8rem !important;
    color: #0f172a !important;
    letter-spacing: -0.02em !important;
}
</style>
"""


@st.cache_data(ttl=3600, show_spinner=False)
def get_token() -> str:
    token = os.environ.get("RELIF_JWT_TOKEN", "")
    if token:
        return token
    st.error("Configura RELIF_JWT_TOKEN en el archivo .env")
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(start: str, end: str, dedup_clients: bool = False) -> pd.DataFrame:
    token = get_token()
    if dedup_clients:
        query = f"""
            SELECT "BankOfferRequests".*, c."id" as "clientId", c."rut", c."source"
            FROM "BankOfferRequests"
            LEFT JOIN (
                SELECT DISTINCT ON ("rut") "id", "rut", "source"
                FROM "Clients"
                WHERE "businessUnitId" = 73
                ORDER BY "rut", "createdAt" DESC
            ) c ON "BankOfferRequests"."rut" = c."rut"
            WHERE "BankOfferRequests"."createdAt" >= '{start}'
              AND "BankOfferRequests"."createdAt" <  '{end}'
        """
    else:
        query = f"""
            SELECT "BankOfferRequests".*, "Clients"."id" as "clientId", "Clients"."rut", "Clients"."source"
            FROM "BankOfferRequests"
            LEFT JOIN "Clients" ON "BankOfferRequests"."rut" = "Clients"."rut"
              AND "Clients"."businessUnitId" = 73
            WHERE "BankOfferRequests"."createdAt" >= '{start}'
              AND "BankOfferRequests"."createdAt" <  '{end}'
        """
    resp = requests.post(
        RELIF_EXECUTE_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"userQuery": query.strip()},
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return pd.DataFrame()

    rows = []
    for r in results:
        rows.append({
            "id":        r.get("id"),
            "bukLeadId": r.get("bukLeadId"),
            "bank":      r.get("bank"),
            "status":    r.get("status"),
            "rut":       r.get("rut"),
            "source":    r.get("source"),
            "createdAt": r.get("createdAt"),
            "updatedAt": r.get("updatedAt"),
        })

    df = pd.DataFrame(rows)
    # pre_approved = equivalente a enviada al banco (usado por Banco Internacional)
    df["status"] = df["status"].replace("pre_approved", "sent_to_bank")
    df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True).dt.tz_convert("America/Santiago")
    df["updatedAt"] = pd.to_datetime(df["updatedAt"], utc=True).dt.tz_convert("America/Santiago")
    df["date"]    = df["createdAt"].dt.date
    df["hour"]    = df["createdAt"].dt.hour
    df["weekday"] = df["createdAt"].dt.day_name()
    return df


def _trend_arrow(pct: float) -> str:
    if pct > 0:
        return f'<span class="kpi-delta up">↑ {pct:.0f}% vs período anterior</span>'
    elif pct < 0:
        return f'<span class="kpi-delta down">↓ {abs(pct):.0f}% vs período anterior</span>'
    return '<span class="kpi-delta neutral">— igual que período anterior</span>'


def _pct_change(curr, prev):
    if prev == 0:
        return 0
    return round((curr - prev) / prev * 100)


def _section_header(title: str, icon: str = ""):
    """Separador estilizado con línea horizontal y título a la izquierda."""
    icon_html = f'<span style="font-size:0.9rem;line-height:1">{icon}</span>' if icon else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.7rem;margin:2rem 0 1rem">
        {icon_html}
        <span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#64748b;white-space:nowrap">{title}</span>
        <div style="flex:1;height:1px;background:linear-gradient(90deg,#e2e8f0,transparent)"></div>
    </div>""", unsafe_allow_html=True)


def _ring_svg(tasa: int, tasa_prev: int) -> str:
    """Anillo circular de progreso, estilo moderno (Apple Watch / Linear)."""
    cx, cy, r, sw = 110, 110, 80, 14
    circ = round(2 * math.pi * r, 2)           # circunferencia total
    filled = round(circ * max(0, min(tasa, 100)) / 100, 2)
    gap    = round(circ - filled, 2)
    # stroke-dashoffset = circ/4 para que el arco empiece arriba (−90°)
    offset = round(circ / 4, 2)

    color = "#22c55e" if tasa >= 50 else "#ef4444"
    color_bg = f"{color}18"   # tint muy suave para el fondo del card

    delta = tasa - tasa_prev
    if delta > 0:
        delta_str, delta_color = f"▲ {delta}pts", "#22c55e"
    elif delta < 0:
        delta_str, delta_color = f"▼ {abs(delta)}pts", "#ef4444"
    else:
        delta_str, delta_color = "—", "#94a3b8"

    period_label = "vs período anterior"

    return (
        f'<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,.04),0 4px 20px rgba(0,0,0,.05);'
        f'padding:1.4rem 1rem 1.2rem;display:flex;flex-direction:column;align-items:center">'

        # ── Título ──
        f'<p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:#94a3b8;margin:0 0 1rem;text-align:center">'
        f'Tasa de Envío al Banco</p>'

        # ── Anillo SVG ──
        f'<svg width="220" height="220" viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg">'

        # Fondo suave dentro del anillo
        f'<circle cx="{cx}" cy="{cy}" r="{r-sw//2-2}" fill="{color_bg}"/>'

        # Pista gris
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#f0f4f8" stroke-width="{sw}"/>'

        # Arco de valor
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" '
        f'stroke-dasharray="{filled} {gap}" stroke-dashoffset="{offset}" '
        f'style="transition:stroke-dasharray 0.6s ease"/>'

        # Número central grande
        f'<text x="{cx}" y="{cy-14}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="Inter,sans-serif" font-size="28" font-weight="800" '
        f'fill="#0f172a" letter-spacing="-1">{tasa}%</text>'

        # Delta pequeño debajo del número
        f'<text x="{cx}" y="{cy+12}" text-anchor="middle" '
        f'font-family="Inter,sans-serif" font-size="13" font-weight="600" fill="{delta_color}">'
        f'{delta_str}</text>'

        f'<text x="{cx}" y="{cy+28}" text-anchor="middle" '
        f'font-family="Inter,sans-serif" font-size="11" fill="#94a3b8">'
        f'{period_label}</text>'

        f'</svg>'
        f'</div>'
    )


def _style_status(df: pd.DataFrame):
    """Colorea filas de la tabla según el status."""
    bg_map = {
        "rejected_by_bank": "#fef2f2",
        "sent_to_bank":     "#f0fdf4",
        "created":          "#eff6ff",
    }
    def row_bg(row):
        bg = bg_map.get(row.get("status", ""), "")
        return [f"background-color:{bg}" if bg else "" for _ in row]
    return df.style.apply(row_bg, axis=1)


RANGOS_SUELDO = [
    (0,          600_000,   "< $600k",      "#f1f5f9", "#475569"),
    (600_000,  1_600_000,   "$600k – $1.6M","#dbeafe", "#1d4ed8"),
    (1_600_000,2_500_000,   "$1.6M – $2.5M","#dcfce7", "#15803d"),
    (2_500_000,4_000_000,   "$2.5M – $4M",  "#fef9c3", "#92400e"),
    (4_000_000,8_000_000,   "$4M – $8M",    "#fed7aa", "#c2410c"),
    (8_000_000,999_999_999, "Más de $8M",   "#fce7f3", "#be185d"),
]

def _rango_badge(monto):
    if pd.isna(monto):
        return '<span class="status-badge" style="background:#f1f5f9;color:#94a3b8">Sin datos</span>'
    for lo, hi, label, bg, color in RANGOS_SUELDO:
        if lo <= monto < hi:
            return f'<span class="status-badge" style="background:{bg};color:{color}">{label}</span>'
    return "—"

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_sueldos_por_rut():
    token = os.environ.get("RELIF_JWT_TOKEN", "")
    query = """
        SELECT c.rut, ROUND(AVG((d.data->>'incomeGross')::numeric)) AS avg_gross
        FROM "Documents" d
        JOIN "Clients" c ON d."clientId" = c.id
        WHERE d.type = 'buk_settlement'
          AND (d.data->>'incomeGross') IS NOT NULL
        GROUP BY c.rut
    """
    resp = requests.post(RELIF_EXECUTE_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"userQuery": query.strip()}, timeout=60)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return {r["rut"]: float(r["avg_gross"]) for r in results if r.get("avg_gross")}


def render_dashboard(bank_filter: str = None, show_salary_range: bool = False, chart_scroll: bool = False, dedup_clients: bool = False, chart_days: int = None):
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.markdown(SCROLL_ANIM, unsafe_allow_html=True)

    # ── Logos base64 (usados en sidebar y header) ──
    _logo_path = Path(__file__).parent / "relif-logo-DkXo5dGJ.png"
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode() if _logo_path.exists() else ""

    _bci_path = Path(__file__).parent / "bci_logo.png"
    _bci_b64  = base64.b64encode(_bci_path.read_bytes()).decode() if _bci_path.exists() else ""

    _bi_path = Path(__file__).parent / "banco_internacional.png"
    _bi_b64  = base64.b64encode(_bi_path.read_bytes()).decode() if _bi_path.exists() else ""
    _logo_img = (
        f'<img src="data:image/png;base64,{_logo_b64}" '
        f'style="height:36px;filter:brightness(0) invert(1);opacity:0.92">'
        if _logo_b64 else
        '<span style="font-size:1.1rem;font-weight:800;color:white">RELIF</span>'
    )

    # ── Sidebar ──
    with st.sidebar:
        # Logo / branding
        st.markdown(
            f"<div style='text-align:center;padding:1.6rem 0 1.2rem'>"
            f"<div style='display:inline-flex;align-items:center;justify-content:center;"
            f"padding:0.6rem 1rem;background:rgba(255,255,255,0.06);border-radius:12px;"
            f"border:1px solid rgba(255,255,255,0.08);margin-bottom:0.5rem'>"
            f"{_logo_img}</div>"
            f"<div style='font-size:0.6rem;color:#475569;margin-top:4px;text-transform:uppercase;"
            f"letter-spacing:0.12em'>Analytics</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        # Navegación — solo si hay más de una página disponible
        _base = Path(__file__).parent
        _all_nav = [
            ("🏦",     "Consolidado",        "Acumulado.py",                   None,    None,   "/"),
            (_bci_b64, "BCI",                "pages/1_BCI.py",                 None,    "18px", "/BCI"),
            (_bi_b64,  "Banco Internacional","pages/2_Banco_Internacional.py", None,    "13px", "/Banco_Internacional"),
            ("📣",     "Campañas (prueba)",  "pages/99_Prueba.py",             None,    None,   "/Prueba"),
        ]
        nav_pages = [(l, lbl, p, f, h, url) for l, lbl, p, f, h, url in _all_nav if (_base / p).exists()]
        if len(nav_pages) > 1:
            st.markdown(
                "<div style='font-size:0.6rem;font-weight:700;text-transform:uppercase;"
                "letter-spacing:0.1em;color:#475569;padding:0 0.2rem 0.6rem'>Páginas</div>",
                unsafe_allow_html=True,
            )
            nav_html = ""
            for logo, label, page_file, img_filter, img_h, url in nav_pages:
                if logo and logo not in ("🏦",):
                    icon_html = f'<img src="data:image/png;base64,{logo}" style="height:20px;width:auto;flex-shrink:0;vertical-align:middle">'
                else:
                    icon_html = f'<span style="font-size:1.1rem;flex-shrink:0">{logo}</span>'
                nav_html += (
                    f'<a href="{url}" target="_self" style="display:flex;align-items:center;gap:0.7rem;'
                    f'padding:0.4rem 0.3rem;text-decoration:none;border-radius:6px;'
                    f'color:#cbd5e1;font-size:0.9rem;font-weight:500;transition:background 0.15s">'
                    f'{icon_html}'
                    f'<span>{label}</span>'
                    f'</a>'
                )
            st.markdown(nav_html, unsafe_allow_html=True)
        st.markdown(
            "<hr style='border:none;border-top:1px solid #1e293b;margin:1rem 0 0.8rem'>",
            unsafe_allow_html=True,
        )
        # Controles
        st.markdown(
            "<div style='font-size:0.6rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.1em;color:#475569;padding:0 0.2rem 0.6rem'>Controles</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        comparar          = False  # desactivado
        alerta_threshold  = 999  # desactivado
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        rut_search = st.text_input("🔍 Buscar RUT", placeholder="ej: 12.345.678-9", key=f"rut_search_{bank_filter}")

    # ── Header ──
    if bank_filter == "BCI":
        title_text = "BCI"
        subtitle_text = "Banco de Crédito e Inversiones"
    elif bank_filter:
        title_text = bank_filter
        subtitle_text = "Panel de operaciones"
    else:
        title_text = "Consolidado"
        subtitle_text = "Todos los bancos"

    # Logo para el header (más grande)
    _logo_html = (
        f'<img src="data:image/png;base64,{_logo_b64}" style="height:52px;filter:brightness(0) invert(1);opacity:0.95">'
        if _logo_b64 else ""
    )

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
                border-radius:0 0 20px 20px;padding:2.4rem 2.5rem 2.2rem;
                margin:-1rem -2rem 1.5rem;position:relative;overflow:hidden">
        <div style="position:absolute;top:-30px;right:-30px;width:200px;height:200px;
                    background:rgba(255,255,255,0.04);border-radius:50%"></div>
        <div style="position:absolute;bottom:-50px;right:80px;width:130px;height:130px;
                    background:rgba(255,255,255,0.03);border-radius:50%"></div>
        <div style="position:relative;z-index:1;display:flex;align-items:center;justify-content:flex-end">
            {_logo_html}
        </div>
    </div>""", unsafe_allow_html=True)

    subtitle_ph = st.empty()  # subtítulo con período + conteo

    # ── Filtros de fecha ──
    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Desde", value=date.today())
    with dc2:
        end_date = st.date_input("Hasta", value=date.today() + timedelta(days=1))

    delta_days = max((end_date - start_date).days, 1)
    # Si el rango es ≤ 7 días, comparar contra la misma ventana de la semana anterior
    # Si es > 7 días, comparar contra el período inmediatamente anterior de igual duración
    if delta_days <= 7:
        prev_start = str(start_date - timedelta(weeks=1))
        prev_end   = str(end_date   - timedelta(weeks=1))
    else:
        prev_start = str(start_date - timedelta(days=delta_days))
        prev_end   = str(start_date)

    with st.spinner("Cargando datos..."):
        df_raw  = fetch_data(str(start_date), str(end_date), dedup_clients=dedup_clients)
        df_prev = fetch_data(prev_start, prev_end, dedup_clients=dedup_clients)

    now_cl = datetime.now(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M")
    st.markdown(f'<p class="last-updated">Actualizado: {now_cl}</p>', unsafe_allow_html=True)

    if df_raw.empty:
        st.warning("No hay datos para el período seleccionado.")
        return

    if bank_filter:
        df_raw  = df_raw[df_raw["bank"] == bank_filter]
        df_prev = df_prev[df_prev["bank"] == bank_filter] if not df_prev.empty else df_prev
        if df_raw.empty:
            st.warning(f"No hay datos para {bank_filter} en el período seleccionado.")
            return

    # ── Métricas ──
    total_curr = len(df_raw)
    total_prev = len(df_prev) if not df_prev.empty else 0
    env_curr   = int((df_raw["status"] == "sent_to_bank").sum())
    env_prev   = int((df_prev["status"] == "sent_to_bank").sum()) if not df_prev.empty else 0
    rec_curr   = int((df_raw["status"] == "rejected_by_bank").sum())
    rec_prev   = int((df_prev["status"] == "rejected_by_bank").sum()) if not df_prev.empty else 0
    tasa       = round(env_curr / total_curr * 100) if total_curr else 0
    tasa_prev  = round(env_prev / total_prev * 100) if total_prev else 0

    pct_total = _pct_change(total_curr, total_prev)
    pct_env   = _pct_change(env_curr, env_prev)
    pct_rec   = _pct_change(rec_curr, rec_prev)

    by_day_spark = df_raw.groupby("date").size().reset_index(name="n").set_index("date")["n"]

    # ── Rellenar placeholders ──
    subtitle_ph.markdown(
        f'<p style="color:#64748b;font-size:0.9rem;margin:-0.5rem 0 1.2rem;'
        f'padding-bottom:0.6rem;border-bottom:1px solid #f1f5f9">'
        f'📅 {start_date} → {end_date} &nbsp;·&nbsp; '
        f'<b style="color:#0f172a">{total_curr}</b> registros</p>',
        unsafe_allow_html=True,
    )


    # ── Alertas ──
    pct_rec_actual = round(rec_curr / total_curr * 100) if total_curr else 0
    if pct_rec_actual >= alerta_threshold:
        st.markdown(
            f'<div class="alert-banner">🚨 Tasa de rechazo en <b>{pct_rec_actual}%</b> — supera el umbral configurado de {alerta_threshold}%</div>',
            unsafe_allow_html=True,
        )
    elif pct_rec_actual >= alerta_threshold - 10:
        st.markdown(
            f'<div class="alert-banner warning">⚠️ Tasa de rechazo en <b>{pct_rec_actual}%</b> — acercándose al umbral de {alerta_threshold}%</div>',
            unsafe_allow_html=True,
        )

    # ── KPI Cards ──
    k1, k2, k3, k4 = st.columns(4)
    env_spark = df_raw[df_raw["status"] == "sent_to_bank"].groupby("date").size().reindex(by_day_spark.index, fill_value=0)
    rec_spark = df_raw[df_raw["status"] == "rejected_by_bank"].groupby("date").size().reindex(by_day_spark.index, fill_value=0)

    with k1:
        st.markdown(f"""
        <div class="kpi-card blue" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0s;opacity:0">
            <span class="kpi-icon">📋</span>
            <div class="kpi-label">Total Requests</div>
            <div class="kpi-value" data-counter="{total_curr}">{total_curr}</div>
            {_trend_arrow(pct_total)}
        </div>""", unsafe_allow_html=True)
    with k2:
        color = "green" if tasa >= 50 else "red"
        st.markdown(f"""
        <div class="kpi-card {color}" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.1s;opacity:0">
            <span class="kpi-icon">🏦</span>
            <div class="kpi-label">Tasa de Envío al Banco</div>
            <div class="kpi-value" data-counter="{tasa}" data-suffix="%">{tasa}%</div>
            {_trend_arrow(_pct_change(tasa, tasa_prev))}
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card green" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.2s;opacity:0">
            <span class="kpi-icon">✅</span>
            <div class="kpi-label">Enviadas al banco</div>
            <div class="kpi-value" data-counter="{env_curr}">{env_curr}</div>
            {_trend_arrow(pct_env)}
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card red" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.3s;opacity:0">
            <span class="kpi-icon">❌</span>
            <div class="kpi-label">Rechazadas</div>
            <div class="kpi-value" data-counter="{rec_curr}">{rec_curr}</div>
            {_trend_arrow(-pct_rec)}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Modo comparación ──
    if comparar and not df_prev.empty:
        _section_header("Comparación de períodos")
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"📅 {start_date} → {end_date}")
            st.metric("Total", total_curr)
            st.metric("Enviadas", env_curr)
            st.metric("Rechazadas", rec_curr)
        with c2:
            st.caption(f"📅 {prev_start} → {prev_end}")
            st.metric("Total", total_prev)
            st.metric("Enviadas", env_prev)
            st.metric("Rechazadas", rec_prev)

    # ── Gauge + contexto ──
    gauge_col, ctx_col = st.columns([3, 2])
    with gauge_col:
        st.markdown(_ring_svg(tasa, tasa_prev), unsafe_allow_html=True)

    with ctx_col:
        by_bank = df_raw.groupby("bank").agg(
            total=("status", "count"),
            enviadas=("status", lambda x: (x == "sent_to_bank").sum()),
        ).sort_values("total", ascending=False).reset_index()

        rows_html = ""
        for _, brow in by_bank.iterrows():
            b_tasa = round(brow["enviadas"] / brow["total"] * 100) if brow["total"] else 0
            bar_color = "#22c55e" if b_tasa >= 50 else "#ef4444"
            rows_html += (
                f'<div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.5rem">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.4rem">'
                f'<span style="font-size:0.82rem;font-weight:700;color:#0f172a">{brow["bank"]}</span>'
                f'<span style="font-size:0.75rem;font-weight:600;color:{bar_color}">{b_tasa}% envío</span>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:0.4rem">'
                f'<span style="font-size:0.7rem;color:#64748b">{int(brow["total"])} requests · {int(brow["enviadas"])} enviadas</span>'
                f'</div>'
                f'<div style="background:#f1f5f9;border-radius:999px;height:5px;overflow:hidden">'
                f'<div style="width:{b_tasa}%;height:100%;background:{bar_color};border-radius:999px;transition:width 0.6s ease"></div>'
                f'</div>'
                f'</div>'
            )
        st.markdown(
            f'<div style="padding-top:1.2rem">'
            f'<p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8;margin:0 0 0.8rem">Banco</p>'
            f'{rows_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── 2. Actividad reciente ──
    _section_header("Actividad reciente", "⚡")
    ultimos = df_raw.sort_values("createdAt", ascending=False).head(5)
    for _, row in ultimos.iterrows():
        status = row["status"]
        color  = STATUS_COLORS.get(status, "#94a3b8")
        label  = STATUS_LABELS.get(status, status)
        hora   = row["createdAt"].strftime("%d/%m %H:%M")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;padding:0.6rem 1rem;
                    background:white;border:1px solid #e2e8f0;border-radius:10px;
                    margin-bottom:0.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.04)">
            <span style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;display:inline-block"></span>
            <span style="font-size:0.82rem;color:#0f172a;font-weight:600;flex:1">{row['rut']}</span>
            <span style="font-size:0.78rem;color:#64748b">{row['bank']}</span>
            <span style="font-size:0.75rem;font-weight:600;color:{color};background:{color}18;padding:2px 10px;border-radius:999px">{label}</span>
            <span style="font-size:0.75rem;color:#94a3b8;min-width:80px;text-align:right">{hora}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── 3. Análisis temporal ──
    _section_header("Análisis temporal", "📈")
    gb1, gb2 = st.columns(2)
    with gb1:
        banks2 = ["Todos"] + sorted(df_raw["bank"].dropna().unique().tolist())
        sel_b2 = st.selectbox("Banco ", banks2, key=f"gb_{bank_filter}")
    with gb2:
        stats2 = ["Todos"] + sorted(df_raw["status"].dropna().unique().tolist())
        sel_s2 = st.selectbox("Status ", stats2, key=f"gs_{bank_filter}")

    df_g = df_raw.copy()
    if sel_b2 != "Todos": df_g = df_g[df_g["bank"]   == sel_b2]
    if sel_s2 != "Todos": df_g = df_g[df_g["status"] == sel_s2]

    st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#64748b;margin:0.5rem 0 0.3rem">Requests por día + tendencia</p>', unsafe_allow_html=True)
    by_day = df_g.groupby("date").size().reset_index(name="Count")
    if chart_days:
        by_day = by_day.tail(chart_days).reset_index(drop=True)
    by_day["Enviados"] = df_g[df_g["status"] == "sent_to_bank"].groupby("date").size().reindex(by_day["date"]).fillna(0).values
    by_day["Otros"] = by_day["Count"] - by_day["Enviados"]
    by_day["Tendencia"] = by_day["Enviados"].rolling(window=3, min_periods=1).mean()

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(x=by_day["date"], y=by_day["Enviados"], name="Enviados al banco", marker_color="#22c55e", marker_line_width=0))
    fig_combo.add_trace(go.Bar(x=by_day["date"], y=by_day["Otros"], name="Otros", marker_color="#3b82f6", marker_line_width=0))
    fig_combo.add_trace(go.Scatter(x=by_day["date"], y=by_day["Tendencia"], name="Tendencia (3d)", line=dict(color="#8b5cf6", width=2.5, dash="dot")))
    _xaxis = dict(showgrid=False)
    if chart_scroll:
        _xaxis.update(dict(
            range=[by_day["date"].iloc[0] - pd.Timedelta(days=0.5),
                   by_day["date"].iloc[-1] + pd.Timedelta(days=1)],
            rangeslider=dict(visible=True, thickness=0.06, bgcolor="#f1f5f9"),
        ))
    fig_combo.update_layout(
        barmode="stack",
        margin=dict(t=10, b=40 if chart_scroll else 10, r=20), height=300 if chart_scroll else 280,
        xaxis_title="", yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9", zeroline=False),
        xaxis=_xaxis,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_combo, use_container_width=True)

    # ── 4. Resumen ──
    _section_header("Resumen", "📊")
    t1, t2, rank_col = st.columns(3)
    with t1:
        st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#64748b;margin:0 0 0.3rem">Por banco</p>', unsafe_allow_html=True)
        st.dataframe(
            df_raw.groupby("bank").size().reset_index(name="Count").sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with t2:
        st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#64748b;margin:0 0 0.3rem">Por status</p>', unsafe_allow_html=True)
        st.dataframe(
            df_raw.groupby("status").size().reset_index(name="Count").sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with rank_col:
        st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#64748b;margin:0 0 0.3rem">Top empresas</p>', unsafe_allow_html=True)
        df_src = df_raw[df_raw["source"].notna() & (df_raw["source"] != "")].copy()
        if df_src.empty:
            st.caption("Sin datos de empresa")
        else:
            rank = df_src.groupby("source").agg(
                leads=("id", "count"),
                enviadas=("status", lambda x: (x == "sent_to_bank").sum()),
            ).sort_values("leads", ascending=False).head(5).reset_index()
            max_leads = rank["leads"].max()
            rows_html = ""
            medals = ["🥇", "🥈", "🥉", "4.", "5."]
            for i, row in rank.iterrows():
                pct_bar  = round(row["leads"] / max_leads * 100)
                tasa     = round(row["enviadas"] / row["leads"] * 100) if row["leads"] else 0
                clr_tasa = "#22c55e"
                medal    = medals[i] if i < len(medals) else f"{i+1}."
                rows_html += (
                    f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;border-bottom:1px solid #f1f5f9">'
                    f'<span style="font-size:0.8rem;width:20px;flex-shrink:0">{medal}</span>'
                    f'<div style="flex:1;min-width:0">'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
                    f'<span style="font-size:0.75rem;font-weight:600;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{row["source"]}</span>'
                    f'<span style="font-size:0.7rem;font-weight:700;color:{clr_tasa};margin-left:0.3rem;flex-shrink:0">{tasa}%</span>'
                    f'</div>'
                    f'<div style="background:#f1f5f9;border-radius:999px;height:3px;margin-top:3px">'
                    f'<div style="width:{pct_bar}%;height:100%;background:#3b82f6;border-radius:999px"></div>'
                    f'</div></div>'
                    f'<span style="font-size:0.72rem;font-weight:700;color:#64748b;flex-shrink:0;margin-left:0.3rem">{int(row["leads"])}</span>'
                    f'</div>'
                )
            st.markdown(rows_html, unsafe_allow_html=True)

    # ── 6. Heatmap ──
    _section_header("Heatmap — requests por hora y día", "🌡️")
    WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    WEEKDAY_ES    = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    heat = df_raw.groupby(["weekday", "hour"]).size().reset_index(name="count")
    heat_pivot = heat.pivot(index="weekday", columns="hour", values="count").reindex(WEEKDAY_ORDER).fillna(0)
    heat_pivot.index = WEEKDAY_ES
    heat_pivot = heat_pivot.loc[:, (heat_pivot > 0).any(axis=0)]

    peak_dia_idx = heat_pivot.sum(axis=1).idxmax()
    peak_hora    = heat_pivot.sum(axis=0).idxmax()

    fig_heat = px.imshow(
        heat_pivot,
        labels=dict(x="Hora del día", y="", color="Requests"),
        color_continuous_scale=[[0, "#f0f9ff"], [0.5, "#3b82f6"], [1, "#1d4ed8"]],
        aspect="auto", text_auto=True,
    )
    fig_heat.update_traces(textfont=dict(size=11, family="Inter"))
    fig_heat.update_layout(
        height=280, margin=dict(t=10, b=10, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
        xaxis=dict(tickmode="linear", tick0=heat_pivot.columns[0], dtick=1),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Conclusiones
    hora_by     = heat.groupby("hour")["count"].sum()
    dia_by      = heat.groupby("weekday")["count"].sum()
    dia_peak_es = WEEKDAY_ES[WEEKDAY_ORDER.index(dia_by.idxmax())]
    dia_bajo_es = WEEKDAY_ES[WEEKDAY_ORDER.index(dia_by.idxmin())]
    horario_tot = heat["count"].sum()
    pct_of      = round(heat[heat["hour"].between(9, 18)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    pct_manana  = round(heat[heat["hour"].between(9, 13)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    pct_tarde   = round(heat[heat["hour"].between(14, 18)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    bloque_peak = "mañana (9–13h)" if pct_manana >= pct_tarde else "tarde (14–18h)"
    top2_horas  = hora_by.nlargest(2).index.tolist()
    top3_pct    = round(hora_by.nlargest(3).sum() / horario_tot * 100) if horario_tot else 0
    pct_fds     = round(heat[heat["weekday"].isin(["Saturday", "Sunday"])]["count"].sum() / horario_tot * 100) if horario_tot else 0

    insights = [
        f"El día más activo es <b>{dia_peak_es}</b> y el menos activo es <b>{dia_bajo_es}</b>",
        f"Las horas peak son las <b>{top2_horas[0]}:00 y {top2_horas[1]}:00 hrs</b> — concentran el <b>{top3_pct}%</b> del tráfico",
        f"El <b>{pct_of}%</b> llega en horario de oficina, con mayor carga en la <b>{bloque_peak}</b>",
        f"El fin de semana representa solo el <b>{pct_fds}%</b> del total — operación esencialmente laboral",
    ]
    items_html = "".join(f"<li>{i}</li>" for i in insights)
    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-left:4px solid #8b5cf6;
                border-radius:14px;padding:1rem 1.4rem;margin-top:0.5rem;
                box-shadow:0 1px 4px rgba(0,0,0,0.05)">
        <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
                  color:#94a3b8;margin:0 0 0.6rem">💡 Conclusiones</p>
        <ul style="margin:0;padding-left:1.2rem;color:#374151;font-size:0.88rem;line-height:1.9">{items_html}</ul>
    </div>""", unsafe_allow_html=True)

    # ── Contador animado en KPI cards ──
    components.html("""
<script>
(function () {
    function run() {
        window.parent.document.querySelectorAll('[data-counter]').forEach(function (el) {
            if (el.dataset.animated) return;
            el.dataset.animated = '1';
            var target = parseFloat(el.getAttribute('data-counter'));
            var suffix = el.getAttribute('data-suffix') || '';
            var start  = null;
            function step(ts) {
                if (!start) start = ts;
                var t    = Math.min((ts - start) / 900, 1);
                var ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.round(target * ease).toLocaleString('es-CL') + suffix;
                if (t < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });
    }
    setTimeout(run, 400);
})();
</script>
""", height=0)

    # ── 6. Detalle de registros ──
    _section_header("Detalle de registros", "🔍")
    _cols = [1, 1, 1] if show_salary_range else [1, 1]
    filter_cols = st.columns(_cols)
    with filter_cols[0]:
        banks = ["Todos"] + sorted(df_raw["bank"].dropna().unique().tolist())
        sel_bank = st.selectbox("Banco", banks, key=f"fb_{bank_filter}")
    with filter_cols[1]:
        stats = ["Todos"] + sorted(df_raw["status"].dropna().unique().tolist())
        sel_status = st.selectbox("Status", stats, key=f"fs_{bank_filter}")
    if show_salary_range:
        with filter_cols[2]:
            st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            sort_by_salary = st.checkbox("↓ Ordenar por sueldo", key=f"sort_sal_{bank_filter}")
    else:
        sort_by_salary = False

    df_f = df_raw.copy()
    if sel_bank   != "Todos": df_f = df_f[df_f["bank"]   == sel_bank]
    if sel_status != "Todos": df_f = df_f[df_f["status"] == sel_status]
    if rut_search:
        term = rut_search.strip().lower()
        df_f = df_f[df_f["rut"].astype(str).str.lower().str.contains(term, na=False)]

    df_display = df_f[["id", "bukLeadId", "bank", "status", "rut", "source", "createdAt", "updatedAt"]].copy()
    if sort_by_salary and show_salary_range:
        sueldos_map_sort = _fetch_sueldos_por_rut()
        df_display = df_display.copy()
        df_display["_avg_gross"] = df_display["rut"].map(sueldos_map_sort).fillna(-1)
        df_display = df_display.sort_values("_avg_gross", ascending=False).drop(columns=["_avg_gross"])
    else:
        df_display = df_display.sort_values("createdAt", ascending=False)

    # Tabla HTML con badges de status
    STATUS_BADGE = {
        "sent_to_bank":     ('<span class="status-badge" style="background:#dcfce7;color:#15803d">✅ Enviada</span>'),
        "rejected_by_bank": ('<span class="status-badge" style="background:#fee2e2;color:#b91c1c">❌ Rechazada</span>'),
        "created":          ('<span class="status-badge" style="background:#dbeafe;color:#1d4ed8">🔵 Creada</span>'),
    }

    sueldos_map = _fetch_sueldos_por_rut() if show_salary_range else {}
    col_headers = ["ID", "BukLeadId", "Banco", "Status", "RUT", "Empresa", "Creado", "Rango sueldo bruto" if show_salary_range else "Actualizado"]
    header = "<tr>" + "".join(f"<th>{c}</th>" for c in col_headers) + "</tr>"
    body_rows = []
    for _, r in df_display.head(200).iterrows():
        badge   = STATUS_BADGE.get(r["status"], f'<span class="status-badge" style="background:#f1f5f9;color:#64748b">{r["status"]}</span>')
        c_at    = r["createdAt"].strftime("%d/%m/%y %H:%M") if pd.notna(r["createdAt"]) else "—"
        source  = r["source"] if pd.notna(r.get("source")) else "—"
        if show_salary_range:
            avg = sueldos_map.get(r["rut"])
            last_col = _rango_badge(avg) if avg else '<span class="status-badge" style="background:#f1f5f9;color:#94a3b8">Sin datos</span>'
        else:
            last_col = r["updatedAt"].strftime("%d/%m/%y %H:%M") if pd.notna(r["updatedAt"]) else "—"
        body_rows.append(
            f"<tr><td>{r['id']}</td><td>{r['bukLeadId']}</td><td>{r['bank']}</td>"
            f"<td>{badge}</td><td>{r['rut']}</td><td>{source}</td><td>{c_at}</td><td>{last_col}</td></tr>"
        )
    table_html = f"""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;
                box-shadow:0 1px 3px rgba(0,0,0,0.04),0 4px 20px rgba(0,0,0,0.05);
                overflow:hidden;margin-bottom:0.8rem">
        <div style="overflow-x:auto;max-height:360px;overflow-y:auto">
            <table class="detail-table">
                <thead style="position:sticky;top:0;z-index:1">{header}</thead>
                <tbody>{"".join(body_rows)}</tbody>
            </table>
        </div>
        <div style="padding:0.6rem 1rem;background:#f8fafc;border-top:1px solid #e2e8f0;
                    font-size:0.7rem;color:#94a3b8">
            Mostrando {min(200, len(df_display))} de {len(df_display)} registros
        </div>
    </div>"""
    st.markdown(table_html, unsafe_allow_html=True)

    if show_salary_range:
        _sueldos = _fetch_sueldos_por_rut()
        _rango_meta = {label: (bg, color) for _, _, label, bg, color in RANGOS_SUELDO}
        def _get_rango(rut):
            avg = _sueldos.get(rut)
            if not avg:
                return "Sin datos"
            for lo, hi, label, _, _ in RANGOS_SUELDO:
                if lo <= avg < hi:
                    return label
            return "Sin datos"

        col_dist, col_env = st.columns(2)

        _TH = "style='text-align:left;padding:0.4rem 1rem 0.4rem 0.6rem;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#94a3b8;border-bottom:1px solid #e2e8f0'"
        _TD = "style='padding:0.45rem 1rem 0.45rem 0.6rem;font-size:0.82rem;border-bottom:1px solid #f1f5f9'"
        _TABLE = "style='border-collapse:collapse;font-family:Inter,sans-serif;width:100%;background:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06)'"

        # ── Fetch 10 días (compartido entre distribución y enviados) ──
        _today = date.today()
        _df_10d = fetch_data(str(_today - timedelta(days=10)), str(_today + timedelta(days=1)), dedup_clients=dedup_clients)
        if not _df_10d.empty:
            if bank_filter:
                _df_10d = _df_10d[_df_10d["bank"] == bank_filter]
            _df_10d["status"] = _df_10d["status"].replace("pre_approved", "sent_to_bank")
        _enviados = _df_10d[_df_10d["status"] == "sent_to_bank"].sort_values("createdAt", ascending=False).head(20) if not _df_10d.empty else pd.DataFrame()

        # ── Distribución por rango ──
        with col_dist:
            # Total: df_raw (período seleccionado, sin sub-filtros). Filtrado: df_f (con sub-filtros activos)
            _df_dist_total = df_raw.copy()
            _df_dist_total["_rango"] = _df_dist_total["rut"].map(_get_rango)
            _df_dist_fil = df_f.copy()
            _df_dist_fil["_rango"] = _df_dist_fil["rut"].map(_get_rango)

            _dist_total_leads = _df_dist_total.groupby("_rango").size().rename("Total")
            _dist_fil_leads   = _df_dist_fil.groupby("_rango").size().rename("Filtrado")
            _dist_env         = _df_dist_total[_df_dist_total["status"] == "sent_to_bank"].groupby("_rango").size().rename("Enviados")

            _conteo = pd.concat([_dist_total_leads, _dist_fil_leads, _dist_env], axis=1).fillna(0).astype({"Total": int, "Filtrado": int, "Enviados": int})
            _conteo = _conteo.sort_values("Total", ascending=False).reset_index()
            _conteo.columns = ["Rango", "Total", "Filtrado", "Enviados"]

            _has_subfilter = (sel_bank != "Todos" or sel_status != "Todos" or bool(rut_search))
            _period_label = f"{start_date.strftime('%-d %b')} – {end_date.strftime('%-d %b %Y')}"

            _rows_html = ""
            for _, row in _conteo.iterrows():
                bg, color = _rango_meta.get(row["Rango"], ("#f1f5f9", "#94a3b8"))
                badge = f'<span class="status-badge" style="background:{bg};color:{color}">{row["Rango"]}</span>'
                _pct = round(row["Enviados"] / row["Total"] * 100) if row["Total"] > 0 else 0
                _pct_color = "#15803d" if _pct >= 50 else "#92400e" if _pct >= 20 else "#64748b"
                _fil_cell = f"<td {_TD} style='font-size:0.82rem;border-bottom:1px solid #f1f5f9;color:#6366f1;font-weight:600'>{int(row['Filtrado'])}</td>" if _has_subfilter else ""
                _rows_html += f"<tr><td {_TD} style='font-size:0.82rem;border-bottom:1px solid #f1f5f9;font-weight:600'>{int(row['Total'])}</td>{_fil_cell}<td {_TD}>{badge}</td><td {_TD} style='font-size:0.82rem;font-weight:700;color:{_pct_color};border-bottom:1px solid #f1f5f9'>{_pct}%</td></tr>"

            _fil_header = f"<th {_TH} style='color:#6366f1'>Filtrado</th>" if _has_subfilter else ""
            st.markdown(f"""
            <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8;margin:0.8rem 0 0.4rem">Distribución por rango sueldo bruto · {_period_label}</p>
            <table {_TABLE}>
                <thead><tr><th {_TH}>Total período</th>{_fil_header}<th {_TH}>Rango sueldo bruto</th><th {_TH}>% Enviado</th></tr></thead>
                <tbody>{_rows_html}</tbody>
            </table>""", unsafe_allow_html=True)

        # ── Últimos enviados al banco (10 días) ──
        with col_env:
            if _df_10d.empty:
                _enviados = pd.DataFrame()
            _env_rows = ""
            for _, r in _enviados.iterrows():
                rango = _get_rango(r["rut"])
                bg, color = _rango_meta.get(rango, ("#f1f5f9", "#94a3b8"))
                rango_badge = f'<span class="status-badge" style="background:{bg};color:{color}">{rango}</span>'
                env_badge = '<span class="status-badge" style="background:#dcfce7;color:#15803d">✅ Enviado</span>'
                _fecha = pd.to_datetime(r["createdAt"]).strftime("%-d %b %Y") if pd.notna(r["createdAt"]) else "—"
                _env_rows += f"<tr><td {_TD}>{r['rut']}</td><td {_TD}>{rango_badge}</td><td {_TD}>{_fecha}</td><td {_TD}>{env_badge}</td></tr>"
            if not _env_rows:
                _env_rows = f"<tr><td colspan='4' {_TD} style='color:#94a3b8'>Sin registros en los últimos 10 días</td></tr>"
            st.markdown(f"""
            <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8;margin:0.8rem 0 0.4rem">Últimos enviados al banco (10 días)</p>
            <div style="max-height:220px;overflow-y:auto;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
            <table {_TABLE} style="border-collapse:collapse;font-family:Inter,sans-serif;width:100%;background:white">
                <thead style="position:sticky;top:0;z-index:1;background:white"><tr><th {_TH}>RUT</th><th {_TH}>Rango sueldo bruto</th><th {_TH}>Fecha</th><th {_TH}>Status</th></tr></thead>
                <tbody>{_env_rows}</tbody>
            </table>
            </div>""", unsafe_allow_html=True)
            if not _enviados.empty:
                _csv_enviados = _enviados[["rut", "bank", "createdAt"]].copy()
                _csv_enviados["rango_sueldo_bruto"] = _enviados["rut"].map(_get_rango)
                _csv_enviados["status"] = "Enviado al banco"
                st.markdown("""
                <style>
                div[data-testid="stDownloadButton"] button {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    color: #475569;
                    font-size: 0.75rem;
                    font-weight: 600;
                    padding: 0.35rem 0.9rem;
                    border-radius: 6px;
                    margin-top: 0.5rem;
                    transition: all 0.2s;
                }
                div[data-testid="stDownloadButton"] button:hover {
                    background: #f1f5f9;
                    border-color: #cbd5e1;
                    color: #1e293b;
                }
                </style>""", unsafe_allow_html=True)
                st.download_button(
                    label="⬇️ Exportar CSV",
                    data=_csv_enviados.to_csv(index=False).encode("utf-8"),
                    file_name="enviados_banco_10dias.csv",
                    mime="text/csv",
                    key="dl_enviados",
                )

    DOWNLOAD_EMAILS = {"manuelbunster@gmail.com"}  # ← agrega aquí los emails con permiso
    user_email = getattr(getattr(st, "experimental_user", None), "email", None)
    if user_email in DOWNLOAD_EMAILS:
        st.download_button(
            label="⬇️ Descargar CSV",
            data=df_display.to_csv(index=False).encode("utf-8"),
            file_name=f"detalle_registros_{bank_filter or 'consolidado'}.csv",
            mime="text/csv",
        )

    # ── Footer ──
    st.markdown("""
    <div style="margin-top:3rem;padding:1.2rem 0;border-top:1px solid #e2e8f0;
                display:flex;align-items:center;justify-content:space-between;
                flex-wrap:wrap;gap:0.5rem">
        <span style="font-size:0.72rem;font-weight:700;color:#94a3b8;letter-spacing:0.05em">RELIF</span>
        <span style="font-size:0.7rem;color:#cbd5e1">Dashboard de operaciones bancarias</span>
    </div>""", unsafe_allow_html=True)
