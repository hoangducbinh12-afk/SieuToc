import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN SÁNG CHUẨN MOBILE ---
st.set_page_config(page_title="TUAN PHONG V14.4 MASTER", layout="wide")
st.markdown("""
    <style>
    .main-box { 
        background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; 
        font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; 
        border: 2px solid #3b82f6; margin-bottom: 10px; line-height: 1.5; font-weight: 700; 
        text-align: center; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .stMetric { background: #f1f5f9; padding: 8px; border-radius: 8px; border-left: 5px solid #3b82f6; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. QUY LUẬT TOÁN HỌC ---
BO_MAP = {"00":[0,5,50,55],"01":[1,10,6,60,51,15,56,65],"02":[2,20,7,70,52,25,57,75],"03":[3,30,8,80,53,35,58,85],"04":[4,40,9,90,54,45,59,95],"11":[11,16,61,66],"12":[12,21,17,71,62,26,67,76],"13":[13,31,18,81,63,36,68,86],"14":[14,41,19,91,64,46,69,96],"22":[22,27,72,77],"23":[23,32,28,82,73,37,78,87],"24":[24,42,29,92,74,47,79,97],"33":[33,38,83,88],"34":[34,43,39,93,84,48,89,98],"44":[44,49,94,99]}
BONG_DUONG = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}; BONG_AM = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

def get_root_val(s):
    try:
        t = sum(int(x) for x in str(s) if x.isdigit())
        while t > 9: t = sum(int(x) for x in str(t))
        return t
    except: return 1

def build_ma_tran_120(gdb_str):
    g_str = str(gdb_str).strip()
    if not g_str or len(g_str) < 5: return []
    digits = [int(d) for d in g_str[-5:]]
    tien = [[(d + step) % 10 for d in digits] for step in range(10)]
    bong = [digits]; current = digits
    for i in range(9):
        current = [BONG_DUONG[d] for d in current] if i % 2 == 0 else [BONG_AM[d] for d in current]
        bong.append(current)
    return [item for sub in tien for item in sub] + [item for sub in bong for item in sub]

def create_blank_station():
    return {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10, "hieu": [0]*10, "cham": [0]*10,
        "bang_b_points": [{"dau":1,"duoi":1,"tong":1,"hieu":1,"cham":1} for _ in range(120)],
        "last_gdb_full": "00000", "ky_quay": 1, "history": [], "use_root": True,
        "weights": [25.0, 25.0, 25.0, 25.0],
        "ref_dau": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_duoi": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_tong": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_hieu": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_bo": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(15)}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {"MB": create_blank_station(), "ST": create_blank_station()}
if 'current_station' not in st.session_state:
    st.session_state.current_station = "MB"

def get_rank_array_v144(scores, reverse=False):
    # Dùng method='average' để Rank không bị trùng lắp quá nhiều khi điểm bằng nhau
    return stats.rankdata(-scores if reverse else scores, method='average')

# --- HÀM TÍNH TOÁN ENGINE V14.4 (FIX ENGINE 3) ---
def calculate_master_v144(st_name):
    st_db = st.session_state.multi_db[st_name]
    last_gdb = st_db["last_gdb_full"]
    curr_n = int(last_gdb[-2:]) if len(str(last_gdb))>=2 else 0
    
    e1_raw, e2_raw, e3_raw, e4_raw = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    ma_tran_120 = build_ma_tran_120(last_gdb)
    
    # 1. Tính toán điểm nền cho E3 (Tịnh tiến)
    list_e3 = [{"val":0} for _ in range(10)]
    if len(ma_tran_120) == 120:
        pts_b = st_db["bang_b_points"]
        for n in range(10):
            score = 0
            for idx in range(120):
                if ma_tran_120[idx] == n:
                    score += pts_b[idx]["dau"] + pts_b[idx]["duoi"] + pts_b[idx]["tong"]
            list_e3[n]["val"] = score

    # 2. Key phản xạ E4
    dk, uk, tk = str(curr_n//10), str(curr_n%10), str((curr_n//10+curr_n%10)%10)

    for i in range(100):
        d, u, t, h = i//10, i%10, (i//10+i%10)%10, (i//10-i%10+10)%10
        # E1: Khan
        e1_raw[i] = st_db["dau"][d] + st_db["duoi"][u] + st_db["tong"][t] + st_db["cham"][d] + st_db["cham"][u]
        # E2: GĐB Root (Tính toán nhanh)
        e2_raw[i] = get_root_val(last_gdb) + get_root_val(i)
        # E3: FIX GÁN ĐIỂM VÀO MA TRẬN
        e3_raw[i] = list_e3[d]["val"] + list_e3[u]["val"] + list_e3[t]["val"]
        # E4: Phản xạ
        for m_name, k in [("ref_dau",dk), ("ref_duoi",uk), ("ref_tong",tk)]:
            if k in st_db[m_name]:
                m = st_db[m_name][k]
                e4_raw[i] += m["dau"][d] + m["duoi"][u] + m["tong"][t]

    # Chuẩn hóa hạng
    r1 = get_rank_array_v144(e1_raw, False)
    r2 = get_rank_array_v144(e2_raw, False)
    r3 = get_rank_array_v144(e3_raw, True) # Điểm tịnh tiến cao là hạng tốt
    r4 = get_rank_array_v144(e4_raw, True) # Tần suất phản xạ cao là hạng tốt
    
    df = pd.DataFrame({"SO": [f"{k:02d}" for k in range(100)], "R1":r1, "R2":r2, "R3":r3, "R4":r4})
    w = st_db["weights"]
    df["DIEM_TONG"] = (df["R1"]*w[0] + df["R2"]*w[1] + df["R3"]*w[2] + df["R4"]*w[3]) / 100
    return df

def process_v144():
    st_name = st.session_state.current_station
    st_db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    
    df_old = calculate_master_v144(st_name)
    
    # Lưu Rank thực tế vào lịch sử
    st_db["history"].insert(0, {
        "Kỳ": int(st_db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats.rankdata(df_old["DIEM_TONG"], method='min')[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    # 1. Nuôi điểm khan
    dv, duv, tv = n//10, n%10, (n//10+n%10)%10
    for i in range(10):
        st_db["dau"][i] = 0 if i==dv else st_db["dau"][i]+1
        st_db["duoi"][i] = 0 if i==duv else st_db["duoi"][i]+1
        st_db["tong"][i] = 0 if i==tv else st_db["tong"][i]+1
        st_db["cham"][i] = 0 if (i==dv or i==duv) else st_db["cham"][i]+1
    
    # 2. Nuôi phản xạ
    if len(st_db["history"]) >= 2:
        c_num = int(st_db["history"][1]["Số"]); n_num = int(st_db["history"][0]["Số"])
        dk, uk, tk = str(c_num//10), str(c_num%10), str((c_num//10+c_num%10)%10)
        dn, un, tn = n_num//10, n_num%10, (n_num//10+n_num%10)%10
        for m, k in [("ref_dau",dk), ("ref_duoi",uk), ("ref_tong",tk)]:
            st_db[m][k]["dau"][dn]+=1; st_db[m][k]["duoi"][un]+=1; st_db[m][k]["tong"][tn]+=1

    # 3. Nuôi tịnh tiến Engine 3
    ma_tran_prev = build_ma_tran_120(st_db["last_gdb_full"])
    if len(ma_tran_prev) == 120:
        for idx in range(120):
            v = ma_tran_prev[idx]
            st_db["bang_b_points"][idx]["dau"] = 0 if v==dv else st_db["bang_b_points"][idx]["dau"]+1
            st_db["bang_b_points"][idx]["duoi"] = 0 if v==duv else st_db["bang_b_points"][idx]["duoi"]+1
            st_db["bang_b_points"][idx]["tong"] = 0 if v==tv else st_db["bang_b_points"][idx]["tong"]+1

    st_db["last_gdb_full"], st_db["ky_quay"] = raw, st_db["ky_quay"]+1

# --- GIAO DIỆN ---
st.title("🛡️ COMMANDER V14.4 MASTER")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT", on_click=process_v144, type="primary", use_container_width=True)

df_m = calculate_master_v144(st.session_state.current_station)
t1, t2 = st.tabs(["🎯 DÀN AI", "📋 NHẬT KÝ"])
with t1:
    danh_sach = df_m.sort_values("DIEM_TONG")["SO"].tolist()
    st.subheader("Dàn mỏng (36 số):")
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.subheader("Dàn dày (51 số):")
    st.markdown(f"<div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)
with t2:
    if db["history"]:
        st.table(pd.DataFrame(db["history"])[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
    st.download_button("💾 LƯU DỮ LIỆU", json.dumps(st.session_state.multi_db), "DATA_MASTER.json", use_container_width=True)
