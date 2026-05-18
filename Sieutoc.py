import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
from itertools import combinations

# --- 1. CONFIG ---
st.set_page_config(page_title="8-BIT INFINITE V4.5", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 0.72rem !important; }
    .dan-box { background-color: #ffffff; border: 2px solid #1e3a8a; border-radius: 10px; padding: 10px; font-family: monospace; font-weight: 700; color: #1e3a8a; text-align: center; font-size: 1rem; }
    .stMetric { background: #1e293b; padding: 10px; border-radius: 8px; color: #00d9ff; }
    .deep-scan-card { background: #0f172a; color: #32cd32; padding: 10px; border-left: 5px solid #32cd32; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
SO_THUONG = [2,3,4,6,8,13,15,17,18,19,20,24,25,26,28,30,31,35,37,39,40,42,46,47,48,51,52,53,57,59,60,62,64,68,69,71,73,74,75,79,80,81,82,84,86,91,93,95,96,97]
BIT_LABELS = ["Đ.CL", "Đu.CL", "T.CL", "Đ.TB", "Đu.TB", "T.TB", "Hệ", "Hi.TB"]

def get_8bit(n):
    try:
        val = int(n); d, u = val // 10, val % 10
        return [1 if d % 2 != 0 else 0, 1 if u % 2 != 0 else 0, 1 if (d+u) % 2 != 0 else 0,
                1 if d >= 5 else 0, 1 if u >= 5 else 0, 1 if (d+u) % 10 >= 5 else 0,
                1 if val in SO_THUONG else 0, 1 if (d-u+10) % 10 >= 5 else 0]
    except: return [0]*8

# --- 3. MÁY QUÉT VÔ CỰC (INFINITE SCAN) ---
def infinite_deep_scan(history, last_n):
    if len(history) < 2: return [0.5]*8, []
    
    current_bits = get_8bit(last_n)
    all_history_bits = [get_8bit(h["Số"]) for h in history][::-1]
    
    final_probs = np.array([0.0] * 8)
    total_weight = 0.0
    insights = []

    # Cấu hình các tầng quét (Số bit cố định, Số kỳ quét, Trọng số)
    layers = [
        {"bits": 1, "lookback": 10, "weight": 0.2},
        {"bits": 2, "lookback": 22, "weight": 0.3},
        {"bits": 3, "lookback": 60, "weight": 0.3},
        {"bits": 4, "lookback": 120, "weight": 0.2}
    ]

    for layer in layers:
        num_fixed = layer["bits"]
        lookback = layer["lookback"]
        weight = layer["weight"]
        
        if len(history) < lookback: continue # Bỏ qua nếu ko đủ dữ liệu tầng đó

        # Lấy dữ liệu theo lookback
        bits_segment = all_history_bits[-lookback:]
        
        # Tạo tổ hợp các vị trí bit để cố định
        combos = list(combinations(range(8), num_fixed))
        
        layer_scores = np.zeros(8)
        layer_match_count = 0
        
        for combo in combos:
            # Trạng thái hiện tại của tổ hợp bit này
            target_states = [current_bits[idx] for idx in combo]
            
            # Tìm trong quá khứ
            matches = []
            for k in range(len(bits_segment) - 1):
                if all(bits_segment[k][idx] == target_states[i] for i, idx in enumerate(combo)):
                    matches.append(bits_segment[k+1])
            
            if matches:
                ratios = np.mean(matches, axis=0)
                layer_scores += ratios
                layer_match_count += 1
                
                # Lưu lại những tổ hợp "độc" có xác suất tuyệt đối
                if (np.max(ratios) >= 0.9 or np.min(ratios) <= 0.1) and num_fixed >= 3:
                    insights.append({
                        "Cấp độ": f"{num_fixed}-Bit",
                        "Tổ hợp": ", ".join([BIT_LABELS[i] for i in combo]),
                        "Mẫu": len(matches),
                        "Xác suất": f"{int(np.max(ratios)*100)}%"
                    })
        
        if layer_match_count > 0:
            final_probs += (layer_scores / layer_match_count) * weight
            total_weight += weight

    return (final_probs / total_weight).tolist(), insights

def get_v45_rank(history, last_n):
    probs, insights = infinite_deep_scan(history, last_n)
    scores = []
    for i in range(100):
        bits = get_8bit(i)
        match = sum(bits[j] * probs[j] + (1 - bits[j]) * (1 - probs[j]) for j in range(8))
        scores.append({"S": f"{i:02d}", "M": match})
    df = pd.DataFrame(scores).sort_values("M", ascending=False)
    df['R'] = range(1, 101)
    return df, probs, insights

# --- 4. GIAO DIỆN ---
if 'history' not in st.session_state: st.session_state.history = []
if 'last_n' not in st.session_state: st.session_state.last_n = -1

st.title("🛡️ 8-BIT INFINITE QUANTUM V4.5")

with st.sidebar:
    st.header("📂 DỮ LIỆU")
    up = st.file_uploader("Nạp lịch sử lớn (JSON):", type="json")
    if up:
        data = json.load(up)
        st.session_state.history = sorted(data.get("history", []), key=lambda x: int(x["Kỳ"]), reverse=True)
        st.session_state.last_n = int(st.session_state.history[0]["Số"])
        st.rerun()
    st.download_button("💾 Backup", json.dumps({"history": st.session_state.history, "last_n": st.session_state.last_n}), "8bit_v4.5.json")
    if st.button("🔴 RESET"): st.session_state.history = []; st.rerun()

# Nhập liệu
with st.expander("📝 NHẬP KẾT QUẢ KỲ MỚI", expanded=True):
    c1, c2, c3 = st.columns(3)
    n_in = c1.text_input("GĐB:")
    k_in = c2.number_input("Kỳ:", value=len(st.session_state.history)+1)
    d_in = c3.text_input("Ngày:", datetime.now().strftime("%d/%m"))
    if st.button("🚀 CHẠY PHỄU LỌC VÔ CỰC"):
        val = int(n_in[-2:])
        df_r, _, _ = get_v45_rank(st.session_state.history, st.session_state.last_n)
        r_val = df_r[df_r['S'] == f"{val:02d}"]['R'].values[0] if not df_r.empty else 0
        st.session_state.history.insert(0, {"Ngày": d_in, "Kỳ": int(k_in), "Số": f"{val:02d}", "Rank": r_val})
        st.session_state.last_n = val
        st.rerun()

if st.session_state.history:
    df_rank, probs, insights = get_v45_rank(st.session_state.history, st.session_state.last_n)
    t1, t2, t3 = st.tabs(["🎯 DÀN TINH ANH V4.5", "🔍 DEEP SCAN INSIGHTS", "📊 NHẬT KÝ"])
    
    with t1:
        st.write(f"🔢 Số gốc: **{st.session_state.last_n:02d}** | Dữ liệu: **{len(st.session_state.history)} kỳ**")
        ca, cb = st.columns(2)
        ca.markdown(f"**Dàn A (50 số):** <div class='dan-box'>{' '.join(df_rank.head(50)['S'].tolist())}</div>", unsafe_allow_html=True)
        cb.markdown(f"**Dàn B (36 số):** <div class='dan-box'>{' '.join(df_rank.head(36)['S'].tolist())}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.write("📊 **Xác suất hội tụ đa tầng:**")
        cols = st.columns(8)
        for i, (label, p) in enumerate(zip(BIT_LABELS, probs)):
            cols[i].metric(label, f"{int(p*100)}%")

    with t2:
        st.header("⚡ CẢNH BÁO TỔ HỢP SÂU (3-BIT & 4-BIT)")
        if insights:
            for item in insights:
                st.markdown(f"<div class='deep-scan-card'>🔥 {item['Cấp độ']} nòng cốt: Tổ hợp [{item['Tổ hợp']}] có mẫu {item['Mẫu']} kỳ - Xác suất nổ: {item['Xác suất']}</div>", unsafe_allow_html=True)
        else:
            st.warning("Dữ liệu chưa đủ lớn để kích hoạt Deep Scan (Cần > 60 kỳ cho 3-Bit, > 120 kỳ cho 4-Bit).")

    with t3:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
