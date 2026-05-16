import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN Master ---
st.set_page_config(page_title="TUAN PHONG V17.5 PRECISION", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT & HÀM KHỞI TẠO ---
B_D = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
B_A = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_5050_attrs(n):
    d, u = n // 10, n % 10
    t = (d + u) % 10
    return {
        "D_CL": "Chẵn" if d % 2 == 0 else "Lẻ", "U_CL": "Chẵn" if u % 2 == 0 else "Lẻ",
        "T_CL": "Chẵn" if t % 2 == 0 else "Lẻ", "D_TB": "To" if d >= 5 else "Bé",
        "U_TB": "To" if u >= 5 else "Bé", "T_TB": "To" if t >= 5 else "Bé",
        "HE": "Thường" if n in SO_THUONG else "HệKép", "H_TB": "To" if (d-u+10)%10 >= 5 else "Bé"
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

# --- 3. BỘ NÃO AI DỰ ĐOÁN CHU KỲ & TIE-BREAKER ---
def predict_5050_momentum(history):
    if len(history) < 3: return {}
    recent = [int(h["Số"]) for h in history[:10]]
    attrs = [get_5050_attrs(n) for n in recent]
    preds = {}
    for k in ["D_CL","U_CL","T_CL","D_TB","U_TB","T_TB","HE","H_TB"]:
        seq = [a[k] for a in attrs]
        last = seq[0]; streak = 0
        for v in seq:
            if v == last: streak += 1
            else: break
        if streak < 5: preds[k] = last
        elif len(seq) >= 3 and seq[0] != seq[1] and seq[1] == seq[2]: preds[k] = seq[1]
        else: preds[k] = "To" if last == "Bé" else "Lẻ"
    return preds

def stats_rank(arr, rev=False):
    vals = np.array(arr)
    return np.argsort(np.argsort(-vals if rev else vals)) + 1

# --- 4. ENGINE TÍNH TOÁN ---
def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    last_g = db.get("last_gdb_full", "00000")
    p_50 = predict_5050_momentum(db["history"])
    
    e1, e2, e3, e4, penalty = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    val_e3 = [sum(db["bang_b_points"][idx].get("dau", 1) for idx, v in enumerate(mt) if v == n) for n in range(10)]

    for i in range(100):
        d, u = i//10, i%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][(d+u)%10]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        e3[i] = val_e3[d] + val_e3[u]
        dk, uk = last_g[-2:-1] if len(last_g)>=2 else "0", last_g[-1:] if len(last_g)>=1 else "0"
        if dk in db["ref_dau"]: e4[i] += db["ref_dau"][dk]["d"][d]
        if uk in db["ref_duoi"]: e4[i] += db["ref_duoi"][uk]["u"][u]
        
        # BỘ PHÂN XỬ: Tính điểm phạt cho số không khớp nhịp 50/50
        at = get_5050_attrs(i)
        mismatch = 0
        for k, v in p_50.items():
            if at[k] != v: mismatch += 1
        penalty[i] = mismatch * 0.1 # Điểm phạt nhỏ để tách các số trùng Rank

    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e3, True), stats_rank(e4, True)
    w = db.get("weights", [25.0]*4)
    total = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3])/100 + penalty
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":total, "R1":r1, "R2":r2, "R3":r3, "R4":r4}), p_50

# --- 5. GIAO DIỆN ---
if 'multi_db' not in st.session_state: 
    st.session_state.multi_db = {"MB": create_blank()}

with st.sidebar:
    st.header("📂 HỆ THỐNG")
    st.session_state.current_station = st.selectbox("ĐÀI SOI:", list(st.session_state.multi_db.keys()))
    up = st.file_uploader("Nạp .JSON", type="json")
    if up and st.button("✅ XÁC NHẬN NẠP"): st.session_state.multi_db = json.load(up); st.rerun()
    if st.button("🔴 RESET ALL"): st.session_state.clear(); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2, c3 = st.columns([1,2,1])
with c1: st.text_input("Ngày:", value=datetime.now().strftime("%d/%m"), key="day_in")
with c2: st.text_input("GĐB Vừa Ra:", value=db.get("last_gdb_full", "00000"), key="gdb_in")
with c3: db["ky_quay"] = st.number_input("Kỳ:", value=int(db.get("ky_quay", 1)), step=1)

if st.button("🚀 CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
    raw = st.session_state.gdb_in.strip()
    if len(raw)>=5:
        df_old, _ = calculate_master(st.session_state.current_station)
        target = f"{int(raw[-2:]):02d}"
        db["history"].insert(0, {"Ngày": st.session_state.day_in, "Kỳ": int(db["ky_quay"]), "GĐB": raw, "Số": target, "Rank_AI": int(stats_rank(df_old["TOTAL"])[df_old[df_old['SO']==target].index[0]]), "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]), "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]), "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]), "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])})
        db["last_gdb_full"], db["ky_quay"] = raw, db["ky_quay"]+1
        st.rerun()

df_m, p_active = calculate_master(st.session_state.current_station)
t1, t2, t3, t4 = st.tabs(["🎯 DÀN AI", "⚖️ ĐỐI TRỌNG", "📊 NHẬT KÝ", "🔍 BIẾN 50/50"])

with t1:
    cs1, cs2 = st.columns(2); num1 = cs1.slider("Dàn 1:", 10, 90, 36); num2 = cs2.slider("Dàn 2:", 10, 90, 51)
    ds = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN {num1} (Lọc 50/50):**<br><div class='main-box'>{' '.join(ds[:num1])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN {num2} (Lọc 50/50):**<br><div class='main-box' style='border-color:#10b981'>{' '.join(ds[:num2])}</div>", unsafe_allow_html=True)
with t2:
    st.toggle("🤖 AI TỰ ĐIỀU CHỈNH %", key="ai_auto_w")
    w = db.get("weights", [25.0]*4)
    cw = st.columns(4); names = ["E1","E2","E3","E4"]
    for i in range(4):
        db["weights"][i] = cw[i].number_input(f"{names[i]} (%)", 0.0, 100.0, float(w[i]), disabled=st.session_state.ai_auto_w)
    st.divider(); st.download_button("💾 LƯU FILE", json.dumps(st.session_state.multi_db), "DATA.json", use_container_width=True)
with t3:
    if db["history"]: st.table(pd.DataFrame(db["history"])[[c for c in ['Ngày','Kỳ','GĐB','Số','Rank_AI','Rank_E1','Rank_E2','Rank_E3','Rank_E4'] if c in pd.DataFrame(db["history"]).columns]])
with t4:
    if db["history"]:
        df_50 = pd.DataFrame([get_5050_attrs(int(h["Số"])) for h in db["history"][:10]])
        df_50.index = [h["Kỳ"] for h in db["history"][:10]]; st.table(df_50)
