streamlit
gspread
oauth2client
pandas
plotly
requests
ccxt
PyJWT

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import ccxt
import jwt
import uuid
import requests
import hmac
import hashlib
import base64
from datetime import datetime
import time
import pandas as pd

# ==========================================
# 1. API 키 설정
# ==========================================
UPBIT_ACCESS = 'inxeHLXi0oKQ74Ga6ppdxgC1JAvlkY4LNN4rhRHD'
UPBIT_SECRET = 'fdyGowyTM6TxD6ab1z7I9BYynYzE3WCfzIefzeyn'
BYBIT_KEY = 'XiogJO7AaizaAbSxUa'
BYBIT_SECRET = 'qa9arnqW7FFlKyI2ejCls94FFRZLjQI1JJZl'
OKX_KEY = '9c3f0132-67a8-48c0-8813-b53b631ec4ca'
OKX_SECRET = 'EAD312A95AED3F44481048092D133B83'
OKX_PW = 'TimProject123!'
BINGX_KEY = 'mLlBMSELwFEdoLsxlcGnjJWAL3vSjQn5c3vu63yBLjuRDgDqvJUXbMFYm3IIsZhrN8kW9OGRjcCvW7hh41TZcA'
BINGX_SECRET = 'LCXKWDo2ed77BvDD66sRKkpLRLSIH3NeLHSndX0YCgqq3gNllfZ7Mo8elIy99lJkH36E3o0wZCMzcugkuGfA'

# 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('google_key.json', scope)
client = gspread.authorize(creds)
db = client.open("TIM_Portfolio_DB")
sheet_main, sheet_pos = db.get_worksheet(0), db.get_worksheet(1)

def get_upbit_price(ticker):
    try: return requests.get(f"https://api.upbit.com/v1/ticker?markets={ticker}").json()[0]['trade_price']
    except: return 0

def fmt_krw(val): return f"₩{int(val):,}" if val != '-' else '-'
def fmt_usd(val): return f"${val:,.4f}" if val != '-' else '-'

def compress_old_data():
    try:
        all_data = sheet_main.get_all_values()
        if len(all_data) < 2: return

        df = pd.DataFrame(all_data[1:], columns=all_data[0])
        df['시간'] = pd.to_datetime(df['시간'])
        for c in ['김프차익', 'OKX통합', '빙엑스 선물', '총자산']:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        now        = pd.Timestamp.now()
        cutoff_7d  = now - pd.Timedelta(days=7)
        cutoff_30d = now - pd.Timedelta(days=30)

        recent = df[df['시간'] >= cutoff_7d].copy()
        mid = df[(df['시간'] >= cutoff_30d) & (df['시간'] < cutoff_7d)].copy()
        if not mid.empty:
            mid = mid.set_index('시간').resample('1h').last().dropna().reset_index()
        old = df[df['시간'] < cutoff_30d].copy()
        if not old.empty:
            old = old.set_index('시간').resample('D').last().dropna().reset_index()

        compressed = pd.concat([old, mid, recent]).sort_values('시간').reset_index(drop=True)
        compressed['시간'] = compressed['시간'].dt.strftime('%Y-%m-%d %H:%M:%S')
        for c in ['김프차익', 'OKX통합', '빙엑스 선물', '총자산']:
            compressed[c] = compressed[c].astype(int).astype(str)

        before_rows = len(all_data) - 1
        after_rows  = len(compressed)

        sheet_main.clear()
        sheet_main.append_row(['시간', '김프차익', 'OKX통합', '빙엑스 선물', '총자산'])
        sheet_main.append_rows(compressed.values.tolist())

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now_str}] 🗜️ 압축 완료: {before_rows}행 → {after_rows}행")

    except Exception as e:
        print(f"❌ 압축 에러: {e}")

def collect_data():
    try:
        usdt_krw = get_upbit_price("KRW-USDT")
        time.sleep(0.2)
        positions_data = []

        # ✅ 청산가 컬럼 추가
        header = ['거래소', '종목', '방향', '수량', '보유금액(₩)', '진입가', '현재가', '미실현 PNL(₩)', '청산가']

        # ── 1. 업비트 (BTC) ──────────────────────────
        payload = {'access_key': UPBIT_ACCESS, 'nonce': str(uuid.uuid4())}
        up_data = requests.get(
            "https://api.upbit.com/v1/accounts",
            headers={"Authorization": f"Bearer {jwt.encode(payload, UPBIT_SECRET)}"}
        ).json()
        up_krw_total = 0
        for b in up_data:
            curr, amt = b['currency'], float(b['balance']) + float(b['locked'])
            if curr == 'KRW':
                up_krw_total += amt
            elif curr == 'BTC' and amt > 0.0001:
                price = get_upbit_price(f"KRW-{curr}")
                up_krw_total += (amt * price)
                avg = float(b['avg_buy_price'])
                positions_data.append([
                    'Upbit', 'BTC', 'SPOT', round(amt, 4),
                    fmt_krw(amt * price), fmt_krw(avg), fmt_krw(price),
                    fmt_krw((price - avg) * amt),
                    '-'  # 현물은 청산가 없음
                ])

        # ── 2. 바이빗 (BTC 선물) ─────────────────────
        by = ccxt.bybit({'apiKey': BYBIT_KEY, 'secret': BYBIT_SECRET})
        by_usdt = by.fetch_balance()['total'].get('USDT', 0)
        kimp_total = up_krw_total + (by_usdt * usdt_krw)
        try:
            for p in by.fetch_positions():
                size = float(p.get('contracts', 0) or 0)
                if size > 0 and 'BTC' in p['symbol']:
                    sym      = p['symbol']
                    side     = p['side'].upper()
                    entry    = float(p.get('entryPrice', 0))
                    curr_p   = float(p.get('markPrice', 0))
                    upnl     = float(p.get('unrealizedPnl', 0))
                    # ✅ 청산가 추가
                    liq_price = float(p.get('liquidationPrice', 0) or 0)
                    positions_data.append([
                        'Bybit', sym, side, round(size, 4),
                        fmt_krw(size * curr_p * usdt_krw),
                        fmt_usd(entry), fmt_usd(curr_p),
                        fmt_krw(upnl * usdt_krw),
                        fmt_usd(liq_price) if liq_price > 0 else '-'  # ✅ 청산가
                    ])
        except Exception as e:
            print(f"바이빗 포지션 수집 에러: {e}")

        # ── 3. OKX (현물 + 시그널봇 선물) ────────────
        ok = ccxt.okx({'apiKey': OKX_KEY, 'secret': OKX_SECRET, 'password': OKX_PW})
        ok_bal     = ok.fetch_balance()
        ok_tickers = ok.fetch_tickers()

        ok_total_krw = 0
        for coin, amt in ok_bal['total'].items():
            if amt > 0:
                if coin == 'USDT':
                    ok_total_krw += amt * usdt_krw
                elif coin == 'BTC':
                    btc_price = ok_tickers.get('BTC/USDT', {}).get('last', 0)
                    ok_total_krw += amt * btc_price * usdt_krw
                elif coin != 'KRW':
                    sym = f"{coin}/USDT"
                    if sym in ok_tickers:
                        ok_total_krw += amt * ok_tickers[sym]['last'] * usdt_krw

        for coin, amt in ok_bal['total'].items():
            if amt > 0:
                if coin == 'USDT':
                    positions_data.append([
                        'OKX(현물)', 'USDT', 'CASH', round(amt, 2),
                        fmt_krw(amt * usdt_krw), '-', '-', '-', '-'
                    ])
                elif coin == 'BTC':
                    btc_price = ok_tickers.get('BTC/USDT', {}).get('last', 0)
                    positions_data.append([
                        'OKX(현물)', 'BTC', 'SPOT', round(amt, 4),
                        fmt_krw(amt * btc_price * usdt_krw),
                        '-', fmt_usd(btc_price), '-', '-'
                    ])
                elif coin != 'KRW':
                    sym = f"{coin}/USDT"
                    if sym in ok_tickers:
                        curr_p = ok_tickers[sym]['last']
                        positions_data.append([
                            'OKX(현물)', coin, 'SPOT', round(amt, 4),
                            fmt_krw(amt * curr_p * usdt_krw),
                            '-', fmt_usd(curr_p), '-', '-'
                        ])

        try:
            ok_pos_resp = ok.private_get_account_positions()
            if 'data' in ok_pos_resp:
                for p in ok_pos_resp['data']:
                    size = float(p.get('pos', 0))
                    if size != 0 and 'BTC' in p['instId']:
                        side    = "LONG" if size > 0 else "SHORT"
                        entry   = float(p.get('avgPx', 0))
                        curr_p  = float(p.get('lastPx', 0))
                        upnl    = float(p.get('upl', 0))
                        val_usd = abs(float(p.get('notionalUsd', 0)))
                        positions_data.append([
                            'OKX(선물)', p['instId'].split('-')[0], side, abs(size),
                            fmt_krw(val_usd * usdt_krw),
                            fmt_usd(entry), fmt_usd(curr_p),
                            fmt_krw(upnl * usdt_krw),
                            '-'
                        ])
        except Exception as e:
            print(f"OKX 선물 수집 에러: {e}")

        # ── 4. 빙엑스 (선물 계좌 및 포지션) ────────────────
        try:
            bx = ccxt.bingx({
                'apiKey': BINGX_KEY,
                'secret': BINGX_SECRET,
                'options': {'defaultType': 'swap'}
            })
            
            bx_bal = bx.fetch_balance()
            bx_usdt_total = bx_bal['total'].get('USDT', 0)
            bx_total_krw = bx_usdt_total * usdt_krw

            try:
                for p in bx.fetch_positions():
                    size = float(p.get('contracts', 0) or 0)
                    if size > 0:
                        sym    = p['symbol']
                        side   = p['side'].upper()
                        entry  = float(p.get('entryPrice', 0))
                        curr_p = float(p.get('markPrice', 0))
                        upnl   = float(p.get('unrealizedPnl', 0))
                        val_usd = float(p.get('notional', size * curr_p))
                        clean_sym = sym.split('/')[0] if '/' in sym else sym

                        positions_data.append([
                            'BingX(선물)', clean_sym, side, round(size, 4),
                            fmt_krw(val_usd * usdt_krw),
                            fmt_usd(entry), fmt_usd(curr_p),
                            fmt_krw(upnl * usdt_krw),
                            '-'
                        ])
            except Exception as e:
                print(f"빙엑스 선물 포지션 수집 에러: {e}")

            print(f"빙엑스 총자산(선물): ₩{int(bx_total_krw):,}")

        except Exception as e:
            print(f"❌ 빙엑스 에러: {e}")
            bx_total_krw = 0

        # ── 기록 ──────────────────────────────────────
        now       = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_all = int(kimp_total + ok_total_krw + bx_total_krw)
        sheet_main.append_row([now, int(kimp_total), int(ok_total_krw), int(bx_total_krw), total_all])
        sheet_pos.clear()
        sheet_pos.append_rows([header] + positions_data)
        print(f"[{now}] ✅ 동기화 완료! 총 자산: ₩{total_all:,} (김프: ₩{int(kimp_total):,} / OKX: ₩{int(ok_total_krw):,} / 빙엑스: ₩{int(bx_total_krw):,})")

    except Exception as e:
        print(f"❌ 전체 에러: {e}")

if __name__ == "__main__":
    run_count = 0
    while True:
        collect_data()
        run_count += 1
        if run_count % 288 == 0:
            compress_old_data()
        time.sleep(300)
