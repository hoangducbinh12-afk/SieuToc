import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import random

# --- 1. GIAO DIỆN SÁNG CHUẨN MOBILE - CHỮ SIÊU NHỎ ---
st.set_page_config(page_title="TUAN PHONG V12.8 MULTI", layout="wide")
st.markdown("""
    <style>
    .main-box { 
        background-color: #ffffff; color: #334155; padding: 10px; border-radius: 8px; 
        font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; 
        border: 1.5px solid #fbbf24; margin-bottom: 10px; line-height: 1.4; font-weight: 600; 
        text-align: center; letter-spacing: 0.3px;
    }
    .stMetric { background: #f8fafc; padding: 5px; border-radius: 5px; border: 1px solid #e2e8f0; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; padding: 3px !important; }
    @media (max-width: 640px) {
        .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 4px 6px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CÁC BẢNG QUY LUẬT TOÁN HỌC ---
BO_MAP = {"00":[0,5,50,55],"01":[1,10,6,60,51,15,56,65],"02":[2,20,7,70,52,25,57,75],"03":[3,30,8,80,53,35,58,85],"04":[4,40,9,90,54,45,59,95],"11":[11,16,61,66],"12":[12,21,17,71,62,26,67,76],"13":[13,31,18,81,63,36,68,86],"14":[14,41,19,91,64,46,69,96],"22":[22,27,72,77],"23":[23,32,28,82,73,37,78,87],"24":[24,42,29,92,74,47,79,97],"33":[33,38,83,88],"34":[34,43,39,93,84,48,89,98],"44":[44,49,94,99]}
CL_4 = {"CC":[0,22,44,66,88,2,20,4,40,6,60,8,80,24,42,26,62,28,82,46,64,48,84,68,86], "CL":[1,3,5,7,9,21,23,25,27,29,41,43,45,47,49,61,63,65,67,69,81,83,85,87,89], "LL":[11,33,55,77,99,13,31,15,51,17,71,19,91,35,53,37,73,39,93,57,75,59,95,79,97], "LC":[10,12,14,16,18,30,32,34,36,38,50,52,54,56,58,70,72,74,76,78,90,92,94,96,98]}
BT_4 = {"BB":[0,11,22,33,44,1,10,2,20,3,30,4,40,12,21,13,31,14,41,23,32,24,42,34,43], "BT":[5,6,7,8,9,15,16,17,18,19,25,26,27,28,29,35,36,37,38,39,45,46,47,48,49], "TB":[90,91,92,93,94,80,81,82,83,84,70,71,72,73,74,60,61,62,63,64,50,51,52,53,54], "TT":[55,66,77,88,99,56,65,57,75,58,85,59,95,67,76,68,86,69,96,78,87,79,97,89,98]}
GIAP_12 = {"TI":[0,12,24,36,48,60,72,84,96],"SUU":[1,13,25,37,49,61,73,85,97],"DAN":[2,14,26,38,50,62,74,86,98],"MAO":[3,15,27,39,51,63,75,87,99],"THIN":[4,16,28,40,52,64,76,88],"TY":[5,17,29,41,53,65,77,89],"NGO":[6,18,30,42,54,66,78,90],"MUI":[7,19,31,43,55,67,79,91],"THAN":[8,20,32,44,56,68,80,92],"DAU":[9,21,33,45,57,69,81,93],"TUAT":[10,22,34,46,58,70,82,94],"HOI":[11,23,35,47,59,71,83,95]}
DANG_5 = {"KEP":[0,55,11,66,22,77,33,88,44,99,5,50,16,61,27,72,38,83,49,94], "SAT KEP":[1,10,12,21,23,32,34,43,45,54,56,65,67,76,78,87,89,98,9,90], "CACH 1":[2,20,8,80,13,31,19,91,24,42,35,53,46,64,57,75,79,97,68,86], "CACH 2":[3,30,18,81,25,52,47,74,69,96,7,70,14,41,29,92,36,63,58,85], "CACH 3":[4,40,6,60,15,51,17,71,28,82,26,62,37,73,39,93,48,84,59,95]}
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]
BONG_DUONG = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}; BONG_AM = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

ROOT_DATA = {
    1:{"cham":[1,6,0,5,2,7,3,8,4,9],"dau":[1,6,0,5,4,9,2,7,3,8],"duoi":[1,6,2,7,0,5,4,9,3,8],"tong":[1,6,2,7,4,9,0,5,3,8],"hieu":[0,5,1,6,2,7,4,9,3,8]},
    2:{"cham":[2,7,1,6,3,8,4,9,0,5],"dau":[2,7,1,6,5,0,3,8,4,9],"duoi":[2,7,3,8,1,6,5,0,4,9],"tong":[2,7,3,8,5,0,1,6,4,9],"hieu":[0,5,2,7,1,6,3,8,4,9]},
    3:{"cham":[3,8,2,7,4,9,0,5,1,6],"dau":[3,8,2,7,6,1,4,9,5,0],"duoi":[3,8,4,9,2,7,6,1,5,0],"tong":[3,8,4,9,1,6,2,7,0,5],"hieu":[0,5,3,8,4,9,1,6,2,7]},
    4:{"cham":[4,9,3,8,0,5,1,6,2,7],"dau":[4,9,3,8,7,2,5,0,6,1],"duoi":[4,9,5,0,3,8,7,2,6,1],"tong":[4,9,0,5,2,7,1,6,3,8],"hieu":[0,5,4,9,1,6,2,7,3,8]},
    5:{"cham":[5,0,4,9,2,7,1,6,3,8],"dau":[5,0,2,7,3,8,4,9,1,6],"duoi":[5,0,4,9,1,6,2,7,3,8],"tong":[5,0,8,3,2,7,4,9,1,6],"hieu":[0,5,1,6,4,9,2,7,3,8]},
    6:{"cham":[6,1,5,0,3,8,2,7,4,9],"dau":[6,1,5,0,9,4,7,2,8,3],"duoi":[6,1,7,2,5,0,9,4,8,3],"tong":[6,1,9,4,3,8,5,0,2,7],"hieu":[0,5,1,6,2,7,3,8,4,9]},
    7:{"cham":[7,2,6,1,4,9,3,8,0,5],"dau":[7,2,6,1,0,5,8,3,9,4],"duoi":[7,2,8,3,6,1,0,5,9,4],"tong":[7,2,0,5,4,9,6,1,3,8],"hieu":[0,5,2,7,3,8,4,9,1,6]},
    8:{"cham":[8,3,7,2,5,0,4,9,1,6],"dau":[8,3,7,2,1,6,9,4,0,5],"duoi":[8,3,9,4,7,2,1,6,0,5],"tong":[8,3,1,6,5,0,7,2,4,9],"hieu":[0,5,3,8,2,7,1,6,4,9]},
    9:{"cham":[9,4,8,3,6,1,5,0,2,7],"dau":[9,4,8,3,2,7,0,5,1,6],"duoi":[9,4,0,5,8,3,2,7,1,6],"tong":[9,4,2,7,6,1,8,3,5,0],"hieu":[0,5,4,9,3,8,2,7,1,6]}
}

def get_bo_idx(n):
    for i, (k, v) in enumerate(BO_MAP.items()):
        if n in v: return i
    return 0

def find_idx_universal(n, mapping):
    for i, nums in enumerate(mapping.values()):
        if n in nums: return i
    return 0

def get_root_val(s):
    try:
        t = sum(int(x) for x in str(s) if x.isdigit())
        while t > 9: t = sum(int(x) for x in str(t))
        return t
    except: return 1

def build_bang_a_tien_tien(gdb_str):
    if not gdb_str or len(gdb_str) < 5: return []
    digits = [int(d) for d in gdb_str[-5:]]
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
        "weights": [25.0, 25.0, 25.0, 25.0], "reflex_memory": {}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {
        "MB": create_blank_station(),
        "BINH_DUONG": create_blank_station(),
        "VINH_LONG": create_blank_station()
    }
if 'current_station' not in st.session_state:
    st.session_state.current_station = "MB"

# --- TỐI ƯU HÓA: Hàm quét lịch sử dựng phản xạ (Bỏ chặn lệnh dưới 2 kỳ để nhận diện ngay) ---
def rebuild_reflex_memory_v128(st_name):
    st_db = st.session_state.multi_db[st_name]
    memory = {f"{i:02d}": {"dau": [0]*10, "duoi": [0]*10, "tong": [0]*10, "hieu": [0]*10, "bo": [0]*15} for i in range(100)}
    if len(st_db["history"]) < 2:
        st_db["reflex_memory"] = memory
        return
    hist_reversed = st_db["history"][::-1]
    for k in range(len(hist_reversed) - 1):
        num_curr = hist_reversed[k]["Số"]
        num_next = hist_reversed[k+1]["Số"]
        n_next = int(num_next)
        if num_curr in memory:
            memory[num_curr]["dau"][n_next//10] += 1
            memory[num_curr]["duoi"][n_next%10] += 1
            memory[num_curr]["tong"][(n_next//10 + n_next%10)%10] += 1
            memory[num_curr]["hieu"][(n_next//10 - n_next%10 + 10)%10] += 1
            memory[num_curr]["bo"][get_bo_idx(n_next)] += 1
    st_db["reflex_memory"] = memory

def update_ai_weights_v128(st_name):
    st_db = st.session_state.multi_db[st_name]
    if len(st_db["history"]) < 3: return [25.0, 25.0, 25.0, 25.0]
    recent = st_db["history"][:3]
    new_w = [25.0, 25.0, 25.0, 25.0]
    for i in range(4):
        ranks = [h.get(f"Rank_E{i+1}", 50) for h in recent]
        if all(r < 30 for r in ranks[:2]): new_w[i] -= 6.0
        if ranks[0] > 70: new_w[i] += 10.0
    total = sum(new_w) if sum(new_w) > 0 else 100
    return [(x / total) * 100 for x in new_w]

def calculate_master_v128(st_name):
    st_db = st.session_state.multi_db[st_name]
    last_gdb = st_db["last_gdb_full"]
    current_num = last_gdb[-2:] if len(last_gdb) >= 2 else "00"
    
    n_gdb = get_root_val(last_gdb)
    n_date = get_root_val(st.session_state.date_in)
    n_ky = get_root_val(str(st_db["ky_quay"]))
    
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    all_a_old = build_bang_a_tien_tien(last_gdb)
    
    list_c_tmp = []
    if len(all_a_old) == 120:
        for n in range(10):
            row = {"da":0,"du":0,"to":0,"hi":0,"ch":0}
            for i in range(120):
                if all_a_old[i] == n:
                    row["da"]+=st_db["bang_b_points"][i]["dau"]; row["du"]+=st_db["bang_b_points"][i]["duoi"]
                    row["to"]+=st_db["bang_b_points"][i]["tong"]; row["hi"]+=st_db["bang_b_points"][i]["hieu"]
                    row["ch"]+=st_db["bang_b_points"][i]["cham"]
            list_c_tmp.append(row)

    # ĐẢM BẢO QUÉT THỜI GIAN THỰC: Ép cập nhật sơ đồ thói quen trước khi đọc
    rebuild_reflex_memory_v128(st_name)
    ref_map = st_db["reflex_memory"].get(current_num, {})

    for i in range(100):
        d, u = i // 10, i % 10
        t, h = (d + u) % 10, (d - u + 10) % 10
        b_idx = get_bo_idx(i)
        
        # E1: Khan Thuộc Tính
        e1[i] = st_db["dau"][d] + st_db["duoi"][u] + st_db["tong"][t] + st_db["hieu"][h] + \
                ((st_db["cham"][d]*2) if d==u else (st_db["cham"][d]+st_db["cham"][u])) + \
                st_db["bo"][b_idx] + st_db["giap"][find_idx_universal(i, GIAP_12)] + \
                st_db["dang5"][find_idx_universal(i, DANG_5)] + st_db["cl4"][find_idx_universal(i, CL_4)] + st_db["bt4"][find_idx_universal(i, BT_4)] + \
                st_db["d_cl"][d%2] + st_db["u_cl"][u%2] + st_db["t_cl"][t%2] + \
                st_db["d_tb"][1 if d>=5 else 0] + st_db["u_tb"][1 if u>=5 else 0] + \
                st_db["t_tb"][1 if t>=5 else 0] + st_db["h_tb"][1 if h>=5 else 0] + \
                st_db["so_he"][1 if i not in SO_THUONG else 0]
        
        # E2: Điểm Root
        sr = 0
        if st_db["use_root"]:
            for r in [n_date, n_ky, n_gdb]:
                if r in ROOT_DATA:
                    sr += ROOT_DATA[r]["dau"].index(d) + ROOT_DATA[r]["duoi"].index(u) + \
                          ROOT_DATA[r]["tong"].index(t) + ROOT_DATA[r]["hieu"].index(h)
        e2[i] = sr
        
        # E3: Tịnh Tiến Bóng Hình Học
        if len(list_c_tmp) == 10:
            e3[i] = list_c_tmp[d]["da"] + list_c_tmp[u]["du"] + list_c_tmp[t]["to"] + list_c_tmp[h]["hi"]
            e3[i] += (list_c_tmp[d]["ch"] * 2) if d == u else (list_c_tmp[d]["ch"] + list_c_tmp[u]["ch"])
            
        # E4: Phản Xạ Lịch Sử (Tra cứu động)
        if ref_map:
            e4[i] = 1000 - ((ref_map["dau"][d] + ref_map["duoi"][u] + ref_map["tong"][t] + ref_map["hieu"][h] + ref_map["bo"][b_idx]) * 15)
        else:
            e4[i] = 1000

    df = pd.DataFrame({"SO": [f"{k:02d}" for k in range(100)], "E1": e1, "E2": e2, "E3": e3, "E4": e4})
    w = st_db["weights"]
    df["DIEM_TONG"] = (df["E1"]*w[0] + df["E2"]*w[1] + df["E3"]*w[2] + df["E4"]*w[3]) / 4
    return df

def find_rank_unique_v128(df, target, col, asc=True):
    temp = df[['SO', col]].sort_values(by=[col, 'SO'], ascending=[asc, True]).reset_index(drop=True)
    match = temp[temp['SO'] == target].index
    return int(match[0]) + 1 if len(match) > 0 else 50

# --- SỬA LUỒNG XỬ LÝ: Đồng bộ hóa cập nhật, loại bỏ st.rerun() chống lỗi no-op ---
def process_multi_update():
    st_name = st.session_state.current_station
    st_db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw) < 5:
        st.warning("GĐB độ dài tối thiểu phải 5 số!")
        return
    
    n = int(raw[-2:])
    target_str = f"{n:02d}"
    
    # Bước 1: Tính toán Rank độc lập của ngày hôm nay trước khi ghi đè dữ liệu nền mới
    df_old = calculate_master_v128(st_name)
    r_ai = find_rank_unique_v128(df_old, target_str, "DIEM_TONG", asc=True)
    r_e1 = find_rank_unique_v127(df_old, target_str, "E1", asc=True)
    r_e2 = find_rank_unique_v127(df_old, target_str, "E2", asc=True)
    r_e3 = find_rank_unique_v127(df_old, target_str, "E3", asc=False) 
    r_e4 = find_rank_unique_v127(df_old, target_str, "E4", asc=True)
    
    st_db["history"].insert(0, {
        "Kỳ": int(st_db["ky_quay"]), "GĐB": raw, "Số": target_str,
        "Rank_AI": r_ai, "Rank_E1": r_e1, "Rank_E2": r_e2, "Rank_E3": r_e3, "Rank_E4": r_e4,
        "Time": datetime.now().strftime("%H:%M")
    })
    
    dv, duv, tv, hv = n//10, n%10, (n//10+n%10)%10, (n//10-n%10+10)%10
    
    # Nuôi ma trận tịnh tiến 120 tọa độ hình học
    all_a_old = build_bang_a_tien_tien(st_db["last_gdb_full"])
    if len(all_a_old) == 120:
        target_tt = {"dau": dv, "duoi": duv, "tong": tv, "hieu": hv, "cham": [dv, duv]}
        for i in range(120):
            val = all_a_old[i]; p = st_db["bang_b_points"][i]
            for key in ["dau", "duoi", "tong", "hieu"]:
                p[key] = 0 if val == target_tt[key] else p[key] + 1
            p["cham"] = 0 if val in target_tt["cham"] else p["cham"] + 1

    # Nuôi Khan 10 Thuộc tính gốc của đài lẻ
    for i in range(10):
        st_db["dau"][i] = 0 if i==dv else st_db["dau"][i]+1
        st_db["duoi"][i] = 0 if i==duv else st_db["duoi"][i]+1
        st_db["tong"][i] = 0 if i==tv else st_db["tong"][i]+1
        st_db["hieu"][i] = 0 if i==hv else st_db["hieu"][i]+1
        st_db["cham"][i] = 0 if (i==dv or i==duv) else st_db["cham"][i]+1
        
    b_idx, g_idx, d5_idx, c4_idx, b4_idx = find_idx_universal(n, BO_MAP), find_idx_universal(n, GIAP_12), find_idx_universal(n, DANG_5), find_idx_universal(n, CL_4), find_idx_universal(n, BT_4)
    st_db["bo"] = [0 if i==b_idx else x+1 for i,x in enumerate(st_db["bo"])]
    st_db["giap"] = [0 if i==g_idx else x+1 for i,x in enumerate(st_db["giap"])]
    st_db["dang5"] = [0 if i==d5_idx else x+1 for i,x in enumerate(st_db["dang5"])]
    st_db["cl4"] = [0 if i==c4_idx else x+1 for i,x in enumerate(st_db["cl4"])]
    st_db["bt4"] = [0 if i==b4_idx else x+1 for i,x in enumerate(st_db["bt4"])]
    
    st_db["d_cl"][dv%2]=0; st_db["d_cl"][(dv+1)%2]+=1
    st_db["u_cl"][duv%2]=0; st_db["u_cl"][(duv+1)%2]+=1
    st_db["t_cl"][tv%2]=0; st_db["t_cl"][(tv+1)%2]+=1
    st_db["so_he"][1 if n not in SO_THUONG else 0]=0; st_db["so_he"][0 if n not in SO_THUONG else 1]+=1
    st_db["d_tb"][1 if dv>=5 else 0]=0; st_db["d_tb"][0 if dv>=5 else 1]+=1
    st_db["u_tb"][1 if duv>=5 else 0]=0; st_db["u_tb"][0 if duv>=5 else 1]+=1
    st_db["t_tb"][1 if tv>=5 else 0]=0; st_db["t_tb"][0 if tv>=5 else 1]+=1
    st_db["h_tb"][1 if hv>=5 else 0]=0; st_db["h_tb"][0 if hv>=5 else 1]+=1

    # Cập nhật thông số chu kỳ nền ngày mới
    st_db["last_gdb_full"] = raw
    st_db["ky_quay"] += 1
    rebuild_reflex_memory_v128(st_name) # Ép buộc tính phản xạ số ngay tại chỗ
    st_db["weights"] = update_ai_weights_v128(st_name)
    # Đã bóc bỏ st.rerun() ở đây để triệt tiêu lỗi no-op của Streamlit callback

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🛡️ COMMANDER MASTER V12.8")

with st.sidebar:
    st.header("🏢 KHU VỰC ĐÀI QUAY")
    st.session_state.current_station = st.selectbox(
        "CHỌN ĐÀI SOI:", list(st.session_state.multi_db.keys()), key="station_select"
    )
    
    new_st = st.text_input("➕ Kích hoạt đài mới (Gõ liền):")
    if st.button("TẠO ĐÀI MỚI") and new_st:
        new_st_clean = new_st.strip().upper()
        if new_st_clean not in st.session_state.multi_db:
            st.session_state.multi_db[new_st_clean] = create_blank_station()
            st.rerun()
            
    st.divider()
    up = st.file_uploader("📥 Chọn File .Json Toàn Đài:", type="json")
    if up:
        if st.button("✅ KÍCH HOẠT NẠP DỮ LIỆU ĐÀI", type="primary", use_container_width=True):
            st.session_state.multi_db = json.load(up)
            st.success("Hệ thống đã nạp dữ liệu!")
            st.rerun()
            
    if st.button("🔴 LÀM SẠCH BỘ NHỚ (RESET)", use_container_width=True):
        st.session_state.clear()
        st.rerun()

current_st = st.session_state.current_station
current_db = st.session_state.multi_db[current_st]

st.info(f"🛰️ Đang nạp hệ thống đài: **[{current_st}]**")

c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.2, 1])
with c1: st.text_input(f"Nhập GĐB Đài {current_st}:", value="67294", key="gdb_in")
with c2: st.text_input("Ngày Quay Số:", datetime.now().strftime("%d%m%Y"), key="date_in")
with c3: current_db["ky_quay"] = st.number_input("Kỳ hiện tại:", value=int(current_db["ky_quay"]), step=1)
with c4: st.write("##"); st.toggle("M.TRẬN ROOT", value=current_db["use_root"], key="use_root")

st.button("🚀 CẬP NHẬT RIÊNG CHO ĐÀI NÀY", on_click=process_multi_update, type="primary", use_container_width=True)

df_master = calculate_master_v128(current_st)
active_w = update_ai_weights_v128(current_st)
current_db["weights"] = active_w

t1, t2, t3, t4 = st.tabs(["🎯 DÀN AI THEO ĐÀI", "⚖️ ĐỐI TRỌNG ENGINE", "📋 NHẬT KÝ ĐÀI (THÔNG MINH)", "🧠 PHẢN XẠ SỐ"])

with t1:
    col_n1, col_n2 = st.columns(2)
    n1 = col_n1.number_input("Số quân dàn kết mỏng:", 1, 100, 36, step=1)
    n2 = col_n2.number_input("Số quân dàn tiêu chuẩn:", 1, 100, 51, step=1)
    st.write("---")
    
    danh_sach_all = df_master.sort_values("DIEM_TONG", ascending=True)["SO"].tolist()
    st.subheader(f"🔥 DÀN KẾT ĐÀI {current_st} ({n1} SỐ)")
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach_all[:n1])}</div>", unsafe_allow_html=True)
    st.subheader(f"🔥 DÀN TIÊU CHUẨN ĐÀI {current_st} ({n2} SỐ)")
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach_all[:n2])}</div>", unsafe_allow_html=True)

with t2:
    st.subheader(f"⚖️ Phân Phối Đối Trọng Đài {current_st} (%)")
    w_df = pd.DataFrame({
        "Bộ máy phân tích": ["E1 (Khan Thuộc Tính)", "E2 (Ma Trận Điểm Root)", "E3 (120 Tịnh Tiến Matrix)", "E4 (Bộ Nhớ Phản Xạ Lịch Sử)"],
        "Tỷ trọng (%)": [round(x, 1) for x in active_w]
    })
    st.table(w_df.set_index("Bộ máy phân tích").T)
    st.line_chart(active_w)
    st.divider()
    st.download_button("💾 XUẤT SAO LƯU TOÀN BỘ CÁC ĐÀI (.JSON)", json.dumps(st.session_state.multi_db), "MULTI_STATION_DATA.json", use_container_width=True)

with t3:
    if current_db["history"]:
        st.subheader("📋 Bảng Tra Cứu Rank Hiệu Quả Thực Tế")
        df_hist = pd.DataFrame(current_db["history"])
        st.table(df_hist[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
        
        st.divider()
        st.subheader("📊 Phân Nhóm Thống Kê Hiệu Quả Vị Trí Ăn")
        rks = df_hist["Rank_AI"].tolist()
        gs = [sum(1 for r in rks if 1<=r<=10), sum(1 for r in rks if 11<=r<=39), sum(1 for r in rks if 40<=r<=59), sum(1 for r in rks if 60<=r<=75), sum(1 for r in rks if 76<=r<=100)]
        st.table(pd.DataFrame({"Phân nhóm Rank": ["1-10 (Siêu chuẩn)","11-39 (Trong Dàn 36)","40-59 (Trong Dàn 51)","60-75 (Rìa Dàn)","76-100 (Trượt Cầu)"], "Số lần nổ": gs, "Tỷ lệ đạt (%)": [f"{(x/len(rks))*100:.1f}%" for x in gs]}))
        st.line_chart(df_hist['Rank_AI'])
    else:
        st.info("Chưa có lịch sử quay thưởng.")

with t4:
    last_gdb = current_db["last_gdb_full"]
    last_num = last_gdb[-2:] if len(last_gdb) >= 2 else "00"
    st.subheader(f"🧠 Sơ Đồ Thói Quen Phản Xạ Đài {current_st} Sau Con Số: [{last_num}]")
    if current_db.get("reflex_memory") and last_num in current_db["reflex_memory"]:
        st.json(current_db["reflex_memory"][last_num])
    else:
        st.info("Chưa nạp đủ lịch sử để bóc tách thói quen của số này.")
