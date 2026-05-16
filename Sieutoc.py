import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN SÁNG CHUẨN MOBILE ---
st.set_page_config(page_title="TUAN PHONG V14.3 ULTRA", layout="wide")
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
GIAP_12 = {"TI":[0,12,24,36,48,60,72,84,96],"SUU":[1,13,25,37,49,61,73,85,97],"DAN":[2,14,26,38,50,62,74,86,98],"MAO":[3,15,27,39,51,63,75,87,99],"THIN":[4,16,28,40,52,64,76,88],"TY":[5,17,29,41,53,65,77,89],"NGO":[6,18,30,42,54,66,78,90],"MUI":[7,19,31,43,55,67,79,91],"THAN":[8,20,32,44,56,68,80,92],"DAU":[9,21,33,45,57,69,81,93],"TUAT":[10,22,34,46,58,70,82,94],"HOI":[11,23,35,47,59,71,83,95]}
BONG_DUONG = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}; BONG_AM = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

ROOT_DATA = {
    1:{"cham":[1,6,0,5,2,7,3,8,4,9],"dau":[1,6,0,5,4,9,2,7,3,8],"duoi":[1,6,2,7,0,5,4,9,3,8],"tong":[1,6,2,7,4,9,0,5,3,8],"hieu":[0,5,1,6,2,7,4,9,3,8]},
    2:{"cham":[2,7,1,6,3,8,4,9,0,5],"dau":[2,7,1,6,5,0,3,8,4,9],"duoi":[2,7,3,8,1,6,5,0,4,9],"tong":[2,7,3,8,5,0,1,6,4,9],"hieu":[0,5,2,7,1,6,3,8,4,9]},
    3:{"cham":[3,8,2,7,4,9,0,5,1,6],"dau":[3,8,2,7,6,1,4,9,5,0],"duoi":[3,8,4,9,2,7,6,1,5,0],"tong":[3,8,4,9,1,6,2,7,0,5],"hieu":[0,5,3,8,4,9,1,6,2,7]}
}

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
        "bo": [0]*15, "giap": [0]*12, "dang5": [0]*5, "cl4": [0]*4, "bt4": [0]*4,
        "d_cl": [0,0], "u_cl": [0,0], "t_cl": [0,0], "so_he": [0,0],
        "d_tb": [0,0], "u_tb": [0,0], "t_tb": [0,0], "h_tb": [0,0],
        "bang_b_points": [{"dau":1,"duoi":1,"tong":1,"hieu":1,"cham":1} for _ in range(120)],
        "last_gdb_full": "00000", "ky_quay": 1, "history": [], "use_root": True,
        "weights": [25.0, 25.0, 25.0, 25.0],
        "ref_dau": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15} for i in range(10)},
        "ref_duoi": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15} for i in range(10)},
        "ref_tong": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15} for i in range(10)},
        "ref_hieu": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15} for i in range(10)},
        "ref_bo": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15} for i in range(15)}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {"MB": create_blank_station(), "ST": create_blank_station()}
if 'current_station' not in st.session_state:
    st.session_state.current_station = "MB"

# --- ENGINE TÍNH TOÁN V14.3 (FIX INDEXERROR) ---
def get_rank_array_v143(scores, reverse=False):
    return stats.rankdata(scores if not reverse else -scores, method='min')

def calculate_master_v143(st_name, date_str):
    st_db = st.session_state.multi_db[st_name]
    last_gdb = st_db["last_gdb_full"]
    curr_n = int(last_gdb[-2:]) if len(str(last_gdb))>=2 else 0
    
    e1_raw, e2_raw, e3_raw, e4_raw = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    ma_tran_120 = build_ma_tran_120(last_gdb)
    
    # FIX INDEXERROR: Chỉ tính E3 khi ma trận đủ 120 tọa độ
    list_e3 = [{"d":0,"u":0,"t":0,"h":0,"c":0} for _ in range(10)]
    if len(ma_tran_120) == 120:
        pts_b = st_db["bang_b_points"]
        for n in range(10):
            d_p, u_p, t_p, h_p, c_p = 0, 0, 0, 0, 0
            for idx in range(120):
                if ma_tran_120[idx] == n:
                    d_p += pts_b[idx]["dau"]; u_p += pts_b[idx]["duoi"]
                    t_p += pts_b[idx]["tong"]; h_p += pts_b[idx]["hieu"]
                    c_p += pts_b[idx]["cham"]
            list_e3[n] = {"d":d_p, "u":u_p, "t":t_p, "h":h_p, "c":c_p}

    d_k, u_k = str(curr_n//10), str(curr_n%10)
    t_k, h_k = str((curr_n//10 + curr_n%10)%10), str((curr_n//10 - curr_n%10 + 10)%10)
    b_k = str(next((i for i, (k, v) in enumerate(BO_MAP.items()) if curr_n in v), 0))

    for i in range(100):
        d, u, t, h = i//10, i%10, (i//10+i%10)%10, (i//10-i%10+10)%10
        e1_raw[i] = st_db["dau"][d] + st_db["duoi"][u] + st_db["tong"][t] + st_db["hieu"][h] + st_db["cham"][d] + st_db["cham"][u]
        if st_db["use_root"]:
            for r_val in [get_root_val(date_str), get_root_val(str(st_db["ky_quay"]))]:
                if r_val in ROOT_DATA: e2_raw[i] += ROOT_DATA[r_val]["dau"].index(d) + ROOT_DATA[r_val]["duoi"].index(u)
        
        e3_raw[i] = list_e3[d]["d"] + list_e3[u]["u"] + list_e3[t]["t"] + list_e3[h]["h"] + list_e3[d]["c"] + list_e3[u]["c"]
        
        for m_name, k in [("ref_dau",d_k), ("ref_duoi",u_k), ("ref_tong",t_k), ("ref_hieu",h_k), ("ref_bo",b_k)]:
            if k in st_db.get(m_name, {}):
                m = st_db[m_name][k]
                e4_raw[i] += m["dau"][d] + m["duoi"][u] + m["tong"][t]

    r1, r2 = get_rank_array_v143(e1_raw, False), get_rank_array_v143(e2_raw, False)
    r3, r4 = get_rank_array_v143(e3_raw, True), get_rank_array_v143(e4_raw, True)
    df = pd.DataFrame({"SO": [f"{k:02d}" for k in range(100)], "R1":r1, "R2":r2, "R3":r3, "R4":r4})
    w = st_db["weights"]
    df["DIEM_TONG"] = (df["R1"]*w[0] + df["R2"]*w[1] + df["R3"]*w[2] + df["R4"]*w[3]) / 100
    return df

def process_v143():
    st_name = st.session_state.current_station
    st_db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master_v143(st_name, st.session_state.date_in)
    
    st_db["history"].insert(0, {
        "Kỳ": int(st_db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats.rankdata(df_old["DIEM_TONG"], method='min')[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    dv, duv, tv, hv = n//10, n%10, (n//10+n%10)%10, (n//10-n%10+10)%10
    for i in range(10):
        for k, v in [("dau",dv),("duoi",duv),("tong",tv),("hieu",hv)]: st_db[k][i] = 0 if i==v else st_db[k][i]+1
        st_db["cham"][i] = 0 if (i==dv or i==duv) else st_db["cham"][i]+1
    
    if len(st_db["history"]) >= 2:
        c_num = int(st_db["history"][1]["Số"]); n_num = int(st_db["history"][0]["Số"])
        dk, uk, tk, hk = str(c_num//10), str(c_num%10), str((c_num//10+c_num%10)%10), str((c_num//10-c_num%10+10)%10)
        bk = str(next((i for i, (k, v) in enumerate(BO_MAP.items()) if c_num in v), 0))
        dn, un, tn = n_num//10, n_num%10, (n_num//10+n_num%10)%10
        for m_name, k in [("ref_dau",dk), ("ref_duoi",uk), ("ref_tong",tk), ("ref_hieu",hk), ("ref_bo",bk)]:
            if k in st_db[m_name]: st_db[m_name][k]["dau"][dn]+=1; st_db[m_name][k]["duoi"][un]+=1; st_db[m_name][k]["tong"][tn]+=1

    ma_tran_prev = build_ma_tran_120(st_db["last_gdb_full"])
    if len(ma_tran_prev) == 120:
        for idx in range(120):
            val = ma_tran_prev[idx]
            for k, v in [("dau",dv),("duoi",duv),("tong",tv),("hieu",hv)]: st_db["bang_b_points"][idx][k] = 0 if val==v else st_db["bang_b_points"][idx][k]+1
            st_db["bang_b_points"][idx]["cham"] = 0 if (val==dv or val==duv) else st_db["bang_b_points"][idx]["cham"]+1

    st_db["last_gdb_full"], st_db["ky_quay"] = raw, st_db["ky_quay"]+1

# --- 4. GIAO DIỆN ---
st.title("🛡️ COMMANDER ULTRA V14.3")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2, c3 = st.columns([2,1,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: st.text_input("Ngày:", value=datetime.now().strftime("%d%m%Y"), key="date_in")
with c3: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT HỆ THỐNG", on_click=process_v143, type="primary", use_container_width=True)

df_m = calculate_master_v143(st.session_state.current_station, st.session_state.date_in)

t1, t2, t3 = st.tabs(["🎯 DÀN AI", "📊 ĐỐI TRỌNG", "📋 NHẬT KÝ"])
with t1:
    n1 = st.number_input("Số quân:", 1, 100, 51, step=1)
    danh_sach = df_m.sort_values("DIEM_TONG")["SO"].tolist()
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach[:n1])}</div>", unsafe_allow_html=True)
with t2:
    st.table(pd.DataFrame({"Engine": ["E1", "E2", "E3", "E4"], "Tỷ trọng (%)": [round(x,1) for x in db["weights"]]}).set_index("Engine").T)
    st.download_button("💾 LƯU DỮ LIỆU", json.dumps(st.session_state.multi_db), "DATA_V143.json", use_container_width=True)
with t3:
    if db["history"]:
        df_h = pd.DataFrame(db["history"])
        st.table(df_h[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
