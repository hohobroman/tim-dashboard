import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objects as go
import time
import requests

st.set_page_config(page_title="T.I.M Portfolio", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0F1219; color: #E0E0E0; font-family: 'Pretendard', sans-serif; }
    header, footer, #MainMenu { visibility: hidden; }
    .block-container { padding-top: 1.5rem; max-width: 1400px; }
    [data-testid="stRadio"] { display: flex !important; justify-content: flex-end !important; width: 100% !important; }
    [role="radiogroup"] { justify-content: flex-end !important; gap: 15px !important; margin-left: auto !important; }
    .metric-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 14px 0 10px 0; text-align: center; width: 100%; }
    .metric-label { font-size: 13px; color: #8B949E; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
    .metric-pct-pos { font-size: 14px; font-weight: 600; color: #00E676; margin-bottom: 5px; }
    .metric-pct-neg { font-size: 14px; font-weight: 600; color: #FF5370; margin-bottom: 5px; }
    .metric-delta-pos { display: inline-block; font-size: 13px; font-weight: 600; color: #00E676; background-color: rgba(0,230,118,0.12); padding: 2px 8px; border-radius: 4px; }
    .metric-delta-neg { display: inline-block; font-size: 13px; font-weight: 600; color: #FF5370; background-color: rgba(255,83,112,0.12); padding: 2px 8px; border-radius: 4px; }
    .pnl-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .pnl-table th { color: #8B949E; font-weight: 500; padding: 8px 12px; border-bottom: 1px solid #2A2E39; text-align: right; }
    .pnl-table th:first-child { text-align: left; }
    .pnl-table td { padding: 8px 12px; border-bottom: 1px solid #1E2330; text-align: right; color: #E0E0E0; }
    .pnl-table td:first-child { text-align: left; color: #8B949E; }
    .pnl-table tr:hover td { background-color: #1E2330; }
    .pos { color: #00E676 !important; }
    .neg { color: #FF5370 !important; }
    .stat-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 12px 16px; }
    .stat-label { font-size: 12px; color: #8B949E; margin-bottom: 4px; }
    .stat-value { font-size: 20px; font-weight: 700; color: #FFFFFF; }
    .alloc-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 14px 18px; height: 100%; }
    .alloc-label { font-size: 13px; color: #8B949E; margin-bottom: 10px; font-weight: 500; }
    .alloc-row { display: flex; align-items: center; margin-bottom: 8px; gap: 10px; }
    .alloc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .alloc-name { font-size: 13px; color: #E0E0E0; width: 50px; }
    .alloc-bar-bg { flex: 1; background-color: #2A2E39; border-radius: 3px; height: 6px; }
    .alloc-bar-fill { height: 6px; border-radius: 3px; }
    .alloc-pct { font-size: 13px; color: #E0E0E0; font-weight: 600; width: 40px; text-align: right; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
def get_exchange_rate():
    try: return requests.get("https://api.upbit.com/v1/ticker?markets=KRW-USDT").json()[0]['trade_price']
    except: return 1350.0

@st.cache_data(ttl=5)
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]), scope
)
        client = gspread.authorize(creds)
        db = client.open("TIM_Portfolio_DB")

        m_data = db.get_worksheet(0).get_all_values()
        df_m = pd.DataFrame(m_data[1:], columns=m_data[0])
        df_m['시간'] = pd.to_datetime(df_m['시간'])
        for c in ['김프차익', 'OKX통합', '총자산']:
            df_m[c] = pd.to_numeric(df_m[c].str.replace(',', ''), errors='coerce').fillna(0)

        p_data = db.get_worksheet(1).get_all_values()
        df_p = pd.DataFrame(p_data[1:], columns=p_data[0]) if len(p_data) > 1 else pd.DataFrame()

        t_data = db.get_worksheet(2).get_all_values()
        if len(t_data) > 1:
            df_t = pd.DataFrame(t_data[1:], columns=t_data[0])
            df_t['날짜'] = pd.to_datetime(df_t['날짜'])
            df_t['금액'] = pd.to_numeric(df_t['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        else:
            df_t = pd.DataFrame(columns=['날짜', '유형', '금액', '메모'])

        return df_m, df_p, df_t
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(columns=['날짜', '유형', '금액', '메모'])

usdt_rate = get_exchange_rate()
df, pos_df, transfer_df = load_data()

# ── session state 초기화 ───────────────────────────
if 'currency' not in st.session_state:
    st.session_state.currency = 'KRW'
if 'range_radio' not in st.session_state:
    st.session_state.range_radio = 'D'

params = st.query_params
if 'currency' in params:
    st.session_state.currency = params['currency']
    st.query_params.clear()

is_usd = (st.session_state.currency == "USD")
currency_sym = "$" if is_usd else "₩"
fmt_hover = ",.2f" if is_usd else ",.0f"

def fmt(val): return f"${val/usdt_rate:,.2f}" if is_usd else f"₩{int(val):,}"
def fmt_signed(val):
    sign = "+" if val >= 0 else ""
    return f"{sign}${val/usdt_rate:,.2f}" if is_usd else f"{sign}₩{int(val):,}"
def delta_html(val):
    sym = "▲" if val >= 0 else "▼"
    css = "metric-delta-pos" if val >= 0 else "metric-delta-neg"
    return f'<span class="{css}">{sym} {fmt(abs(val))}</span>'
def pct_html(pct):
    sign = "+" if pct >= 0 else ""
    css = "metric-pct-pos" if pct >= 0 else "metric-pct-neg"
    return f'<div class="{css}">{sign}{pct:.2f}%</div>'
def metric_card(label, value, diff, pct):
    return f"""<div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{fmt(value)}</div>
        {pct_html(pct)}
        {delta_html(diff)}
    </div>"""

def currency_btn(label):
    active = st.session_state.currency == label
    bg     = "#00E676" if active else "transparent"
    color  = "#000"    if active else "#8B949E"
    border = "#00E676" if active else "#2A2E39"
    return (
        f"<a href='?currency={label}' style='text-decoration:none;'>"
        f"<span style='padding:3px 12px;border-radius:20px;font-size:13px;font-weight:600;"
        f"background:{bg};color:{color};border:1px solid {border};cursor:pointer;'>{label}</span></a>"
    )

# ── 헤더 ──────────────────────────────────────────
l_time = df.iloc[-1]['시간'].strftime('%Y-%m-%d %H:%M:%S') if not df.empty else "..."
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h3 style='margin:0; color:#fff; font-weight:700; padding-top:10px;'>🤖 T.I.M Live Dashboard</h3>", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div style='display:flex; flex-direction:column; align-items:flex-end; gap:8px; padding-top:8px;'>
        <div style='color:#00E676; font-size:14px; font-weight:600;'>🟢 LIVE | {l_time}</div>
        <div style='display:flex; gap:6px;'>
            {currency_btn('KRW')}
            {currency_btn('USD')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 요약 카드 + Allocation ─────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if not df.empty:
    curr  = df.iloc[-1]
    prev  = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    first = df.iloc[0]

    def pct_change(col):
        return 0.0 if first[col] == 0 else (curr[col] - first[col]) / first[col] * 100

    total_val  = curr['총자산'] if curr['총자산'] != 0 else 1
    kimp_ratio = curr['김프차익'] / total_val * 100
    okx_ratio  = curr['OKX통합']  / total_val * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(metric_card("TOTAL (총 자산)",          curr['총자산'],   curr['총자산']  -prev['총자산'],   pct_change('총자산')),   unsafe_allow_html=True)
    with col2: st.markdown(metric_card("김프차익 (업비트&바이비트)", curr['김프차익'], curr['김프차익']-prev['김프차익'], pct_change('김프차익')), unsafe_allow_html=True)
    with col3: st.markdown(metric_card("OKX (시그널봇&현물)",       curr['OKX통합'],  curr['OKX통합'] -prev['OKX통합'],  pct_change('OKX통합')),  unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="alloc-card">
            <div class="alloc-label">ALLOCATION</div>
            <div class="alloc-row">
                <div class="alloc-dot" style="background:#00E676;"></div>
                <div class="alloc-name">KIMP</div>
                <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{kimp_ratio:.1f}%;background:#00E676;"></div></div>
                <div class="alloc-pct">{kimp_ratio:.1f}%</div>
            </div>
            <div class="alloc-row">
                <div class="alloc-dot" style="background:#3B82F6;"></div>
                <div class="alloc-name">OKX</div>
                <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{okx_ratio:.1f}%;background:#3B82F6;"></div></div>
                <div class="alloc-pct">{okx_ratio:.1f}%</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ── 차트 ─────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
ct, cb = st.columns([3, 1])
with ct:
    st.markdown("<h4 style='color:#E0E0E0; font-weight:600;'>📈 Cumulative P&L</h4>", unsafe_allow_html=True)
with cb:
    period = st.radio("Range", ["4H", "D", "W", "M"], horizontal=True, label_visibility="collapsed", key="range_radio")

chart_filter = st.radio("Chart Filter", ["All", "KIMP", "OKX"], horizontal=True, label_visibility="collapsed", key="chart_filter")

if not df.empty:
    pdf = df.copy().set_index('시간').sort_index()
    now = pdf.index.max()

    if period == "4H":
        pdf = pdf[pdf.index >= now - pd.Timedelta(days=7)]
        pdf = pdf.resample('4h').last().dropna()
        xaxis_cfg = dict(
            tickformat="%m-%d %H:%M",
            gridcolor='#2A2E39',
            range=[pdf.index.min(), pdf.index.max()],
            dtick=4 * 60 * 60 * 1000,
            tickangle=0,
        )
    elif period == "D":
        pdf = pdf.groupby(pdf.index.date).last()
        pdf.index = pd.to_datetime(pdf.index)
        xaxis_cfg = dict(
            tickformat="%m-%d",
            gridcolor='#2A2E39',
            range=[pdf.index.min(), pdf.index.max()],
        )
    elif period == "W":
        pdf = pdf[pdf.index >= now - pd.Timedelta(days=90)]
        pdf = pdf.resample('W-MON').last().dropna()
        xaxis_cfg = dict(
            tickformat="%m-%d",
            gridcolor='#2A2E39',
            range=[pdf.index.min(), pdf.index.max()],
        )
    else:
        pdf = pdf.resample('ME').last().dropna()
        xaxis_cfg = dict(
            tickformat="%Y-%m",
            gridcolor='#2A2E39',
            range=[pdf.index.min(), pdf.index.max()],
        )

    if is_usd:
        pdf[['총자산', '김프차익', 'OKX통합']] /= usdt_rate

    fig = go.Figure()
    if chart_filter == "All":
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['총자산'], mode='lines', name='TOTAL',
            line=dict(color='#A855F7', width=3), fill='tozeroy', fillcolor='rgba(168,85,247,0.1)',
            hovertemplate=f"<b style='color:#A855F7'>TOTAL</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['김프차익'], mode='lines', name='KIMP',
            line=dict(color='#00E676', width=2),
            hovertemplate=f"<b style='color:#00E676'>KIMP</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['OKX통합'], mode='lines', name='OKX',
            line=dict(color='#3B82F6', width=2),
            hovertemplate=f"<b style='color:#3B82F6'>OKX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
    elif chart_filter == "KIMP":
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['김프차익'], mode='lines', name='KIMP',
            line=dict(color='#00E676', width=3), fill='tozeroy', fillcolor='rgba(0,230,118,0.1)',
            hovertemplate=f"<b style='color:#00E676'>KIMP</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['OKX통합'], mode='lines', name='OKX',
            line=dict(color='#3B82F6', width=3), fill='tozeroy', fillcolor='rgba(59,130,246,0.1)',
            hovertemplate=f"<b style='color:#3B82F6'>OKX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))

    fig.update_layout(
        plot_bgcolor='#171B26', paper_bgcolor='#171B26', font=dict(color='#8B949E'),
        margin=dict(l=10, r=10, t=10, b=10), height=350, hovermode="x unified",
        hoverlabel=dict(bgcolor="#1E2433", bordercolor="#2A2E39", font=dict(color="#E0E0E0", size=13), namelength=-1),
        xaxis=xaxis_cfg,
        yaxis=dict(gridcolor='#2A2E39', tickprefix=currency_sym, tickformat=",.2f" if is_usd else ",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# ── 포지션 현황 ───────────────────────────────────
st.markdown("<h4 style='color:#E0E0E0; font-weight:600;'>🎯 포지션 현황</h4>", unsafe_allow_html=True)
if not pos_df.empty:
    kimp_only = pos_df[pos_df['거래소'].isin(['Upbit', 'Bybit'])]
    if not kimp_only.empty:
        st.dataframe(kimp_only, use_container_width=True, hide_index=True)
    else:
        st.info("현재 포지션이 없습니다.")
else:
    st.info("현재 포지션이 없습니다.")

# ── 손익 내역 ─────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#E0E0E0; font-weight:600;'>📋 손익 내역</h4>", unsafe_allow_html=True)

if not df.empty:
    daily = df.copy().set_index('시간').sort_index()
    daily = daily.groupby(daily.index.date).last()
    daily.index = pd.to_datetime(daily.index)

    daily['일손익_총']  = daily['총자산'].diff().fillna(0)
    daily['일손익_김프'] = daily['김프차익'].diff().fillna(0)
    daily['일손익_OKX'] = daily['OKX통합'].diff().fillna(0)

    if not transfer_df.empty:
        transfer_daily = transfer_df.copy()
        transfer_daily['조정금액'] = transfer_daily.apply(
            lambda r: r['금액'] if r['유형'] == '입금' else -r['금액'], axis=1
        )
        transfer_daily = transfer_daily.groupby(pd.to_datetime(transfer_daily['날짜']).dt.normalize())['조정금액'].sum()
        daily = daily.join(transfer_daily, how='left')
        daily['조정금액'] = daily['조정금액'].fillna(0)
        daily['일손익_총'] = daily['일손익_총'] - daily['조정금액']
    else:
        daily['조정금액'] = 0

    pnl_filter = st.radio("PnL Filter", ["전체", "KIMP", "OKX"], horizontal=True, label_visibility="collapsed", key="pnl_filter")

    if pnl_filter == "KIMP":
        pnl_col, cum_col = '일손익_김프', '김프차익'
    elif pnl_filter == "OKX":
        pnl_col, cum_col = '일손익_OKX', 'OKX통합'
    else:
        pnl_col, cum_col = '일손익_총', '총자산'

    pnl_vals   = daily[pnl_col]
    wins       = (pnl_vals > 0).sum()
    total_days = (pnl_vals != 0).sum()
    win_rate   = wins / total_days * 100 if total_days > 0 else 0
    total_pnl  = pnl_vals.sum()
    max_profit = pnl_vals.max()
    max_loss   = pnl_vals.min()

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1: st.markdown(f"<div class='stat-card'><div class='stat-label'>총 손익</div><div class='stat-value' style='color:{'#00E676' if total_pnl>=0 else '#FF5370'}'>{fmt_signed(total_pnl)}</div></div>", unsafe_allow_html=True)
    with sc2: st.markdown(f"<div class='stat-card'><div class='stat-label'>승률</div><div class='stat-value'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)
    with sc3: st.markdown(f"<div class='stat-card'><div class='stat-label'>최대 수익</div><div class='stat-value' style='color:#00E676'>{fmt_signed(max_profit)}</div></div>", unsafe_allow_html=True)
    with sc4: st.markdown(f"<div class='stat-card'><div class='stat-label'>최대 손실</div><div class='stat-value' style='color:#FF5370'>{fmt_signed(max_loss)}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    rows_html = ""
    for date, row in daily.sort_index(ascending=False).iterrows():
        d_val = row[pnl_col]
        c_val = row[cum_col] - daily[cum_col].iloc[0]
        transfer_val = row.get('조정금액', 0)

        d_cls = "pos" if d_val >= 0 else "neg"
        c_cls = "pos" if c_val >= 0 else "neg"

        transfer_badge = ""
        if transfer_val > 0:
            transfer_badge = f"<span style='background:rgba(59,130,246,0.15);color:#3B82F6;font-size:11px;padding:1px 6px;border-radius:3px;margin-left:6px;'>입금 {fmt(transfer_val)}</span>"
        elif transfer_val < 0:
            transfer_badge = f"<span style='background:rgba(255,170,0,0.15);color:#FFAA00;font-size:11px;padding:1px 6px;border-radius:3px;margin-left:6px;'>출금 {fmt(abs(transfer_val))}</span>"

        rows_html += f"<tr><td>{date.strftime('%Y-%m-%d')}{transfer_badge}</td><td class='{d_cls}'>{fmt_signed(d_val)}</td><td class='{c_cls}'>{fmt_signed(c_val)}</td></tr>"

    table_html = (
        "<div style='background:#171B26;border:1px solid #2A2E39;border-radius:8px;padding:0 4px;max-height:400px;overflow-y:auto;'>"
        "<table class='pnl-table'>"
        "<thead><tr><th>날짜</th><th>일 손익</th><th>누적 손익</th></tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

time.sleep(300)
st.rerun()
