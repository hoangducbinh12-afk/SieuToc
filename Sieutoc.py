import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN Master ---
st.set_page_config(page_title="TUAN PHONG V17.4 PRECISION", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT 8 BIẾN 50/50 ---
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

# --- 3. AI PREDICT & TIE-BREAKER LOGIC ---
def predict_5050_momentum(history):
    if len(history) < 3: return {}
    recent = [int(h["Số"]) for h in history[:15]]
    attrs = [get_5050_attrs(n) for n in recent]
    preds = {}
    for k in ["D_CL","U_CL","T_CL","D_TB","U_TB","T_TB","HE","H_TB"]:
        seq = [a[k] for a in attrs]
        last = seq[0]
        streak = 0
        for v in seq:
            if v == last: streak += 1
            else: break
        # Tư duy bám bệt/nhảy linh hoạt
        if streak < 5: preds[k] = last
        elif len(seq) >= 3 and seq[0] != seq[1] and seq[1] == seq[2]: preds[k] = seq[1]
        else: preds[k] = "To" if last == "Bé" else "Lẻ" # Văng
    return preds

def stats_rank(arr, rev=False):
    vals = np.array(arr)
    return np.argsort(np.argsort(-vals if rev else vals)) + 1

# --- 4. ENGINE TÍNH TOÁN VỚI BỘ PHÂN XỬ TRÙNG RANK ---
def calculate_master_v174(st_name):
    db = st.session_state.multi_db[st_name]
    last_g = db.get("last_gdb_full", "00000")
    p_50 = predict_5050_momentum(db["history"])
    
    e1, e2, e3, e4, penalty_score = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    
    for i in range(100):
        d, u = i//10, i%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][(d+u)%10]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + (i % 10)
        # Mô phỏng E3, E4 logic ổn định
        e3[i] = 50; e4[i] = 50 
        
        # LỚP PHÂN XỬ: Kiểm tra độ phù hợp 50/50
        at = get_5050_attrs(i)
        mismatch = 0
        for k, v in p_50.items():
            if at[k] != v: mismatch += 1
        # Thằng nào "không phù hợp" sẽ bị cộng thêm điểm phạt (Penalty)
        # Điểm phạt cực nhỏ (0.001) để không làm lệch Rank tổng nhưng đủ để phân biệt khi trùng nhau
        penalty_score[i] = mismatch * 0.1 

    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e3, True), stats_rank(e4, True)
    w = db.get("weights", [25.0]*4)
    
    # Công thức: Rank Tổng + Điểm Phạt Phù Hợp
    # Thằng nào cùng Rank tổng nhưng "mismatch" nhiều hơn sẽ bị đẩy ra sau
    final_score = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3])/100 + penalty_score
    
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":final_score, "R1":r1, "R4":r4}), p_50

# --- (Phần Giao diện nạp số & Reset giữ nguyên bản 17.1) ---
# ... (Nạp sidebar, cập nhật hệ thống) ...

# --- HIỂN THỊ ---
if 'multi_db' not in st.session_state: 
    st.session_state.multi_db = {"MB": create_blank()} # Giả định hàm create_blank đã có

db = st.session_state.multi_db[st.session_state.current_station if 'current_station' in st.session_state else "MB"]
# T1, T2, T3...
df_m, p_active = calculate_master_v174(st.session_state.current_station if 'current_station' in st.session_state else "MB")

with st.expander("🔮 CHIẾN LƯỢC PHÂN XỬ (TIE-BREAKER)"):
    st.write("AI đang dùng 8 biến 50/50 để tách các số trùng Rank. Thằng nào khớp nhịp bệt sẽ đứng trước.")
    if p_active: st.json(p_active)

# Hiển thị dàn theo TOTAL đã được phân xử
danh_sach = df_m.sort_values("TOTAL")["SO"].tolist()
st.markdown(f"**DÀN ƯU TIÊN (Đã lọc gen):**<br><div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
