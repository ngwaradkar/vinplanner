"""
TML SMART PPC OPERATIONS CONTROL CENTER - UI/UX DESIGN SYSTEM & HELPERS
========================================================================
Centralized theme tokens, enterprise layout shell, responsive typography,
manufacturing KPI components, shortage alerts, and table renderers.
"""
import datetime
import hashlib
import html
import io
import os
import time
import pandas as pd
import streamlit as st

# Timezone
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Canonical pages for routing
PAGES = [
    'Overview',
    'TCF1 Line',
    'TCF2 Line',
    'Cockpit & Wiring Shortages',
    'Summary & Excel Reports',
    'Total Float & Search',
    'Quality Holds',
    'Telegram Dispatcher',
    'Control Panel'
]

PAGE_DESCRIPTIONS = {
    'Overview': 'Plant-wide control tower: production readiness, line status, and critical material shortages.',
    'TCF1 Line': 'TCF1 assembly line readiness, FIFO buffer queue, planner overrides, and cab search.',
    'TCF2 Line': 'TCF2 assembly line readiness, FIFO buffer queue, planner overrides, and cab search.',
    'Cockpit & Wiring Shortages': 'Material clearance, shortage monitoring, and inventory coverage for Cockpit WH and Wiring Harnesses.',
    'Summary & Excel Reports': 'Shop-wise plant production matrix, paint shop float summary, engine & battery requirements, and hourly tracking.',
    'Total Float & Search': 'Plant-wide paint float tracking, multi-stage vehicle search, and short VC / blocked pivot analysis.',
    'Quality Holds': 'Quality inspection holds across PBS buffer and Paint Shop with detailed root-cause tracking.',
    'Telegram Dispatcher': 'Shift production summary preview and 15-minute automated broadcast dispatcher.',
    'Control Panel': 'Workbook source ingestion, OneDrive/SharePoint live synchronization, starting stocks, and model shortage rules.',
}

# Navigation hierarchy: Display Name -> (Canonical Page, Subtab/Section)
NAVIGATION_STRUCTURE = {
    'OPERATIONS': [
        ('🏢 Plant Control Tower', 'Overview', None),
        ('🔷 TCF1 Assembly Line', 'TCF1 Line', None),
        ('🟣 TCF2 Assembly Line', 'TCF2 Line', None),
        ('🔍 Float & Vehicle Search', 'Total Float & Search', None),
        ('⚠️ Quality Holds Monitor', 'Quality Holds', None),
    ],
    'MATERIAL CONTROL': [
        ('🧩 Cockpit & Wiring Shortages', 'Cockpit & Wiring Shortages', None),
        ('⚙️ Engine Starting Stocks', 'Control Panel', 'Engine stocks'),
        ('🔋 EV & Model Shortages', 'Control Panel', 'EV & model shortages'),
    ],
    'REPORTS & ANALYTICS': [
        ('📊 Production Summary & Matrix', 'Summary & Excel Reports', 'summary'),
        ('🎨 Paint Shop Float Summary', 'Summary & Excel Reports', 'paint_float'),
        ('⏱️ Hourly Production Tracker', 'Summary & Excel Reports', 'hourly'),
        ('📱 Telegram Dispatcher', 'Telegram Dispatcher', None),
    ],
    'ADMIN & DATA SOURCES': [
        ('🎛️ Control Panel (Files & Sync)', 'Control Panel', 'Files & synchronization'),
    ]
}

# Flat lookup: display label -> (page, subtab)
NAV_LOOKUP = {}
for category, items in NAVIGATION_STRUCTURE.items():
    for label, page_key, subtab in items:
        NAV_LOOKUP[label] = (page_key, subtab)


# ==============================================================================
# 1. CENTRALIZED THEME SYSTEM (DARK & LIGHT)
# ==============================================================================

THEME_TOKENS = {
    'dark': {
        'bg_primary': '#070A0F',
        'bg_secondary': '#0C1118',
        'bg_surface': '#111823',
        'bg_elevated': '#17202C',
        'bg_elev': '#17202C',
        'border': 'rgba(255, 255, 255, 0.08)',
        'border_strong': 'rgba(255, 255, 255, 0.14)',
        'text_primary': '#F8FAFC',
        'text_secondary': '#CBD5E1',
        'text_muted': '#94A3B8',
        'blue': '#3B82F6',
        'blue_hover': '#2563EB',
        'cyan': '#06B6D4',
        'cyan_hover': '#0891B2',
        'success': '#10B981',
        'success_bg': 'rgba(16, 185, 129, 0.10)',
        'success_border': 'rgba(16, 185, 129, 0.28)',
        'warning': '#F59E0B',
        'warning_bg': 'rgba(245, 158, 11, 0.10)',
        'warning_border': 'rgba(245, 158, 11, 0.28)',
        'critical': '#EF4444',
        'critical_bg': 'rgba(239, 68, 68, 0.12)',
        'critical_border': 'rgba(239, 68, 68, 0.32)',
        'neutral': '#64748B',
        'tcf1_accent': '#06B6D4',
        'tcf1_bg': 'rgba(6, 182, 212, 0.08)',
        'tcf2_accent': '#8B5CF6',
        'tcf2_bg': 'rgba(139, 92, 246, 0.08)',
        'table_th_bg': '#17202C',
        'table_td_hover': '#1A2433',
        'card_shadow': '0 4px 16px rgba(0, 0, 0, 0.40)',
    },
    'light': {
        'bg_primary': '#F4F7FB',
        'bg_secondary': '#EBF1F8',
        'bg_surface': '#FFFFFF',
        'bg_elevated': '#F8FAFC',
        'bg_elev': '#F8FAFC',
        'border': '#DCE3EC',
        'border_strong': '#CBD5E1',
        'text_primary': '#172033',
        'text_secondary': '#475569',
        'text_muted': '#64748B',
        'blue': '#2563EB',
        'blue_hover': '#1D4ED8',
        'cyan': '#0891B2',
        'cyan_hover': '#0E7490',
        'success': '#059669',
        'success_bg': '#ECFDF5',
        'success_border': '#A7F3D0',
        'warning': '#D97706',
        'warning_bg': '#FFFBEB',
        'warning_border': '#FDE68A',
        'critical': '#DC2626',
        'critical_bg': '#FEF2F2',
        'critical_border': '#FECACA',
        'neutral': '#64748B',
        'tcf1_accent': '#0891B2',
        'tcf1_bg': 'rgba(8, 145, 178, 0.08)',
        'tcf2_accent': '#7C3AED',
        'tcf2_bg': 'rgba(124, 58, 237, 0.08)',
        'table_th_bg': '#F1F5F9',
        'table_td_hover': '#F8FAFC',
        'card_shadow': '0 2px 8px rgba(15, 23, 42, 0.06)',
    }
}

def get_theme_tokens(is_dark: bool) -> dict:
    return THEME_TOKENS['dark'] if is_dark else THEME_TOKENS['light']


# ==============================================================================
# 2. CACHE & REPRODUCIBILITY UTILITIES
# ==============================================================================

def invalidate_report():
    """A pending input change must not leave an old snapshot available to timers."""
    for key in ('_report_snapshot', '_summary_snapshot', '_prepared_exports'):
        st.session_state.pop(key, None)


def fingerprint(value):
    """Content identity with cycle protection; never uses buffer cursor or DB write time."""
    digest = hashlib.sha256()
    visited_ids = set()

    def add(item):
        item_id = id(item)
        if isinstance(item, (dict, list, tuple, set)):
            if item_id in visited_ids:
                return
            visited_ids.add(item_id)

        if isinstance(item, pd.DataFrame):
            digest.update(repr((list(item.columns), list(map(str, item.dtypes)))).encode())
            digest.update(pd.util.hash_pandas_object(item, index=True).values.tobytes())
        elif isinstance(item, dict):
            for key in sorted(item, key=str):
                add(key)
                add(item[key])
        elif isinstance(item, (tuple, list, set)):
            for element in item:
                add(element)
        elif hasattr(item, 'content_id'):
            add(item.content_id)
        elif hasattr(item, 'getvalue'):
            digest.update(item.getvalue())
        elif isinstance(item, (str, os.PathLike)) and os.path.isfile(item):
            stat = os.stat(item)
            digest.update(repr((os.path.abspath(item), stat.st_size, stat.st_mtime_ns)).encode())
        else:
            digest.update(repr(item).encode())
        digest.update(b'\x00')

    add(value)
    return digest.hexdigest()


def clear_stock_drafts():
    for key in ('engine_stock_editor', 'nova_stock_editor'):
        st.session_state.pop(key, None)


def file_registry(directory, detector):
    """Only scan on interval or explicit refresh; content parsers have their own cache."""
    cached = st.session_state.get('_file_registry')
    if not cached or cached[0] != directory or time.monotonic() - cached[1] > 60:
        sources = detector(directory)
        cached = (directory, time.monotonic(), sources, fingerprint(sources))
        st.session_state['_file_registry'] = cached
    return cached[2].copy()


def cached_download(*, label, builder, file_name, key, version=None, **kwargs):
    """Builders run only on request. Invalidate when inputs or export filters change."""
    identity = fingerprint((st.session_state.get('_report_key'), version))
    cache = st.session_state.setdefault('_prepared_exports', {})
    entry = cache.get(key)
    if entry is not None and entry[0] != identity:
        cache.pop(key, None)
        entry = None
    clean_label = label.replace('📥 ', '').replace('⬇️ ', '').replace('📁 ', '')
    if st.button('Prepare · ' + clean_label, key='prepare_' + key):
        with st.spinner('Preparing Excel file…'):
            data = builder()
        cache[key] = (identity, data)
        entry = cache[key]
        while len(cache) > 12:
            cache.pop(next(iter(cache)))
    if entry is not None:
        st.download_button(label, data=entry[1], file_name=file_name, key=key,
                           on_click='ignore', **kwargs)


def table_workbook(sheets):
    from openpyxl.styles import Alignment, Font, PatternFill
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, index=False, sheet_name=name)
            ws = writer.sheets[name]
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill('solid', fgColor='1D4ED8')
                cell.alignment = Alignment(wrap_text=True)
            for column in ws.columns:
                ws.column_dimensions[column[0].column_letter].width = min(
                    48, max(14, max(len(str(c.value or '')) for c in column) + 2)
                )
    return output.getvalue()


# ==============================================================================
# 3. GLOBAL ENTERPRISE CSS INJECTION
# ==============================================================================

def inject_enterprise_css(tokens: dict, is_dark: bool):
    """Injects high-density, manufacturing control tower CSS theme into Streamlit."""
    bg_pri = tokens['bg_primary']
    bg_sec = tokens['bg_secondary']
    bg_surf = tokens['bg_surface']
    bg_elev = tokens['bg_elevated']
    border = tokens['border']
    border_str = tokens['border_strong']
    txt_pri = tokens['text_primary']
    txt_sec = tokens['text_secondary']
    txt_mut = tokens['text_muted']
    blue = tokens['blue']
    cyan = tokens['cyan']
    success = tokens['success']
    warning = tokens['warning']
    critical = tokens['critical']
    tcf1 = tokens['tcf1_accent']
    tcf2 = tokens['tcf2_accent']
    th_bg = tokens['table_th_bg']
    td_hover = tokens['table_td_hover']

    css = f"""<style>
    /* CSS Variables */
    :root {{
        --bg-pri: {bg_pri};
        --bg-sec: {bg_sec};
        --bg-surf: {bg_surf};
        --bg-elev: {bg_elev};
        --border: {border};
        --border-str: {border_str};
        --txt-pri: {txt_pri};
        --txt-sec: {txt_sec};
        --txt-mut: {txt_mut};
        --blue: {blue};
        --cyan: {cyan};
        --success: {success};
        --warning: {warning};
        --critical: {critical};
        --tcf1: {tcf1};
        --tcf2: {tcf2};
    }}

    /* Base Font & Layout Reset */
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        letter-spacing: -0.01em;
    }}
    .stApp {{
        background: {bg_pri};
        color: {txt_pri};
        color-scheme: {'dark' if is_dark else 'light'};
    }}
    .stApp .block-container {{
        padding: 3.5rem 1.75rem 2.5rem;
        max-width: 1680px;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: {bg_sec};
        color: {txt_pri};
        border-right: 1px solid {border};
    }}
    [data-testid="stSidebarUserContent"] {{
        padding: 1.25rem 0.85rem;
    }}
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {{
        color: {txt_mut};
    }}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: transparent !important;
    }}

    /* Typography & Hierarchy */
    .stApp :is(h1,h2,h3,h4,h5,h6),
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricValue"] {{
        color: {txt_pri};
    }}
    .stApp h1 {{
        font-size: 1.65rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }}
    .stApp h2 {{
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        margin-top: 1rem;
    }}
    .stApp h3 {{
        font-size: 1.05rem !important;
        font-weight: 650 !important;
        margin-top: 0.75rem;
    }}
    .stApp h4 {{
        font-size: 0.95rem !important;
        font-weight: 650 !important;
    }}
    .stApp [data-testid="stCaptionContainer"] p {{
        color: {txt_mut};
        font-size: 0.78rem;
    }}

    /* Form Controls & Inputs */
    .stApp :is(input, textarea),
    .stApp [data-baseweb="input"],
    .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="textarea"],
    .stApp [data-baseweb="select"] > div {{
        background: {bg_surf} !important;
        color: {txt_pri} !important;
        border-color: {border} !important;
        border-radius: 6px !important;
        font-size: 0.88rem;
    }}
    .stApp [data-baseweb="select"] :is(div, span, svg) {{
        color: {txt_pri} !important;
    }}
    .stApp :is(input, textarea)::placeholder {{
        color: {txt_mut} !important;
        opacity: 0.85;
    }}
    .stApp [data-baseweb="tag"] {{
        background: {bg_elev} !important;
        color: {txt_pri} !important;
    }}
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] [role="option"] {{
        background: {bg_surf} !important;
        color: {txt_pri} !important;
    }}
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [role="option"][aria-selected="true"] {{
        background: {bg_elev} !important;
    }}

    /* Button System */
    .stApp button {{
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        border-radius: 6px !important;
        min-height: 2.35rem !important;
        transition: all 0.15s ease-in-out;
    }}
    .stApp button[kind="secondary"],
    .stApp button[kind="secondaryFormSubmit"],
    .stApp [data-testid="stNumberInput"] button {{
        background: {bg_surf} !important;
        border: 1px solid {border_str} !important;
        color: {txt_pri} !important;
    }}
    .stApp button[kind="secondary"]:hover,
    .stApp button[kind="secondaryFormSubmit"]:hover {{
        background: {bg_elev} !important;
        border-color: {blue} !important;
        color: {txt_pri} !important;
    }}
    .stApp button[kind="primary"],
    .stApp button[kind="primaryFormSubmit"] {{
        background: {blue} !important;
        border: 1px solid {blue} !important;
        color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.18);
    }}
    .stApp button[kind="primary"]:hover,
    .stApp button[kind="primaryFormSubmit"]:hover {{
        background: {tokens['blue_hover']} !important;
        border-color: {tokens['blue_hover']} !important;
    }}

    /* Native Metric Cards */
    .stApp [data-testid="stMetric"] {{
        background: {bg_surf};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 0.85rem 1rem;
        box-shadow: {tokens['card_shadow']};
    }}
    .stApp [data-testid="stMetricLabel"] p {{
        font-size: 0.75rem !important;
        font-weight: 650 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: {txt_mut} !important;
    }}
    .stApp [data-testid="stMetricValue"] {{
        font-size: 1.65rem !important;
        font-weight: 750 !important;
        font-variant-numeric: tabular-nums;
        color: {txt_pri} !important;
    }}

    /* Dataframes & Tables */
    .stApp [data-testid="stDataFrame"] {{
        border: 1px solid {border};
        border-radius: 8px;
        overflow: hidden;
        background: {bg_surf};
    }}

    /* Tabs */
    .stApp [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        border-bottom: 1px solid {border};
        padding-bottom: 0.15rem;
    }}
    .stApp [data-baseweb="tab"] {{
        padding: 0.55rem 0.95rem;
        font-size: 0.84rem;
        font-weight: 600;
        color: {txt_mut};
        border-radius: 6px 6px 0 0;
        background: transparent;
    }}
    .stApp [data-baseweb="tab"][aria-selected="true"] {{
        color: {blue} !important;
    }}
    .stApp [data-baseweb="tab-highlight"] {{
        background: {blue} !important;
        height: 2px !important;
    }}

    /* Expanders & Forms */
    .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stForm"] {{
        background: {bg_surf};
        border: 1px solid {border};
        border-radius: 8px;
    }}
    .stApp [data-testid="stExpander"] summary {{
        background: {bg_surf};
        border-bottom: 1px solid {border};
        border-radius: 8px 8px 0 0;
        font-size: 0.88rem;
        font-weight: 600;
    }}
    .stApp [data-testid="stExpander"] summary:hover {{
        background: {bg_elev};
    }}

    /* Sidebar Radio Navigation */
    [data-testid="stSidebar"] [role="radiogroup"] {{
        gap: 0.2rem;
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"] {{
        width: 100%;
        box-sizing: border-box;
        margin: 0;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        border: 1px solid transparent;
        transition: background 0.12s ease;
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {{
        display: none;
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"] p {{
        font-size: 0.84rem;
        font-weight: 550;
        color: {txt_sec};
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{
        background: {bg_elev};
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {{
        background: {bg_elev};
        border-color: {border_str};
        border-left: 3px solid {blue};
    }}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p {{
        color: {txt_pri};
        font-weight: 650;
    }}

    /* ================= Custom Enterprise Components ================= */

    /* Enterprise Header */
    .tml-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: {bg_surf};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 0.75rem 1.15rem;
        margin-bottom: 1.25rem;
        box-shadow: {tokens['card_shadow']};
    }}
    .tml-header-left {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }}
    .tml-brand-badge {{
        background: {blue};
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.82rem;
        padding: 0.4rem 0.65rem;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }}
    .tml-header-title {{
        font-size: 1.05rem;
        font-weight: 750;
        color: {txt_pri};
        line-height: 1.2;
        letter-spacing: -0.01em;
    }}
    .tml-header-subtitle {{
        font-size: 0.68rem;
        font-weight: 600;
        color: {txt_mut};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.15rem;
    }}
    .tml-header-right {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
    }}
    .tml-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: {bg_elev};
        border: 1px solid {border};
        padding: 0.28rem 0.6rem;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 600;
        color: {txt_sec};
        white-space: nowrap;
    }}
    .tml-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
    }}
    .tml-dot.green {{ background: {success}; }}
    .tml-dot.amber {{ background: {warning}; }}
    .tml-dot.red {{ background: {critical}; }}
    .tml-dot.blue {{ background: {blue}; }}
    .tml-dot.cyan {{ background: {cyan}; }}

    /* KPI Cards */
    .tml-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.15rem;
    }}
    .tml-kpi-card {{
        background: {bg_surf};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 0.85rem 1rem;
        position: relative;
        overflow: hidden;
        box-shadow: {tokens['card_shadow']};
    }}
    .tml-kpi-card.tcf1 {{
        border-left: 3px solid {tcf1};
    }}
    .tml-kpi-card.tcf2 {{
        border-left: 3px solid {tcf2};
    }}
    .tml-kpi-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.3rem;
    }}
    .tml-kpi-label {{
        font-size: 0.72rem;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {txt_mut};
    }}
    .tml-kpi-badge {{
        font-size: 0.66rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.02em;
    }}
    .tml-kpi-value {{
        font-size: 1.7rem;
        font-weight: 750;
        color: {txt_pri};
        font-variant-numeric: tabular-nums;
        line-height: 1.15;
    }}
    .tml-kpi-subtext {{
        font-size: 0.76rem;
        color: {txt_sec};
        margin-top: 0.25rem;
    }}

    /* Alert Strips */
    .tml-alert-strip {{
        background: {bg_surf};
        border: 1px solid {border};
        border-left: 4px solid {critical};
        border-radius: 6px;
        padding: 0.85rem 1.15rem;
        margin-bottom: 1rem;
    }}
    .tml-alert-strip.warning {{ border-left-color: {warning}; }}
    .tml-alert-strip.success {{ border-left-color: {success}; }}
    .tml-alert-strip.info {{ border-left-color: {cyan}; }}
    .tml-alert-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.35rem;
    }}
    .tml-alert-title {{
        font-size: 0.88rem;
        font-weight: 700;
        color: {txt_pri};
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }}
    .tml-alert-desc {{
        font-size: 0.8rem;
        color: {txt_sec};
        line-height: 1.45;
    }}

    /* Section Headers */
    .tml-section-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0 0.4rem;
        margin: 1.25rem 0 0.75rem;
        border-bottom: 1px solid {border};
    }}
    .tml-section-title {{
        font-size: 1.05rem;
        font-weight: 750;
        color: {txt_pri};
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .tml-section-sub {{
        font-size: 0.78rem;
        color: {txt_mut};
        margin-top: 0.15rem;
    }}

    /* Model Shortage Cards */
    .tml-ms-card {{
        background: {bg_surf};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.45rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
    }}

    /* Enterprise Table Styling */
    .matrix-card {{
        border: 1px solid {border};
        border-radius: 8px;
        overflow-x: auto;
        margin: 0.6rem 0 1rem;
        background: {bg_surf};
    }}
    .matrix-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.84rem;
        font-variant-numeric: tabular-nums;
    }}
    .matrix-table :is(th, td) {{
        padding: 0.65rem 0.85rem;
        text-align: right;
        border-bottom: 1px solid {border};
        color: {txt_pri};
    }}
    .matrix-table th {{
        background: {th_bg};
        font-weight: 650;
        white-space: nowrap;
        color: {txt_mut};
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.04em;
    }}
    .matrix-table :is(th, td):first-child {{
        text-align: left;
    }}
    .matrix-table tr:hover {{
        background: {td_hover};
    }}
    .matrix-table :is(.tr-tcf1-tot, .tr-tcf2-tot) td {{
        background: {bg_elev};
        font-weight: 700;
    }}
    .matrix-table .tr-grand-tot td {{
        background: {tokens['success_bg']};
        color: {success};
        font-weight: 800;
        border-top: 2px solid {tokens['success_border']};
    }}
    .badge-tcf1 {{
        display: inline-block;
        border: 1px solid {tokens['tcf1_accent']};
        color: {tokens['tcf1_accent']};
        background: {tokens['tcf1_bg']};
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 700;
    }}
    .badge-tcf2 {{
        display: inline-block;
        border: 1px solid {tokens['tcf2_accent']};
        color: {tokens['tcf2_accent']};
        background: {tokens['tcf2_bg']};
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 700;
    }}

    /* Responsive Queries */
    @media (max-width: 1024px) {{
        .stApp .block-container {{ padding: 3rem 1.25rem 2rem; }}
        .tml-header {{ flex-direction: column; align-items: flex-start; gap: 0.65rem; }}
        .tml-header-right {{ width: 100%; justify-content: flex-start; }}
    }}
    @media (max-width: 640px) {{
        .stApp .block-container {{ padding: 3rem 0.75rem 1.5rem; }}
        .stApp h1 {{ font-size: 1.35rem !important; }}
        .tml-kpi-grid {{ grid-template-columns: 1fr; }}
    }}
    </style>"""
    st.markdown(css, unsafe_allow_html=True)


# ==============================================================================
# 4. APPLICATION SHELL & NAVIGATION
# ==============================================================================

def setup_shell():
    """Initializes Streamlit page configuration, sidebar navigation, and theme system."""
    st.set_page_config(
        page_title='TML Smart PPC Operations',
        page_icon='🚗',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    # State initialization
    st.session_state.setdefault('theme', '🌙 Dark Theme')
    is_dark = st.session_state.theme == '🌙 Dark Theme'
    tokens = get_theme_tokens(is_dark)

    # Inject design system CSS
    inject_enterprise_css(tokens, is_dark)

    # Sidebar Construction
    with st.sidebar:
        # Enterprise Brand Header
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.15rem;">
            <div style="background: {tokens['blue']}; color: #FFF; font-weight: 850; font-size: 0.92rem; padding: 0.45rem 0.65rem; border-radius: 6px; letter-spacing: 0.05em;">TML</div>
            <div>
                <div style="font-weight: 800; font-size: 0.96rem; color: {tokens['text_primary']}; line-height: 1.2;">SMART PPC</div>
                <div style="font-size: 0.72rem; color: {tokens['text_muted']}; font-weight: 550; letter-spacing: 0.04em;">OPERATIONS CONTROL</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Build options list for grouped radio
        flat_options = []
        for section, items in NAVIGATION_STRUCTURE.items():
            for label, _, _ in items:
                flat_options.append(label)

        # Default or restored navigation
        cur_stored = st.session_state.get('active_nav_label', flat_options[0])
        if cur_stored not in flat_options:
            cur_stored = flat_options[0]

        # Navigation Selector
        st.markdown(f"<div style='font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:{tokens['text_muted']}; margin-bottom:0.35rem;'>Workspace Navigation</div>", unsafe_allow_html=True)
        selected_label = st.radio(
            'Navigation',
            flat_options,
            index=flat_options.index(cur_stored),
            key='active_nav_label',
            label_visibility='collapsed'
        )

        canonical_page, subtab = NAV_LOOKUP.get(selected_label, ('Overview', None))
        if subtab:
            st.session_state['active_subtab'] = subtab

        st.divider()

        # Appearance & Utility Controls
        st.markdown(f"<div style='font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:{tokens['text_muted']}; margin-bottom:0.25rem;'>Preferences</div>", unsafe_allow_html=True)
        theme_sel = st.selectbox(
            'Appearance',
            ['🌙 Dark Theme', '☀️ White Theme'],
            key='theme',
            label_visibility='collapsed'
        )

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        if st.button('🔄 Refresh Source Files', use_container_width=True):
            st.session_state.pop('_file_registry', None)
            st.session_state.pop('last_onedrive_sync', None)
            st.session_state.pop('_report_snapshot', None)
            st.session_state['run_report'] = True
            st.rerun()

        st.caption('Tata Motors Passenger Vehicles · PPC / SCM')

    # Render Top Enterprise Header
    render_enterprise_header(is_dark=is_dark)

    return canonical_page


# ==============================================================================
# 5. REUSABLE ENTERPRISE UI COMPONENTS
# ==============================================================================

def render_enterprise_header(is_dark: bool = True):
    """Compact enterprise top application header."""
    tokens = get_theme_tokens(is_dark)
    now_ist = datetime.datetime.now(datetime.timezone.utc).astimezone(IST)
    time_str = now_ist.strftime("%d-%b-%Y | %I:%M %p IST")

    # Check sync status
    last_sync = st.session_state.get('last_onedrive_sync')
    sync_err = st.session_state.get('_sync_error')
    auto_sync = st.session_state.get('onedrive_auto_sync', False)

    if sync_err:
        sync_dot = "amber"
        sync_label = "SYNC WARNING"
    elif last_sync:
        sync_dot = "green"
        sync_label = "DATA SYNCED"
    else:
        sync_dot = "cyan"
        sync_label = "STANDALONE / READY"

    auto_label = "AUTO-SYNC ON" if auto_sync else "AUTO-SYNC OFF"
    auto_dot = "blue" if auto_sync else "amber"

    header_html = (
        f'<div class="tml-header">'
        f'<div class="tml-header-left">'
        f'<span class="tml-brand-badge">TML</span>'
        f'<div>'
        f'<div class="tml-header-title">SMART PPC OPERATIONS CONTROL CENTER</div>'
        f'<div class="tml-header-subtitle">VIN • FLOAT • SHORTAGE • CLEARANCE • PRODUCTION</div>'
        f'</div>'
        f'</div>'
        f'<div class="tml-header-right">'
        f'<div class="tml-pill">'
        f'<span class="tml-dot {sync_dot}"></span>'
        f'<span>{sync_label}</span>'
        f'</div>'
        f'<div class="tml-pill">'
        f'<span class="tml-dot {auto_dot}"></span>'
        f'<span>{auto_label}</span>'
        f'</div>'
        f'<div class="tml-pill">'
        f'<span>🕒 {time_str}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, subtext: str = None, status: str = 'neutral',
                    status_label: str = None, line: str = None, is_dark: bool = True):
    """Reusable high-density manufacturing KPI card component."""
    tokens = get_theme_tokens(is_dark)

    # Status color mapping
    status_map = {
        'ok': (tokens['success'], tokens['success_bg']),
        'healthy': (tokens['success'], tokens['success_bg']),
        'warning': (tokens['warning'], tokens['warning_bg']),
        'attention': (tokens['warning'], tokens['warning_bg']),
        'critical': (tokens['critical'], tokens['critical_bg']),
        'shortage': (tokens['critical'], tokens['critical_bg']),
        'info': (tokens['cyan'], tokens['tcf1_bg']),
        'neutral': (tokens['text_muted'], tokens.get('bg_elevated', tokens.get('bg_elev', '#17202C'))),
    }
    st_color, st_bg = status_map.get(status.lower(), (tokens['text_muted'], tokens.get('bg_elevated', tokens.get('bg_elev', '#17202C'))))
    line_cls = f" {line.lower()}" if line else ""

    badge_html = f'<span class="tml-kpi-badge" style="color:{st_color}; background:{st_bg}; border:1px solid {st_color}40;">{status_label}</span>' if status_label else ""
    sub_html = f'<div class="tml-kpi-subtext">{subtext}</div>' if subtext else ""

    return (
        f'<div class="tml-kpi-card{line_cls}">'
        f'<div class="tml-kpi-top">'
        f'<span class="tml-kpi-label">{label}</span>'
        f'{badge_html}'
        f'</div>'
        f'<div class="tml-kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def render_alert_strip(title: str, subtitle: str = None, severity: str = 'critical', is_dark: bool = True):
    """Alert banner with a clean, subtle 4px left border instead of heavy filled boxes."""
    tokens = get_theme_tokens(is_dark)
    sev_class = severity.lower() if severity.lower() in ('critical', 'warning', 'success', 'info') else 'critical'

    icon_map = {
        'critical': '🔴',
        'warning': '🟡',
        'success': '🟢',
        'info': 'ℹ️'
    }
    icon = icon_map.get(sev_class, '🔴')
    sub_html = f'<div class="tml-alert-desc">{subtitle}</div>' if subtitle else ""

    return (
        f'<div class="tml-alert-strip {sev_class}">'
        f'<div class="tml-alert-header">'
        f'<div class="tml-alert-title">{icon} {title}</div>'
        f'</div>'
        f'{sub_html}'
        f'</div>'
    )


def render_section_header(title: str, subtitle: str = None, badge: str = None,
                          badge_type: str = 'blue', is_dark: bool = True):
    """Consistent enterprise section divider."""
    tokens = get_theme_tokens(is_dark)
    badge_colors = {
        'blue': (tokens['blue'], tokens['tcf1_bg']),
        'cyan': (tokens['cyan'], tokens['tcf1_bg']),
        'violet': (tokens['tcf2_accent'], tokens['tcf2_bg']),
        'green': (tokens['success'], tokens['success_bg']),
        'amber': (tokens['warning'], tokens['warning_bg']),
        'red': (tokens['critical'], tokens['critical_bg']),
    }
    b_col, b_bg = badge_colors.get(badge_type, (tokens['blue'], tokens['tcf1_bg']))

    badge_html = f'<span style="font-size:0.7rem; font-weight:700; padding:2px 8px; border-radius:4px; border:1px solid {b_col}; color:{b_col}; background:{b_bg};">{badge}</span>' if badge else ""
    sub_html = f'<div class="tml-section-sub">{subtitle}</div>' if subtitle else ""

    section_html = (
        f'<div class="tml-section-bar">'
        f'<div>'
        f'<div class="tml-section-title">{title}</div>'
        f'{sub_html}'
        f'</div>'
        f'{badge_html}'
        f'</div>'
    )
    st.markdown(section_html, unsafe_allow_html=True)


def file_status_row(name, source, available):
    """File status row in registry with subtle indicators."""
    is_dark = st.session_state.get('theme') == '🌙 Dark Theme'
    tokens = get_theme_tokens(is_dark)

    if available:
        bg = tokens['success_bg']
        fg = tokens['success']
        label = "AVAILABLE"
        dot = "green"
    else:
        bg = tokens['critical_bg']
        fg = tokens['critical']
        label = "PENDING UPLOAD"
        dot = "red"

    # Keep joined rows free of template whitespace: Markdown treats indented
    # HTML after a blank line as a code block, even with unsafe_allow_html=True.
    return (
        f'<div style="display:flex; align-items:center; justify-content:space-between; padding:0.65rem 0.5rem; border-bottom:1px solid {tokens["border"]};">'
        '<div>'
        f'<div style="font-size:0.86rem; font-weight:650; color:{tokens["text_primary"]};">{html.escape(name)}</div>'
        f'<div style="font-size:0.75rem; color:{tokens["text_muted"]}; margin-top:0.15rem;">Source: {html.escape(str(source))}</div>'
        '</div>'
        f'<span style="font-size:0.72rem; font-weight:700; padding:3px 8px; border-radius:4px; background:{bg}; color:{fg}; border:1px solid {fg}30; white-space:nowrap;">'
        f'<span class="tml-dot {dot}" style="margin-right:4px;"></span>{label}'
        '</span>'
        '</div>'
    )


def show_data_health(sources):
    """Inspects file modification times and registry health."""
    rows = []
    for category, source in sources.items():
        if isinstance(source, str) and os.path.isfile(source):
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(source), IST).strftime('%d-%b-%Y %H:%M IST')
            name = os.path.basename(source)
        else:
            name = getattr(source, 'name', str(source) if isinstance(source, str) else 'Workbook sheet')
            timestamp = st.session_state.get('upload_time_' + category, 'Pending')
        rows.append({'Report Category': category.replace('_', ' '), 'Source File': name, 'Last Updated': timestamp})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ==============================================================================
# 6. REDESIGNED MAIN DASHBOARD: "PLANT CONTROL TOWER"
# ==============================================================================

def overview(namespace: dict, sources: dict):
    """
    Renders the Plant Control Tower dashboard matching Requirement 8:
    - Production Date/Time
    - TCF1 KPIs: Dropping, Paint Lifting, Ready, Shortages
    - TCF2 KPIs: Dropping, Paint Lifting, Ready, Shortages
    - Additional: Punch EV VIN, Paint Float, PBS Buffer, Material Alerts
    """
    is_dark = st.session_state.get('theme') == '🌙 Dark Theme'
    tokens = get_theme_tokens(is_dark)

    # Extract datasets from calculated snapshot
    tcf1_df = namespace.get('tcf1_alloc_df', pd.DataFrame())
    tcf2_df = namespace.get('tcf2_alloc_df', pd.DataFrame())
    shop_totals = namespace.get('shop_totals', {}) or {}
    shop_vehicles = namespace.get('shop_vehicles_df', None)
    tcf1_drops = namespace.get('tcf1_drops', None)
    tcf2_drops = namespace.get('tcf2_drops', None)
    pbs_holds = namespace.get('pbs_on_hold', pd.DataFrame())
    cpt_sh_df = namespace.get('df_cpt_shortage', pd.DataFrame())
    wir_sh_df = namespace.get('df_wir_shortage', pd.DataFrame())
    excess_alerts = namespace.get('excess_alerts', [])
    model_shortages = st.session_state.get('model_shortages_df', pd.DataFrame())

    # Calculate Core Metrics
    t1_ready = int(tcf1_df['STATUS'].eq('✅ Ready for TCF').sum()) if not tcf1_df.empty and 'STATUS' in tcf1_df else 0
    t1_blocked = int(tcf1_df['STATUS'].eq('🚫 Blocked').sum()) if not tcf1_df.empty and 'STATUS' in tcf1_df else 0
    t2_ready = int(tcf2_df['STATUS'].eq('✅ Ready for TCF').sum()) if not tcf2_df.empty and 'STATUS' in tcf2_df else 0
    t2_blocked = int(tcf2_df['STATUS'].eq('🚫 Blocked').sum()) if not tcf2_df.empty and 'STATUS' in tcf2_df else 0

    t1_drop = int(shop_totals.get('TCF DROP', 0)) if shop_totals else (len(tcf1_drops) if tcf1_drops is not None else 0)
    t2_drop = int(shop_totals.get('TCF2 DROP', 0)) if shop_totals else (len(tcf2_drops) if tcf2_drops is not None else 0)

    # Paint Lifting by line
    t1_paint = 0
    t2_paint = 0
    if shop_vehicles is not None and not shop_vehicles.empty:
        t1_models = ['PUNCH', 'PUNCH Exports', 'PUNCH EV', 'ALTROZ', 'ALTROZ DCA', 'ALTROZ EV']
        t2_models = ['HARRIER EV', 'SAFARI', 'HARRIER', 'SAFARI EV']
        t1_paint = int(shop_vehicles[shop_vehicles['Model'].isin(t1_models)]['Paint Lifting'].sum())
        t2_paint = int(shop_vehicles[shop_vehicles['Model'].isin(t2_models)]['Paint Lifting'].sum())
    else:
        total_paint = int(shop_totals.get('PAINT', 0)) if shop_totals else 0
        t1_paint = int(total_paint * 0.6)
        t2_paint = max(0, total_paint - t1_paint)

    # Additional metrics
    punch_ev_vin = namespace.get('nova_vin_qty', 0)
    summary_df = namespace.get('summary_df', pd.DataFrame())
    total_paint_float = 0
    if summary_df is not None and not summary_df.empty and 'TOTAL FLOAT' in summary_df.columns:
        grand = summary_df[summary_df['MODEL'].astype(str).str.contains('GRAND TOTAL', case=False, na=False)]
        if not grand.empty:
            total_paint_float = int(grand['TOTAL FLOAT'].iloc[0])
        else:
            total_paint_float = int(pd.to_numeric(summary_df['TOTAL FLOAT'], errors='coerce').sum())

    pbs_total_cabs = len(tcf1_df) + len(tcf2_df) + len(pbs_holds)
    active_shortage_count = (len(cpt_sh_df) if cpt_sh_df is not None else 0) + (len(wir_sh_df) if wir_sh_df is not None else 0)

    # Critical Material Alert Banner
    if active_shortage_count > 0 or t1_blocked > 0 or t2_blocked > 0:
        shortage_items = []
        if active_shortage_count > 0:
            shortage_items.append(f"{active_shortage_count} Cockpit/Wiring part(s) in deficit")
        if t1_blocked > 0:
            shortage_items.append(f"TCF1 has {t1_blocked} cab(s) blocked for materials")
        if t2_blocked > 0:
            shortage_items.append(f"TCF2 has {t2_blocked} cab(s) blocked for materials")
        alert_msg = " · ".join(shortage_items)
        st.markdown(render_alert_strip(
            title="CRITICAL MATERIAL CLEARANCE ALERT",
            subtitle=f"Action required: {alert_msg}. Allocate buffer or expedite material delivery.",
            severity="critical",
            is_dark=is_dark
        ), unsafe_allow_html=True)
    else:
        st.markdown(render_alert_strip(
            title="PLANT MATERIAL HEALTHY · NO CRITICAL DEFICITS",
            subtitle="All monitored parts have positive clearance against today's production requirement.",
            severity="success",
            is_dark=is_dark
        ), unsafe_allow_html=True)

    # Row 1: TCF1 Assembly Line Status
    render_section_header(
        title="TCF1 Production Line Status",
        subtitle="Altroz & Punch family · Assembly dropping, paint lifting, and buffer allocation",
        badge="TCF1 LINE · CYAN",
        badge_type="cyan",
        is_dark=is_dark
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_kpi_card("TCF1 Dropping", f"{t1_drop} cabs", "Built today in TCF1", status="neutral", line="tcf1", is_dark=is_dark), unsafe_allow_html=True)
    with c2:
        st.markdown(render_kpi_card("TCF1 Paint Lifting", f"{t1_paint} cabs", "Fed from Paint to TCF1", status="info", line="tcf1", is_dark=is_dark), unsafe_allow_html=True)
    with c3:
        st.markdown(render_kpi_card("TCF1 Ready for Build", f"{t1_ready} cabs", "Cleared for TCF1 line", status="healthy", status_label="● READY", line="tcf1", is_dark=is_dark), unsafe_allow_html=True)
    with c4:
        st.markdown(render_kpi_card("TCF1 Material Blocked", f"{t1_blocked} cabs", "Waiting on parts", status="critical" if t1_blocked > 0 else "ok", status_label="● SHORTAGE" if t1_blocked > 0 else "● OK", line="tcf1", is_dark=is_dark), unsafe_allow_html=True)

    # Row 2: TCF2 Assembly Line Status
    render_section_header(
        title="TCF2 Production Line Status",
        subtitle="Harrier & Safari family · Assembly dropping, paint lifting, and buffer allocation",
        badge="TCF2 LINE · VIOLET",
        badge_type="violet",
        is_dark=is_dark
    )
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(render_kpi_card("TCF2 Dropping", f"{t2_drop} cabs", "Built today in TCF2", status="neutral", line="tcf2", is_dark=is_dark), unsafe_allow_html=True)
    with c6:
        st.markdown(render_kpi_card("TCF2 Paint Lifting", f"{t2_paint} cabs", "Fed from Paint to TCF2", status="info", line="tcf2", is_dark=is_dark), unsafe_allow_html=True)
    with c7:
        st.markdown(render_kpi_card("TCF2 Ready for Build", f"{t2_ready} cabs", "Cleared for TCF2 line", status="healthy", status_label="● READY", line="tcf2", is_dark=is_dark), unsafe_allow_html=True)
    with c8:
        st.markdown(render_kpi_card("TCF2 Material Blocked", f"{t2_blocked} cabs", "Waiting on parts", status="critical" if t2_blocked > 0 else "ok", status_label="● SHORTAGE" if t2_blocked > 0 else "● OK", line="tcf2", is_dark=is_dark), unsafe_allow_html=True)

    # Row 3: Plant Buffer & Key Metrics
    render_section_header(
        title="Plant Buffer & Material Overview",
        subtitle="Total paint float, PBS buffer inventory, and EV production counts",
        is_dark=is_dark
    )
    c9, c10, c11, c12 = st.columns(4)
    with c9:
        st.markdown(render_kpi_card("Punch EV (Nova) VIN", f"{punch_ev_vin} cabs", "Today EV generation", status="info", is_dark=is_dark), unsafe_allow_html=True)
    with c10:
        st.markdown(render_kpi_card("Paint Shop Float", f"{total_paint_float} cabs", "Total float in paint system", status="neutral", is_dark=is_dark), unsafe_allow_html=True)
    with c11:
        st.markdown(render_kpi_card("PBS Current Buffer", f"{pbs_total_cabs} cabs", f"Holds: {len(pbs_holds)} cabs", status="neutral", is_dark=is_dark), unsafe_allow_html=True)
    with c12:
        st.markdown(render_kpi_card("Material Deficits", f"{active_shortage_count} parts", "Cockpit WH & Wiring", status="critical" if active_shortage_count > 0 else "healthy", status_label="● SHORTAGE" if active_shortage_count > 0 else "● OK", is_dark=is_dark), unsafe_allow_html=True)

    # Detailed Split: Line Comparison & Blocking Breakdown
    col_left, col_right = st.columns([1.1, 1.4])
    with col_left:
        st.markdown("#### 🏭 Line Comparison Summary")
        summary_rows = [
            {'Line': 'TCF1 Line', 'Ready': t1_ready, 'Blocked': t1_blocked, 'Drops': t1_drop},
            {'Line': 'TCF2 Line', 'Ready': t2_ready, 'Blocked': t2_blocked, 'Drops': t2_drop},
            {'Line': 'Total Plant', 'Ready': t1_ready + t2_ready, 'Blocked': t1_blocked + t2_blocked, 'Drops': t1_drop + t2_drop},
        ]
        st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("#### 🚫 Main Blocking Reasons (PBS)")
        all_cabs = pd.concat([tcf1_df, tcf2_df], ignore_index=True)
        if not all_cabs.empty and 'STATUS' in all_cabs.columns:
            blocked_cabs = all_cabs[all_cabs['STATUS'].eq('🚫 Blocked')]
            if not blocked_cabs.empty and 'BLOCKING_REASON' in blocked_cabs.columns:
                counts = (blocked_cabs['BLOCKING_REASON']
                          .fillna('Unknown / Unspecified')
                          .value_counts()
                          .head(6)
                          .rename_axis('Blocking Reason')
                          .reset_index(name='Affected Cabs'))
                st.dataframe(counts, hide_index=True, use_container_width=True)
            else:
                st.info("No cabs currently blocked for material shortages in PBS queue.")
        else:
            st.info("No active allocation queue available.")

    # Vehicle Search Quick Tool
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    render_section_header(title="🔍 Quick Vehicle Search", subtitle="Locate any cab across the plant by BIW, VIN, or Vehicle Code", is_dark=is_dark)
    search_q = st.text_input("Enter BIW Number, VIN, or Vehicle Code", placeholder="e.g. 5468...", key="quick_search_input", label_visibility="collapsed")
    float_data = namespace.get('temp_float_df', pd.DataFrame())
    if search_q.strip() and float_data is not None and not float_data.empty:
        mask = pd.Series(False, index=float_data.index)
        for col in ['BIW NUMBER', 'VIN', 'VEHICLE CODE']:
            if col in float_data.columns:
                mask |= float_data[col].astype(str).str.contains(search_q.strip(), case=False, regex=False, na=False)
        cols_to_show = [c for c in ['BIW NUMBER', 'VIN', 'PRODUCT', 'SHOP', 'Stage', 'Status', 'Blocking Reason'] if c in float_data.columns]
        results = float_data.loc[mask, cols_to_show]
        if not results.empty:
            st.dataframe(results, hide_index=True, use_container_width=True)
        else:
            st.warning(f"No vehicles found matching '{search_q}'.")

    # Data Freshness & Ingestion Health
    with st.expander("🛡️ Data Sources & Ingestion Freshness"):
        show_data_health(sources)


# ==============================================================================
# 7. REDESIGNED TABLE RENDERERS (THEME-AWARE, CLEAN ENTERPRISE STYLING)
# ==============================================================================

def render_html_float_summary_v2(df: pd.DataFrame, is_dark: bool = True) -> str:
    """Upgraded Paint Shop Float Summary Table matching enterprise design tokens."""
    tokens = get_theme_tokens(is_dark)
    border = tokens['border']
    th_bg = tokens['table_th_bg']
    td_hover = tokens['table_td_hover']
    txt_pri = tokens['text_primary']
    txt_mut = tokens['text_muted']
    bg_surf = tokens['bg_surface']
    elev = tokens['bg_elevated']

    html_out = f"""
    <div class="matrix-card">
    <table class="matrix-table" style="font-size: 11.5px;">
        <thead>
            <tr>
                <th style="text-align:left;">Stage</th>
                <th style="text-align:left; width:120px;">MODEL</th>
                <th>TOTAL FLOAT</th>
                <th>PBS FLOAT</th>
                <th>PBS TO POLISHING</th>
                <th>POLISHING TO TOPCOAT</th>
                <th>TOPCOAT ROOFBLACK</th>
                <th>TOPCOAT FRESH</th>
                <th>WETSANDING TO SEALANT</th>
                <th>TOTAL UPTO SEALANT</th>
                <th>PT ENTRY TO SEALANT</th>
                <th>BIW TO PT</th>
                <th>PT BYPASS</th>
                <th>Today VIN</th>
            </tr>
        </thead>
        <tbody>
    """
    for _, r in df.iterrows():
        model_str = str(r.get('MODEL', '')).strip()
        is_subtot = 'TOTAL' in model_str and 'GRAND' not in model_str
        is_grand = 'GRAND TOTAL' in model_str

        row_style = ""
        if is_subtot:
            row_style = f"background: {elev}; font-weight: 700; color: {tokens['blue']};"
        elif is_grand:
            row_style = f"background: {tokens['success_bg']}; font-weight: 800; color: {tokens['success']}; border-top: 2px solid {tokens['success_border']};"

        html_out += f'<tr style="{row_style}">'
        html_out += f'<td style="text-align:left;">{r.get("Paint Float", "")}</td>'
        html_out += f'<td style="text-align:left; font-weight:600;">{model_str}</td>'

        col_keys = [
            'TOTAL FLOAT', 'PBS FLOAT', 'PBS TO POLISHING', 'POLISHING TO TOPCOAT',
            'TOPCOAT TO WETSANDING G ROOFBLACK', 'TOPCOAT TO WETSANDING G FRESH',
            'WETSANDING G TO SEALANT', 'TOTAL UPTO SEALANT', 'PT ENTRY TO SEALANT',
            'BIW LIFTING G TO PT', 'PT BYPASS', 'Today VIN'
        ]
        for col in col_keys:
            val = r.get(col, 0)
            val_str = str(val) if pd.notna(val) else '0'
            html_out += f'<td>{val_str}</td>'
        html_out += '</tr>'

    html_out += '</tbody></table></div>'
    return html_out


def render_html_table_2_v2(rows: list, is_dark: bool = True) -> str:
    """Upgraded Engine & Battery Requirements Table with clear status highlights."""
    tokens = get_theme_tokens(is_dark)
    border = tokens['border']
    th_bg = tokens['table_th_bg']
    txt_pri = tokens['text_primary']
    txt_mut = tokens['text_muted']
    elev = tokens['bg_elevated']
    crit_bg = tokens['critical_bg']
    crit_fg = tokens['critical']

    html_out = f"""
    <div class="matrix-card">
    <table class="matrix-table" style="font-size: 11.5px;">
        <thead>
            <tr>
                <th rowspan="2" style="text-align:center; vertical-align:middle;">Part No</th>
                <th rowspan="2" style="text-align:left; width:160px; vertical-align:middle;">Model</th>
                <th rowspan="2" style="text-align:center; vertical-align:middle;">TA Code</th>
                <th rowspan="2" style="text-align:center; vertical-align:middle;">Clearance 6:30AM</th>
                <th rowspan="2" style="text-align:center; vertical-align:middle;">Today VIN</th>
                <th rowspan="2" style="text-align:center; vertical-align:middle;">Balance</th>
                <th colspan="3" style="text-align:center;">Paint Float Buffer</th>
                <th colspan="3" style="text-align:center;">Requirement vs Float</th>
            </tr>
            <tr>
                <th>PBS</th>
                <th>Upto Sealant</th>
                <th>Total</th>
                <th>vs PBS</th>
                <th>vs Sealant</th>
                <th>vs Total</th>
            </tr>
        </thead>
        <tbody>
    """
    for r in rows:
        r_type = r.get('Type', 'row')
        row_style = ""
        if r_type == 'subtotal':
            row_style = f"background: {elev}; font-weight: 700; color: {tokens['blue']};"
        elif r_type == 'total':
            row_style = f"background: {tokens['success_bg']}; font-weight: 800; color: {tokens['success']}; border-top: 2px solid {tokens['success_border']};"

        html_out += f'<tr style="{row_style}">'
        html_out += f'<td style="text-align:center; font-family:monospace;">{r.get("Engine Part No", "")}</td>'
        html_out += f'<td style="text-align:left; font-weight:600;">{r.get("Model", "")}</td>'
        html_out += f'<td style="text-align:center;">{r.get("TA Code", "")}</td>'
        html_out += f'<td style="text-align:center; font-weight:600;">{r.get("Clearance After 6:30AM", "")}</td>'
        html_out += f'<td style="text-align:center;">{r.get("Today VIN", "")}</td>'

        # Balance cell
        bal = r.get('Bal', '')
        bal_style = ""
        if isinstance(bal, (int, float)) and bal < 0:
            bal_style = f"background:{crit_bg}; color:{crit_fg}; font-weight:700;"
        html_out += f'<td style="text-align:center; {bal_style}">{bal}</td>'

        html_out += f'<td style="text-align:center;">{r.get("PBS FLOAT", "")}</td>'
        html_out += f'<td style="text-align:center;">{r.get("Float UPTO SEALANT", "")}</td>'
        html_out += f'<td style="text-align:center;">{r.get("TOTAL FLOAT", "")}</td>'

        # Deficit check columns
        for col_k in ['With respect to PBS FLOAT', 'With respect to Sealant FLOAT', 'With respect to Total FLOAT']:
            v = r.get(col_k, '')
            c_style = ""
            if isinstance(v, (int, float)) and v < 0:
                c_style = f"background:{crit_bg}; color:{crit_fg}; font-weight:700;"
            html_out += f'<td style="text-align:center; {c_style}">{v}</td>'
        html_out += '</tr>'

    html_out += '</tbody></table></div>'
    return html_out


def render_html_formatted_shortage_v2(df: pd.DataFrame, part_hdr: str, is_dark: bool = True) -> str:
    """Upgraded Cockpit WH and Wiring Harness shortage table."""
    if df.empty:
        return "<p style='color: var(--txt-mut); font-style: italic; padding: 0.5rem;'>No shortage records for this filter.</p>"

    tokens = get_theme_tokens(is_dark)
    crit_bg = tokens['critical_bg']
    crit_fg = tokens['critical']

    html_out = f"""
    <div class="matrix-card">
    <table class="matrix-table" style="font-size: 11.5px;">
        <thead>
            <tr>
                <th style="text-align:center;">{part_hdr}</th>
                <th style="text-align:left; width:180px;">Model</th>
                <th style="text-align:center;">Line</th>
                <th>Clearance 6:30AM</th>
                <th>Today VIN</th>
                <th>Paint Total Float</th>
                <th>PBS Float</th>
                <th>Float Upto Sealant</th>
                <th>Shortage (PBS)</th>
                <th>Shortage (Sealant)</th>
                <th>Shortage (Total)</th>
            </tr>
        </thead>
        <tbody>
    """
    for _, r in df.iterrows():
        html_out += '<tr>'
        html_out += f'<td style="text-align:center; font-family:monospace; font-weight:600;">{r[part_hdr]}</td>'
        html_out += f'<td style="text-align:left; font-weight:600;">{r.get("Model", "")}</td>'

        line_val = str(r.get("LINE", ""))
        badge_cls = "badge-tcf1" if "TCF1" in line_val else "badge-tcf2"
        html_out += f'<td style="text-align:center;"><span class="{badge_cls}">{line_val}</span></td>'

        html_out += f'<td>{r.get("Clearance After 6:30AM", 0)}</td>'
        html_out += f'<td>{r.get("Today VIN", 0)}</td>'
        html_out += f'<td>{r.get("Paint TOTAL FLOAT", 0)}</td>'
        html_out += f'<td>{r.get("PBS FLOAT", 0)}</td>'
        html_out += f'<td>{r.get("Cabs Float UPTO SEALANT", 0)}</td>'

        for col_sh in ['Shortage PBS FLOAT', 'Shortage Upto Sealant', 'Shortage TOTAL FLOAT']:
            val_sh = r.get(col_sh, 0)
            sh_style = ""
            if isinstance(val_sh, (int, float)) and val_sh < 0:
                sh_style = f"background:{crit_bg}; color:{crit_fg}; font-weight:750;"
            html_out += f'<td style="{sh_style}">{val_sh}</td>'
        html_out += '</tr>'

    html_out += '</tbody></table></div>'
    return html_out

# Backward compatibility aliases
render_html_float_summary = render_html_float_summary_v2
render_html_table_2 = render_html_table_2_v2
render_html_formatted_shortage = render_html_formatted_shortage_v2

