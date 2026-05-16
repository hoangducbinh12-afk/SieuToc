import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. GIAO DIỆN ---
st.set_page_config(page_title="TUAN PHONG V17.7 FIX RANK", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT ---
B_D = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}; B_A = {0:7, 1:4, 2:9, 3:6, 4:1, 5:8, 6:3, 7:0, 8:5, 9:2}

def build_mt_120(g):
    g_str = str(g).strip()
    if len(g_str) < 5: return [0]*120
    dts = [int(x) for x in g_str[-5:]]
    tien = [[(d + s) % 10 for d in dts] for s in range(10)]; bong = [dts]; c = dts
    for i in range(14):
        c = [B_D[x] for x in c] if i%2==0 else [B_A[x] for x in c]
        bong.append(c)
    return ([x for sub in tien for x in sub] + [x for sub in bong for x in sub])[:120]

def stats_rank(arr, rev=False):
    vals = np.array(arr)
    # Dùng lexsort để đảm bảo nếu trùng điểm thì không bị trùng Rank tuyệt đối
    return np.argsort(np.argsort(-vals if rev else vals)) + 1

# --- 3. ENGINE TÍNH TOÁN (ĐÃ SỬA LỖI TRÙNG RANK) ---
def calculate_master(st_name):
    db = st.session_state.multi_db[st_name]
    w_calc = run_ai_weights_v2(db["history"]) if st.session_state.get('ai_auto_w', False) else db.get("weights", [25.0]*4)
    
    last_g = db.get("last_gdb_full", "00000")
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    
    # E3: Tịnh tiến
    mt = build_mt_120(last_g)
    val_e3 = [sum(db["bang_b_points"][idx].get("dau", 1) for idx, v in enumerate(mt) if v == n) for n in range(10)]
    
    # Lấy dữ liệu kỳ trước cho E4
    dk = last_g[-2:-1] if len(last_g)>=2 else "0"
    uk = last_g[-1:] if len(last_g)>=1 else "0"

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        # E1: KHAN (Gốc 1)
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        
        # E2: GĐB (Gốc 2)
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + u
        
        # E3: TỊNH TIẾN (Gốc 3)
        e3[i] = val_e3[d] + val_e3[u]
        
        # E4: PHẢN XẠ (Gốc 4 - ĐÃ TÁCH RIÊNG)
        # Chỉ lấy từ bộ nhớ ref_dau và ref_duoi, không cộng thêm điểm khan
        if dk in db["ref_dau"]: e4[i] += db["ref_dau"][dk]["d"][d]
        if uk in db["ref_duoi"]: e4[i] += db["ref_duoi"][uk]["u"][u]

    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e3, True), stats_rank(e4, True)
    
    # Tính toán Total
    total = (r1*w_calc[0] + r2*w_calc[1] + r3*w_calc[2] + r4*w_calc[3])/100
    
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":total, "R1":r1, "R2":r2, "R3":r3, "R4":r4}), w_calc

# --- 4. HÀM PHỤ TRỢ (GIỮ NGUYÊN) ---
def run_ai_weights_v2(history):
    if len(history) < 3: return [25.0]*4
    scores = []
    for k in ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]:
        vals = [h.get(k, 50) for h in history[:15]]
        avg = np.mean(vals); std = np.std(vals) if np.std(vals) > 0 else 1
        scores.append(avg / std)
    t = sum(scores); final_w = [round((s/t)*100, 1) for s in scores]
    final_w[0] = round(final_w[0] + (100.0 - sum(final_w)), 1)
    return final_w

# --- (Phần Giao diện nạp số, Sidebar... giữ nguyên bản 17.6) ---
# ...
