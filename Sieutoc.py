import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN ---
st.set_page_config(page_title="TUAN PHONG V16.7 FULL", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT & HÀM HỖ TRỢ ---
B_D = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
B_A = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_5050_attrs(n):
    d, u = n // 10, n % 10
    t, h = (d + u) % 10, (d - u + 10) % 10
    return {
        "D_CL": "Chẵn" if d % 2 == 0 else "Lẻ", "U_CL": "Chẵn" if u % 2 == 0 else "Lẻ",
        "T_CL": "Chẵn" if t % 2 == 0 else "Lẻ", "D_TB": "To" if d >= 5 else "Bé",
        "U_TB": "To" if u >= 5 else "Bé", "T_TB": "To" if t >= 5 else "Bé",
        "HE": "Thường" if n in SO_THUONG else "HệKép", "H_TB": "To" if h >= 5 else "Bé"
    }

def build_mt_120(g):
    g_str = str(g).strip()
    if len(g_str) < 5: return [0]*120
    dts = [int(x) for x in g_str[-5:]]
    tien = [[(d + s) % 10 for d in dts] for s in range(10)]
    bong = [dts]; c = dts
    for i in range(14):
        c = [B_D[x] for x in c] if i%2==0 else [B_A[x] for x in c]
        bong.append(c)
    return ([x for sub in tien for x in sub] + [x for sub in bong for x in sub])[:120]

def create_blank():
    return {
        "dau":[0]*10, "duoi":[0]*10, "tong":[0]*10, "last_gdb_full":"00000", "ky_quay":1, "history":[],
        "bang_b_points":[{"dau":1} for _ in range(120)],
        "ref_dau":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)},
        "ref_duoi":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)},
        "weights": [25.0, 25.0, 25.0, 25.0]
    }

# --- 3. CORE ENGINE (BẢN 15.2) ---
def stats_rank(arr, rev=False):
    vals = np.array(arr)
    if rev: vals = -vals
    return np.argsort(np.argsort(vals)) + 1

def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    last_g = db.get("last_gdb_full", "00000")
    curr_n = int(last_g[-2:]) if len(last_g)>=2 else 0
    
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    val_e3 = [sum(db["bang_b_points"][idx].get("dau", 1) for idx, v in enumerate(mt) if v == n) for n in range(10)]

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u]
        dk, uk = str(curr_n//10), str(curr_n%10)
        if dk in db.get("ref_dau", {}): e4[i] += db["ref_dau"][dk]["d"][d]
        if uk in db.get("ref_duoi", {}): e4[i] += db["ref_duoi"][uk]["u"][u]

    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e3, True), stats_rank(e4, True)
    w = db.get("weights", [25.0]*4)
    total = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3]) / 100
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":total, "R1":r1, "R2":r2, "R3":r3, "R4":r4})

def process_v167():
    st_name = st.session_state.current_station
    db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    day_val = st.session_state.day_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master(st_name)
    
    db["history"].insert(0, {
        "Ngày": day_val, "Kỳ": int(db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats_rank(df_old["TOTAL"])[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    dv, duv = n//10, n%10
    for i in range(10):
        db["dau"][i] = 0 if i==dv else db["dau"][i]+1
        db["duoi"][i] = 0 if i==duv else db["duoi"][i]+1
        db["tong"][i] = 0 if i==((dv+duv)%10) else db["tong"][i]+1
    
    mt_prev = build_mt_120(db["last_gdb_full"])
    for idx, v in enumerate(mt_prev):
        if idx < len(db["bang_b_points"]):
            db["bang_b_points"][idx]["dau"] = 0 if v==dv else db["bang_b_points"][idx].get("dau", 0)+1

    db["last_gdb_full"], db["ky_quay"] = raw, db["ky_quay"]+1

# --- 4. GIAO DIỆN CHÍNH ---
if 'multi_db' not in st.session_state: st.session_state.multi_db = {"MB": create_blank()}

with st.sidebar:
    st.header("📂 HỆ THỐNG FILE")
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    
    # NÚT LOAD FILE ĐÂY MÀY ƠI!
    up = st.file_uploader("Nạp dữ liệu .JSON", type="json")
    if up:
        if st.button("✅ XÁC NHẬN NẠP FILE"):
            st.session_state.multi_db = json.load(up)
            st.rerun()
            
    if st.button("🔴 RESET TOÀN BỘ"):
        st.session_state.clear()
        st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
col1, col2, col3 = st.columns([1,2,1])
with col1: st.text_input("Ngày:", value=datetime.now().strftime("%d/%m"), key="day_in")
with col2: st.text_input("GĐB Vừa Ra:", value=db.get("last_gdb_full", "00000"), key="gdb_in")
with col3: db["ky_quay"] = st.number_input("Kỳ:", value=int(db.get("ky_quay", 1)), step=1)

st.button("🚀 CẬP NHẬT & SOI DÀN", on_click=process_v167, type="primary", use_container_width=True)

df_m = calculate_master(st.session_state.current_station)
t1, t2, t3, t4 = st.tabs(["🎯 DÀN AI", "⚖️ ĐỐI TRỌNG", "📊 NHẬT KÝ", "🔍 BIẾN 50/50"])

with t1:
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN 36 SỐ:**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN 51 SỐ:**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)

with t2:
    st.subheader("⚖️ Điều chỉnh Đối trọng (%)")
    w = db.get("weights", [25.0, 25.0, 25.0, 25.0])
    cw1, cw2, cw3, cw4 = st.columns(4)
    db["weights"][0] = cw1.number_input("E1 (Khan)", 0.0, 100.0, float(w[0]))
    db["weights"][1] = cw2.number_input("E2 (GĐB)", 0.0, 100.0, float(w[1]))
    db["weights"][2] = cw3.number_input("E3 (Tịnh)", 0.0, 100.0, float(w[2]))
    db["weights"][3] = cw4.number_input("E4 (Phản)", 0.0, 100.0, float(w[3]))
    
    st.divider()
    st.download_button("💾 LƯU FILE .JSON VỀ MÁY", json.dumps(st.session_state.multi_db), "DATA_TUANPHONG.json", use_container_width=True)

with t3:
    if db["history"]:
        df_h = pd.DataFrame(db["history"])
        cols = [c for c in ['Ngày', 'Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4'] if c in df_h.columns]
        st.table(df_h[cols])

with t4:
    if db["history"]:
        recent_nums = [int(h["Số"]) for h in db["history"][:10]]
        df_50 = pd.DataFrame([get_5050_attrs(n) for n in recent_nums])
        df_50.index = [h["Kỳ"] for h in db["history"][:10]]
        st.table(df_50)
