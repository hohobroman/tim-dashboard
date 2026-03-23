import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="T.I.M Portfolio", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #0F1219; color: #E0E0E0; font-family: 'Pretendard', sans-serif; }
    header, footer, #MainMenu { visibility: hidden; }
    .block-container { padding-top: 1.5rem; max-width: 1400px; }

    .cards-container { display: flex; gap: 12px; margin-top: 16px; margin-bottom: 16px; }
    @media (max-width: 768px) {
        .cards-container { flex-wrap: wrap !important; }
        .cards-container > div { flex: 0 0 calc(50% - 6px) !important; min-width: calc(50% - 6px) !important; }
    }
    .metric-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 16px 0 8px 0; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .metric-label { font-size: 13px; color: #8B949E; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
    .metric-pct-pos { font-size: 14px; font-weight: 600; color: #00E676; margin-bottom: 4px; }
    .metric-pct-neg { font-size: 14px; font-weight: 600; color: #FF5370; margin-bottom: 4px; }
    .metric-delta-pos { display: inline-block; font-size: 13px; font-weight: 600; color: #00E676; background-color: rgba(0,230,118,0.12); padding: 2px 10px; border-radius: 4px; }
    .metric-delta-neg { display: inline-block; font-size: 13px; font-weight: 600; color: #FF5370; background-color: rgba(255,83,112,0.12); padding: 2px 10px; border-radius: 4px; }

    .pos-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .pos-table th { color: #8B949E; font-weight: 500; padding: 10px 12px; border-bottom: 1px solid #2A2E39; text-align: left; }
    .pos-table td { padding: 10px 12px; border-bottom: 1px solid #1E2330; color: #E0E0E0; text-align: left; }
    .pos-table tr:last-child td { border-bottom: none; }
    .pos-table tr:hover td { background-color: #1E2330; }

    .pnl-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .pnl-table th { color: #8B949E; font-weight: 500; padding: 8px 12px; border-bottom: 1px solid #2A2E39; text-align: right; }
    .pnl-table th:first-child { text-align: left; }
    .pnl-table td { padding: 8px 12px; border-bottom: 1px solid #1E2330; text-align: right; color: #E0E0E0; }
    .pnl-table td:first-child { text-align: left; color: #8B949E; }
    .pnl-table tr:hover td { background-color: #1E2330; }
    .pnl-table tr.transfer-row td { background-color: #0F1520; color: #8B949E; }
    .pnl-table tr.transfer-row:hover td { background-color: #141a2a; }
    .pos { color: #00E676 !important; }
    .neg { color: #FF5370 !important; }

    .stat-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 12px 16px; }
    .stat-label { font-size: 12px; color: #8B949E; margin-bottom: 4px; }
    .stat-value { font-size: 20px; font-weight: 700; color: #FFFFFF; }

    .alloc-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: center; }
    .alloc-label { font-size: 13px; color: #8B949E; margin-bottom: 10px; font-weight: 500; }
    .alloc-row { display: flex; align-items: center; margin-bottom: 8px; gap: 10px; }
    .alloc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .alloc-name { font-size: 13px; color: #E0E0E0; width: 60px; }
    .alloc-bar-bg { flex: 1; background-color: #2A2E39; border-radius: 3px; height: 6px; }
    .alloc-bar-fill { height: 6px; border-radius: 3px; }
    .alloc-pct { font-size: 13px; color: #E0E0E0; font-weight: 600; width: 40px; text-align: right; }

    /* ── Pill 라디오 버튼 (All/KIMP/OKX/빙엑스, 4H/D/W/M, 손익필터) ── */
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important; flex-direction: row !important;
        flex-wrap: nowrap !important; gap: 6px !important;
        background: transparent !important; padding: 0 !important;
        align-items: center !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        display: inline-flex !important; align-items: center !important;
        justify-content: center !important; background: transparent !important;
        border: 1px solid #3A3E4A !important; border-radius: 20px !important;
        padding: 4px 14px !important; margin: 0 !important;
        cursor: pointer !important; min-width: fit-content !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important; width: 0 !important; height: 0 !important;
        overflow: hidden !important; position: absolute !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:last-child p {
        color: #8B949E !important; font-size: 13px !important;
        font-weight: 600 !important; margin: 0 !important; line-height: 1.4 !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: #00E676 !important; border-color: #00E676 !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) > div:last-child p {
        color: #000 !important;
    }

    /* ── 마커 처리 ── */
    div.element-container:has(.marker) { display: none !important; }
    div.element-container:has(.align-right) + div.element-container div[role="radiogroup"] {
        justify-content: flex-end !important;
    }
    div.element-container:has(.color-red) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: #FF5370 !important; border-color: #FF5370 !important;
    }
    div.element-container:has(.color-red) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) > div:last-child p {
        color: #fff !important;
    }
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
        for c in ['김프차익', 'OKX통합', '빙엑스 현물DCA', '총자산']:
            df_m[c] = pd.to_numeric(df_m[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

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

# ── session_state 초기화 ──
if 'currency' not in st.session_state:
    st.session_state['currency'] = 'KRW'

is_usd = st.session_state['currency'] == 'USD'
currency_sym = "$" if is_usd else "₩"
fmt_hover = ",.2f" if is_usd else ",.0f"

def fmt(val):
    return f"${val/usdt_rate:,.2f}" if is_usd else f"₩{int(val):,}"
def fmt_signed(val):
    sign = "+" if val >= 0 else ""
    return f"{sign}${val/usdt_rate:,.2f}" if is_usd else f"{sign}₩{int(val):,}"
def delta_html(val):
    sym = "▲" if val >= 0 else "▼"
    css = "metric-delta-pos" if val >= 0 else "metric-delta-neg"
    return f'<div style="padding-bottom:8px;"><span class="{css}">{sym} {fmt(abs(val))}</span></div>'
def pct_html(pct):
    sign = "+" if pct >= 0 else ""
    css = "metric-pct-pos" if pct >= 0 else "metric-pct-neg"
    return f'<div class="{css}">{sign}{pct:.2f}%</div>'

# ══════════════════════════════════════════════════
# ── 헤더
# ══════════════════════════════════════════════════
l_time = df.iloc[-1]['시간'].strftime('%Y-%m-%d %H:%M:%S') if not df.empty else "..."

h1, h2 = st.columns([3, 1])
with h1:
    st.markdown(
        "<h3 style='margin:0; color:#fff; font-weight:700; padding-top:10px;'>"
        "🚀 나 대신 매매 (T.I.M) Live Dashboard</h3>",
        unsafe_allow_html=True
    )
with h2:
    # 마지막 업데이트 + KRW/USD 를 하나의 HTML 블록으로
    krw_s = "background:#00E676;color:#000;border:1px solid #00E676;" if not is_usd else "background:transparent;color:#8B949E;border:1px solid #3A3E4A;"
    usd_s = "background:#00E676;color:#000;border:1px solid #00E676;" if is_usd     else "background:transparent;color:#8B949E;border:1px solid #3A3E4A;"
    st.markdown(f"""
    <div style='display:flex;flex-direction:column;align-items:flex-end;gap:8px;padding-top:8px;'>
        <div style='display:flex;flex-direction:column;align-items:flex-end;gap:2px;'>
            <div style='color:#8B949E;font-size:12px;'>마지막 업데이트</div>
            <div style='color:#E0E0E0;font-size:14px;font-weight:600;'>{l_time}</div>
        </div>
        <div style='display:flex;gap:6px;'>
            <button onclick="window.location.href='?currency=KRW'"
                style='{krw_s}border-radius:20px;padding:4px 14px;font-size:13px;
                font-weight:600;cursor:pointer;font-family:Pretendard,sans-serif;'>KRW</button>
            <button onclick="window.location.href='?currency=USD'"
                style='{usd_s}border-radius:20px;padding:4px 14px;font-size:13px;
                font-weight:600;cursor:pointer;font-family:Pretendard,sans-serif;'>USD</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

# URL 파라미터로 currency 처리 (같은 탭 reload)
params = st.query_params
if 'currency' in params:
    val = params['currency']
    if val in ('KRW', 'USD') and st.session_state['currency'] != val:
        st.session_state['currency'] = val
        st.rerun()

# ══════════════════════════════════════════════════
# ── 요약 카드
# ══════════════════════════════════════════════════
st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
if not df.empty:
    curr  = df.iloc[-1]
    prev  = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    first = df.iloc[0]

    def pct_change(col):
        return 0.0 if first[col] == 0 else (curr[col] - first[col]) / first[col] * 100

    total_val  = curr['총자산'] if curr['총자산'] != 0 else 1
    kimp_ratio = curr['김프차익'] / total_val * 100
    okx_ratio  = curr['OKX통합']  / total_val * 100
    bx_ratio   = curr['빙엑스 현물DCA'] / total_val * 100

    st.markdown(f"""
    <div class='cards-container'>
        <div class="metric-card" style='flex:1;'>
            <div class="metric-label">TOTAL (총 자산)</div>
            <div class="metric-value">{fmt(curr['총자산'])}</div>
            {pct_html(pct_change('총자산'))}
            {delta_html(curr['총자산']-prev['총자산'])}
        </div>
        <div class="metric-card" style='flex:1;'>
            <div class="metric-label">김프차익 (업비트&바이비트)</div>
            <div class="metric-value">{fmt(curr['김프차익'])}</div>
            {pct_html(pct_change('김프차익'))}
            {delta_html(curr['김프차익']-prev['김프차익'])}
        </div>
        <div class="metric-card" style='flex:1;'>
            <div class="metric-label">OKX (시그널봇&현물)</div>
            <div class="metric-value">{fmt(curr['OKX통합'])}</div>
            {pct_html(pct_change('OKX통합'))}
            {delta_html(curr['OKX통합']-prev['OKX통합'])}
        </div>
        <div class="metric-card" style='flex:1;'>
            <div class="metric-label">빙엑스 현물DCA</div>
            <div class="metric-value">{fmt(curr['빙엑스 현물DCA'])}</div>
            {pct_html(pct_change('빙엑스 현물DCA'))}
            {delta_html(curr['빙엑스 현물DCA']-prev['빙엑스 현물DCA'])}
        </div>
        <div class="alloc-card" style='flex:1;'>
            <div class="alloc-label">자산 비중</div>
            <div style='height:10px;'></div>
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
            <div class="alloc-row">
                <div class="alloc-dot" style="background:#F59E0B;"></div>
                <div class="alloc-name">BingX</div>
                <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{bx_ratio:.1f}%;background:#F59E0B;"></div></div>
                <div class="alloc-pct">{bx_ratio:.1f}%</div>
            </div>
            <div style='height:10px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# ── 차트 헤더: 제목 + 필터(왼쪽) | 기간(오른쪽)
# ══════════════════════════════════════════════════
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)

title_col, filter_col, period_col = st.columns([3, 4, 2])

with title_col:
    st.markdown(
        "<h4 style='color:#E0E0E0;font-weight:600;margin:0;padding-top:5px;white-space:nowrap;'>"
        "📈 누적 손익 추이</h4>",
        unsafe_allow_html=True
    )

with filter_col:
    chart_filter = st.radio(
        "", ["All", "KIMP", "OKX", "빙엑스"],
        horizontal=True, label_visibility="collapsed",
        key="chart_filter_radio"
    )

with period_col:
    st.markdown('<span class="marker align-right color-red"></span>', unsafe_allow_html=True)
    period = st.radio(
        "", ["4H", "D", "W", "M"],
        horizontal=True, label_visibility="collapsed",
        index=1, key="period_radio"
    )

# ══════════════════════════════════════════════════
# ── 차트
# ══════════════════════════════════════════════════
if not df.empty:
    pdf = df.copy().set_index('시간').sort_index()
    now = pdf.index.max()
    today = pd.Timestamp.now()

    if period == "4H":
        pdf = pdf[pdf.index >= now - pd.Timedelta(days=7)]
        pdf = pdf.resample('4h').last().dropna()
        xaxis_cfg = dict(tickformat="%m-%d %H:%M", gridcolor='#2A2E39',
                         range=[pdf.index.min(), pdf.index.max()],
                         dtick=4*60*60*1000, tickangle=0)
    elif period == "D":
        pdf = pdf.groupby(pdf.index.date).last()
        pdf.index = pd.to_datetime(pdf.index)
        xaxis_cfg = dict(tickformat="%m-%d", gridcolor='#2A2E39',
                         range=[pdf.index.min(), today + pd.Timedelta(days=14)],
                         dtick=86400000)
    elif period == "W":
        pdf = pdf[pdf.index >= now - pd.Timedelta(days=90)]
        pdf = pdf.resample('W-SUN').last().dropna()
        xaxis_cfg = dict(tickformat="%m-%d", gridcolor='#2A2E39',
                         range=[pdf.index.min(), today + pd.Timedelta(weeks=4)],
                         dtick=7*86400000)
    else:
        pdf = pdf.resample('ME').last().dropna()
        xaxis_cfg = dict(tickformat="%Y-%m", gridcolor='#2A2E39',
                         range=[pdf.index.min(), today + pd.DateOffset(months=3)],
                         dtick='M1')

    if is_usd:
        for c in ['총자산', '김프차익', 'OKX통합', '빙엑스 현물DCA']:
            pdf[c] = pdf[c] / usdt_rate

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
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['빙엑스 현물DCA'], mode='lines', name='BingX',
            line=dict(color='#F59E0B', width=2),
            hovertemplate=f"<b style='color:#F59E0B'>BingX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
    elif chart_filter == "KIMP":
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['김프차익'], mode='lines', name='KIMP',
            line=dict(color='#00E676', width=3), fill='tozeroy', fillcolor='rgba(0,230,118,0.1)',
            hovertemplate=f"<b style='color:#00E676'>KIMP</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
    elif chart_filter == "OKX":
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['OKX통합'], mode='lines', name='OKX',
            line=dict(color='#3B82F6', width=3), fill='tozeroy', fillcolor='rgba(59,130,246,0.1)',
            hovertemplate=f"<b style='color:#3B82F6'>OKX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=pdf.index, y=pdf['빙엑스 현물DCA'], mode='lines', name='BingX',
            line=dict(color='#F59E0B', width=3), fill='tozeroy', fillcolor='rgba(245,158,11,0.1)',
            hovertemplate=f"<b style='color:#F59E0B'>BingX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))

    fig.update_layout(
        plot_bgcolor='#171B26', paper_bgcolor='#171B26', font=dict(color='#8B949E'),
        margin=dict(l=10, r=10, t=10, b=10), height=350, hovermode="x unified",
        hoverlabel=dict(bgcolor="#1E2433", bordercolor="#2A2E39",
                        font=dict(color="#E0E0E0", size=13), namelength=-1),
        xaxis=xaxis_cfg,
        yaxis=dict(gridcolor='#2A2E39', tickprefix=currency_sym,
                   tickformat=",.2f" if is_usd else ",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="#E0E0E0"))
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ══════════════════════════════════════════════════
# ── 포지션 현황
# ══════════════════════════════════════════════════
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#E0E0E0;font-weight:600;margin-bottom:12px;'>🎯 포지션 현황</h4>", unsafe_allow_html=True)
if not pos_df.empty:
    show = pos_df[pos_df['거래소'].isin(['Upbit', 'Bybit', 'BingX(현물)'])].copy()
    if not show.empty:
        if '방향' in show.columns:
            show['방향'] = show['방향'].replace({'SPOT': 'LONG'})
        if '종목' in show.columns:
            show['종목'] = show['종목'].str.replace(':USDT', ' PERP', regex=False)
        headers = show.columns.tolist()
        rows_html = ""
        for _, row in show.iterrows():
            rows_html += "<tr>"
            for col in headers:
                val = str(row[col])
                if col == '미실현 PNL(₩)':
                    try:
                        num = float(val.replace('₩','').replace(',','').replace('+',''))
                        color = "#00E676" if num >= 0 else "#FF5370"
                        rows_html += f"<td style='color:{color};'>{val}</td>"
                    except:
                        rows_html += f"<td>{val}</td>"
                else:
                    rows_html += f"<td>{val}</td>"
            rows_html += "</tr>"
        header_html = "".join(f"<th>{h}</th>" for h in headers)
        st.markdown(f"""
        <div style='background:#171B26;border:1px solid #2A2E39;border-radius:8px;padding:0 4px;overflow-x:auto;'>
            <table class='pos-table'><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("현재 포지션이 없습니다.")
else:
    st.info("현재 포지션이 없습니다.")

# ══════════════════════════════════════════════════
# ── 손익 내역
# ══════════════════════════════════════════════════
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#E0E0E0;font-weight:600;margin-bottom:12px;'>📋 손익 내역</h4>", unsafe_allow_html=True)

if not df.empty:
    daily = df.copy().set_index('시간').sort_index()
    daily = daily.groupby(daily.index.date).last()
    daily.index = pd.to_datetime(daily.index)

    daily['일손익_총']   = daily['총자산'].diff().fillna(0)
    daily['일손익_김프'] = daily['김프차익'].diff().fillna(0)
    daily['일손익_OKX']  = daily['OKX통합'].diff().fillna(0)
    daily['일손익_BX']   = daily['빙엑스 현물DCA'].diff().fillna(0)

    pnl_filter = st.radio(
        "", ["전체", "KIMP", "OKX", "빙엑스"],
        horizontal=True, label_visibility="collapsed",
        key="pnl_filter_radio"
    )

    if pnl_filter == "KIMP":     pnl_col, cum_col = '일손익_김프', '김프차익'
    elif pnl_filter == "OKX":    pnl_col, cum_col = '일손익_OKX',  'OKX통합'
    elif pnl_filter == "빙엑스": pnl_col, cum_col = '일손익_BX',   '빙엑스 현물DCA'
    else:                         pnl_col, cum_col = '일손익_총',   '총자산'

    pnl_vals   = daily[pnl_col]
    wins       = (pnl_vals > 0).sum()
    total_days = (pnl_vals != 0).sum()
    win_rate   = wins / total_days * 100 if total_days > 0 else 0
    total_pnl  = pnl_vals.sum()
    max_profit = pnl_vals.max()
    max_loss   = pnl_vals.min()

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"<div class='stat-card'><div class='stat-label'>총 손익</div><div class='stat-value' style='color:{'#00E676' if total_pnl>=0 else '#FF5370'}'>{fmt_signed(total_pnl)}</div></div>", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"<div class='stat-card'><div class='stat-label'>승률</div><div class='stat-value'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"<div class='stat-card'><div class='stat-label'>최대 수익</div><div class='stat-value' style='color:#00E676'>{fmt_signed(max_profit)}</div></div>", unsafe_allow_html=True)
    with sc4:
        st.markdown(f"<div class='stat-card'><div class='stat-label'>최대 손실</div><div class='stat-value' style='color:#FF5370'>{fmt_signed(max_loss)}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    transfer_rows = {}
    if not transfer_df.empty:
        for _, tr in transfer_df.iterrows():
            d = pd.Timestamp(tr['날짜']).normalize()
            if d not in transfer_rows:
                transfer_rows[d] = []
            transfer_rows[d].append(tr)

    rows_html = ""
    for date, row in daily.sort_index(ascending=False).iterrows():
        d_val = row[pnl_col]
        c_val = row[cum_col] - daily[cum_col].iloc[0]
        d_cls = "pos" if d_val >= 0 else "neg"
        c_cls = "pos" if c_val >= 0 else "neg"
        if date in transfer_rows:
            for tr in transfer_rows[date]:
                is_dep = tr['유형'] == '입금'
                bc = "#3B82F6" if is_dep else "#FFAA00"
                bb = "rgba(59,130,246,0.15)" if is_dep else "rgba(255,170,0,0.15)"
                bt = f"입금 {fmt(tr['금액'])}" if is_dep else f"출금 {fmt(tr['금액'])}"
                memo = tr.get('메모', '')
                mb = f"<span style='color:#8B949E;font-size:11px;margin-left:4px;'>{memo}</span>" if memo else ""
                rows_html += (
                    f"<tr class='transfer-row'><td>{date.strftime('%Y-%m-%d')} "
                    f"<span style='background:{bb};color:{bc};font-size:11px;padding:1px 6px;border-radius:3px;'>{bt}</span>{mb}</td>"
                    f"<td style='color:#2A2E39;'>—</td><td style='color:#2A2E39;'>—</td></tr>"
                )
        rows_html += (
            f"<tr><td>{date.strftime('%Y-%m-%d')}</td>"
            f"<td class='{d_cls}'>{fmt_signed(d_val)}</td>"
            f"<td class='{c_cls}'>{fmt_signed(c_val)}</td></tr>"
        )

    st.markdown(
        "<div style='background:#171B26;border:1px solid #2A2E39;border-radius:8px;"
        "padding:0 4px;max-height:400px;overflow-y:auto;'>"
        "<table class='pnl-table'><thead><tr><th>날짜</th><th>일 손익</th><th>누적 손익</th></tr></thead>"
        "<tbody>" + rows_html + "</tbody></table></div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

# ── 5분마다 자동 새로고침 ──
components.html(
    "<script>setTimeout(function(){ window.location.reload(); }, 300000);</script>",
    height=0
)
