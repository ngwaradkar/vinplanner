"""Navigation, report identities and on-demand downloads for the PPC dashboard."""
import datetime
import hashlib
import html
import io
import os
import time

import pandas as pd
import streamlit as st

PAGES = ['Overview', 'Summary & Excel Reports', 'Cockpit & Wiring Shortages',
         'TCF1 Line', 'TCF2 Line', 'Total Float & Search', 'Quality Holds',
         'Control Panel', 'Telegram Dispatcher']
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
PAGE_DESCRIPTIONS = {
    'Overview': 'Production readiness, line status, and the issues that need attention.',
    'Summary & Excel Reports': 'Review production totals and prepare your Excel reports.',
    'Cockpit & Wiring Shortages': 'Check material coverage and identify parts holding up production.',
    'TCF1 Line': 'Readiness, material shortages, and vehicle details for TCF1.',
    'TCF2 Line': 'Readiness, material shortages, and vehicle details for TCF2.',
    'Total Float & Search': 'Find vehicles and inspect the current plant float.',
    'Quality Holds': 'Review held vehicles and the reasons for each hold.',
    'Control Panel': 'Manage report sources, starting stocks, and model settings.',
    'Telegram Dispatcher': 'Preview reports and manage Telegram delivery.',
}


def invalidate_report():
    """A pending input change must not leave an old snapshot available to timers."""
    for key in ('_report_snapshot', '_summary_snapshot', '_prepared_exports'):
        st.session_state.pop(key, None)


def fingerprint(value):
    """Content identity; never use a buffer cursor or DB metadata write time."""
    digest = hashlib.sha256()
    def add(item):
        if isinstance(item, pd.DataFrame):
            digest.update(repr((list(item.columns), list(map(str, item.dtypes)))).encode())
            digest.update(pd.util.hash_pandas_object(item, index=True).values.tobytes())
        elif isinstance(item, dict):
            for key in sorted(item, key=str):
                add(key)
                add(item[key])
        elif isinstance(item, (tuple, list)):
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


def setup_shell():
    st.set_page_config(page_title='PPC Production Dashboard', page_icon='🚗',
                       layout='wide', initial_sidebar_state='expanded')
    # Preserve filter widget values when their page is not rendered.
    for key in list(st.session_state):
        if any(word in key for word in ('filter', 'search', 'view_mode', 'subview', 'detail_columns')):
            st.session_state[key] = st.session_state[key]
    st.session_state.setdefault('theme', '☀️ White Theme')
    with st.sidebar:
        st.markdown('<div class="ppc-brand"><span class="ppc-brand-mark">PPC</span>'
                    '<div><strong>Production Control</strong><small>Plant dashboard</small></div></div>',
                    unsafe_allow_html=True)
        page = st.radio('Workspace', PAGES, key='dashboard_page', label_visibility='collapsed')
        st.divider()
        st.selectbox('Appearance', ['☀️ White Theme', '🌙 Dark Theme'], key='theme')
        if st.button('Refresh source files', use_container_width=True):
            st.session_state.pop('_file_registry', None)
            st.session_state.pop('last_onedrive_sync', None)
            st.session_state.pop('_report_snapshot', None)
            st.session_state['run_report'] = True
            st.rerun()
        st.caption('Stock and upload settings are in Control Panel.')
    dark = st.session_state.theme == '🌙 Dark Theme'
    bg, card, text, border = ('#0f172a','#1e293b','#f1f5f9','#334155') if dark else ('#f6f8fb','#ffffff','#172033','#e2e8f0')
    muted = '#cbd5e1' if dark else '#475569'
    accent = '#93c5fd' if dark else '#1d4ed8'
    hover = '#334155' if dark else '#eff6ff'
    # Streamlit's browser theme is independent of our Appearance selector.
    # Set widget surfaces and foregrounds together, including portaled menus.
    st.markdown(f'''<style>
    html, body, [class*="css"] {{font-family: system-ui, -apple-system, "Segoe UI", sans-serif;}}
    .stApp {{background:{bg}; color:{text}; color-scheme:{'dark' if dark else 'light'};}}
    [data-testid="stSidebar"], [data-testid="stHeader"],
    [data-testid="stToolbar"] {{background:{card}; color:{text};}}
    .stApp :is(h1,h2,h3,h4,h5,h6),
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stExpander"] summary {{color:{text};}}
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] [data-testid="stMarkdownContainer"] {{color:{muted};}}
    .stApp [data-testid="stMarkdownContainer"] a {{color:{accent};}}
    .stApp :is(input,textarea),
    .stApp [data-baseweb="input"],
    .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="textarea"],
    .stApp [data-baseweb="select"] > div {{background:{card}; color:{text}; border-color:{border};}}
    .stApp :is(input,textarea)::placeholder {{color:{muted}; opacity:1;}}
    .stApp [data-baseweb="select"] :is(div,span,svg) {{color:{text};}}
    .stApp [data-baseweb="tag"] {{background:{hover}; color:{text};}}
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] [role="option"] {{background:{card}; color:{text};}}
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [role="option"][aria-selected="true"] {{background:{hover};}}
    .stApp button {{color:{text};}}
    .stApp button[kind="secondary"],
    .stApp button[kind="secondaryFormSubmit"],
    .stApp [data-testid="stNumberInput"] button {{background:{card}; border-color:{border};}}
    .stApp button[kind="secondary"]:hover,
    .stApp button[kind="secondaryFormSubmit"]:hover {{background:{hover}; border-color:{accent};}}
    .stApp button[kind="primary"],
    .stApp button[kind="primaryFormSubmit"] {{background:#1d4ed8; color:#ffffff; border-color:#1d4ed8;}}
    .stApp button [data-testid="stMarkdownContainer"] {{color:inherit;}}
    .stApp button:disabled {{color:{muted}; opacity:.65;}}
    .stApp [data-baseweb="tab"] {{color:{muted};}}
    .stApp [data-baseweb="tab"][aria-selected="true"] {{color:{accent};}}
    .stApp [data-baseweb="tab-highlight"] {{background:{accent};}}
    .stApp [data-testid="stFileUploaderDropzone"] {{background:{card}; color:{text}; border-color:{border};}}
    .stApp [data-testid="stFileUploaderDropzone"] small {{color:{muted};}}
    .stApp [data-testid="stAlertContainer"] {{color:{text};}}
    .stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{background:{'#422f12' if dark else '#fff4ce'};}}
    .stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{background:{'#451f29' if dark else '#fee2e2'};}}
    .stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{background:{'#123c32' if dark else '#dcfce7'};}}
    .stApp [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{background:{'#173352' if dark else '#dbeafe'};}}
    .stApp hr, .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stForm"] {{border-color:{border};}}
    .stApp {{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;}}
    [data-testid="stSidebar"] {{border-right:1px solid {border};}}
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {{color:{muted};}}
    [data-testid="stSidebarUserContent"] {{padding:1.5rem 1rem;}}
    .ppc-brand {{display:flex;align-items:center;gap:.75rem;margin:0 0 1.5rem;}}
    .ppc-brand-mark {{background:#1d4ed8;color:#fff;border-radius:10px;padding:.8rem .55rem;font-weight:750;font-size:.9rem;}}
    .ppc-brand strong {{font-size:.95rem;display:block;color:{text};}}
    .ppc-brand small {{display:block;color:{muted};font-size:.78rem;margin-top:.2rem;}}
    [data-testid="stSidebar"] [role="radiogroup"] {{gap:.25rem;}}
    [data-testid="stSidebar"] label[data-baseweb="radio"] {{width:100%;box-sizing:border-box;margin:0;padding:.65rem .75rem;border-radius:8px;border:1px solid transparent;}}
    [data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {{display:none;}}
    [data-testid="stSidebar"] label[data-baseweb="radio"] > div:last-child {{padding:0;}}
    [data-testid="stSidebar"] label[data-baseweb="radio"] p {{font-size:.88rem;line-height:1.4;}}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{background:{hover};}}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {{background:{hover};border-color:{border};box-shadow:inset 3px 0 {accent};}}
    [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p {{color:{accent};font-weight:650;}}
    .stApp :is(button,input,textarea,[role="combobox"]):focus-visible,
    [data-testid="stSidebar"] label[data-baseweb="radio"]:focus-within {{outline:2px solid {accent};outline-offset:3px;}}
    .stApp .block-container {{padding:4.5rem 2rem 2.5rem;max-width:1600px;}}
    .stApp h1 {{font-size:1.85rem !important;line-height:1.25;font-weight:700;padding-bottom:.3rem;text-wrap:balance;}}
    .stApp h2 {{font-size:1.3rem !important;line-height:1.4;}}
    .stApp h3 {{font-size:1.1rem !important;line-height:1.4;}}
    .stApp h4 {{font-size:1rem !important;line-height:1.4;}}
    .ppc-page-description {{color:{muted};font-size:.9rem;line-height:1.5;margin:0 0 .9rem;}}
    .stApp [data-testid="stCaptionContainer"] p {{color:{muted};font-size:.8rem;opacity:1;}}
    .stApp [data-testid="stWidgetLabel"] p {{font-size:.85rem;font-weight:550;}}
    .stApp [data-testid="stMetric"] {{background:{card};border:1px solid {border};border-radius:12px;padding:1rem 1.1rem;}}
    .stApp [data-testid="stMetricLabel"] p {{font-size:.8rem;color:{muted};}}
    .stApp [data-testid="stMetricValue"] {{font-size:1.75rem;font-weight:650;font-variant-numeric:tabular-nums;}}
    .stApp [data-testid="stDataFrame"] {{border:1px solid {border};border-radius:10px;overflow:hidden;}}
    .stApp button[kind="secondary"], .stApp button[kind="primary"],
    .stApp button[kind="primaryFormSubmit"] {{border-radius:8px;min-height:2.65rem;font-weight:550;}}
    .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] {{border-radius:8px;min-height:2.65rem;}}
    .stApp [data-baseweb="tab-list"] {{gap:1.25rem;border-bottom:1px solid {border};}}
    .stApp [data-baseweb="tab"] {{padding:.7rem .2rem;height:auto;}}
    .stApp [data-baseweb="tab"] p {{font-size:.88rem;}}
    .stApp [data-baseweb="tab-border"] {{background:transparent;}}
    .stApp [data-testid="stExpander"] details, .stApp [data-testid="stForm"] {{background:{card};border-radius:12px;}}
    .stApp [data-testid="stExpander"] summary {{background:{card};border-bottom:1px solid {border};border-radius:12px 12px 0 0;}}
    .stApp [data-testid="stExpander"] summary:hover {{background:{hover};}}
    .stApp label[data-baseweb="checkbox"]:has(input:checked) > div:first-child {{background:#1d4ed8;border-color:#1d4ed8;}}
    .stApp [data-testid="stAlertContainer"] {{border-radius:10px;padding:1rem;}}
    .stApp hr {{margin:1rem 0;}}
    .stApp .st-key-sticky_kpi_bar {{position:sticky;top:3.75rem;z-index:10;background:{bg};padding:.5rem 0;border-bottom:1px solid {border};}}
    .matrix-card {{border:1px solid {border};border-radius:10px;overflow-x:auto;margin:.5rem 0 1rem;background:{card};}}
    .matrix-table {{width:100%;border-collapse:collapse;font-size:.85rem;font-variant-numeric:tabular-nums;}}
    .matrix-table :is(th,td) {{padding:.75rem 1rem;text-align:right;border-bottom:1px solid {border};color:{text};}}
    .matrix-table th {{background:{hover};font-weight:650;white-space:nowrap;}}
    .matrix-table :is(th,td):first-child {{text-align:left;}}
    .matrix-table tr:hover {{background:{hover};}}
    .matrix-table :is(.tr-tcf1-tot,.tr-tcf2-tot) td {{background:{hover};font-weight:650;}}
    .matrix-table .tr-grand-tot td {{background:#1e3a8a;color:#fff;font-weight:700;}}
    .badge-tcf1,.badge-tcf2 {{display:inline-block;border:1px solid {border};color:{muted};padding:.15rem .4rem;border-radius:5px;font-size:.7rem;}}
    .ppc-file-row {{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem 0;border-bottom:1px solid {border};}}
    .ppc-file-row:last-child {{border-bottom:0;}}
    .ppc-file-name {{font-size:.85rem;font-weight:600;color:{text};overflow-wrap:anywhere;}}
    .ppc-file-time {{font-size:.78rem;color:{muted};margin-top:.2rem;}}
    .ppc-file-badge {{font-size:.75rem;font-weight:600;border-radius:6px;padding:.25rem .55rem;white-space:nowrap;}}
    @media(max-width:1100px) {{
      .stApp .st-key-sticky_kpi_bar {{position:static;}}
      .stApp .block-container {{padding-left:1.25rem;padding-right:1.25rem;}}
      [data-testid="stHorizontalBlock"] {{flex-wrap:wrap;gap:1rem;}}
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{min-width:min(210px,100%) !important;flex:1 1 210px !important;}}
    }}
    @media(max-width:600px) {{
      .stApp .block-container {{padding:4.5rem 1rem 2rem;}}
      .stApp h1 {{font-size:1.55rem !important;}}
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{min-width:100% !important;flex-basis:100% !important;}}
      .stApp [data-baseweb="tab-list"] {{gap:.75rem;}}
    }}
    </style>''', unsafe_allow_html=True)
    st.title(page)
    st.markdown(f'<p class="ppc-page-description">{PAGE_DESCRIPTIONS[page]}</p>', unsafe_allow_html=True)
    return page


def file_status_row(name, source, available):
    """Readable status rows; report names and timestamps can wrap on mobile."""
    dark = st.session_state.get('theme') == '🌙 Dark Theme'
    background, foreground = (('#123c32', '#bbf7d0') if dark else ('#dcfce7', '#166534')) if available else (('#422f12', '#fde68a') if dark else ('#fff4ce', '#854d0e'))
    status = 'Available' if available else 'Missing'
    return (f'<div class="ppc-file-row"><div><div class="ppc-file-name">{html.escape(name)}</div>'
            f'<div class="ppc-file-time">{html.escape(source)}</div></div>'
            f'<span class="ppc-file-badge" style="background:{background};color:{foreground}">{status}</span></div>')


def cached_download(*, label, builder, file_name, key, version=None, **kwargs):
    """Builders run only on request. Invalidate when inputs or export filters change."""
    identity = fingerprint((st.session_state.get('_report_key'), version))
    cache = st.session_state.setdefault('_prepared_exports', {})
    entry = cache.get(key)
    if entry is not None and entry[0] != identity:
        cache.pop(key, None)
        entry = None
    if st.button('Prepare · ' + label.replace('📥 ', '').replace('⬇️ ', ''), key='prepare_' + key):
        with st.spinner('Preparing Excel file…'):
            data = builder()
        cache[key] = (identity, data)
        entry = cache[key]
        # Keep memory bounded; each report refresh also clears this cache.
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
                ws.column_dimensions[column[0].column_letter].width = min(48, max(14, max(len(str(c.value or '')) for c in column) + 2))
    return output.getvalue()


def file_registry(directory, detector):
    """Only scan on interval or explicit refresh; content parsers have their own cache."""
    cached = st.session_state.get('_file_registry')
    if not cached or cached[0] != directory or time.monotonic() - cached[1] > 60:
        sources = detector(directory)
        cached = (directory, time.monotonic(), sources, fingerprint(sources))
        st.session_state['_file_registry'] = cached
    return cached[2].copy()


def clear_stock_drafts():
    for key in ('engine_stock_editor', 'nova_stock_editor'):
        st.session_state.pop(key, None)


def show_data_health(sources):
    rows = []
    for category, source in sources.items():
        if isinstance(source, str) and os.path.isfile(source):
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(source), IST).strftime('%d %b %H:%M IST')
            name = os.path.basename(source)
        else:
            name = getattr(source, 'name', str(source) if isinstance(source, str) else 'Workbook sheet')
            timestamp = st.session_state.get('upload_time_' + category, 'Not supplied')
        rows.append({'Report': category.replace('_', ' '), 'Source': name, 'File modified / received': timestamp})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption('File modified / received time is not necessarily the source report’s production cutoff time.')


def overview(namespace, sources):
    frames = [namespace['tcf1_alloc_df'], namespace['tcf2_alloc_df']]
    queue = pd.concat(frames, ignore_index=True)
    status = queue.get('STATUS', pd.Series(dtype=str))
    drops = sum(int(df['VIN_Count'].sum()) if 'VIN_Count' in df else len(df)
                for df in [namespace['tcf1_drops'], namespace['tcf2_drops']] if df is not None)
    holds = namespace['pbs_on_hold']
    metrics = [('VIN generated · both lines', drops), ('PBS ready', int(status.eq('✅ Ready for TCF').sum())),
               ('PBS material blocked', int(status.eq('🚫 Blocked').sum())), ('PBS quality holds', len(holds)),
               ('PBS BOM issues', int(status.str.startswith('⚠️', na=False).sum()))]
    for column, (label, value) in zip(st.columns(5), metrics):
        column.metric(label, value)
    st.subheader('Line status')
    rows = []
    for line, frame in zip(['TCF1', 'TCF2'], frames):
        values = frame.get('STATUS', pd.Series(dtype=str))
        rows.append({'Line': line, 'Ready': int(values.eq('✅ Ready for TCF').sum()),
                     'Blocked': int(values.eq('🚫 Blocked').sum()), 'BOM issues': int(values.str.startswith('⚠️',na=False).sum())})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.subheader('Main blocking reasons · PBS')
    blocked = queue[status.eq('🚫 Blocked')] if not queue.empty else queue
    if not blocked.empty:
        counts = blocked['BLOCKING_REASON'].fillna('Unknown').value_counts().head(8).rename_axis('Reason').reset_index(name='Affected cabs')
        st.dataframe(counts, hide_index=True, use_container_width=True)
    else:
        st.info('No PBS material blocking reasons in this report.')
    st.subheader('Find a vehicle')
    query = st.text_input('BIW / VIN / vehicle code', key='overview_search')
    data = namespace['temp_float_df']
    if query.strip() and not data.empty:
        mask = pd.Series(False,index=data.index)
        for col in ['BIW NUMBER','VIN','VEHICLE CODE']:
            if col in data: mask |= data[col].astype(str).str.contains(query.strip(),case=False,regex=False,na=False)
        columns = [c for c in ['BIW NUMBER','VIN','PRODUCT','SHOP','Stage','Status','Blocking Reason'] if c in data]
        st.dataframe(data.loc[mask,columns], hide_index=True,use_container_width=True)
    with st.expander('Source files and freshness'):
        show_data_health(sources)
