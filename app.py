import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="T.I.M Portfolio", layout="wide", initial_sidebar_state="collapsed")

# --- 스타일 --- #
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
    .metric-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 16px 12px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; }
    .metric-label { font-size: 13px; color: #8B949E; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
    .metric-pct-pos { font-size: 14px; font-weight: 600; color: #10B981; margin-bottom: 4px; } /* Improved green */
    .metric-pct-neg { font-size: 14px; font-weight: 600; color: #EF4444; margin-bottom: 4px; } /* Improved red */
    .metric-delta-pos { display: inline-block; font-size: 13px; font-weight: 600; color: #10B981; background-color: rgba(16,185,129,0.12); padding: 2px 10px; border-radius: 4px; }
    .metric-delta-neg { display: inline-block; font-size: 13px; font-weight: 600; color: #EF4444; background-color: rgba(239,68,68,0.12); padding: 2px 10px; border-radius: 4px; }

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
    .pos { color: #10B981 !important; } /* Improved green */
    .neg { color: #EF4444 !important; } /* Improved red */

    .stat-card { background-color: #171B26; border: 1px solid #2A2E39; border-radius: 8px; padding: 12px 16px; height: 100%; }
    .stat-label { font-size: 12px; color: #8B949E; margin-bottom: 4px; }
    .stat-value { font-size: 20px; font-weight: 700; color: #FFFFFF; }

    /* 빈 상태 디자인 */
    .empty-state-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        padding: 40px 20px; background-color: #171B26; border: 1px solid #2A2E39;
        border-radius: 8px; text-align: center; color: #8B949E; font-size: 14px;
    }
    .empty-state-icon { font-size: 48px; margin-bottom: 15px; color: #4A5568; } /* Subtle icon color */
    .empty-state-text { font-weight: 500; }

    /* 손익 내역 테이블 스크롤 최적화 */
    .pnl-table-container {
        background:#171B26; border:1px solid #2A2E39; border-radius:8px;
        padding:0 4px; max-height: 500px; overflow-y: auto; /* Increased height */
    }
    
    /* Pill 라디오 버튼 */
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
        padding: 0 14px !important; margin: 0 !important;
        cursor: pointer !important; min-width: fit-content !important;
        height: 28px !important; 
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
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
    </style>
""", unsafe_allow_html=True)

# --- 데이터 로드 --- #
@st.cache_data(ttl=60)
def get_exchange_rate():
    try:
        return requests.get("https://api.upbit.com/v1/ticker?markets=KRW-USDT").json()[0]["trade_price"]
    except Exception as e:
        st.error(f"환율 정보를 불러오는 중 오류가 발생했습니다: {e}")
        return 1350.0 # Fallback value

@st.cache_data(ttl=60)
def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        db = client.open("TIM_Portfolio_DB")

        m_data = db.get_worksheet(0).get_all_values()
        df_m = pd.DataFrame(m_data[1:], columns=m_data[0])
        df_m["시간"] = pd.to_datetime(df_m["시간"])
        
        for c in ["김프차익", "OKX통합", "빙엑스 선물", "총자산"]:
            df_m[c] = pd.to_numeric(df_m[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

        p_data = db.get_worksheet(1).get_all_values()
        df_p = pd.DataFrame(p_data[1:], columns=p_data[0]) if len(p_data) > 1 else pd.DataFrame(columns=["거래소", "종목", "수량", "방향", "진입가격", "현재가격", "미실현 PNL(₩)"])

        t_data = db.get_worksheet(2).get_all_values()
        if len(t_data) > 1:
            df_t = pd.DataFrame(t_data[1:], columns=t_data[0])
            df_t["날짜"] = pd.to_datetime(df_t["날짜"])
            df_t["금액"] = pd.to_numeric(df_t["금액"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
        else:
            df_t = pd.DataFrame(columns=["날짜", "유형", "금액", "메모"])

        return df_m, df_p, df_t
    except Exception as e:
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

usdt_rate = get_exchange_rate()
df, pos_df, transfer_df = load_data()

if df.empty:
    st.error("데이터를 불러오지 못했습니다. 구글 시트 연결을 확인해주세요.")
    st.stop()

# --- 상태 관리 및 포맷터 --- #
if "currency" not in st.session_state:
    st.session_state["currency"] = "KRW"

is_usd = st.session_state["currency"] == "USD"
currency_sym = "$" if is_usd else "₩"
fmt_hover = ",.2f" if is_usd else ",.0f"

def fmt(val):
    return f"${val/usdt_rate:,.2f}" if is_usd else f"₩{int(val):,}"

def fmt_signed(val):
    sign = "+" if val >= 0 else ""
    return f"{sign}${val/usdt_rate:,.2f}" if is_usd else f"{sign}₩{int(val):,}"

# --- 헤더 --- #
l_time = df.iloc[-1]["시간"].strftime("%Y-%m-%d %H:%M:%S")

h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("<h3 style='margin:0; color:#fff; font-weight:700; padding-top:10px;'>🚀 나 대신 매매 (T.I.M) Live Dashboard</h3>", unsafe_allow_html=True)
with h2:
    st.markdown(f"""
    <div style='text-align:right; padding-top:8px;'>
        <div style='color:#8B949E;font-size:12px;'>마지막 업데이트</div>
        <div style='color:#E0E0E0;font-size:14px;font-weight:600;'>{l_time}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["currency"] = st.radio("", ["KRW", "USD"], horizontal=True, index=1 if is_usd else 0, key="currency_radio")

# --- 요약 카드 --- #
curr  = df.iloc[-1]
prev  = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
first = df.iloc[0]

def pct_change(col):
    return 0.0 if first[col] == 0 else (curr[col] - first[col]) / first[col] * 100

summary_cols = st.columns([1.2, 1, 1, 1, 1])

with summary_cols[0]:
    st.markdown(f"""
    <div class="metric-card" title="총 자산의 현재 가치입니다.">
        <div class="metric-label">TOTAL (총 자산)</div>
        <div class="metric-value">{fmt(curr["총자산"])}</div>
        <div class="{'metric-pct-pos' if pct_change('총자산') >= 0 else 'metric-pct-neg'}">{pct_change('총자산'):+.2f}%</div>
        <div class="{'metric-delta-pos' if (curr['총자산']-prev['총자산']) >= 0 else 'metric-delta-neg'}">{'▲' if (curr['총자산']-prev['총자산']) >= 0 else '▼'} {fmt(abs(curr['총자산']-prev['총자산']))}</div>
    </div>
    """, unsafe_allow_html=True)

with summary_cols[1]:
    st.markdown(f"""
    <div class="metric-card" title="업비트와 바이비트 간의 김치 프리미엄 차익 거래 수익입니다.">
        <div class="metric-label">김프차익</div>
        <div class="metric-value">{fmt(curr["김프차익"])}</div>
        <div class="{'metric-pct-pos' if pct_change('김프차익') >= 0 else 'metric-pct-neg'}">{pct_change('김프차익'):+.2f}%</div>
        <div class="{'metric-delta-pos' if (curr['김프차익']-prev['김프차익']) >= 0 else 'metric-delta-neg'}">{'▲' if (curr['김프차익']-prev['김프차익']) >= 0 else '▼'} {fmt(abs(curr['김프차익']-prev['김프차익']))}</div>
    </div>
    """, unsafe_allow_html=True)

with summary_cols[2]:
    st.markdown(f"""
    <div class="metric-card" title="OKX 거래소의 시그널봇 및 현물 자산입니다.">
        <div class="metric-label">OKX 통합</div>
        <div class="metric-value">{fmt(curr["OKX통합"])}</div>
        <div class="{'metric-pct-pos' if pct_change('OKX통합') >= 0 else 'metric-pct-neg'}">{pct_change('OKX통합'):+.2f}%</div>
        <div class="{'metric-delta-pos' if (curr['OKX통합']-prev['OKX통합']) >= 0 else 'metric-delta-neg'}">{'▲' if (curr['OKX통합']-prev['OKX통합']) >= 0 else '▼'} {fmt(abs(curr['OKX통합']-prev['OKX통합']))}</div>
    </div>
    """, unsafe_allow_html=True)

with summary_cols[3]:
    st.markdown(f"""
    <div class="metric-card" title="BingX 거래소의 선물 자산입니다.">
        <div class="metric-label">빙엑스 선물</div>
        <div class="metric-value">{fmt(curr["빙엑스 선물"])}</div>
        <div class="{'metric-pct-pos' if pct_change('빙엑스 선물') >= 0 else 'metric-pct-neg'}">{pct_change('빙엑스 선물'):+.2f}%</div>
        <div class="{'metric-delta-pos' if (curr['빙엑스 선물']-prev['빙엑스 선물']) >= 0 else 'metric-delta-neg'}">{'▲' if (curr['빙엑스 선물']-prev['빙엑스 선물']) >= 0 else '▼'} {fmt(abs(curr['빙엑스 선물']-prev['빙엑스 선물']))}</div>
    </div>
    """, unsafe_allow_html=True)

with summary_cols[4]:
    total_val = curr["총자산"] if curr["총자산"] != 0 else 1
    alloc_data = {
        "labels": ["김프차익", "OKX통합", "빙엑스 선물"],
        "values": [curr["김프차익"]/total_val*100, curr["OKX통합"]/total_val*100, curr["빙엑스 선물"]/total_val*100]
    }
    fig_pie = go.Figure(data=[go.Pie(labels=alloc_data["labels"], values=alloc_data["values"], hole=.7, 
                                    marker_colors=["#10B981", "#3B82F6", "#F59E0B"], sort=False,
                                    hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>")])

    fig_pie.update_layout(showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=150, paper_bgcolor='#171B26', plot_bgcolor='#171B26')
    st.markdown("<div class='metric-card'><div class='metric-label'>자산 비중</div></div>", unsafe_allow_html=True)
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

# --- 누적 손익 추이 차트 --- #
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
title_col, period_col = st.columns([8, 1])
with title_col:
    st.markdown("<h4 style='color:#E0E0E0;font-weight:600;margin:0;padding-top:5px;'>📈 누적 손익 추이</h4>", unsafe_allow_html=True)
with period_col:
    period = st.radio("", ["4H", "D", "W", "M"], horizontal=True, index=1, key="period_radio")

pdf = df.copy().set_index("시간").sort_index()
now = pdf.index.max()

resample_map = {'4H': '4h', 'D': 'D', 'W': 'W-SUN', 'M': 'ME'}
df_resampled = pdf.resample(resample_map[period]).last().dropna()

if is_usd:
    for c in ["총자산", "김프차익", "OKX통합", "빙엑스 선물"]:
        df_resampled[c] = df_resampled[c] / usdt_rate

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled["총자산"], mode='lines', name='TOTAL', line=dict(color='#A855F7', width=3), fill='tozeroy', fillcolor='rgba(168,85,247,0.1)', hovertemplate=f"<b>TOTAL</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled["김프차익"], mode='lines', name='KIMP', line=dict(color='#10B981', width=2), hovertemplate=f"<b>KIMP</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled["OKX통합"], mode='lines', name='OKX', line=dict(color='#3B82F6', width=2), hovertemplate=f"<b>OKX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))
fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled["빙엑스 선물"], mode='lines', name='BingX', line=dict(color='#F59E0B', width=2), hovertemplate=f"<b>BingX</b>: {currency_sym}%{{y:{fmt_hover}}}<extra></extra>"))

fig.update_layout(plot_bgcolor='#171B26', paper_bgcolor='#171B26', font=dict(color='#8B949E'), margin=dict(l=10, r=10, t=10, b=10), height=350, hovermode="x unified", hoverlabel=dict(bgcolor="#1E2433", bordercolor="#2A2E39", font=dict(color="#E0E0E0", size=13), namelength=-1), yaxis=dict(gridcolor='#2A2E39', tickprefix=currency_sym, tickformat=fmt_hover), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#E0E0E0")))

if period == "4H":
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10), tickformat="%m-%d %H:%M", gridcolor='#2A2E39')
else:
    fig.update_xaxes(gridcolor='#2A2E39') # Ensure gridcolor is applied for other periods too

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 포지션 현황 & 손익 내역 --- #
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
pos_col, pnl_col = st.columns(2)

with pos_col:
    st.markdown("<h4 style='color:#E0E0E0;font-weight:600;margin-bottom:12px;'>🎯 포지션 현황</h4>", unsafe_allow_html=True)
    show_pos = pos_df[pos_df["거래소"].isin(["Upbit", "Bybit", "BingX(선물)"])].copy()
    if not show_pos.empty:
        show_pos["방향"] = show_pos["방향"].replace({"SPOT": "LONG"})
        show_pos["종목"] = show_pos["종목"].str.replace(":USDT", " PERP", regex=False)
        # Streamlit의 st.dataframe을 사용하여 테이블 렌더링
        st.dataframe(show_pos, hide_index=True, use_container_width=True)
    else:
        st.markdown("""<div class="empty-state-container"><div class="empty-state-icon">🚫</div><div class="empty-state-text">현재 활성 포지션이 없습니다.</div></div>""", unsafe_allow_html=True)

with pnl_col:
    st.markdown("<h4 style='color:#E0E0E0;font-weight:600;margin-bottom:12px;'>📋 손익 내역</h4>", unsafe_allow_html=True)
    daily = df.copy().set_index("시간").sort_index().groupby(pd.Grouper(freq='D')).last()
    daily["일손익"] = daily["총자산"].diff().fillna(0)
    daily["누적손익"] = daily["총자산"] - df["총자산"].iloc[0]

    stat_cols = st.columns(4)
    pnl_vals = daily["일손익"]
    wins = (pnl_vals > 0).sum()
    total_days = (pnl_vals != 0).sum()
    
    # 수익률 색상 대비 개선을 위해 stat-card CSS를 사용하지 않고 직접 스타일 적용
    stat_cols[0].markdown(f"""
    <div class='stat-card'>
        <div class='stat-label'>총 손익</div>
        <div class='stat-value' style='color: {'#10B981' if pnl_vals.sum() >= 0 else '#EF4444'};'>{fmt_signed(pnl_vals.sum())}</div>
    </div>
    """, unsafe_allow_html=True)
    stat_cols[1].markdown(f"""
    <div class='stat-card'>
        <div class='stat-label'>승률</div>
        <div class='stat-value'>{wins / total_days * 100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    stat_cols[2].markdown(f"""
    <div class='stat-card'>
        <div class='stat-label'>최대 수익</div>
        <div class='stat-value' style='color: #10B981;'>{fmt_signed(pnl_vals.max())}</div>
    </div>
    """, unsafe_allow_html=True)
    stat_cols[3].markdown(f"""
    <div class='stat-card'>
        <div class='stat-label'>최대 손실</div>
        <div class='stat-value' style='color: #EF4444;'>{fmt_signed(pnl_vals.min())}</div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit의 st.dataframe을 사용하여 테이블 렌더링 (페이지네이션은 Streamlit 기본 기능으로 대체)
    st.dataframe(daily[daily["일손익"] != 0][["일손익", "누적손익"]].sort_index(ascending=False).style.format(fmt_signed).applymap(lambda x: 'color: #10B981' if not isinstance(x, str) and x >= 0 else ('color: #EF4444' if not isinstance(x, str) else '')), use_container_width=True, height=400)

# --- 자동 새로고침 --- #
components.html("<script>setTimeout(function(){window.parent.location.reload()}, 300000);</script>", height=0)
