import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats # Để tính toán chuẩn hóa Rank

# --- 1. CẤU HÌNH MOBILE SIÊU TINH GỌN ---
st.set_page_config(page_title="TUAN PHONG V14.0 ULTRA", layout="wide")
st.markdown("""
    <style>
    .main-box { 
        background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; 
        font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; 
        border: 2px solid #3b82f6; margin-bottom: 10px; line-height: 1.5; font-weight: 700; 
        text-align: center; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .stMetric { background: #f1f5f9; padding: 8px; border-radius: 8px; border-left: 5px solid #3b82f6; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HỆ THỐNG QUY LUẬT ---
BO_MAP = {"00":[0,5,50,55],"01":[1,10,6,60,51,15,56,65],"02":[2,20,7,70,52,25,57,75],"03":[3,30,8,80,53,35,58,85],"04":[4,40,9,90,54,45,59,95],"11":[11,16,61,66],"12":[12,21,17,71,62,26,67,76],"13":[13,31,18,81,63,36,68,86],"14":[14,41,19,91,64,46,69,96],"22":[22,27,72,77],"23":[23,32,28,82,73,37,78,87],"24":[24,42,29,92,74,47,79,97],"33":[33,38,83,88],"34":[34,43,39,93,84,48,89,98],"44":[44,49,94,99]}
GIAP_12 = {"TI":[0,12,24,36,48,60,72,84,96],"SUU":[1,13,25,37,49,61,73,85,97],"DAN":[2,14,26,38,50,62,74,86,98],"MAO":[3,15,27,39,51,63,75,87,99],"THIN":[4,16,28,40,52,64,76,88],"TY":[5,17,29,41,53,65,77,89],"NGO":[6,18,30,42,54,66,78,90],"MUI":[7,19,31,43,55,67,79,91],"THAN":[8,20,32,44,56,68,80,92],"DAU":[9,21,33,45,57,69,81,93],"TUAT":[10,22,34,46,58,70,82,94],"HOI":[11,23,35,47,59,71,83,95]}
BONG_DUONG = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}; BONG_AM = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_bo_idx(n):
    for i, (k, v) in enumerate(BO_MAP.items()):
        if n in v: return i
    return 0

def find_idx_universal(n, mapping):
    for i, nums in enumerate(mapping.values()):
        if n in nums: return i
    return 0

def build_bang_a(gdb_str):
    if not gdb_str or len(gdb_str) < 5: return []
    digits = [int(d) for d in gdb_str[-5:]]
    tien = [[(d + step) % 10 for d in digits] for step in range(10)]
    bong = [digits]; current = digits
    for i in range(9):
        current = [BONG_DUONG[d] for d in current] if i % 2 == 0 else [BONG_AM[d] for d in current]
        bong.append(current)
    return [item for sub in tien for item in sub] + [item for sub in bong for item in sub]

# --- 3. KHỞI TẠO BỘ NHỚ ---
def create_blank_station():
    return {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10, "hieu": [0]*10, "cham": [0]*10,
        "bo": [0]*15, "giap": [0]*12, "dang5": [0]*5, "cl4": [0]*4, "bt4": [0]*4,
        "d_cl": [0,0], "u_cl": [0,0], "t_cl": [0,0], "so_he": [0,0],
        "d_tb": [0,0], "u_tb": [0,0], "t_tb": [0,0], "h_tb": [0,0],
        "bang_b_points": [{"dau":1,"duoi":1,"tong":1,"hieu":1,"cham":1} for _ in range(120)],
        "last_gdb_full": "00000", "ky_quay": 1, "history": [], "use_root": True,
        "weights": [25.0, 25.0, 25.0, 25.0],
        "ref_dau": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(10)},
        "ref_duoi": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(10)},
        "ref_tong": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(10)},
        "ref_hieu": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(10)},
        "ref_bo": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(15)},
        "ref_cham": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10,"hieu":[0]*10,"bo":[0]*15,"cham":[0]*10} for i in range(10)}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {"MB": create_blank_station(), "BINH_DUONG": create_blank_station()}
if 'current_station' not in st.session_state:
    st.session_state.current_station = "MB"

# --- 4. BỘ NÃO PHẢN XẠ 6 NHÁNH (THÊM CHẠM) ---
def rebuild_reflex_v140(st_name):
    st_db = st.session_state.multi_db[st_name]
    blank = create_blank_station()
    for k in ["ref_dau", "ref_duoi", "ref_tong", "ref_hieu", "ref_bo", "ref_cham"]:
        st_db[k] = blank[k]
    
    if len(st_db["history"]) < 2: return
    hist = st_db["history"][::-1]
    for k in range(len(hist)-1):
        c, n = int(hist[k]["Số"]), int(hist[k+1]["Số"])
        attrs_c = {"ref_dau":str(c//10), "ref_duoi":str(c%10), "ref_tong":str((c//10+c%10)%10), 
                   "ref_hieu":str((c//10-c%10+10)%10), "ref_bo":str(get_bo_idx(c)), "ref_cham": [str(c//10), str(c%10)]}
        d_n, u_n, t_n, h_n, b_n = n//10, n%10, (n//10+n%10)%10, (n//10-n%10+10)%10, get_bo_idx(n)
        
        for mat_key, val_c in attrs_c.items():
            vals = val_c if isinstance(val_c, list) else [val_c]
            for v in vals:
                if v in st_db[mat_key]:
                    m = st_db[mat_key][v]
                    m["dau"][d_n]+=1; m["duoi"][u_n]+=1; m["tong"][t_n]+=1; m["hieu"][h_n]+=1; m["bo"][b_n]+=1
                    m["cham"][d_n]+=1; m["cham"][u_n]+=1

# --- 5. HỆ THỐNG TÍNH TOÁN CHUẨN HÓA RANK (SIÊU QUAN TRỌNG) ---
def get_rank_array(scores, reverse=False):
    # Chuyển đổi điểm số sang thứ hạng từ 1-100
    return stats.rankdata(scores if not reverse else -scores, method='min')

def calculate_master_v140(st_name):
    st_db = st.session_state.multi_db[st_name]
    last_gdb = st_db["last_gdb_full"]
    curr_n = int(last_gdb[-2:]) if len(last_gdb)>=2 else 0
    rebuild_reflex_v140(st_name)
    
    # Chuẩn bị keys phản xạ
    keys = {"d":str(curr_n//10), "u":str(curr_n%10), "t":str((curr_n//10+curr_n%10)%10), 
            "h":str((curr_n//10-curr_n%10+10)%10), "b":str(get_bo_idx(curr_n)), "c":[str(curr_n//10), str(curr_n%10)]}

    e1_raw, e2_raw, e3_raw, e4_raw = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    all_a_old = build_bang_a(last_gdb)
    
    # Bảng tịnh tiến App 3
    list_c = []
    if len(all_a_old)==120:
        for n in range(10):
            row = {"da":0,"du":0,"to":0,"hi":0,"ch":0}
            for i in range(120):
                if all_a_old[i]==n:
                    p = st_db["bang_b_points"][i]
                    row["da"]+=p["dau"]; row["du"]+=p["duoi"]; row["to"]+=p["tong"]; row["hi"]+=p["hieu"]; row["ch"]+=p["cham"]
            list_c.append(row)

    for i in range(100):
        d, u, t, h, b = i//10, i%10, (i//10+i%10)%10, (i//10-i%10+10)%10, get_bo_idx(i)
        
        # E1: Khan
        e1_raw[i] = st_db["dau"][d] + st_db["duoi"][u] + st_db["tong"][t] + st_db["hieu"][h] + \
                    ((st_db["cham"][d]*2) if d==u else (st_db["cham"][d]+st_db["cham"][u])) + \
                    st_db["bo"][b] + st_db["giap"][find_idx_universal(i, GIAP_12)] + st_db["so_he"][1 if i not in SO_THUONG else 0]
        
        # E2: Root
        if st_db["use_root"]:
            for r in [get_root_val(st.session_state.date_in), get_root_val(str(st_db["ky_quay"])), get_root_val(last_gdb)]:
                if r in ROOT_DATA:
                    e2_raw[i] += ROOT_DATA[r]["dau"].index(d) + ROOT_DATA[r]["duoi"].index(u) + ROOT_DATA[r]["tong"].index(t)
        
        # E3: Tịnh Tiến
        if len(list_c)==10:
            e3_raw[i] = list_c[d]["da"] + list_c[u]["du"] + list_c[t]["to"] + list_c[h]["hi"] + (list_c[d]["ch"]+list_c[u]["ch"])
            
        # E4: Phản xạ 6 nhánh
        sc_e4 = 0
        for mk, k in [("ref_dau",keys["d"]), ("ref_duoi",keys["u"]), ("ref_tong",keys["t"]), ("ref_hieu",keys["h"]), ("ref_bo",keys["b"])]:
            m = st_db[mk].get(k, {})
            if m: sc_e4 += m["dau"][d] + m["duoi"][u] + m["tong"][t] + m["bo"][b]
        for ck in keys["c"]:
            m = st_db["ref_cham"].get(ck, {})
            if m: sc_e4 += m["cham"][d] + m["cham"][u]
        e4_raw[i] = sc_e4

    # --- CHUẨN HÓA BƯỚC CUỐI ---
    # Chuyển mọi Engine về thang Rank 1-100 (Cùng hệ quy chiếu)
    r1 = get_rank_array(e1_raw, reverse=False)
    r2 = get_rank_array(e2_raw, reverse=False)
    r3 = get_rank_array(e3_raw, reverse=True) # E3 ưu tiên điểm cao
    r4 = get_rank_array(e4_raw, reverse=True) # E4 ưu tiên tần suất cao
    
    df = pd.DataFrame({"SO": [f"{k:02d}" for k in range(100)], "R1": r1, "R2": r2, "R3": r3, "R4": r4})
    w = st_db["weights"]
    # Điểm tổng là trung bình cộng có trọng số của các thứ hạng
    df["DIEM_TONG"] = (df["R1"]*w[0] + df["R2"]*w[1] + df["R3"]*w[2] + df["R4"]*w[3]) / 100
    return df

def find_rank_unique_v140(df, target, col, asc=True):
    temp = df[['SO', col]].sort_values(by=[col, 'SO'], ascending=[asc, True]).reset_index(drop=True)
    match = temp[temp['SO'] == target].index
    return int(match[0]) + 1 if len(match) > 0 else 50

def update_ai_weights_momentum(st_name):
    st_db = st.session_state.multi_db[st_name]
    if len(st_db["history"]) < 3: return [25.0]*4
    recent = st_db["history"][0]
    new_w = [20.0, 20.0, 20.0, 20.0]
    
    # Engine nào vừa nổ hạng < 15 thì chiếm ngay 40% trọng số (Momentum)
    hot_engine = None
    for i in range(4):
        if recent.get(f"Rank_E{i+1}", 100) <= 15:
            hot_engine = i
            break
    
    if hot_engine is not None:
        new_w[hot_engine] = 40.0
        # Chia đều 60% còn lại cho 3 thằng kia
        rem = 60.0 / 3
        for i in range(4):
            if i != hot_engine: new_w[i] = rem
    else:
        new_w = [25.0]*4
    return new_w

# --- 6. XỬ LÝ CẬP NHẬT ---
def process_v140():
    st_name = st.session_state.current_station
    st_db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master_v140(st_name)
    
    # Lưu lịch sử với chuẩn Rank mới
    st_db["history"].insert(0, {
        "Kỳ": int(st_db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": find_rank_unique_v140(df_old, target, "DIEM_TONG"),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    # Nuôi điểm
    dv, duv, tv, hv = n//10, n%10, (n//10+n%10)%10, (n//10-n%10+10)%10
    for i in range(10):
        st_db["dau"][i]=0 if i==dv else st_db["dau"][i]+1
        st_db["duoi"][i]=0 if i==duv else st_db["duoi"][i]+1
        st_db["tong"][i]=0 if i==tv else st_db["tong"][i]+1
        st_db["hieu"][i]=0 if i==hv else st_db["hieu"][i]+1
        st_db["cham"][i]=0 if (i==dv or i==duv) else st_db["cham"][i]+1
    
    # Nuôi tịnh tiến
    all_a = build_bang_a(st_db["last_gdb_full"])
    if len(all_a)==120:
        for i in range(120):
            val = all_a[i]; p = st_db["bang_b_points"][i]
            for k, v in [("dau",dv),("duoi",duv),("tong",tv),("hieu",hv)]: p[k]=0 if val==v else p[k]+1
            p["cham"]=0 if val in [dv,duv] else p["cham"]+1

    st_db["last_gdb_full"], st_db["ky_quay"] = raw, st_db["ky_quay"]+1
    st_db["weights"] = update_ai_weights_momentum(st_name)

# --- 7. GIAO DIỆN ---
st.title("🛡️ COMMANDER ULTRA V14.0")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up: 
        if st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2, c3 = st.columns([2,1,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: st.text_input("Ngày:", datetime.now().strftime("%d%m%Y"), key="date_in")
with c3: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT HỆ THỐNG", on_click=process_v140, type="primary", use_container_width=True)

df_m = calculate_master_v140(st.session_state.current_station)
t1, t2, t3, t4 = st.tabs(["🎯 DÀN AI", "📊 ĐỐI TRỌNG", "📋 NHẬT KÝ", "🧠 PHẢN XẠ"])

with t1:
    n1 = st.number_input("Dàn mỏng:", 1, 100, 36, step=1)
    danh_sach = df_m.sort_values("DIEM_TONG")["SO"].tolist()
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach[:n1])}</div>", unsafe_allow_html=True)
    st.write(f"Dàn tiêu chuẩn (51 số):")
    st.markdown(f"<div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)

with t2:
    st.table(pd.DataFrame({"Bộ máy": ["E1 (Khan)", "E2 (Root)", "E3 (Tịnh Tiến)", "E4 (Phản Xạ)"], "Tỷ trọng (%)": [round(x,1) for x in db["weights"]]}).set_index("Bộ máy").T)
    st.download_button("💾 LƯU DỮ LIỆU", json.dumps(st.session_state.multi_db), "DATA_V14.json", use_container_width=True)

with t3:
    if db["history"]:
        df_h = pd.DataFrame(db["history"])
        st.table(df_h[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
        rks = df_h["Rank_AI"].tolist()
        gs = [sum(1 for r in rks if 1<=r<=10), sum(1 for r in rks if 11<=r<=39), sum(1 for r in rks if 40<=r<=59), sum(1 for r in rks if 60<=r<=100)]
        st.table(pd.DataFrame({"Hạng": ["1-10","11-39","40-59","Trượt"], "Lần": gs, "%": [f"{(x/len(rks))*100:.1f}%" for x in gs]}))

with t4:
    last_num = int(db["last_gdb_full"][-2:]) if len(db["last_gdb_full"])>=2 else 0
    st.write(f"Phản xạ sau con số: {last_num:02d}")
    sel = st.selectbox("Nhánh:", ["Đầu", "Đuôi", "Tổng", "Hiệu", "Bộ", "Chạm"])
    maps = {"Đầu":"ref_dau", "Đuôi":"ref_duoi", "Tổng":"ref_tong", "Hiệu":"ref_hieu", "Bộ":"ref_bo", "Chạm":"ref_cham"}
    k_map = {"Đầu":str(last_num//10), "Đuôi":str(last_num%10), "Tổng":str((last_num//10+last_num%10)%10), "Hiệu":str((last_num//10-last_num%10+10)%10), "Bộ":str(get_bo_idx(last_num)), "Chạm":str(last_num//10)}
    st.json(db[maps[sel]].get(k_map[sel], {}))
