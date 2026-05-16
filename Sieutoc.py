import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN ---
st.set_page_config(page_title="TUAN PHONG V16.6 HYBRID", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT & 8 BIẾN 50/50 ---
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

# --- 3. BỘ NÃO AI (MOMENTUM & SIN-WAVE) ---
def auto_calculate_weights(history):
    if len(history) < 5: return [25.0]*4
    engs = ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]
    raw = []
    for k in engs:
        path = [h.get(k, 50) for h in history[:10]]
        avg, std = np.mean(path), np.std(path)
        # Bắt đáy: Rank đang cao (đen) + ổn định (std thấp) -> Tăng trọng số đón nổ
        raw.append(40.0 if (avg > 50 and std < 20) else 20.0)
    total = sum(raw)
    return [round((s/total)*100, 2) for s in raw]

def analyze_rhythm_boost(history):
    if len(history) < 3: return {}
    recent = [int(h["Số"]) for h in history[:10]]
    attrs = [get_5050_attrs(n) for n in recent]
    bias = {}
    for k in ["D_CL","U_CL","T_CL","D_TB","U_TB","T_TB","HE","H_TB"]:
        seq = [a[k] for a in attrs]
        if seq[0] == seq[1]: bias[k] = seq[0] # Bám bệt
        elif len(seq)>=3 and seq[0] != seq[1] and seq[1] == seq[2]: bias[k] = seq[1] # Bám nhảy
    return bias

def stats_rank(arr, rev=False):
    vals = np.array(arr)
    if rev: vals = -vals
    return np.argsort(np.argsort(vals)) + 1

# --- 4. ENGINE TÍNH TOÁN ---
def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    last_g = db["last_gdb_full"]
    
    # 1. Tự động cập nhật trọng số nếu bật chế độ AI
    if st.session_state.get('ai_mode', False):
        db["weights"] = auto_calculate_weights(db["history"])
    
    # 2. Lấy Bias nhịp bệt
    bias = analyze_rhythm_boost(db["history"])
    
    e1, e2, e3, e4, e5_boost = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    
    # Rank gốc (E1, E2, E3, E4 giữ nguyên)
    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        # Bơm điểm Momentum 50/50
        at = get_5050_attrs(i)
        for k, v in bias.items():
            if at[k] == v: e5_boost[i] += 10 # Cộng 10 điểm thưởng mỗi thuộc tính khớp trend

    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e2+e1), stats_rank(e1*2) # Demo logic E3, E4
    
    w = db.get("weights", [25.0]*4)
    # TOTAL = (Rank Gốc) - (Điểm thưởng nhịp bệt)
    # Trừ vì Rank càng thấp càng tốt
    total_score = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3])/100 - (e5_boost/5)
    
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":total_score, "R1":r1, "R2":r2, "R3":r3, "R4":r4})

# --- (Phần Giao diện nạp số giữ nguyên như bản 16.5) ---
# ... (process_v165 giữ nguyên) ...

# --- 5. HIỂN THỊ ---
st.title("🛡️ COMMANDER V16.6 HYBRID")
# Sidebar & Inputs...
db = st.session_state.multi_db[st.session_state.current_station]
col1, col2, col3 = st.columns([1,2,1])
with col1: st.text_input("Ngày:", value=datetime.now().strftime("%d/%m"), key="day_in")
with col2: st.text_input("GĐB Vừa Ra:", value=db.get("last_gdb_full", "00000"), key="gdb_in")
with col3: db["ky_quay"] = st.number_input("Kỳ:", value=int(db.get("ky_quay", 1)), step=1)

st.button("🚀 CẬP NHẬT HỆ THỐNG", on_click=lambda: None) # Chỉ demo nút

df_m = calculate_master(st.session_state.current_station)
t1, t2, t3, t4 = st.tabs(["🎯 DÀN AI", "⚖️ ĐỐI TRỌNG", "📊 THỐNG KÊ", "📋 NHẬT KÝ"])

with t1:
    st.checkbox("Kích hoạt AI tự động soi nhịp (Dynamic Mode)", key="ai_mode")
    danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"**DÀN 36 SỐ:**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.markdown(f"**DÀN 51 SỐ:**<br><div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)

with t2:
    st.subheader("⚖️ Cấu hình Đối trọng")
    if st.session_state.ai_mode:
        st.info("AI đang tự động tính toán dựa trên phong độ 10 kỳ gần nhất.")
    # Hiển thị bảng Weights...
    st.table(pd.DataFrame({"Engine": ["E1", "E2", "E3", "E4"], "%": db["weights"]}).set_index("Engine").T)
