import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN MOBILE TINH GỌN ---
st.set_page_config(page_title="TUAN PHONG V15.1 PRO", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stMetric { background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. HỆ THỐNG BÓNG ÂM DƯƠNG (120 TỌA ĐỘ) ---
B_D = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
B_A = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

def build_ma_tran_120(gdb_str):
    g = str(gdb_str).strip()
    if len(g) < 5: return [0]*120
    dts = [int(d) for d in g[-5:]]
    tien = [[(d + s) % 10 for d in dts] for s in range(10)]
    bong = [dts]; c = dts
    for i in range(13):
        c = [B_D[d] for d in c] if i % 2 == 0 else [B_A[d] for d in c]
        bong.append(c)
    return ([d for sub in tien for d in sub] + [d for sub in bong for d in sub])[:120]

def create_blank():
    return {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10,
        "bang_b": [{"dau":1,"duoi":1} for _ in range(120)],
        "last_gdb": "00000", "ky": 1, "history": [],
        "ref": {"dau":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)}, 
                "duoi":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)}}
    }

if 'multi_db' not in st.session_state: st.session_state.multi_db = {"MB": create_blank()}
if 'active_w' not in st.session_state: st.session_state.active_w = [25.0]*4

# --- 3. THUẬT TOÁN AI ---
def run_sin_ai(st_name):
    h = st.session_state.multi_db[st_name]["history"]
    if len(h) < 5: return [25.0]*4
    engs = ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]
    raw = []
    for k in engs:
        p = [x[k] for x in h[:10]]
        avg, std = np.mean(p), np.std(p)
        raw.append(40.0 if (avg > 50 and std < 20) else (15.0 if avg < 20 else 25.0))
    t = sum(raw)
    return [round((s/t)*100, 2) for s in raw]

def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    st.session_state.active_w = run_sin_ai(st_name)
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_ma_tran_120(db["last_gdb"])
    
    val_e3 = [sum(db["bang_b"][idx]["dau"] for idx, v in enumerate(mt) if v == n) for n in range(10)]
    curr_n = int(db["last_gdb"][-2:]) if len(db["last_gdb"])>=2 else 0
    dk, uk = str(curr_n//10), str(curr_n%10)

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in db["last_gdb"] if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u]
        if dk in db["ref"]["dau"]: e4[i] += db["ref"]["dau"][dk]["d"][d] + db["ref"]["dau"][dk]["u"][u]
        if uk in db["ref"]["duoi"]: e4[i] += db["ref"]["duoi"][uk]["d"][d] + db["ref"]["duoi"][uk]["u"][u]

    def rk(s, rev=False): return stats.rankdata(-s if rev else s, method='min')
    r1, r2, r3, r4 = rk(e1), rk(e2), rk(e3, True), rk(e4, True)
    w = st.session_state.active_w
    final = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3]) / 100
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "R1":r1, "R2":r2, "R3":r3, "R4":r4, "TOTAL":final})

def process_v151():
    st_name = st.session_state.current_station
    db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master(st_name)
    
    db["history"].insert(0, {
        "Kỳ": int(db["ky"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats.rankdata(df_old["TOTAL"], method='min')[df_old[df_old['SO']==target].index[0]]),
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

    if len(db["history"]) >= 2:
        c_n = int(db["history"][1]["Số"]); n_n = int(db["history"][0]["Số"])
        for m, k in [("dau",str(c_n//10)), ("duoi",str(c_n%10))]:
            db["ref"][m][k]["d"][n_n//10]+=1; db["ref"][m][k]["u"][n_n%10]+=1

    mt_prev = build_ma_tran_120(db["last_gdb"])
    for idx, v in enumerate(mt_prev):
        db["bang_b"][idx]["dau"] = 0 if v==dv else db["bang_b"][idx]["dau"]+1
        db["bang_b"][idx]["duoi"] = 0 if v==duv else db["bang_b"][idx]["duoi"]+1

    db["last_gdb"], db["ky"] = raw, db["ky"]+1

# --- 4. GIAO DIỆN ---
st.title("🛡️ COMMANDER V15.1 PRO")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb"], key="gdb_in")
with c2: db["ky"] = st.number_input("Kỳ:", value=int(db["ky"]), step=1)

st.button("🚀 CẬP NHẬT", on_click=process_v151, type="primary", use_container_width=True)

df_m = calculate_master(st.session_state.current_station)
t1, t2, t3 = st.tabs(["🎯 DÀN AI", "📊 ĐỐI TRỌNG & TỶ LỆ", "📋 NHẬT KÝ"])

with t1:
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN 36 SỐ:**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN 51 SỐ:**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)

with t2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Đối trọng Sin")
        st.table(pd.DataFrame({"Eng": ["E1", "E2", "E3", "E4"], "%": st.session_state.active_w}).set_index("Eng").T)
    with col_b:
        st.subheader("🎯 Tỷ lệ ăn dàn")
        if db["history"]:
            total_k = len(db["history"])
            win_36 = sum(1 for x in db["history"] if x["Rank_AI"] <= 36)
            win_51 = sum(1 for x in db["history"] if x["Rank_AI"] <= 51)
            st.write(f"Ăn Dàn 36: **{win_36}/{total_k}** ({round(win_36/total_k*100,1)}%)")
            st.write(f"Ăn Dàn 51: **{win_51}/{total_k}** ({round(win_51/total_k*100,1)}%)")
    st.download_button("💾 LƯU DỮ LIỆU .JSON", json.dumps(st.session_state.multi_db), "DATA_V151.json", use_container_width=True)

with t3:
    if db["history"]:
        st.table(pd.DataFrame(db["history"])[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
