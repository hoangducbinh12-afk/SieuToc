import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN MOBILE CHUẨN ---
st.set_page_config(page_title="TUAN PHONG V16.2 FINAL", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
    .stMetric { background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; }
</style>""", unsafe_allow_html=True)

# --- 2. HỆ THỐNG BÓNG & 8 BIẾN 50/50 ---
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
    res = [x for sub in tien for x in sub] + [x for sub in bong for x in sub]
    return res[:120]

def create_blank():
    return {
        "dau":[0]*10, "duoi":[0]*10, "tong":[0]*10, "last_gdb_full":"00000", "ky_quay":1, "history":[],
        "bang_b_points":[{"dau":1,"duoi":1} for _ in range(120)],
        "ref_dau":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)},
        "ref_duoi":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)},
        "weights": [25.0]*4
    }

if 'multi_db' not in st.session_state: st.session_state.multi_db = {"MB": create_blank()}

# --- 3. LOGIC AI MOMENTUM ---
def analyze_rhythm(history):
    if len(history) < 3: return {}
    recent = [int(h["Số"]) for h in history[:10]]
    attrs = [get_5050_attrs(n) for n in recent]
    bias = {}
    for k in ["D_CL","U_CL","T_CL","D_TB","U_TB","T_TB","HE","H_TB"]:
        seq = [a[k] for a in attrs]
        if seq[0] == seq[1]: bias[k] = seq[0] # Ưu tiên bệt
        elif len(seq)>=3 and seq[0] != seq[1] and seq[1] == seq[2]: bias[k] = seq[1] # Ưu tiên nhảy
    return bias

def get_rank(arr, rev=False):
    vals = np.array(arr)
    if rev: vals = -vals
    temp = vals.argsort()
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(vals)) + 1
    return ranks

def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    last_g = db["last_gdb_full"]
    curr_n = int(last_g[-2:]) if len(last_g)>=2 else 0
    bias = analyze_rhythm(db["history"])
    
    e1, e2, e3, e4, e5 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    val_e3 = [sum(db["bang_b_points"][idx]["dau"] for idx, v in enumerate(mt) if v == n) for n in range(10)]

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u]
        dk, uk = str(curr_n//10), str(curr_n%10)
        if dk in db["ref_dau"]: e4[i] += db["ref_dau"][dk]["d"][d] + db["ref_dau"][dk]["u"][u]
        
        at = get_5050_attrs(i)
        for k, v in bias.items():
            if at[k] == v: e5[i] += 15

    r1, r2, r3, r4 = get_rank(e1), get_rank(e2), get_rank(e3, True), get_rank(e4, True)
    final = (r1 + r2 + r3 + r4) / 4 - (e5 / 5)
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":final, "R1":r1, "R2":r2, "R3":r3, "R4":r4})

def process_v162():
    st_name = st.session_state.current_station
    db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master(st_name)
    
    db["history"].insert(0, {
        "Ngày": datetime.now().strftime("%d/%m"),
        "Kỳ": int(db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(get_rank(df_old["TOTAL"])[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    dv, duv, tv = n//10, n%10, (n//10+n%10)%10
    for i in range(10):
        db["dau"][i] = 0 if i==dv else db["dau"][i]+1
        db["duoi"][i] = 0 if i==duv else db["duoi"][i]+1
        db["tong"][i] = 0 if i==tv else db["tong"][i]+1
    
    mt_prev = build_mt_120(db["last_gdb_full"])
    for idx, v in enumerate(mt_prev):
        if idx < len(db["bang_b_points"]):
            db["bang_b_points"][idx]["dau"] = 0 if v==dv else db["bang_b_points"][idx]["dau"]+1
            
    if len(db["history"]) >= 2:
        c_n = int(db["history"][1]["Số"]); n_n = int(db["history"][0]["Số"])
        dk, uk = str(c_n//10), str(c_n%10)
        if dk in db["ref_dau"]: db["ref_dau"][dk]["d"][n_n//10]+=1
        if uk in db["ref_duoi"]: db["ref_duoi"][uk]["u"][n_n%10]+=1

    db["last_gdb_full"], db["ky_quay"] = raw, db["ky_quay"]+1

# --- 4. GIAO DIỆN ---
st.title("🛡️ COMMANDER V16.2 PRO")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT HỆ THỐNG", on_click=process_v162, type="primary", use_container_width=True)

df_m = calculate_master(st.session_state.current_station)
t1, t2, t3 = st.tabs(["🎯 DÀN AI", "📊 HIỆU QUẢ DÀN", "📋 NHẬT KÝ CHI TIẾT"])

with t1:
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN 36 SỐ:**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN 51 SỐ:**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)

with t2:
    if db["history"]:
        total = len(db["history"])
        w36 = sum(1 for x in db["history"] if x["Rank_AI"] <= 36)
        w51 = sum(1 for x in db["history"] if x["Rank_AI"] <= 51)
        c_a, c_b = st.columns(2)
        c_a.metric("Tỷ lệ Dàn 36", f"{w36}/{total}", f"{round(w36/total*100,1)}%")
        c_b.metric("Tỷ lệ Dàn 51", f"{w51}/{total}", f"{round(w51/total*100,1)}%")
    st.download_button("💾 LƯU DỮ LIỆU .JSON", json.dumps(st.session_state.multi_db), "DATA_PRO.json", use_container_width=True)

with t3:
    if db["history"]:
        st.table(pd.DataFrame(db["history"])[['Ngày', 'Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
