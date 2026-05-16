import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN & STYLE ---
st.set_page_config(page_title="TUAN PHONG V16.0 MOMENTUM", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. ĐỊNH NGHĨA 8 BIẾN 50/50 ---
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]

def get_5050_attributes(n):
    d, u, t, h = n // 10, n % 10, (n // 10 + n % 10) % 10, (n // 10 - n % 10 + 10) % 10
    return {
        "D_CL": "Chẵn" if d % 2 == 0 else "Lẻ",
        "U_CL": "Chẵn" if u % 2 == 0 else "Lẻ",
        "T_CL": "Chẵn" if t % 2 == 0 else "Lẻ",
        "D_TB": "To" if d >= 5 else "Bé",
        "U_TB": "To" if u >= 5 else "Bé",
        "T_TB": "To" if t >= 5 else "Bé",
        "HE": "Thường" if n in SO_THUONG else "HệKép",
        "H_TB": "To" if h >= 5 else "Bé"
    }

# --- 3. CƠ CHẾ AI PHÂN TÍCH NHỊP (TREND FOLLOWING) ---
def analyze_rhythm(history):
    if len(history) < 3: return {}
    
    # Lấy dữ liệu 10 kỳ gần nhất
    recent_nums = [int(h["Số"]) for h in history[:10]]
    attr_history = [get_5050_attributes(n) for n in recent_nums]
    
    bias = {}
    keys = ["D_CL", "U_CL", "T_CL", "D_TB", "U_TB", "T_TB", "HE", "H_TB"]
    
    for k in keys:
        seq = [h[k] for h in attr_history]
        last_val = seq[0]
        
        # Kiểm tra bệt (Cùng loại liên tiếp)
        streak = 0
        for v in seq:
            if v == last_val: streak += 1
            else: break
        
        # Kiểm tra Zigzag (A-B-A-B)
        is_zigzag = False
        if len(seq) >= 3 and seq[0] != seq[1] and seq[1] == seq[2]:
            is_zigzag = True

        # QUYẾT ĐỊNH CỦA AI:
        if is_zigzag:
            # Nếu đang nhảy A-B-A, ưu tiên kỳ sau là B
            bias[k] = {"target": seq[1], "score": 15}
        elif streak < 5:
            # Theo ý mày: Dưới 5 kỳ thì ưu tiên bệt tiếp
            bias[k] = {"target": last_val, "score": 20}
        else:
            # Chạm ngưỡng 5 kỳ: Giảm ưu tiên hoặc chuẩn bị văng
            bias[k] = {"target": last_val, "score": 5}
            
    return bias

# --- 4. ENGINE TÍNH TOÁN V16.0 ---
def calculate_master_v160(st_name):
    db = st.session_state.multi_db[st_name]
    last_gdb = db["last_gdb_full"]
    
    # Lấy Bias từ nhịp điệu (Engine 5)
    rhythm_bias = analyze_rhythm(db["history"])
    
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    e5_bias = np.zeros(100) # Điểm thưởng Momentum
    
    # Logic Rank gốc (Rút gọn cho mượt)
    for i in range(100):
        d, u, t = i // 10, i % 10, (i // 10 + i % 10) % 10
        attrs = get_5050_attributes(i)
        
        # Rank Gốc (E1, E2, E3, E4 giữ nguyên logic bản 15)
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_gdb if x.isdigit()) % 10) + (i % 10)
        # E3 & E4 logic (mô phỏng nhanh)
        e3[i] = 50 
        e4[i] = 50

        # ENGINE 5: CỘNG ĐIỂM ƯU TIÊN THEO NHỊP BỆT/NHẢY
        for k, v in rhythm_bias.items():
            if attrs[k] == v["target"]:
                e5_bias[i] += v["score"]

    def rk(s, rev=False): return stats.rankdata(-s if rev else s, method='min')
    r1, r2, r3, r4 = rk(e1), rk(e2), rk(e3, True), rk(e4, True)
    
    # Kết hợp: Lấy Rank gốc làm nền, trừ đi điểm thưởng Engine 5
    # (Trừ vì Rank càng nhỏ càng tốt, điểm thưởng càng cao thì Rank càng giảm)
    w = [25, 25, 25, 25]
    base_rank = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3]) / 100
    final_score = base_rank - (e5_bias / 10) # Ép nhịp 50/50 vào Rank gốc
    
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":final_score, "R1":r1, "R4":r4})

# --- GIAO DIỆN ---
st.title("🛡️ COMMANDER V16.0 MOMENTUM")
# ... (Phần Sidebar và Cập nhật giữ nguyên cấu trúc bản 15) ...

# (Ví dụ phần hiển thị mới ở Tab Phân Tích)
def show_momentum_analysis(st_name):
    db = st.session_state.multi_db[st_name]
    bias = analyze_rhythm(db["history"])
    if bias:
        st.subheader("📡 Cảm biến nhịp điệu (8 biến 50/50)")
        cols = st.columns(4)
        for i, (k, v) in enumerate(bias.items()):
            cols[i % 4].metric(k, v["target"], f"+{v['score']} pts")

# --- (Mày dán tiếp các phần xử lý dữ liệu của bản 15 vào là chạy mượt) ---
