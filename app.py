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

    /* ── 라디오 버튼 (4H/D/W/M 및 손익 필터용) ── */
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
        color: #000000 !important;
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
        color: #ffffff !important;
    }

    /* ── pill-btn: KRW/USD / All/KIMP/OKX/빙엑스 HTML 버튼 ── */
    .pill-btn {
        display: inline-flex; align-items: center; justify-content: center;
        border-radius: 20px; padding: 4px 14px; font-size: 13px; font-weight: 600;
        cursor: pointer; border: 1px solid #3A3E4A; background: transparent;
        color: #8B949E; font-family: 'Pretendard', sans-serif;
        text-decoration: none; white-space: nowrap;
    }
    .pill-btn.active-green { background: #00E676 !important; border-color: #00E676 !important; color: #000 !important; }
    .pill-btn.active-red   { background: #FF5370 !important; border-color: #FF5370 !important; color: #fff !important; }
    </style>
""", unsafe_allow_html=True)

# ── JavaScript: pill 버튼 클릭 → query param 변경 (새 창 없이) ──
st.markdown("""
<script>
function setParam(key, val) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, val);
    window.history.replaceState({}, '', url);
    window.location.href = url.toString();  // same tab reload
}
</script>
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

def fmt(val):
    return f"${val/usdt_rate:,.2f}" if st.session_state['currency'] == 'USD' else f"₩{int(val):,}"
def fmt_signed(val):
    sign = "+" if val >= 0 else ""
    return f"{sign}${val/usdt_rate:,.2f}" if st.session_state['currency'] == 'USD' else f"{sign}₩{int(val):,}"
def delta_html(val):
    sym = "▲" if val >= 0 else "▼"
    css = "metric-delta-pos" if val >= 0 else "metric-delta-neg"
    return f'<div style="padding-bottom:8px;"><span class="{css}">{sym} {fmt(abs(val))}</span></div>'
def pct_html(pct):
    sign = "+" if pct >= 0 else ""
    css = "metric-pct-pos" if pct >= 0 else "metric-pct-neg"
    return f'<div class="{css}">{sign}{pct:.2f}%</div>'

is_usd = st.session_state['currency'] == 'USD'
currency_sym = "$" if is_usd else "₩"
fmt_hover = ",.2f" if is_usd else ",.0f"

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
    # 마지막 업데이트 HTML
    st.markdown(f"""
    <div style='display:flex; flex-direction:column; align-items:flex-end; gap:2px; padding-top:8px;'>
        <div style='color:#8B949E; font-size:12px;'>마지막 업데이트</div>
        <div style='color:#E0E0E0; font-size:14px; font-weight:600;'>{l_time}</div>
    </div>
    """, unsafe_allow_html=True)

    # KRW / USD — st.button으로 같은 창 전환
    c_krw, c_usd = st.columns(2)
    with c_krw:
        krw_type = "primary" if not is_usd else "secondary"
        if st.button("KRW", key="btn_krw", type=krw_type, use_container_width=True):
            st.session_state['currency'] = 'KRW'
            st.rerun()
    with c_usd:
        usd_type = "primary" if is_usd else "secondary"
        if st.button("USD", key="btn_usd", type=usd_type, use_container_width=True):
            st.session_state['currency'] = 'USD'
            st.rerun()

# st.button 스타일 덮어쓰기 — primary=초록, secondary=테두리만
st.markdown("""
<style>
/* primary 버튼 → 초록 pill */
div[data-testid="stButton"] button[kind="primary"] {
    background: #00E676 !important;
    color: #000 !important;
    border: 1px solid #00E676 !important;
    border-radius: 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 4px 14px !important;
    height: auto !important;
    min-height: 0 !important;
    line-height: 1.6 !important;
    box-shadow: none !important;
}
/* secondary 버튼 → 테두리 pill */
div[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    color: #8B949E !important;
    border: 1px solid #3A3E4A !important;
    border-radius: 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 4px 14px !important;
    height: auto !important;
    min-height: 0 !important;
    line-height: 1.6 !important;
    box-shadow: none !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.05) !important;
    color: #E0E0E0 !important;
    border-color: #8B949E !important;
}
/* 버튼 컨테이너 간격 제거 */
div[data-testid="stHorizontalBlock"] { gap: 4px !important; }
</style>
""", unsafe_allow_html=True)

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
# ── 차트 헤더
# 📌 "📈 누적 손익 추이  All KIMP OKX 빙엑스" 한 줄 왼쪽
#    "4H  D  W  M" 한 줄 오른쪽 끝
# → 전체를 순수 HTML 한 줄로 렌더링하고,
#   라디오 상태는 hidden st.radio로 관리
# ══════════════════════════════════════════════════
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)

# 실제 상태 관리용 hidden radio (화면엔 안 보임, session_state만 씀)
if 'chart_filter' not in st.session_state:
    st.session_state['chart_filter'] = 'All'
if 'period' not in st.session_state:
    st.session_state['period'] = 'D'

chart_filter = st.session_state['chart_filter']
period       = st.session_state['period']

filters  = ["All", "KIMP", "OKX", "빙엑스"]
periods  = ["4H", "D", "W", "M"]

def pill(label, active, color="green"):
    if active:
        bg = "#00E676" if color == "green" else "#FF5370"
        fc = "#000" if color == "green" else "#fff"
        style = f"background:{bg};border:1px solid {bg};color:{fc};"
    else:
        style = "background:transparent;border:1px solid #3A3E4A;color:#8B949E;"
    return (
        f"<span style='display:inline-flex;align-items:center;justify-content:center;"
        f"border-radius:20px;padding:4px 14px;font-size:13px;font-weight:600;"
        f"cursor:pointer;white-space:nowrap;{style}'>{label}</span>"
    )

filter_pills = " ".join(pill(f, f == chart_filter, "green") for f in filters)
period_pills = " ".join(pill(p, p == period, "red")   for p in periods)

# 한 줄 HTML: 왼쪽(제목+필터) | 오른쪽(기간)
st.markdown(f"""
<div style='display:flex; align-items:center; justify-content:space-between; width:100%;'>
    <div style='display:flex; align-items:center; gap:16px;'>
        <h4 style='color:#E0E0E0; font-weight:600; margin:0; white-space:nowrap;'>📈 누적 손익 추이</h4>
        <div style='display:flex; gap:6px; align-items:center;'>{filter_pills}</div>
    </div>
    <div style='display:flex; gap:6px; align-items:center;'>{period_pills}</div>
</div>
""", unsafe_allow_html=True)

# 클릭 감지용 hidden radio — 화면에서 완전히 숨김
st.markdown("""
<style>
div[data-testid="stRadio"].hidden-radio { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── 버튼 클릭 처리: components.html iframe으로 postMessage ──
# 대신 더 간단하게: 각 버튼을 st.button으로 처리 (HTML 위에 투명하게 올리기 어려움)
# → 실용적 해결: st.columns로 버튼 나열하되 CSS로 pill 모양 강제

st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

# filter 버튼 행
fc1, fc2, fc3, fc4, fsp, pc1, pc2, pc3, pc4 = st.columns([1,1,1,1, 5, 1,1,1,1])

with fc1:
    if st.button("All",  key="f_all",  use_container_width=True):
        st.session_state['chart_filter'] = 'All';  st.rerun()
with fc2:
    if st.button("KIMP", key="f_kimp", use_container_width=True):
        st.session_state['chart_filter'] = 'KIMP'; st.rerun()
with fc3:
    if st.button("OKX",  key="f_okx",  use_container_width=True):
        st.session_state['chart_filter'] = 'OKX';  st.rerun()
with fc4:
    if st.button("빙엑스", key="f_bx", use_container_width=True):
        st.session_state['chart_filter'] = '빙엑스'; st.rerun()
with pc1:
    if st.button("4H", key="p_4h", use_container_width=True):
        st.session_state['period'] = '4H'; st.rerun()
with pc2:
    if st.button("D",  key="p_d",  use_container_width=True):
        st.session_state['period'] = 'D';  st.rerun()
with pc3:
    if st.button("W",  key="p_w",  use_container_width=True):
        st.session_state['period'] = 'W';  st.rerun()
with pc4:
    if st.button("M",  key="p_m",  use_container_width=True):
        st.session_state['period'] = 'M';  st.rerun()

# 버튼 행 스타일: 선택된 것 초록/빨강, 나머지 테두리
st.markdown(f"""
<style>
/* filter 버튼 — 선택 초록 */
div[data-testid="stButton"]:has(button[data-testid="baseButton-secondary"]) button {{
    background: transparent !important; color: #8B949E !important;
    border: 1px solid #3A3E4A !important; border-radius: 20px !important;
    font-size: 13px !important; font-weight: 600 !important;
    padding: 3px 0 !important; height: auto !important;
    min-height: 0 !important; line-height: 1.6 !important; box-shadow: none !important;
}}
/* 선택된 filter — 초록 */
{"".join([
    f"div[data-testid='stButton']:has(button[key='f_{k}']) button {{ background: #00E676 !important; color: #000 !important; border-color: #00E676 !important; }}"
    for k in (['all'] if chart_filter=='All' else ['kimp'] if chart_filter=='KIMP' else ['okx'] if chart_filter=='OKX' else ['bx'])
])}
/* 선택된 period — 빨강 */
{"".join([
    f"div[data-testid='stButton']:has(button[key='p_{k}']) button {{ background: #FF5370 !important; color: #fff !important; border-color: #FF5370 !important; }}"
    for k in (['4h'] if period=='4H' else ['d'] if period=='D' else ['w'] if period=='W' else ['m'])
])}
/* 버튼 행 상단 여백 제거 */
div[data-testid="stHorizontalBlock"] {{ margin-top: -48px !important; }}
</style>
""", unsafe_allow_html=True)

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
st.markdown("<h4 style='color:#E0E0E0; font-weight:600; margin-bottom:12px;'>🎯 포지션 현황</h4>", unsafe_allow_html=True)
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
st.markdown("<h4 style='color:#E0E0E0; font-weight:600; margin-bottom:12px;'>📋 손익 내역</h4>", unsafe_allow_html=True)

if not df.empty:
    daily = df.copy().set_index('시간').sort_index()
    daily = daily.groupby(daily.index.date).last()
    daily.index = pd.to_datetime(daily.index)

    daily['일손익_총']   = daily['총자산'].diff().fillna(0)
    daily['일손익_김프'] = daily['김프차익'].diff().fillna(0)
    daily['일손익_OKX']  = daily['OKX통합'].diff().fillna(0)
    daily['일손익_BX']   = daily['빙엑스 현물DCA'].diff().fillna(0)

    st.markdown('<span class="marker"></span>', unsafe_allow_html=True)
    pnl_filter = st.radio(
        "", ["전체", "KIMP", "OKX", "빙엑스"],
        horizontal=True, label_visibility="collapsed", key="pnl_filter_radio"
    )

    if pnl_filter == "KIMP":   pnl_col, cum_col = '일손익_김프', '김프차익'
    elif pnl_filter == "OKX":  pnl_col, cum_col = '일손익_OKX',  'OKX통합'
    elif pnl_filter == "빙엑스": pnl_col, cum_col = '일손익_BX', '빙엑스 현물DCA'
    else:                       pnl_col, cum_col = '일손익_총',   '총자산'

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
                is_deposit  = tr['유형'] == '입금'
                badge_color = "#3B82F6" if is_deposit else "#FFAA00"
                badge_bg    = "rgba(59,130,246,0.15)" if is_deposit else "rgba(255,170,0,0.15)"
                badge_text  = f"입금 {fmt(tr['금액'])}" if is_deposit else f"출금 {fmt(tr['금액'])}"
                memo        = tr.get('메모', '')
                memo_badge  = f"<span style='color:#8B949E;font-size:11px;margin-left:4px;'>{memo}</span>" if memo else ""
                rows_html += (
                    f"<tr class='transfer-row'><td>{date.strftime('%Y-%m-%d')} "
                    f"<span style='background:{badge_bg};color:{badge_color};font-size:11px;padding:1px 6px;border-radius:3px;'>{badge_text}</span>"
                    f"{memo_badge}</td><td style='color:#2A2E39;'>—</td><td style='color:#2A2E39;'>—</td></tr>"
                )
        rows_html += (
            f"<tr><td>{date.strftime('%Y-%m-%d')}</td>"
            f"<td class='{d_cls}'>{fmt_signed(d_val)}</td>"
            f"<td class='{c_cls}'>{fmt_signed(c_val)}</td></tr>"
        )

    st.markdown(
        "<div style='background:#171B26;border:1px solid #2A2E39;border-radius:8px;padding:0 4px;max-height:400px;overflow-y:auto;'>"
        "<table class='pnl-table'><thead><tr><th>날짜</th><th>일 손익</th><th>누적 손익</th></tr></thead>"
        "<tbody>" + rows_html + "</tbody></table></div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

# ── 5분마다 브라우저 자동 새로고침 ──
components.html(
    "<script>setTimeout(function(){ window.location.reload(); }, 300000);</script>",
    height=0
)
