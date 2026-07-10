import os
import re
import random
import time
import difflib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Pakistan District Socioeconomic Dashboard", page_icon="🇵🇰", layout="wide")

# --- Theme: this dashboard is locked to Dark Mode only ---
CHART_FONT_COLOR = "#e2e8f0"
CHART_GRID_COLOR = "rgba(255,255,255,0.08)"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# --- Enhanced Dark-Mode Design System ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    :root {
        --bg-base: #0a0f1c;
        --bg-surface: #131c30;
        --bg-surface-2: #1b2740;
        --border-subtle: rgba(255,255,255,0.08);
        --border-strong: rgba(255,255,255,0.16);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --accent: #06b6d4;
        --accent-bright: #22d3ee;
        --accent-glow: rgba(6,182,212,0.35);
    }

    /* --- Global text-color safety net: catches any native widget text not
       explicitly styled elsewhere. Uses the universal selector to keep specificity
       LOW (tied with single-class rules like .pill), so anything defined later
       in this stylesheet still wins on source order as intended. --- */
    .stApp * { color: #e2e8f0; }

    /* --- Page background: subtle depth via radial glow --- */
    .stApp {
        background:
            radial-gradient(circle at 15% -10%, rgba(6,182,212,0.10), transparent 35%),
            radial-gradient(circle at 90% 10%, rgba(139,92,246,0.07), transparent 35%),
            var(--bg-base);
    }
    header[data-testid="stHeader"] { background: transparent; }

    /* --- Custom scrollbars --- */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(6,182,212,0.35); border-radius: 10px; border: 2px solid transparent; background-clip: content-box; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(6,182,212,0.6); background-clip: content-box; }

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%);
        border-right: 1px solid var(--border-subtle);
        box-shadow: 4px 0 24px rgba(0,0,0,0.3);
    }

    /* --- KPI Metric Cards --- */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, var(--bg-surface-2) 0%, var(--bg-surface) 100%);
        border: 1px solid var(--border-subtle);
        border-left: 3px solid var(--accent);
        border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        position: relative; overflow: hidden;
    }
    div[data-testid="stMetric"]::after {
        content: ""; position: absolute; top: 0; right: 0; width: 60px; height: 60px;
        background: radial-gradient(circle, var(--accent-glow), transparent 70%);
        opacity: 0.6; pointer-events: none;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 28px rgba(6,182,212,0.18), 0 4px 12px rgba(0,0,0,0.4);
        border-left-color: var(--accent-bright);
    }
    div[data-testid="stMetric"] label p { font-size: 12.5px; color: var(--text-secondary); font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; margin-bottom: 6px; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 27px; font-weight: 700; color: var(--text-primary); }

    /* --- Sidebar labels & section headers --- */
    .sidebar-label { font-weight: 700; font-size: 13.5px; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px; margin-top: 18px; display: block; }
    .section-header {
        font-size: 18px; font-weight: 700; color: var(--text-primary);
        margin-top: 12px; margin-bottom: 16px; padding-left: 12px;
        border-left: 4px solid var(--accent); position: relative;
    }

    /* --- Tabs: two-row grid, pill-style active state --- */
    .stTabs [data-baseweb="tab-list"] { gap: 8px !important; flex-wrap: wrap !important; overflow-x: visible !important; row-gap: 10px; border-bottom: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] { flex: 0 0 calc(20% - 7px) !important; box-sizing: border-box !important; justify-content: center !important; white-space: normal !important; text-align: center !important; }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 10px; border-radius: 10px; background: var(--bg-surface);
        border: 1px solid var(--border-subtle); color: var(--text-secondary);
        font-weight: 600; transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { background: var(--bg-surface-2); color: var(--text-primary); border-color: var(--border-strong); }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(160deg, rgba(6,182,212,0.18), rgba(6,182,212,0.06)) !important;
        color: var(--accent-bright) !important; border: 1px solid var(--accent-glow) !important;
        box-shadow: 0 0 16px rgba(6,182,212,0.15);
    }
    button[aria-label*="scroll" i] { display: none !important; }

    /* --- Insights box: glassmorphism --- */
    .insights-box {
        background: linear-gradient(135deg, rgba(6,182,212,0.09), rgba(139,92,246,0.05));
        border: 1px solid rgba(6,182,212,0.25); border-left: 4px solid var(--accent);
        border-radius: 12px; padding: 18px 22px; margin-bottom: 25px; color: var(--text-primary);
        backdrop-filter: blur(6px);
    }
    .insights-box h4 { font-weight: 700; margin-bottom: 12px; color: var(--accent-bright); display: flex; align-items: center; gap: 8px; }
    .insights-box ul { margin-bottom: 0; padding-left: 20px; }
    .insights-box li { margin-bottom: 7px; font-size: 14px; line-height: 1.6; color: #e2e8f0; }

    /* --- Custom dark HTML table (replaces st.dataframe, which is canvas-rendered
       and reads Streamlit's actual theme directly -- CSS cannot restyle it at all) --- */
    .dark-table-wrapper {
        max-width: 100%; overflow-x: auto; overflow-y: auto;
        border: 1px solid var(--border-subtle); border-radius: 12px;
        background: var(--bg-surface);
    }
    table.dark-table { border-collapse: collapse; width: 100%; font-size: 13.5px; color: #e2e8f0; white-space: nowrap; }
    table.dark-table thead th {
        position: sticky; top: 0; z-index: 1;
        background: var(--bg-surface-2); color: #cbd5e1; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.02em; font-size: 12px;
        padding: 12px 16px; text-align: left; border-bottom: 2px solid var(--accent);
        white-space: nowrap;
    }
    table.dark-table tbody td { padding: 10px 16px; border-bottom: 1px solid var(--border-subtle); }
    table.dark-table tbody tr:nth-child(even) { background: rgba(255,255,255,0.02); }
    table.dark-table tbody tr:hover { background: rgba(6,182,212,0.08); }
    table.dark-table tbody td:first-child, table.dark-table thead th:first-child { padding-left: 20px; }

    /* --- Buttons (Clear Chat, quick prompts) --- */
    .stButton > button, .stDownloadButton > button {
        background: var(--bg-surface-2) !important; color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important; border-radius: 10px !important;
        font-weight: 600 !important; transition: all 0.2s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--accent) !important; color: var(--accent-bright) !important;
        box-shadow: 0 0 12px rgba(6,182,212,0.25) !important; transform: translateY(-1px);
    }
    .stButton > button p, .stDownloadButton > button p { color: inherit !important; }

    /* --- Multiselect chips (fix: text color was unset, defaulting to low-contrast) --- */
    [data-baseweb="tag"] { background-color: rgba(6,182,212,0.28) !important; border: 1px solid rgba(6,182,212,0.5) !important; }
    [data-baseweb="tag"] * { background-color: transparent !important; color: #ecfeff !important; fill: #ecfeff !important; }

    /* --- Checkbox & radio labels (e.g. "Select All Provinces") --- */
    .stCheckbox label p, .stCheckbox label span,
    .stRadio label p, .stRadio label span,
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #e2e8f0 !important; opacity: 1 !important;
    }

    /* --- st.caption text (was near-invisible dim gray on dark bg) --- */
    small, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span {
        color: #aab4c5 !important; opacity: 1 !important;
    }

    /* --- Select / multiselect dropdown text, placeholder, and options --- */
    div[data-baseweb="select"] * { color: #e2e8f0 !important; }
    div[data-baseweb="select"] > div { background-color: var(--bg-surface-2) !important; border-color: var(--border-subtle) !important; box-shadow: none !important; }
    div[data-baseweb="select"] svg { fill: #94a3b8 !important; }
    div[data-baseweb="select"] input::placeholder { color: #7c8aa3 !important; }
    ul[data-baseweb="menu"] { background: var(--bg-surface-2) !important; }
    ul[data-baseweb="menu"] li { color: #e2e8f0 !important; }

    /* --- Slider labels / min-max ticks --- */
    div[data-testid="stSlider"] label p { color: #e2e8f0 !important; }
    div[data-testid="stSlider"] div[data-testid="stTickBarMin"],
    div[data-testid="stSlider"] div[data-testid="stTickBarMax"] { color: #aab4c5 !important; }
    div[data-testid="stThumbValue"] { color: #ecfeff !important; }

    /* --- Selectbox current value text --- */
    div[data-testid="stSelectbox"] label p { color: #e2e8f0 !important; }

    /* --- AI Chat Bot Tab Styling --- */
    [data-testid="stChatInput"] {
        background: var(--bg-surface-2) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] > div, [data-testid="stChatInput"] div {
        background: transparent !important;
    }
    [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] textarea * {
        background: transparent !important; color: #f1f5f9 !important; -webkit-text-fill-color: #f1f5f9 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #7c8aa3 !important; opacity: 1 !important; }
    [data-testid="stChatInput"]:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 12px rgba(6,182,212,0.25) !important; }
    [data-testid="stChatInput"] button {
        background: var(--accent) !important; border-radius: 8px !important;
    }
    [data-testid="stChatInput"] button:hover { background: var(--accent-bright) !important; }
    [data-testid="stChatInput"] button svg { fill: #0a0f1c !important; }
    .chatbot-card {
        background: linear-gradient(135deg, #0b1220 0%, #1b2740 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 16px; padding: 20px 26px; margin-bottom: 16px;
        display: flex; align-items: center; gap: 16px;
        box-shadow: 0 8px 28px rgba(6,182,212,0.08), 0 4px 14px rgba(0,0,0,0.3);
    }
    .chatbot-avatar {
        width: 52px; height: 52px; border-radius: 50%;
        background: linear-gradient(135deg, #06b6d4, #0891b2);
        display: flex; align-items: center; justify-content: center;
        font-size: 26px; flex-shrink: 0; box-shadow: 0 4px 14px rgba(6,182,212,0.5);
    }
    .chatbot-title { font-size: 19px; font-weight: 700; color: #ffffff; margin-bottom: 3px; }
    .chatbot-status { font-size: 12.5px; color: #67e8f9; display: flex; align-items: center; gap: 6px; font-weight: 500; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #06b6d4; display: inline-block; box-shadow: 0 0 8px #06b6d4; animation: pulse-dot 1.8s infinite; }
    @keyframes pulse-dot { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    .capability-pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 18px 0; }
    .pill { background: rgba(6,182,212,0.14); color: var(--accent-bright); font-size: 12px; font-weight: 600; padding: 6px 13px; border-radius: 999px; border: 1px solid rgba(6,182,212,0.3); transition: all 0.2s ease; }
    .pill:hover { background: rgba(6,182,212,0.24); }
    div[data-testid="stChatMessage"] { background: var(--bg-surface) !important; border: 1px solid var(--border-subtle); border-radius: 14px; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# HELPER: consistent theme-aware chart styling
# ==========================================
def style_fig(fig, showlegend=None, height=440):
    layout_kwargs = dict(
        font=dict(family="Inter", size=12, color=CHART_FONT_COLOR),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(
            font=dict(color=CHART_FONT_COLOR, family="Inter"),
            bgcolor='rgba(0,0,0,0)', bordercolor=CHART_GRID_COLOR, borderwidth=1,
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color=CHART_FONT_COLOR), title_font=dict(color=CHART_FONT_COLOR),
        ),
    )
    if showlegend is not None:
        layout_kwargs['showlegend'] = showlegend
    if height is not None:
        layout_kwargs['height'] = height
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(gridcolor=CHART_GRID_COLOR)
    fig.update_yaxes(gridcolor=CHART_GRID_COLOR)
    return fig


# ==========================================
# DATA LOADING
# ==========================================
DATA_FILE = "Master_File_-_District.xlsx"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_data_file():
    """Look for the district Excel file: exact name first, then any xlsx that
    looks like it, then fall back to the only xlsx present, if there's just one."""
    import glob
    search_dirs = [os.getcwd(), SCRIPT_DIR]
    all_xlsx = []
    for d in search_dirs:
        all_xlsx += glob.glob(os.path.join(d, "*.xlsx"))
        all_xlsx += glob.glob(os.path.join(d, "*.XLSX"))
    all_xlsx = list(dict.fromkeys(all_xlsx))  # de-dupe, preserve order

    for c in all_xlsx:  # 1) exact filename match
        if os.path.basename(c) == DATA_FILE:
            return c, search_dirs, all_xlsx
    for c in all_xlsx:  # 2) fuzzy match on name
        name = os.path.basename(c).lower()
        if 'master' in name and 'district' in name:
            return c, search_dirs, all_xlsx
    if len(all_xlsx) == 1:  # 3) only one xlsx anywhere nearby -> assume it's the one
        return all_xlsx[0], search_dirs, all_xlsx
    return None, search_dirs, all_xlsx

RATE_EXEMPT_COLS = ['AAPGR', 'Average of avg_hh_size', 'Average of sex_ratio']

AGE_COLS = ['UNDER 5', 'UNDER 10', 'UNDER 15', '15 - 49', '15 - 64', '18 - 60', '18 &  ABOVE', '60 &  ABOVE', '65 &  ABOVE']
MARITAL_COLS = ['Marital Status.Never Married', 'Marital Status.Married', 'Marital Status.Divorced', 'Marital Status.Seperation', 'Marital Status.Widowed']
RELIGION_COLS = ['Religion.MUSLIM', 'Religion.CHRISTIAN', 'Religion.HINDU JATI', 'Religion.QADIANI/AHMADI', 'Religion.SCHEDULED CASTE', 'Religion.SIKH', 'Religion.PARSI', 'Religion.OTHERS']
LANGUAGE_COLS = ['Urdu', 'Punjabi', 'Pushto', 'Sindhi', 'Saraiki', 'Balochi', 'Hindko', 'Brahvi', 'Kashmiri', 'Shina', 'Balti', 'Kohiostani', 'Mewati', 'Kalasha', 'Others']
NATIONALITY_COLS = ['Nationality.Pakistani', 'Nationality.Afghani', 'Nationality.Bengali', 'Nationality.Chinese', 'Nationality.Others']
HOUSING_TYPE_COLS = ['Pakka', 'Semi Pakka', 'Kacha']
ROOM_COLS = ['1 Room', '2 Room', '3 Room', '4 and More Room']
FUEL_COLS = ['Gas', 'LPG/CNG', 'Firewood', 'Other Fuel']
LIGHT_COLS = ['Electricity', 'Solar', 'Other Light Source']
TOILET_COLS = ['Toilet : Flush', 'Toilet : Non-Flush', 'Toilet : Separate', 'Toilet : None']
TENURE_COLS = ['Owned', 'Rented', 'Rent Free']
DISABILITY_COLS = ['Seeing', 'Hearing', 'Walking/ Climbing', 'Self care etc', 'Communication', 'Memorization/ Focus', 'Functional limitation']
BUILDING_TYPE_COLS = ['Normal Residential', 'Normal Economic', 'Normal Residential & Economic', 'High Rise Residential', 'High Rise Economic', 'High Rise Residential & Economic', 'Other Jughi', 'Other Under Construction']
KITCHEN_COLS = ['Kitchen : Separate', 'Kitchen : None']
WASHROOM_COLS = ['Washroom : Separate', 'Washroom : None']
LAND_TENURE_COLS = ['Govt', 'Non - Govt']

ENTITY_COLUMNS = ['District', 'Province', 'Division', 'Gallup Region', 'Region Type']

# Consistent, vivid palette for Province-colored charts across every tab (dark-mode tuned)
PROVINCE_COLORS = px.colors.qualitative.D3


@st.cache_data(ttl=3600)
def load_data(file_source):
    df = pd.read_excel(file_source, sheet_name='Merge1')
    df.columns = df.columns.str.strip()
    df = df.drop(columns=[c for c in ['Province.1', 'District Clean _2', 'Code'] if c in df.columns])
    df = df.rename(columns={'province': 'Province', 'region': 'Region Type', 'Division_1': 'Division', 'Regions 12': 'Gallup Region'})
    df = df.dropna(subset=['District', 'Province'])

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    fill_cols = [c for c in numeric_cols if c not in RATE_EXEMPT_COLS]
    df[fill_cols] = df[fill_cols].fillna(0)

    # --- Derived rate columns (avoid divide-by-zero) ---
    df['Literacy Rate %'] = np.where(df['10 + Population'] > 0, df['Sum of Literacy Rate'] / df['10 + Population'] * 100, np.nan)
    df['School Attendance %'] = np.where(df['School Attendance.5 - 14  Population'] > 0, df['School Attendance'] / df['School Attendance.5 - 14  Population'] * 100, np.nan)
    df['Enrolment Primary %'] = np.where(df['Enrolment Primary.5 - 9  Population'] > 0, df['Enrolment Primary'] / df['Enrolment Primary.5 - 9  Population'] * 100, np.nan)
    return df


data_source, _searched_dirs, _found_xlsx = find_data_file()
if data_source is None:
    st.sidebar.markdown("## 📋 Data Source")
    with st.sidebar.expander("🔧 Why am I seeing this? (debug info)"):
        st.write("**Looked in these folders:**")
        for d in _searched_dirs: st.code(d)
        st.write("**Excel files found nearby:**")
        st.write(_found_xlsx if _found_xlsx else "None found.")
        st.caption("If your file is listed above but wasn't picked, or isn't listed at all, the app can't see it from where it's running — double-check the exact filename and folder, or just upload it below.")
    uploaded = st.sidebar.file_uploader("Upload Master_File_-_District.xlsx", type=["xlsx"])
    if uploaded is None:
        st.info("👋 Please upload **Master_File_-_District.xlsx** in the sidebar to load the dashboard.")
        st.stop()
    data_source = uploaded

df = load_data(data_source)


def weighted_avg(f_df, value_col, weight_col):
    w = f_df[weight_col].sum()
    if w == 0: return np.nan
    return (f_df[value_col] * f_df[weight_col]).sum() / w


def fmt_compact(n):
    """Format large numbers compactly (e.g. 55,696,147 -> '55.7M') so metric cards don't truncate."""
    if pd.isna(n): return "N/A"
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000_000: return f"{sign}{n/1_000_000_000:.2f}B"
    if n >= 1_000_000: return f"{sign}{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{sign}{n/1_000:.1f}K"
    return f"{sign}{n:,.0f}"


def render_dark_table(df, max_height=480):
    """Render a dataframe as a custom dark-themed HTML table.
    Used instead of st.dataframe, whose grid is canvas-rendered and reads Streamlit's
    actual active theme directly -- it cannot be restyled with CSS at all."""
    display_df = df.copy()
    for col in display_df.select_dtypes(include=[np.number]).columns:
        display_df[col] = display_df[col].map(lambda v: f"{v:,.2f}".rstrip('0').rstrip('.') if pd.notna(v) else "")
    html = display_df.to_html(classes='dark-table', index=False, border=0, escape=True)
    st.markdown(f'<div class="dark-table-wrapper" style="max-height:{max_height}px;">{html}</div>', unsafe_allow_html=True)


def rate_from_sums(f_df, num_col, den_col):
    den = f_df[den_col].sum()
    if den == 0: return np.nan
    return f_df[num_col].sum() / den * 100


def col_sum_df(f_df, cols, strip_prefixes=('Religion.', 'Nationality.', 'Marital Status.', 'Toilet : ')):
    data = f_df[cols].sum().reset_index()
    data.columns = ['Category', 'Count']
    for p in strip_prefixes:
        data['Category'] = data['Category'].str.replace(p, '', regex=False)
    return data.sort_values('Count', ascending=False)

# ==========================================
# SIDEBAR FILTERS
# ==========================================
st.sidebar.markdown("## 📋 Dashboard Filters")

st.sidebar.markdown('<div class="sidebar-label">Province</div>', unsafe_allow_html=True)
all_provinces = sorted(df['Province'].dropna().unique())
cb_prov = st.sidebar.checkbox("Select All Provinces", True, key="cb_prov")
if not cb_prov and len(all_provinces) > 0:
    selected_provinces = st.sidebar.multiselect("", all_provinces, default=[], key="ms_prov", label_visibility="collapsed")
    if not selected_provinces: selected_provinces = all_provinces
else: selected_provinces = all_provinces

st.sidebar.markdown('<div class="sidebar-label">Division</div>', unsafe_allow_html=True)
div_df = df[df['Province'].isin(selected_provinces)]
all_divisions = sorted(div_df['Division'].dropna().unique())
cb_div = st.sidebar.checkbox("Select All Divisions", True, key="cb_div")
if not cb_div and len(all_divisions) > 0:
    selected_divisions = st.sidebar.multiselect("", all_divisions, default=[], key="ms_div", label_visibility="collapsed")
    if not selected_divisions: selected_divisions = all_divisions
else: selected_divisions = all_divisions

st.sidebar.markdown('<div class="sidebar-label">Gallup Region</div>', unsafe_allow_html=True)
gallup_df = div_df[div_df['Division'].isin(selected_divisions)]
all_gallup = sorted(gallup_df['Gallup Region'].dropna().unique())
cb_gallup = st.sidebar.checkbox("Select All Gallup Regions", True, key="cb_gallup")
if not cb_gallup and len(all_gallup) > 0:
    selected_gallup = st.sidebar.multiselect("", all_gallup, default=[], key="ms_gallup", label_visibility="collapsed")
    if not selected_gallup: selected_gallup = all_gallup
else: selected_gallup = all_gallup

st.sidebar.markdown('<div class="sidebar-label">Region Type</div>', unsafe_allow_html=True)
region_df = gallup_df[gallup_df['Gallup Region'].isin(selected_gallup)]
all_region_types = sorted(region_df['Region Type'].dropna().unique())
cb_region = st.sidebar.checkbox("Select All (Urban/Rural)", True, key="cb_region")
if not cb_region and len(all_region_types) > 0:
    selected_region_types = st.sidebar.multiselect("", all_region_types, default=[], key="ms_region", label_visibility="collapsed")
    if not selected_region_types: selected_region_types = all_region_types
else: selected_region_types = all_region_types

st.sidebar.markdown('<div class="sidebar-label">District</div>', unsafe_allow_html=True)
dist_df = region_df[region_df['Region Type'].isin(selected_region_types)]
all_districts = sorted(dist_df['District'].dropna().unique())
cb_dist = st.sidebar.checkbox("Select All Districts", True, key="cb_dist")
if not cb_dist and len(all_districts) > 0:
    selected_districts = st.sidebar.multiselect("", all_districts, default=[], key="ms_dist", label_visibility="collapsed")
    if not selected_districts: selected_districts = all_districts
else: selected_districts = all_districts

# --- Numeric range filters (district-level aggregates) ---
range_base = dist_df[dist_df['District'].isin(selected_districts)]
pop_by_district = range_base.groupby('District')['Total Population 2023'].sum()
lit_by_district = range_base.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna()
hh_by_district = range_base.groupby('District').apply(lambda x: weighted_avg(x, 'Average of avg_hh_size', 'Households')).dropna()

st.sidebar.markdown('<div class="sidebar-label">Population Range (by district)</div>', unsafe_allow_html=True)
if not pop_by_district.empty and pop_by_district.min() < pop_by_district.max():
    pop_lo, pop_hi = int(pop_by_district.min()), int(pop_by_district.max())
    pop_range = st.sidebar.slider("", min_value=pop_lo, max_value=pop_hi, value=(pop_lo, pop_hi), label_visibility="collapsed", key="sl_pop")
else:
    pop_range = None

st.sidebar.markdown('<div class="sidebar-label">Literacy Rate Range % (by district)</div>', unsafe_allow_html=True)
if not lit_by_district.empty and lit_by_district.min() < lit_by_district.max():
    lit_lo, lit_hi = float(lit_by_district.min()), float(lit_by_district.max())
    lit_range = st.sidebar.slider("", min_value=0.0, max_value=100.0, value=(round(lit_lo, 1), round(lit_hi, 1)), step=0.5, label_visibility="collapsed", key="sl_lit")
else:
    lit_range = None

st.sidebar.markdown('<div class="sidebar-label">Avg Household Size Range (by district)</div>', unsafe_allow_html=True)
if not hh_by_district.empty and hh_by_district.min() < hh_by_district.max():
    hh_lo, hh_hi = float(hh_by_district.min()), float(hh_by_district.max())
    hh_range = st.sidebar.slider("", min_value=hh_lo, max_value=hh_hi, value=(hh_lo, hh_hi), step=0.1, label_visibility="collapsed", key="sl_hh")
else:
    hh_range = None

# --- Intersect district-level selection with all three numeric ranges ---
range_qualified = set(pop_by_district.index)
if pop_range is not None:
    range_qualified &= set(pop_by_district[(pop_by_district >= pop_range[0]) & (pop_by_district <= pop_range[1])].index)
if lit_range is not None:
    range_qualified &= set(lit_by_district[(lit_by_district >= lit_range[0]) & (lit_by_district <= lit_range[1])].index)
if hh_range is not None:
    range_qualified &= set(hh_by_district[(hh_by_district >= hh_range[0]) & (hh_by_district <= hh_range[1])].index)
final_districts = [d for d in selected_districts if d in range_qualified]

filtered_df = df[
    (df['Province'].isin(selected_provinces)) & (df['Division'].isin(selected_divisions)) &
    (df['Gallup Region'].isin(selected_gallup)) & (df['Region Type'].isin(selected_region_types)) &
    (df['District'].isin(final_districts))
]

# ==========================================
# MAIN DASHBOARD LAYOUT
# ==========================================
st.markdown(f"<h1 style='font-weight: 700; color: #f1f5f9;'>🇵🇰 Pakistan District Socioeconomic Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 16px; margin-top: -10px; margin-bottom: 30px;'><span style='color: #e2e8f0; opacity: 0.65;'>District-level census & socioeconomic indicators (2023)</span> <span style='background:rgba(6,182,212,0.18); padding: 4px 10px; border-radius: 12px; color: #22d3ee; font-weight: 600; margin-left: 10px;'>{filtered_df['District'].nunique()} districts selected</span></p>", unsafe_allow_html=True)

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# ==========================================
# INSIGHT GENERATORS
# ==========================================
def generate_overview_insights(f_df):
    insights = []
    top_prov = f_df.groupby('Province')['Total Population 2023'].sum()
    if not top_prov.empty:
        insights.append(f"<b>{top_prov.idxmax()}</b> has the highest population among selected regions with <b>{top_prov.max():,.0f}</b> people.")
    lit = rate_from_sums(f_df, 'Sum of Literacy Rate', '10 + Population')
    if not np.isnan(lit): insights.append(f"The average literacy rate across selected districts is <b>{lit:.1f}%</b>.")
    urban_pop = f_df[f_df['Region Type'] == 'Urban']['Total Population 2023'].sum()
    rural_pop = f_df[f_df['Region Type'] == 'Rural']['Total Population 2023'].sum()
    total = urban_pop + rural_pop
    if total > 0: insights.append(f"<b>{rural_pop/total*100:.1f}%</b> of the selected population lives in rural areas vs <b>{urban_pop/total*100:.1f}%</b> in urban areas.")
    top_dist = f_df.groupby('District')['Total Population 2023'].sum()
    if not top_dist.empty: insights.append(f"<b>{top_dist.idxmax()}</b> is the most populous district, with <b>{top_dist.max():,.0f}</b> people.")
    hh_size = weighted_avg(f_df, 'Average of avg_hh_size', 'Households')
    if not np.isnan(hh_size): insights.append(f"The average household has <b>{hh_size:.1f}</b> people, across <b>{f_df['Households'].sum():,.0f}</b> households in total.")
    n_dist, n_prov = f_df['District'].nunique(), f_df['Province'].nunique()
    insights.append(f"The current selection covers <b>{n_dist}</b> district(s) across <b>{n_prov}</b> province(s).")
    return insights


def generate_demo_insights(f_df):
    insights = []
    male, female = f_df['Male Population'].sum(), f_df['Female Population'].sum()
    total = male + female
    if total > 0: insights.append(f"Gender split is <b>{male/total*100:.1f}% male</b> and <b>{female/total*100:.1f}% female</b>.")
    sr = weighted_avg(f_df, 'Average of sex_ratio', 'Total Population 2023')
    if not np.isnan(sr): insights.append(f"The average sex ratio is <b>{sr:.1f}</b> males per 100 females.")
    hh_size = weighted_avg(f_df, 'Average of avg_hh_size', 'Households')
    if not np.isnan(hh_size): insights.append(f"The average household size is <b>{hh_size:.1f}</b> people per household.")
    marital = col_sum_df(f_df, MARITAL_COLS)
    if not marital.empty:
        m_total = marital['Count'].sum()
        if m_total > 0: insights.append(f"<b>{marital.iloc[0]['Category']}</b> is the most common marital status, at <b>{marital.iloc[0]['Count']/m_total*100:.1f}%</b> of the population 15+.")
    under15 = f_df['UNDER 15'].sum() if 'UNDER 15' in f_df.columns else 0
    total_pop = f_df['Total Population 2023'].sum()
    if total_pop > 0 and under15 > 0: insights.append(f"<b>{under15/total_pop*100:.1f}%</b> of the population is under 15 years old, indicating a young population.")
    above60 = f_df['60 &  ABOVE'].sum() if '60 &  ABOVE' in f_df.columns else 0
    if total_pop > 0 and above60 > 0: insights.append(f"<b>{above60/total_pop*100:.1f}%</b> of the population is aged 60 and above.")
    return insights


def generate_edu_insights(f_df):
    insights = []
    lit = rate_from_sums(f_df, 'Sum of Literacy Rate', '10 + Population')
    if not np.isnan(lit): insights.append(f"Overall literacy rate stands at <b>{lit:.1f}%</b> for the current selection.")
    sa = rate_from_sums(f_df, 'School Attendance', 'School Attendance.5 - 14  Population')
    if not np.isnan(sa): insights.append(f"<b>{sa:.1f}%</b> of children aged 5-14 have ever attended school.")
    ep = rate_from_sums(f_df, 'Enrolment Primary', 'Enrolment Primary.5 - 9  Population')
    if not np.isnan(ep): insights.append(f"<b>{ep:.1f}%</b> of children aged 5-9 are enrolled in primary school.")
    dist_lit = f_df.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna()
    if not dist_lit.empty:
        insights.append(f"<b>{dist_lit.idxmax()}</b> has the highest district literacy rate at <b>{dist_lit.max():.1f}%</b>.")
        insights.append(f"<b>{dist_lit.idxmin()}</b> has the lowest district literacy rate at <b>{dist_lit.min():.1f}%</b>.")
    urban_lit = rate_from_sums(f_df[f_df['Region Type'] == 'Urban'], 'Sum of Literacy Rate', '10 + Population')
    rural_lit = rate_from_sums(f_df[f_df['Region Type'] == 'Rural'], 'Sum of Literacy Rate', '10 + Population')
    if not (np.isnan(urban_lit) or np.isnan(rural_lit)): insights.append(f"There's a <b>{abs(urban_lit - rural_lit):.1f} point</b> urban-rural literacy gap (<b>{urban_lit:.1f}%</b> urban vs <b>{rural_lit:.1f}%</b> rural).")
    return insights


def generate_housing_insights(f_df):
    insights = []
    housing = col_sum_df(f_df, HOUSING_TYPE_COLS)
    if not housing.empty: insights.append(f"<b>{housing.iloc[0]['Category']}</b> is the most common housing type, covering <b>{housing.iloc[0]['Count']:,.0f}</b> households.")
    owned = f_df['Owned'].sum()
    total_tenure = f_df[TENURE_COLS].sum().sum()
    if total_tenure > 0: insights.append(f"<b>{owned/total_tenure*100:.1f}%</b> of households are owner-occupied.")
    elec = f_df['Electricity'].sum()
    total_light = f_df[LIGHT_COLS].sum().sum()
    if total_light > 0: insights.append(f"<b>{elec/total_light*100:.1f}%</b> of households have electricity as their light source.")
    rooms = col_sum_df(f_df, ROOM_COLS)
    if not rooms.empty: insights.append(f"<b>{rooms.iloc[0]['Category']}</b> homes are the most common household size, with <b>{rooms.iloc[0]['Count']:,.0f}</b> households.")
    toilet = col_sum_df(f_df, TOILET_COLS)
    if not toilet.empty: insights.append(f"<b>{toilet.iloc[0]['Category']}</b> is the most common toilet facility, used by <b>{toilet.iloc[0]['Count']:,.0f}</b> households.")
    fuel = col_sum_df(f_df, FUEL_COLS)
    if not fuel.empty: insights.append(f"<b>{fuel.iloc[0]['Category']}</b> is the most common cooking fuel, used by <b>{fuel.iloc[0]['Count']:,.0f}</b> households.")
    return insights


def generate_diversity_insights(f_df):
    insights = []
    rel = col_sum_df(f_df, RELIGION_COLS)
    if not rel.empty: insights.append(f"<b>{rel.iloc[0]['Category'].title()}</b> is the most common religion, with <b>{rel.iloc[0]['Count']:,.0f}</b> people.")
    if len(rel) > 1: insights.append(f"<b>{rel.iloc[1]['Category'].title()}</b> is the largest religious minority represented, with <b>{rel.iloc[1]['Count']:,.0f}</b> people.")
    lang = col_sum_df(f_df, LANGUAGE_COLS)
    if not lang.empty: insights.append(f"<b>{lang.iloc[0]['Category']}</b> is the most widely spoken language, with <b>{lang.iloc[0]['Count']:,.0f}</b> speakers.")
    if len(lang) > 1: insights.append(f"<b>{lang.iloc[1]['Category']}</b> is the second most widely spoken language, with <b>{lang.iloc[1]['Count']:,.0f}</b> speakers.")
    nat = col_sum_df(f_df, NATIONALITY_COLS)
    if not nat.empty:
        n_total = nat['Count'].sum()
        if n_total > 0: insights.append(f"<b>{nat.iloc[0]['Category']}</b> nationals make up <b>{nat.iloc[0]['Count']/n_total*100:.1f}%</b> of the population.")
    dis = f_df['Disability'].sum() if 'Disability' in f_df.columns else 0
    if dis > 0: insights.append(f"A total of <b>{dis:,.0f}</b> people report some form of disability in the current selection.")
    return insights


def generate_buildings_insights(f_df):
    insights = []
    bt = col_sum_df(f_df, BUILDING_TYPE_COLS)
    if not bt.empty: insights.append(f"<b>{bt.iloc[0]['Category']}</b> is the most common building type, covering <b>{bt.iloc[0]['Count']:,.0f}</b> housing units.")
    kitchen = col_sum_df(f_df, KITCHEN_COLS)
    k_total = kitchen['Count'].sum()
    if k_total > 0: insights.append(f"<b>{kitchen.iloc[0]['Category'].replace('Kitchen : ', '')}</b> kitchens make up <b>{kitchen.iloc[0]['Count']/k_total*100:.1f}%</b> of households.")
    washroom = col_sum_df(f_df, WASHROOM_COLS)
    w_total = washroom['Count'].sum()
    if w_total > 0: insights.append(f"<b>{washroom.iloc[0]['Category'].replace('Washroom : ', '')}</b> washrooms make up <b>{washroom.iloc[0]['Count']/w_total*100:.1f}%</b> of households.")
    land = col_sum_df(f_df, LAND_TENURE_COLS)
    l_total = land['Count'].sum()
    if l_total > 0: insights.append(f"<b>{land.iloc[0]['Category']}</b> land accounts for <b>{land.iloc[0]['Count']/l_total*100:.1f}%</b> of the current selection.")
    highrise = f_df[[c for c in BUILDING_TYPE_COLS if 'High Rise' in c]].sum().sum()
    if highrise > 0: insights.append(f"<b>{highrise:,.0f}</b> housing units are classified as high-rise buildings.")
    under_construction = f_df['Other Under Construction'].sum() if 'Other Under Construction' in f_df.columns else 0
    if under_construction > 0: insights.append(f"<b>{under_construction:,.0f}</b> housing units are currently under construction.")
    return insights


def generate_growth_insights(f_df):
    insights = []
    g = f_df.dropna(subset=['AAPGR'])
    if not g.empty:
        avg_growth = weighted_avg(g, 'AAPGR', 'Total Population 2023')
        if not np.isnan(avg_growth): insights.append(f"The population-weighted average annual growth rate (AAPGR) is <b>{avg_growth*100:.2f}%</b>.")
        dist_growth = g.groupby('District')['AAPGR'].mean()
        if not dist_growth.empty:
            insights.append(f"<b>{dist_growth.idxmax()}</b> is growing fastest at <b>{dist_growth.max()*100:.2f}%</b> per year.")
            insights.append(f"<b>{dist_growth.idxmin()}</b> has the slowest (or most negative) growth at <b>{dist_growth.min()*100:.2f}%</b> per year.")
        declining = (dist_growth < 0).sum() if not dist_growth.empty else 0
        insights.append(f"<b>{declining}</b> district(s) in the current selection show a declining population trend (negative AAPGR).")
        prov_growth = g.groupby('Province').apply(lambda x: weighted_avg(x, 'AAPGR', 'Total Population 2023')).dropna()
        if not prov_growth.empty: insights.append(f"<b>{prov_growth.idxmax()}</b> is the fastest-growing province overall at <b>{prov_growth.max()*100:.2f}%</b> per year.")
        high_growth_count = (dist_growth > 0.03).sum() if not dist_growth.empty else 0
        insights.append(f"<b>{high_growth_count}</b> district(s) are growing faster than <b>3%</b> per year.")
    return insights


def build_district_summary(f_df):
    """One row per district with population-weighted aggregate metrics — used for the Rankings tab."""
    rows = []
    for name, grp in f_df.groupby('District'):
        rows.append({
            'District': name,
            'Province': grp['Province'].iloc[0],
            'Population': grp['Total Population 2023'].sum(),
            'Households': grp['Households'].sum(),
            'Literacy Rate %': rate_from_sums(grp, 'Sum of Literacy Rate', '10 + Population'),
            'School Attendance %': rate_from_sums(grp, 'School Attendance', 'School Attendance.5 - 14  Population'),
            'Enrolment Primary %': rate_from_sums(grp, 'Enrolment Primary', 'Enrolment Primary.5 - 9  Population'),
            'Avg HH Size': weighted_avg(grp, 'Average of avg_hh_size', 'Households'),
            'Sex Ratio': weighted_avg(grp, 'Average of sex_ratio', 'Total Population 2023'),
            'Population Growth %': weighted_avg(grp, 'AAPGR', 'Total Population 2023') * 100,
        })
    return pd.DataFrame(rows)


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Overview", "👥 Demographics", "🎓 Education", "🏠 Housing & Amenities",
    "🏗️ Buildings & Land", "🌍 Diversity & Inclusion", "📈 Population Growth",
    "🏆 District Rankings", "🔍 Raw Data", "🤖 AI Chat Bot"
])

# ==========================================
# TAB 1: OVERVIEW
# ==========================================
with tab1:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_overview_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("👥 Total Population", fmt_compact(filtered_df['Total Population 2023'].sum()), help=f"Exact: {filtered_df['Total Population 2023'].sum():,.0f}")
    with c2: st.metric("📍 Districts", f"{filtered_df['District'].nunique():,}")
    with c3: st.metric("🏠 Households", fmt_compact(filtered_df['Households'].sum()), help=f"Exact: {filtered_df['Households'].sum():,.0f}")
    with c4: st.metric("📚 Avg Literacy Rate", f"{rate_from_sums(filtered_df, 'Sum of Literacy Rate', '10 + Population'):.1f}%")
    with c5: st.metric("👪 Avg HH Size", f"{weighted_avg(filtered_df, 'Average of avg_hh_size', 'Households'):.1f}")

    st.markdown('<div class="section-header" style="margin-top:40px">Population Distribution</div>', unsafe_allow_html=True)
    cl, cr = st.columns([1.4, 1])
    with cl:
        pp = filtered_df.groupby('Province')['Total Population 2023'].sum().reset_index().sort_values('Total Population 2023', ascending=False)
        fig = px.bar(pp, x='Province', y='Total Population 2023', color='Province', text='Total Population 2023', color_discrete_sequence=PROVINCE_COLORS)
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        rp = filtered_df.groupby('Region Type')['Total Population 2023'].sum().reset_index()
        fig = px.pie(rp, values='Total Population 2023', names='Region Type', hole=0.55, color_discrete_sequence=['#06b6d4', '#f97316'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Province ➔ District Population</div>', unsafe_allow_html=True)
    tm = filtered_df.groupby(['Province', 'District'])['Total Population 2023'].sum().reset_index()
    fig = px.treemap(tm, path=['Province', 'District'], values='Total Population 2023', color='Total Population 2023', color_continuous_scale='Tealgrn')
    fig.update_traces(textinfo="label+value")
    fig = style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Population Density: Province × Region Type</div>', unsafe_allow_html=True)
    hdata = filtered_df.groupby(['Province', 'Region Type'])['Total Population 2023'].sum().reset_index()
    fig = px.density_heatmap(hdata, x='Province', y='Region Type', z='Total Population 2023', color_continuous_scale='YlGnBu')
    fig.update_layout(coloraxis_colorbar=dict(title="Population"))
    fig = style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: DEMOGRAPHICS
# ==========================================
with tab2:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_demo_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Gender & Household Composition</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        gender = pd.DataFrame({'Category': ['Male', 'Female', 'Transgender'], 'Count': [filtered_df['Male Population'].sum(), filtered_df['Female Population'].sum(), filtered_df['Tgend Population'].sum()]})
        fig = px.pie(gender, values='Count', names='Category', hole=0.5, color_discrete_sequence=['#06b6d4', '#f97316', '#a78bfa'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        marital = col_sum_df(filtered_df, MARITAL_COLS)
        fig = px.bar(marital, x='Count', y='Category', orientation='h', color='Category', color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Population by Age Bracket</div>', unsafe_allow_html=True)
    age = col_sum_df(filtered_df, AGE_COLS)
    fig = px.bar(age, x='Count', y='Category', orientation='h', color='Category', color_discrete_sequence=px.colors.qualitative.Vivid)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig = style_fig(fig, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Note: Age brackets are cumulative (e.g. \"UNDER 15\" includes \"UNDER 10\" and \"UNDER 5\"), so totals are not mutually exclusive.")

# ==========================================
# TAB 3: EDUCATION
# ==========================================
with tab3:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_edu_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Literacy & School Participation by Province</div>', unsafe_allow_html=True)
    prov_edu = filtered_df.groupby('Province').apply(lambda x: pd.Series({
        'Literacy Rate %': rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population'),
        'School Attendance %': rate_from_sums(x, 'School Attendance', 'School Attendance.5 - 14  Population'),
        'Enrolment Primary %': rate_from_sums(x, 'Enrolment Primary', 'Enrolment Primary.5 - 9  Population'),
    })).reset_index()
    prov_edu_melt = prov_edu.melt(id_vars='Province', var_name='Metric', value_name='Rate')
    fig = px.bar(prov_edu_melt, x='Province', y='Rate', color='Metric', barmode='group', color_discrete_sequence=['#06b6d4', '#f97316', '#8b5cf6'])
    fig.update_layout(yaxis_title="%")
    fig = style_fig(fig, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Top & Bottom 10 Districts by Literacy Rate</div>', unsafe_allow_html=True)
    dist_lit = filtered_df.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna().reset_index()
    dist_lit.columns = ['District', 'Literacy Rate %']
    c1, c2 = st.columns(2)
    with c1:
        top10 = dist_lit.sort_values('Literacy Rate %', ascending=False).head(10).sort_values('Literacy Rate %')
        fig = px.bar(top10, x='Literacy Rate %', y='District', orientation='h', color_discrete_sequence=['#22c55e'] * len(top10))
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        bottom10 = dist_lit.sort_values('Literacy Rate %', ascending=True).head(10).sort_values('Literacy Rate %', ascending=False)
        fig = px.bar(bottom10, x='Literacy Rate %', y='District', orientation='h', color_discrete_sequence=['#ef4444'] * len(bottom10))
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 4: HOUSING & AMENITIES
# ==========================================
with tab4:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_housing_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Housing Type & Room Count</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        housing = col_sum_df(filtered_df, HOUSING_TYPE_COLS)
        fig = px.pie(housing, values='Count', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        rooms = filtered_df[ROOM_COLS].sum().reindex(ROOM_COLS).reset_index()
        rooms.columns = ['Category', 'Count']
        fig = px.area(rooms, x='Category', y='Count', markers=True, color_discrete_sequence=['#06b6d4'])
        fig.update_traces(line=dict(width=3), fill='tozeroy', fillcolor='rgba(6,182,212,0.25)', marker=dict(size=9))
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Utilities & Tenure</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        toilet = col_sum_df(filtered_df, TOILET_COLS).sort_values('Count', ascending=False)
        fig = px.funnel(toilet, x='Count', y='Category', color='Category', color_discrete_sequence=px.colors.qualitative.Bold)
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fuel = col_sum_df(filtered_df, FUEL_COLS + LIGHT_COLS)
        fig = px.bar_polar(fuel, r='Count', theta='Category', color='Category', color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(polar=dict(radialaxis=dict(gridcolor=CHART_GRID_COLOR, showticklabels=True), angularaxis=dict(gridcolor=CHART_GRID_COLOR), bgcolor='rgba(0,0,0,0)'))
        fig = style_fig(fig, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        tenure = col_sum_df(filtered_df, TENURE_COLS)
        fig = px.pie(tenure, values='Count', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 5: BUILDINGS & LAND
# ==========================================
with tab5:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_buildings_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Building Types</div>', unsafe_allow_html=True)
    bt = col_sum_df(filtered_df, BUILDING_TYPE_COLS)
    fig = px.treemap(bt, path=['Category'], values='Count', color='Count', color_continuous_scale='Tealgrn')
    fig.update_traces(textinfo='label+value')
    fig = style_fig(fig, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Kitchen, Washroom & Land Tenure</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        kitchen = col_sum_df(filtered_df, KITCHEN_COLS)
        fig = px.pie(kitchen, values='Count', names='Category', hole=0.5, color_discrete_sequence=['#06b6d4', '#f97316'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        washroom = col_sum_df(filtered_df, WASHROOM_COLS)
        fig = px.pie(washroom, values='Count', names='Category', hole=0.5, color_discrete_sequence=['#8b5cf6', '#f97316'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        land = col_sum_df(filtered_df, LAND_TENURE_COLS)
        fig = px.pie(land, values='Count', names='Category', hole=0.5, color_discrete_sequence=['#22c55e', '#ef4444'])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 6: DIVERSITY & INCLUSION
# ==========================================
with tab6:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_diversity_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Religion & Nationality</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        rel = col_sum_df(filtered_df, RELIGION_COLS)
        fig = px.pie(rel, values='Count', names='Category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        nat = col_sum_df(filtered_df, NATIONALITY_COLS)
        fig = px.bar(nat, x='Count', y='Category', orientation='h', color='Count', color_continuous_scale='Teal')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, coloraxis_showscale=False)
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Languages Spoken (Top 10)</div>', unsafe_allow_html=True)
    lang = col_sum_df(filtered_df, LANGUAGE_COLS).head(10).sort_values('Count')
    fig = px.bar(lang, x='Count', y='Category', orientation='h', color='Count', color_continuous_scale='Sunset')
    fig.update_layout(coloraxis_showscale=False)
    fig = style_fig(fig, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Disability Types</div>', unsafe_allow_html=True)
    dis = col_sum_df(filtered_df, DISABILITY_COLS)
    fig = px.line_polar(dis, r='Count', theta='Category', line_close=True, color_discrete_sequence=['#06b6d4'])
    fig.update_traces(fill='toself', fillcolor='rgba(6,182,212,0.25)', line=dict(width=2))
    fig.update_layout(polar=dict(radialaxis=dict(gridcolor=CHART_GRID_COLOR, showticklabels=True), angularaxis=dict(gridcolor=CHART_GRID_COLOR), bgcolor='rgba(0,0,0,0)'))
    fig = style_fig(fig, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 7: POPULATION GROWTH
# ==========================================
with tab7:
    st.markdown("<div class='insights-box'><h4>💡 Dynamic Key Findings</h4><ul>" + "".join(f"<li>{i}</li>" for i in generate_growth_insights(filtered_df)) + "</ul></div>", unsafe_allow_html=True)
    growth_df = filtered_df.dropna(subset=['AAPGR']).copy()
    if growth_df.empty:
        st.info("No population growth (AAPGR) data available for the current selection.")
    else:
        st.markdown('<div class="section-header">Annual Population Growth Rate (AAPGR) by Province</div>', unsafe_allow_html=True)
        prov_growth = growth_df.groupby('Province').apply(lambda x: weighted_avg(x, 'AAPGR', 'Total Population 2023') * 100).reset_index()
        prov_growth.columns = ['Province', 'AAPGR %']
        prov_growth = prov_growth.sort_values('AAPGR %', ascending=False)
        fig = px.bar(prov_growth, x='Province', y='AAPGR %', color='Province', text='AAPGR %', color_discrete_sequence=PROVINCE_COLORS)
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig = style_fig(fig, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-header" style="margin-top:40px">Fastest & Slowest Growing Districts</div>', unsafe_allow_html=True)
        dist_growth = growth_df.groupby('District')['AAPGR'].mean().reset_index()
        dist_growth.columns = ['District', 'AAPGR']
        dist_growth['AAPGR %'] = dist_growth['AAPGR'] * 100
        c1, c2 = st.columns(2)
        with c1:
            fastest = dist_growth.sort_values('AAPGR %', ascending=False).head(10).sort_values('AAPGR %')
            fig = px.bar(fastest, x='AAPGR %', y='District', orientation='h', color_discrete_sequence=['#22c55e'] * len(fastest))
            fig = style_fig(fig, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            slowest = dist_growth.sort_values('AAPGR %', ascending=True).head(10).sort_values('AAPGR %', ascending=False)
            fig = px.bar(slowest, x='AAPGR %', y='District', orientation='h', color_discrete_sequence=['#ef4444'] * len(slowest))
            fig = style_fig(fig, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-header" style="margin-top:40px">Population vs Growth Rate</div>', unsafe_allow_html=True)
        bubble = growth_df.groupby('District').agg(Population=('Total Population 2023', 'sum'), AAPGR=('AAPGR', 'mean'), Province=('Province', 'first')).reset_index()
        bubble['AAPGR %'] = bubble['AAPGR'] * 100
        fig = px.scatter(bubble, x='Population', y='AAPGR %', size='Population', color='Province', hover_name='District', color_discrete_sequence=PROVINCE_COLORS, size_max=45)
        fig = style_fig(fig, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 8: DISTRICT RANKINGS
# ==========================================
with tab8:
    st.markdown('<div class="section-header">Rank & Compare Districts</div>', unsafe_allow_html=True)
    summary_df = build_district_summary(filtered_df)

    metric_options = ['Population', 'Literacy Rate %', 'School Attendance %', 'Enrolment Primary %', 'Households', 'Avg HH Size', 'Sex Ratio', 'Population Growth %']
    c1, c2 = st.columns([2, 1])
    with c1:
        metric = st.selectbox("Rank districts by:", metric_options, key="rank_metric")
    with c2:
        top_n = st.slider("Show top N:", min_value=5, max_value=min(30, len(summary_df)) if len(summary_df) >= 5 else 5, value=min(15, len(summary_df)) if len(summary_df) >= 1 else 5, key="rank_top_n")

    ranked = summary_df.dropna(subset=[metric]).sort_values(metric, ascending=False).head(top_n).sort_values(metric)
    if ranked.empty:
        st.info("No data available to rank for the current selection.")
    else:
        fig = px.bar(ranked, x=metric, y='District', orientation='h', color='Province', color_discrete_sequence=PROVINCE_COLORS)
        fig = style_fig(fig, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header" style="margin-top:40px">Full District Leaderboard</div>', unsafe_allow_html=True)
    render_dark_table(summary_df.sort_values(metric, ascending=False), max_height=520)

    st.markdown('<div class="section-header" style="margin-top:40px">Compare Districts Side-by-Side</div>', unsafe_allow_html=True)
    compare_districts = st.multiselect("Pick 2-5 districts to compare:", sorted(summary_df['District'].unique()), default=list(summary_df.sort_values('Population', ascending=False)['District'].head(2)) if len(summary_df) >= 2 else [], key="compare_districts")
    radar_metrics = ['Literacy Rate %', 'School Attendance %', 'Enrolment Primary %', 'Sex Ratio', 'Avg HH Size']
    if len(compare_districts) >= 2:
        cmp_df = summary_df[summary_df['District'].isin(compare_districts)].set_index('District')
        fig = go.Figure()
        for d in compare_districts:
            if d not in cmp_df.index: continue
            row = cmp_df.loc[d]
            # Normalize each metric to 0-100 relative to the min/max across ALL districts in the current selection, for a fair radar comparison
            vals = []
            for m in radar_metrics:
                col_min, col_max = summary_df[m].min(), summary_df[m].max()
                v = row[m]
                norm = 50.0 if (pd.isna(col_max - col_min) or col_max == col_min) else (v - col_min) / (col_max - col_min) * 100
                vals.append(norm if not pd.isna(norm) else 0)
            fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=radar_metrics + [radar_metrics[0]], fill='toself', name=d))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor=CHART_GRID_COLOR), bgcolor='rgba(0,0,0,0)'),
                           font=dict(family="Inter", size=12, color=CHART_FONT_COLOR), paper_bgcolor='rgba(0,0,0,0)',
                           legend=dict(font=dict(color=CHART_FONT_COLOR, family="Inter"), bgcolor='rgba(0,0,0,0)', bordercolor=CHART_GRID_COLOR, borderwidth=1),
                           showlegend=True, margin=dict(l=40, r=40, t=30, b=30), height=460)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Values are normalized (0-100) relative to the current filtered selection, so shapes are comparable across different-scale metrics.")
    else:
        st.info("Select at least 2 districts above to see a side-by-side radar comparison.")

# ==========================================
# TAB 9: RAW DATA
# ==========================================
with tab9:
    st.markdown('<div class="section-header">Filtered Raw Data</div>', unsafe_allow_html=True)
    render_dark_table(filtered_df, max_height=550)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download CSV", data=csv, file_name='district_data.csv', mime='text/csv', use_container_width=True)


# ==========================================
# SUPER INTELLIGENT CHATBOT ENGINE
# ==========================================
def get_formatted_list(f_df, column_name, limit=25):
    counts = f_df.groupby(column_name)['Total Population 2023'].sum().sort_values(ascending=False) if column_name in ('District', 'Province', 'Division', 'Gallup Region') else f_df[column_name].value_counts()
    total = len(counts)
    text = f"📋 **Top {limit} {column_name}s by population** (out of {total} total):\n\n"
    for i, (name, val) in enumerate(counts.head(limit).items(), 1):
        text += f"{i}. **{name}** ({val:,.0f})\n"
    if total > limit:
        text += f"\n_*(Showing top {limit}. Download CSV in the Raw Data tab for the full list!)*_"
    return text


def get_regional_comparison(f_df):
    text = "📈 **Regional Comparison** _(note: this is 2023 census snapshot data, not a time series, so this compares regions instead of tracking change over months/years)_:\n\n"
    prov_pop = f_df.groupby('Province')['Total Population 2023'].sum().sort_values(ascending=False)
    if not prov_pop.empty:
        text += f"• **Most populous province:** {prov_pop.index[0]} ({prov_pop.iloc[0]:,.0f} people)\n\n"
    urban_lit = rate_from_sums(f_df[f_df['Region Type'] == 'Urban'], 'Sum of Literacy Rate', '10 + Population')
    rural_lit = rate_from_sums(f_df[f_df['Region Type'] == 'Rural'], 'Sum of Literacy Rate', '10 + Population')
    if not (np.isnan(urban_lit) or np.isnan(rural_lit)):
        gap = urban_lit - rural_lit
        text += f"• **Urban vs Rural literacy gap:** Urban areas average **{urban_lit:.1f}%** literacy vs **{rural_lit:.1f}%** rural — a gap of **{abs(gap):.1f} points**.\n\n"
    dist_lit = f_df.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna()
    if not dist_lit.empty:
        text += f"• **Highest district literacy:** {dist_lit.idxmax()} ({dist_lit.max():.1f}%)\n• **Lowest district literacy:** {dist_lit.idxmin()} ({dist_lit.min():.1f}%)\n"
    return text


def find_entity_matches(q, f_df, columns=ENTITY_COLUMNS, max_matches=3):
    found = []
    for col in columns:
        if col not in f_df.columns: continue
        for v in f_df[col].dropna().unique():
            vs = str(v).lower()
            if len(vs) >= 3 and vs in q:
                found.append((col, v))
    found = list(dict.fromkeys(found))  # de-dupe while preserving column-priority order
    found.sort(key=lambda x: (-len(str(x[1])), columns.index(x[0])))
    return found[:max_matches]


def fuzzy_entity_match(q, f_df, columns=ENTITY_COLUMNS, cutoff=0.75):
    best, best_score = None, 0
    for col in columns:
        if col not in f_df.columns: continue
        for v in f_df[col].dropna().unique():
            score = difflib.SequenceMatcher(None, str(v).lower(), q).ratio()
            if score > best_score:
                best_score, best = score, (col, v)
    return best if best_score >= cutoff else None


def get_entity_profile(f_df, column, value):
    sub = f_df[f_df[column] == value]
    if sub.empty: return f"I couldn't find any data for **{value}**."
    pop, hh = sub['Total Population 2023'].sum(), sub['Households'].sum()
    male, female = sub['Male Population'].sum(), sub['Female Population'].sum()
    lit = rate_from_sums(sub, 'Sum of Literacy Rate', '10 + Population')
    sa = rate_from_sums(sub, 'School Attendance', 'School Attendance.5 - 14  Population')
    ep = rate_from_sums(sub, 'Enrolment Primary', 'Enrolment Primary.5 - 9  Population')
    hh_size = weighted_avg(sub, 'Average of avg_hh_size', 'Households')

    icon = {'District': '📍', 'Province': '🗺️', 'Division': '🧭', 'Gallup Region': '🌐', 'Region Type': '🏙️'}.get(column, '📌')
    text = f"{icon} **{value}**\n\n"
    if column == 'District':
        text += f"• Province: **{sub['Province'].iloc[0]}** | Division: **{sub['Division'].iloc[0]}**\n"
        text += f"• Coverage: **{', '.join(sorted(sub['Region Type'].unique()))}**\n"
    elif column == 'Province':
        text += f"• Districts covered: **{sub['District'].nunique()}**\n"
    elif column in ('Division', 'Gallup Region'):
        text += f"• Districts covered: **{sub['District'].nunique()}** across **{sub['Province'].nunique()}** province(s)\n"
    text += f"• Population: **{pop:,.0f}** ({male:,.0f} male, {female:,.0f} female)\n"
    text += f"• Households: **{hh:,.0f}**"
    if not np.isnan(hh_size): text += f" (avg size **{hh_size:.1f}**)"
    text += "\n"
    if not np.isnan(lit): text += f"• Literacy Rate: **{lit:.1f}%**\n"
    if not np.isnan(sa): text += f"• School Attendance: **{sa:.1f}%**\n"
    if not np.isnan(ep): text += f"• Primary Enrolment: **{ep:.1f}%**\n"
    if column in ('Province', 'Division', 'Gallup Region'):
        top_dist = sub.groupby('District')['Total Population 2023'].sum().sort_values(ascending=False)
        if not top_dist.empty: text += f"• Most populous district: **{top_dist.index[0]}** ({top_dist.iloc[0]:,.0f})\n"
    return text


FULL_COMPARISON_TRIGGERS = r'\b(all possible|all methods|all ways|every way|everything|all metrics|full comparison|complete comparison|in detail|all aspects|every metric|all variables)\b'

# (display name, kind, numerator/plain col, denominator col or None, format string, higher_is_better or None for neutral)
# kind: 'sum' = simple total | 'rate' = numerator/denominator*100 | 'weighted' = weighted average | 'weighted_pct' = weighted average*100
COMPARISON_METRICS = [
    ("Population", 'sum', 'Total Population 2023', None, "{:,.0f}", True),
    ("Households", 'sum', 'Households', None, "{:,.0f}", True),
    ("Literacy Rate %", 'rate', 'Sum of Literacy Rate', '10 + Population', "{:.1f}%", True),
    ("School Attendance %", 'rate', 'School Attendance', 'School Attendance.5 - 14  Population', "{:.1f}%", True),
    ("Enrolment Primary %", 'rate', 'Enrolment Primary', 'Enrolment Primary.5 - 9  Population', "{:.1f}%", True),
    ("Population Growth %", 'weighted_pct', 'AAPGR', 'Total Population 2023', "{:.2f}%", True),
    ("Avg Household Size", 'weighted', 'Average of avg_hh_size', 'Households', "{:.1f}", None),
    ("Sex Ratio", 'weighted', 'Average of sex_ratio', 'Total Population 2023', "{:.1f}", None),
]


def _compute_comparison_metric(sub, kind, col, den_col):
    if kind == 'sum':
        return sub[col].sum()
    if kind == 'rate':
        return rate_from_sums(sub, col, den_col)
    if kind == 'weighted':
        return weighted_avg(sub, col, den_col)
    if kind == 'weighted_pct':
        v = weighted_avg(sub, col, den_col)
        return v * 100 if not pd.isna(v) else v
    return np.nan


def get_full_comparison(f_df, column, val1, val2):
    sub1, sub2 = f_df[f_df[column] == val1], f_df[f_df[column] == val2]
    text = f"⚖️🔬 **Full Comparison: {val1} vs {val2}**\n\n"
    wins1 = wins2 = scored = 0
    for name, kind, col, den_col, fmt, higher_better in COMPARISON_METRICS:
        m1 = _compute_comparison_metric(sub1, kind, col, den_col)
        m2 = _compute_comparison_metric(sub2, kind, col, den_col)
        if pd.isna(m1) or pd.isna(m2):
            continue
        v1_str, v2_str = fmt.format(m1), fmt.format(m2)
        if higher_better is None:
            text += f"• **{name}** — {val1}: {v1_str} | {val2}: {v2_str}\n"
        else:
            scored += 1
            if m1 > m2:
                wins1 += 1
                text += f"• **{name}** — {val1}: **{v1_str}** 🏆 | {val2}: {v2_str}\n"
            elif m2 > m1:
                wins2 += 1
                text += f"• **{name}** — {val1}: {v1_str} | {val2}: **{v2_str}** 🏆\n"
            else:
                text += f"• **{name}** — {val1}: {v1_str} | {val2}: {v2_str} (tie)\n"

    text += "\n"
    if wins1 > wins2:
        text += f"🏆 **Overall, {val1} leads** in **{wins1}** out of **{scored}** measured categories (vs {wins2} for {val2})."
    elif wins2 > wins1:
        text += f"🏆 **Overall, {val2} leads** in **{wins2}** out of **{scored}** measured categories (vs {wins1} for {val1})."
    else:
        text += f"🤝 **It's an overall tie** — both lead in {wins1} categories each."
    return text


def get_comparison(f_df, column, val1, val2, q):
    if re.search(FULL_COMPARISON_TRIGGERS, q):
        return get_full_comparison(f_df, column, val1, val2)
    sub1, sub2 = f_df[f_df[column] == val1], f_df[f_df[column] == val2]
    if 'literacy' in q:
        m1, m2, label = rate_from_sums(sub1, 'Sum of Literacy Rate', '10 + Population'), rate_from_sums(sub2, 'Sum of Literacy Rate', '10 + Population'), "literacy rate"
        fmt = lambda v: f"{v:.1f}%"
    elif 'school' in q or 'attendance' in q:
        m1, m2, label = rate_from_sums(sub1, 'School Attendance', 'School Attendance.5 - 14  Population'), rate_from_sums(sub2, 'School Attendance', 'School Attendance.5 - 14  Population'), "school attendance"
        fmt = lambda v: f"{v:.1f}%"
    elif 'household' in q or 'hh' in q:
        m1, m2, label = sub1['Households'].sum(), sub2['Households'].sum(), "households"
        fmt = lambda v: f"{v:,.0f}"
    else:
        m1, m2, label = sub1['Total Population 2023'].sum(), sub2['Total Population 2023'].sum(), "population"
        fmt = lambda v: f"{v:,.0f}"
    text = f"⚖️ **Comparing {val1} vs {val2} ({label}):**\n\n• **{val1}**: {fmt(m1)}\n• **{val2}**: {fmt(m2)}\n\n"
    if m1 > m2: text += f"🏆 **{val1}** leads in {label}."
    elif m2 > m1: text += f"🏆 **{val2}** leads in {label}."
    else: text += "🤝 It's a tie!"
    text += "\n\n_💡 Tip: ask to \"compare X vs Y in all possible methods\" for a full multi-metric breakdown._"
    return text


def answer_query(query: str, f_df: pd.DataFrame) -> str:
    q = query.lower().strip()

    if re.search(r'\b(bye|goodbye|good night|see (you|ya)|take care|gtg|catch you later|khuda hafiz|allah hafiz)\b', q):
        return random.choice(["Goodbye! 👋 Come back anytime you want to explore the district data.", "See you soon! 🙌 Feel free to ask more questions later.", "Take care! 😊 I'll be here whenever you need more insights."])
    if re.search(r'\b(thank(s| you)?|thankyou|shukriya|appreciate it|thnx)\b', q):
        return random.choice(["You're welcome! 😊 Happy to help with anything else.", "Anytime! 🙌 Let me know if you'd like to explore more of the data.", "Glad I could help! 💚 Ask away if you need anything else."])
    if re.search(r'\b(who are you|what are you|your name|what is your name)\b', q):
        return "🤖 I'm **Data Bot**, your AI assistant for this dashboard. I can look up any province, division, or district, compare regions, and summarize the currently filtered census data."
    if re.search(r'\bhow are you\b', q):
        return random.choice(["I'm doing great and ready to explore some district data! 📊 What would you like to know?", "All systems running smoothly! 🤖 How can I help you today?"])
    if re.search(r'\b(good bot|nice bot|great job|well done|awesome|you\'?re smart|clever bot)\b', q):
        return random.choice(["Thank you! 😊 I try my best to make sense of the data for you.", "Appreciate that! 🙌 Let me know what else you'd like to explore."])
    if re.search(r'\b(help|what can you do|options|commands|capabilities)\b', q):
        return ("🤖 **Here's everything I can do:**\n\n"
                "• 📋 **List** provinces, divisions, or districts by population\n"
                "• 🏆 Find **top/highest/lowest** districts by literacy, population, or school attendance\n"
                "• 🔢 **Count** districts, provinces, population, or households\n"
                "• 📈 Give a **regional comparison** (urban vs rural, top provinces, etc.)\n"
                "• 📐 Calculate **averages** (e.g. \"average household size\")\n"
                "• 🔍 **Look up** any specific district, province, division, or Gallup region by name\n"
                "• ⚖️ **Compare** two districts or provinces — e.g. \"compare Lahore vs Karachi literacy\"\n"
                "• 📊 Give a full **summary** of the current filtered data\n\n"
                "Just type naturally, greet me, or say thanks — I'll understand! 😊")
    if re.search(r'\b(hi+|hello+|hey+|yo|greetings|good morning|good afternoon|good evening|assalam|salam)\b', q):
        return random.choice(["Hello! 👋 I'm Data Bot. Ask me about any district, province, or comparison — or type \"help\" to see everything I can do!", "Hey there! 😊 I'm ready to dig into the census data — what would you like to know?", "Hi! 👋 Try asking about a district or province, or type \"help\"."])

    if re.search(r'\b(summarize|summary|overview|insights|key findings|brief)\b', q):
        all_ins = generate_overview_insights(f_df) + generate_demo_insights(f_df) + generate_edu_insights(f_df) + generate_diversity_insights(f_df)
        summary = "📊 **Here is the summary of the current filtered data:**\n\n"
        for ins in all_ins: summary += f"• {ins.replace('<b>', '**').replace('</b>', '**')}\n\n"
        return summary

    if re.search(r'\b(list|all|every|show me|give me|names of)\b.*\b(district|province|division|region)s?\b', q):
        for col in ['District', 'Province', 'Division', 'Gallup Region']:
            if col.lower().split()[0] in q or (col == 'District' and 'district' in q) or (col == 'Province' and 'province' in q):
                return get_formatted_list(f_df, col)
        return get_formatted_list(f_df, 'District')

    if re.search(r'\b(trends?|growth|regional comparison|compare regions|over time)\b', q) and not find_entity_matches(q, f_df):
        return get_regional_comparison(f_df)

    if re.search(r'\b(most|top|highest)\b.*\bpopul', q):
        s = f_df.groupby('District')['Total Population 2023'].sum()
        return f"👥 The most populous district is **{s.idxmax()}** with **{s.max():,.0f}** people."
    if re.search(r'\b(least|lowest|smallest)\b.*\bpopul', q):
        s = f_df.groupby('District')['Total Population 2023'].sum()
        return f"👥 The least populous district is **{s.idxmin()}** with **{s.min():,.0f}** people."
    if re.search(r'\b(most|top|highest)\b.*\bliterac', q):
        s = f_df.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna()
        return f"📚 **{s.idxmax()}** has the highest literacy rate at **{s.max():.1f}%**."
    if re.search(r'\b(least|lowest)\b.*\bliterac', q):
        s = f_df.groupby('District').apply(lambda x: rate_from_sums(x, 'Sum of Literacy Rate', '10 + Population')).dropna()
        return f"📚 **{s.idxmin()}** has the lowest literacy rate at **{s.min():.1f}%**."
    if re.search(r'\b(most|top|highest)\b.*\b(school|attendance)', q):
        s = f_df.groupby('District').apply(lambda x: rate_from_sums(x, 'School Attendance', 'School Attendance.5 - 14  Population')).dropna()
        return f"🎓 **{s.idxmax()}** has the highest school attendance rate at **{s.max():.1f}%**."
    if re.search(r'\b(most|top|highest)\b.*\bhousehold', q):
        s = f_df.groupby('District')['Households'].sum()
        return f"🏠 **{s.idxmax()}** has the most households (**{s.max():,.0f}**)."

    if re.search(r'\b(how many|total|count)\b.*\bdistrict', q): return f"📊 There are **{f_df['District'].nunique()}** unique districts in the current filtered view."
    if re.search(r'\b(how many|total|count)\b.*\bprovince', q): return f"📊 There are **{f_df['Province'].nunique()}** unique provinces in the current filtered view."
    if re.search(r'\b(how many|total|count)\b.*\bpopul', q): return f"👥 Total population in the current selection is **{f_df['Total Population 2023'].sum():,.0f}**."
    if re.search(r'\b(how many|total|count)\b.*\bhousehold', q): return f"🏠 Total households in the current selection: **{f_df['Households'].sum():,.0f}**."

    if re.search(r'\b(average|avg|mean)\b.*\bhousehold size\b', q):
        v = weighted_avg(f_df, 'Average of avg_hh_size', 'Households')
        return f"📐 The average household size is **{v:.1f}** people."
    if re.search(r'\b(average|avg|mean)\b.*\bliterac', q):
        v = rate_from_sums(f_df, 'Sum of Literacy Rate', '10 + Population')
        return f"📐 The average literacy rate is **{v:.1f}%**."
    if re.search(r'\b(average|avg|mean)\b.*\bsex ratio\b', q):
        v = weighted_avg(f_df, 'Average of sex_ratio', 'Total Population 2023')
        return f"📐 The average sex ratio is **{v:.1f}** males per 100 females."

    matches = find_entity_matches(q, f_df)
    if len(matches) < 2:
        fm = fuzzy_entity_match(q, f_df)
        if fm and fm not in matches:
            matches.append(fm)
    if len(matches) >= 2:
        same_col = [m for m in matches if m[0] == matches[0][0]]
        if len(same_col) >= 2 and re.search(r'\b(vs|versus|compare|comparison|between)\b', q):
            return get_comparison(f_df, same_col[0][0], same_col[0][1], same_col[1][1], q)
    if matches:
        col, val = matches[0]
        return get_entity_profile(f_df, col, val)

    for col in ['Region Type']:
        if col in f_df.columns and re.search(rf'\b{re.escape(col.lower())}\b', q):
            return get_formatted_list(f_df, col)

    return ("🤔 I didn't fully catch that. I'm great at looking up a **district/province/division by name**, finding **top/highest/lowest** metrics, "
            "**counts**, **averages**, **comparisons**, or a full **summary**. Type **\"help\"** to see everything I can do!")


def process_chat_input(prompt_text):
    st.session_state.chat_history.append({"role": "user", "text": prompt_text})
    st.session_state.awaiting_response = True
    st.session_state.pending_prompt = prompt_text
    st.rerun()

# ==========================================
# TAB 10: CHATBOT UI
# ==========================================
with tab10:
    head_col, btn_col = st.columns([6, 1])
    with head_col:
        st.markdown("""
            <div class="chatbot-card">
                <div class="chatbot-avatar">🤖</div>
                <div>
                    <div class="chatbot-title">Data Bot</div>
                    <div class="chatbot-status"><span class="status-dot"></span> Online · Reading current sidebar filters</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with btn_col:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("""
        <div class="capability-pills">
            <span class="pill">📋 Lists</span>
            <span class="pill">🏆 Top / Most</span>
            <span class="pill">📈 Regional Comparison</span>
            <span class="pill">📐 Averages</span>
            <span class="pill">🔍 District / Province Lookup</span>
            <span class="pill">⚖️ Compare</span>
            <span class="pill">📊 Summary</span>
        </div>
    """, unsafe_allow_html=True)

    chat_container = st.container(height=480, border=True)
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("👋 **Hi! I'm your Data Bot.** Ask me about any district, province, or division by name, request comparisons or top metrics, or just say hello!")
        for message in st.session_state.chat_history:
            avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["text"])

        if st.session_state.awaiting_response:
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                for phrase in ["🤔 *Thinking...*", "📊 *Analyzing the filtered data...*", "🔎 *Crunching the numbers...*"]:
                    placeholder.markdown(phrase)
                    time.sleep(0.45)

                answer = answer_query(st.session_state.pending_prompt, filtered_df)

                words = answer.split(" ")
                chunk_size = 4
                displayed = ""
                for i in range(0, len(words), chunk_size):
                    displayed += " ".join(words[i:i + chunk_size]) + " "
                    placeholder.markdown(displayed + "▌")
                    time.sleep(0.035)
                placeholder.markdown(answer)

            st.session_state.chat_history.append({"role": "assistant", "text": answer})
            st.session_state.awaiting_response = False
            st.session_state.pending_prompt = None

    if not st.session_state.chat_history:
        st.markdown("💡 **Try asking me:**")
        r1c1, r1c2, r1c3 = st.columns(3)
        if r1c1.button("Most populous district", key="ex1", use_container_width=True): process_chat_input("most populous district")
        if r1c2.button("Tell me about Lahore", key="ex2", use_container_width=True): process_chat_input("tell me about Lahore")
        if r1c3.button("Urban vs rural comparison", key="ex3", use_container_width=True): process_chat_input("regional comparison")
        r2c1, r2c2, r2c3 = st.columns(3)
        if r2c1.button("Give me a summary", key="ex4", use_container_width=True): process_chat_input("give me a summary")
        if r2c2.button("Average household size", key="ex5", use_container_width=True): process_chat_input("average household size")
        if r2c3.button("What can you do?", key="ex6", use_container_width=True): process_chat_input("what can you do")

    if prompt := st.chat_input("Ask anything — a district/province name, \"hi\", \"thanks\", comparisons...", key="tab10_chat_input"):
        process_chat_input(prompt)