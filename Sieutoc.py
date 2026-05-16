import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. CONFIG MOBILE ---
st.set_page_config(page_title="TUAN PHONG MOBILE PRO", layout="centered")

st.markdown("""
    <style>
    .dan-box { background-color: white; border-radius: 12px; padding: 15px; border: 1px solid #E0E4E8; margin-bottom: 10px; font-family: 'Roboto Mono', monospace; font-weight: 700; color: #1e293b; font-size: 1.2rem; line-height: 1.8; text-align: center; }
    .dan-1 { border-left: 6px solid #10b981; background-color: #f0fdf4; }
    .dan-2 { border-left: 6px solid #3b82f6; background-color: #eff6ff; }
    .stButton button { border-radius: 10px; height: 3rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM TOÁN HỌC CORE ---
B_D = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
B_A = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

def build_mt_120(g):
    g_str = str(g).strip()
    if len(g_str) < 5: return [0]*120
    dts = [int(x) for x in g_str[-5:]]
    tien = [[(d + s) % 10 for d in dts] for s in range(10)]; bong = [dts]; c = dts
    for i in range(14):
        c = [B_D[x] for x in c] if i%2==0 else [B_A[x] for x in c]
        bong.append(c)
    return ([x for sub in tien for x in sub] + [x for sub in bong for x in sub])[:120]

def run_ai_weights(history):
    if len(history) < 3: return [25.0, 25.0, 25.0, 25.0]
    scores = []
    for k in ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]:
        vals = [h.get(k, 50) for h in history[:15]]
        avg = np.mean(vals); std = np.std(vals) if np.std(vals) > 0 else 1
        scores.append(avg / std)
    total = sum(scores)
    return [round((s/total)*100, 1) for s in scores]

# --- 3. KHỞI TẠO BỘ NHỚ (FIXED SYNTAX) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10, 
        "last_gdb_full": "00000", "ky_quay": 1, "history": [], 
        "bang_b_points": [{"dau": 1} for _ in range(120)], 
        "ref_dau": {str(i): {"d": [0]*10, "u": [0]*10} for i in range(10)}, 
        "ref_duoi": {str(i): {"d": [0]*10, "u": [0]*10} for i in range(10)}, 
        "weights": [25.0, 25.0, 25.0, 25.0]
    }

if 'num1' not in st.session_state: st.session_state.num1 = 11
if 'num2' not in st.session_state: st.session_state.num2 = 37

db = st.session_state.db

# --- 4. ENGINE TÍNH TOÁN ---
def calculate_master(use_ai):
    w_calc = run_ai_weights(db["history"]) if use_ai else db.get("weights", [25.0]*4)
    last_g = db.get("last_gdb_full", "00000")
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    v_e3 = [sum(db["bang_b_points"][idx].get("dau", 1) for idx, v in enumerate(mt) if v == n) for n in range(10)]
    dk, uk = last_g[-2:-1] if len(last_g)>=2 else "0", last_g[-1:] if len(last_g)>=1 else "0"
    
    def rk(arr, rev=False): return np.argsort(np.argsort(-np.array(arr) if rev else np.array(arr))) + 1
    for i in range(100):
        d, u = i//10, i%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][(d+u)%10]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + u
        e3[i] = v_e3[d] + v_e3[u]
        if dk in db["ref_dau"]: e4[i] += db["ref_dau"][dk]["d"][d]
        if uk in db["ref_duoi"]: e4[i] += db["ref_duoi"][uk]["u"][u]
    
    total = (rk(e1)*w_calc[0] + rk(e2)*w_calc[1] + rk(e3, True)*w_calc[2] + rk(e4, True)*w_calc[3])/100
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":total, "R1":rk(e1), "R4":rk(e4)}), w_calc

# --- 5. GIAO DIỆN CHÍNH ---
st.title("🛡️ TUAN PHONG MOBILE")

with st.expander("📁 QUẢN LÝ FILE .JSON"):
    up = st.file_uploader("Nạp File", type="json")
    if up: 
        st.session_state.db = json.load(up)
        st.rerun()
    st.download_button("💾 Tải Xuống File", json.dumps(st.session_state.db), f"data_{datetime.now().strftime('%d%H%M')}.json", use_container_width=True)

c_in1, c_in2 = st.columns([2, 1])
with c_in1: gdb_now = st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"])
with c_in2: ky_now = st.number_input("Kỳ Quay:", value=int(db["ky_quay"]), step=1)

if st.button("🚀 CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True):
    if len(gdb_now) >= 5:
        df_old, _ = calculate_master(st.session_state.get('ai_auto_w', True))
        target = f"{int(gdb_now[-2:]):02d}"
        db["history"].insert(0, {"Ngày": datetime.now().strftime("%d/%m"), "Số": target, "Rank_AI": int(df_old[df_old['SO']==target].index[0]+1), "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]), "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])})
        dv, du, tv = int(target)//10, int(target)%10, (int(target)//10 + int(target)%10)%10
        for i in range(10):
            db["dau"][i] = 0 if i==dv else db["dau"][i]+1
            db["duoi"][i] = 0 if i==du else db["duoi"][i]+1
            db["tong"][i] = 0 if i==tv else db["tong"][i]+1
        db["last_gdb_full"], db["ky_quay"] = gdb_now, ky_now + 1
        st.rerun()

st.divider()

# CÀI ĐẶT DÀN
is_ai = st.toggle("🤖 AI Tự Điều Chỉnh", key="ai_auto_w", value=True)
df_res, w_active = calculate_master(is_ai)

col_n1, col_n2 = st.columns(2)
st.session_state.num1 = col_n1.number_input("Số quân Dàn 1:", 1, 90, st.session_state.num1)
st.session_state.num2 = col_n2.number_input("Số quân Dàn 2:", 1, 90, st.session_state.num2)

ds_sorted = df_res.sort_values("TOTAL")["SO"].tolist()
d1_final = ", ".join(ds_sorted[:st.session_state.num1])
d2_final = ", ".join(ds_sorted[:st.session_state.num2])

st.markdown(f"**Dàn 1 ({st.session_state.num1} số):**")
st.markdown(f"<div class='dan-box dan-1'>{d1_final}</div>", unsafe_allow_html=True)

st.markdown(f"**Dàn 2 ({st.session_state.num2} số):**")
st.markdown(f"<div class='dan-box dan-2'>{d2_final}</div>", unsafe_allow_html=True)

with st.expander("📊 Xem 10 kỳ gần nhất"):
    if db["history"]:
        st.table(pd.DataFrame(db["history"]).head(10))
