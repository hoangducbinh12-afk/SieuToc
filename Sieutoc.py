import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN MOBILE CHUẨN ---
st.set_page_config(page_title="TUAN PHONG V15.0 REVOLUTION", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. HỆ THỐNG BÓNG ÂM DƯƠNG CHUẨN (120 TỌA ĐỘ) ---
BONG_DUONG = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
BONG_AM = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

def build_ma_tran_full_120(gdb_str):
    g_str = str(gdb_str).strip()
    if len(g_str) < 5: return [0]*120
    digits = [int(d) for d in g_str[-5:]]
    # 50 số tịnh tiến tiến
    tien = [[(d + step) % 10 for d in digits] for step in range(10)]
    # 70 số biến biến bóng âm dương
    bong = [digits]; curr = digits
    for i in range(13):
        curr = [BONG_DUONG[d] for d in curr] if i % 2 == 0 else [BONG_AM[d] for d in curr]
        bong.append(curr)
    res = [d for sub in tien for d in sub] + [d for sub in bong for d in sub]
    return res[:120]

def create_blank_station():
    return {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10,
        "bang_b_points": [{"dau":1,"duoi":1,"tong":1} for _ in range(120)],
        "last_gdb_full": "00000", "ky_quay": 1, "history": [],
        "ref_dau": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_duoi": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_tong": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {"MB": create_blank_station()}
if 'active_w' not in st.session_state:
    st.session_state.active_w = [25.0, 25.0, 25.0, 25.0]

# --- 3. THUẬT TOÁN HÌNH SIN & RANKING ---
def run_sinusoidal_ai(st_name):
    hist = st.session_state.multi_db[st_name]["history"]
    if len(hist) < 5: return [25.0]*4
    
    eng_keys = ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]
    raw_scores = []
    for k in eng_keys:
        path = [h[k] for h in hist[:10]]
        avg, std = np.mean(path), np.std(path)
        # Bắt đáy hình sin: Càng đen (>50) và càng nén (std thấp) càng ưu tiên
        val = 40.0 if (avg > 50 and std < 20) else (15.0 if avg < 20 else 25.0)
        raw_scores.append(val)
    
    total = sum(raw_scores)
    return [round((s/total)*100, 2) for s in raw_scores]

def calculate_master_v150(st_name):
    db = st.session_state.multi_db[st_name]
    last_gdb = db["last_gdb_full"]
    curr_n = int(last_gdb[-2:]) if len(last_gdb)>=2 else 0
    
    # Cập nhật trọng số ngay lập tức
    st.session_state.active_w = run_sinusoidal_ai(st_name)
    
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt_120 = build_ma_tran_full_120(last_gdb)
    
    # Engine 3: Tịnh tiến bóng (FIXED)
    pts_b = db["bang_b_points"]
    val_e3 = [0]*10
    if len(mt_120) == 120:
        for n in range(10):
            val_e3[n] = sum(pts_b[idx]["dau"] + pts_b[idx]["duoi"] for idx, v in enumerate(mt_120) if v == n)

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_gdb if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u] + val_e3[t]
        for m, k in [("ref_dau",str(curr_n//10)), ("ref_duoi",str(curr_n%10)), ("ref_tong",str((curr_n//10+curr_n%10)%10))]:
            if k in db[m]: e4[i] += db[m][k]["dau"][d] + db[m][k]["duoi"][u]

    def rk(scores, rev=False): return stats.rankdata(-scores if rev else scores, method='min')
    r1, r2, r3, r4 = rk(e1), rk(e2), rk(e3, True), rk(e4, True)
    
    w = st.session_state.active_w
    final_scores = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3]) / 100
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "R1":r1, "R2":r2, "R3":r3, "R4":r4, "TOTAL":final_scores})

def process_v150():
    st_name = st.session_state.current_station
    db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master_v150(st_name)
    
    db["history"].insert(0, {
        "Kỳ": int(db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats.rankdata(df_old["TOTAL"], method='min')[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    # 1. Nuôi điểm
    dv, duv, tv = n//10, n%10, (n//10+n%10)%10
    for i in range(10):
        db["dau"][i] = 0 if i==dv else db["dau"][i]+1
        db["duoi"][i] = 0 if i==duv else db["duoi"][i]+1
        db["tong"][i] = 0 if i==tv else db["tong"][i]+1

    # 2. Nuôi phản xạ
    if len(db["history"]) >= 2:
        c_num = int(db["history"][1]["Số"]); n_num = int(db["history"][0]["Số"])
        keys = [("ref_dau",str(c_num//10)), ("ref_duoi",str(c_num%10)), ("ref_tong",str((c_num//10+c_num%10)%10))]
        for m, k in keys:
            db[m][k]["dau"][n_num//10]+=1; db[m][k]["duoi"][n_num%10]+=1

    # 3. Nuôi tịnh tiến 120 (FIXED)
    mt_prev = build_ma_tran_full_120(db["last_gdb_full"])
    for idx, v in enumerate(mt_prev):
        db["bang_b_points"][idx]["dau"] = 0 if v==dv else db["bang_b_points"][idx]["dau"]+1
        db["bang_b_points"][idx]["duoi"] = 0 if v==duv else db["bang_b_points"][idx]["duoi"]+1

    db["last_gdb_full"], db["ky_quay"] = raw, db["ky_quay"]+1

# --- 4. GIAO DIỆN ---
st.title("🛡️ COMMANDER V15.0 REVOLUTION")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT", on_click=process_v150, type="primary", use_container_width=True)

df_m = calculate_master_v150(st.session_state.current_station)
t1, t2, t3 = st.tabs(["🎯 DÀN AI", "⚖️ ĐỐI TRỌNG SIN", "📋 NHẬT KÝ"])

with t1:
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN MỎNG (36 SỐ):**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN DÀY (51 SỐ):**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)
with t2:
    st.subheader("📊 Trọng số AI Hình Sin (Động)")
    st.table(pd.DataFrame({"Engine": ["E1", "E2", "E3", "E4"], "%": st.session_state.active_w}).set_index("Engine").T)
    st.download_button("💾 LƯU .JSON", json.dumps(st.session_state.multi_db), "DATA_V15.json", use_container_width=True)
with t3:
    if db["history"]:
        df_h = pd.DataFrame(db["history"])
        st.table(df_h[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
        st.line_chart(df_h["Rank_AI"])
