import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN ---
st.set_page_config(page_title="TUAN PHONG V16.3 FIX", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT ---
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

# --- 3. HÀM KHỞI TẠO CHỐNG LỖI (KEY DEFENDER) ---
def check_and_fix_db(db):
    if "ref_dau" not in db: db["ref_dau"] = {}
    if "ref_duoi" not in db: db["ref_duoi"] = {}
    if "bang_b_points" not in db: db["bang_b_points"] = [{"dau":1,"duoi":1} for _ in range(120)]
    # Đảm bảo đủ 10 ngăn kéo 0-9
    for i in range(10):
        k = str(i)
        if k not in db["ref_dau"]: db["ref_dau"][k] = {"d":[0]*10, "u":[0]*10}
        if k not in db["ref_duoi"]: db["ref_duoi"][k] = {"d":[0]*10, "u":[0]*10}
    return db

def create_blank():
    return check_and_fix_db({"dau":[0]*10, "duoi":[0]*10, "tong":[0]*10, "last_gdb_full":"00000", "ky_quay":1, "history":[]})

if 'multi_db' not in st.session_state: st.session_state.multi_db = {"MB": create_blank()}

# --- 4. ENGINE TÍNH TOÁN ---
def calculate_master(st_name):
    db = check_and_fix_db(st.session_state.multi_db[st_name])
    last_g = db["last_gdb_full"]
    curr_n = int(last_g[-2:]) if len(last_g)>=2 else 0
    
    e1, e2, e3, e4, e5 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    val_e3 = [sum(db["bang_b_points"][idx]["dau"] for idx, v in enumerate(mt) if v == n) for n in range(10)]

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u]
        dk, uk = str(curr_n//10), str(curr_n%10)
        # Sửa lỗi KeyError bằng cách .get() an toàn
        e4[i] += db["ref_dau"].get(dk, {"d":[0]*10})["d"][d] + db["ref_duoi"].get(uk, {"u":[0]*10})["u"][u]

    temp_total = (stats_rank(e1) + stats_rank(e2) + stats_rank(e3, True) + stats_rank(e4, True)) / 4
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":temp_total, 
                         "R1":stats_rank(e1), "R2":stats_rank(e2), "R3":stats_rank(e3,True), "R4":stats_rank(e4,True)})

def stats_rank(arr, rev=False):
    vals = np.array(arr)
    if rev: vals = -vals
    return np.argsort(np.argsort(vals)) + 1

def process_v163():
    st_name = st.session_state.current_station
    db = check_and_fix_db(st.session_state.multi_db[st_name])
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master(st_name)
    
    db["history"].insert(0, {
        "Ngày": datetime.now().strftime("%d/%m"), "Kỳ": int(db["ky_quay"]), "GĐB": raw, "Số": target,
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
        db["bang_b_points"][idx]["dau"] = 0 if v==dv else db["bang_b_points"][idx].get("dau", 0)+1

    if len(db["history"]) >= 2:
        c_n = int(db["history"][1]["Số"]); n_n = int(db["history"][0]["Số"])
        dk, uk = str(c_n//10), str(c_n%10)
        db["ref_dau"][dk]["d"][n_n//10]+=1
        db["ref_duoi"][uk]["u"][n_n%10]+=1

    db["last_gdb_full"], db["ky_quay"] = raw, db["ky_quay"]+1

# --- 5. GIAO DIỆN ---
st.title("🛡️ COMMANDER V16.3 FINAL")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = check_and_fix_db(st.session_state.multi_db[st.session_state.current_station])
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT", on_click=process_v163, type="primary", use_container_width=True)

df_m = calculate_master(st.session_state.current_station)
t1, t2, t3 = st.tabs(["🎯 DÀN AI", "📊 TỶ LỆ ĂN", "📋 NHẬT KÝ"])

with t1:
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN 36 SỐ:**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN 51 SỐ:**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)
with t2:
    if db["history"]:
        total = len(db["history"])
        w36 = sum(1 for x in db["history"] if x["Rank_AI"] <= 36)
        w51 = sum(1 for x in db["history"] if x["Rank_AI"] <= 51)
        st.metric("Tỷ lệ Dàn 36", f"{w36}/{total}", f"{round(w36/total*100,1)}%")
        st.metric("Tỷ lệ Dàn 51", f"{w51}/{total}", f"{round(w51/total*100,1)}%")
    st.download_button("💾 LƯU DỮ LIỆU .JSON", json.dumps(st.session_state.multi_db), "DATA_FIXED.json", use_container_width=True)
with t3:
    if db["history"]:
        st.table(pd.DataFrame(db["history"])[['Ngày', 'Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
