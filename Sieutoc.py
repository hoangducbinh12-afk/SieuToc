import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- 1. CONFIG MOBILE ---
st.set_page_config(page_title="TUAN PHONG V19.5", layout="centered")
st.markdown("""<style>
    .dan-box { background-color: white; border-radius: 10px; padding: 10px; border: 1px solid #d1d5db; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #1e293b; font-size: 0.95rem; line-height: 1.6; text-align: center; }
    .dan-1 { border-left: 5px solid #10b981; background-color: #f0fdf4; }
    .dan-2 { border-left: 5px solid #3b82f6; background-color: #eff6ff; }
    .stTable td, .stTable th { font-size: 0.72rem !important; padding: 2px !important; text-align: center !important; white-space: nowrap; }
</style>""", unsafe_allow_html=True)

# --- 2. LOGIC TOÁN HỌC ---
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
    return np.argsort(np.argsort(-vals if rev else vals)) + 1

# --- 3. ENGINE MASTER LOGIC (V19.5) ---
def calculate_master(use_ai):
    db = st.session_state.db
    last_g = db.get("last_gdb_full", "00000")
    
    # 1. Tính 4 Rank gốc
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    mt = build_mt_120(last_g)
    v_e3 = [sum(db["bang_b_points"][idx].get("dau", 1) for idx, v in enumerate(mt) if v == n) for n in range(10)]
    dk, uk = last_g[-2:-1] if len(last_g)>=2 else "0", last_g[-1:] if len(last_g)>=1 else "0"
    
    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = db["dau"][d] + db["duoi"][u] + db["tong"][t]
        e2[i] = (sum(int(x) for x in last_g if x.isdigit()) % 10) + u
        e3[i] = v_e3[d] + v_e3[u]
        if dk in db["ref_dau"]: e4[i] += db["ref_dau"][dk]["d"][d]
        if uk in db["ref_duoi"]: e4[i] += db["ref_duoi"][uk]["u"][u]
    
    r1, r2, r3, r4 = stats_rank(e1), stats_rank(e2), stats_rank(e3, True), stats_rank(e4, True)
    
    # 2. Tính TBC làm rào chắn
    avg_rank = (r1 + r2 + r3 + r4) / 4
    
    # 3. Tính điểm đối trọng (Ưu tiên hạng giống)
    if use_ai and len(db["history"]) >= 3:
        sc = [np.mean([h.get(f"Rank_E{i+1}", 50) for h in db["history"][:15]]) / (np.std([h.get(f"Rank_E{i+1}", 50) for h in db["history"][:15]]) or 1) for i in range(4)]
        w = [round((s/sum(sc))*100, 1) for s in sc]
    else: w = db.get("weights", [25.0]*4)
    
    raw_score = (r1*w[0] + r2*w[1] + r3*w[2] + r4*w[3]) / 100
    
    # 4. CHỐT CHẶN: Điểm cuối không được vượt quá Trung Bình Cộng (Không đưa xuống dưới TBC)
    final_score = np.where(raw_score > avg_rank, avg_rank, raw_score)
    
    return pd.DataFrame({"SO":[f"{k:02d}" for k in range(100)], "TOTAL":final_score, "R1":r1, "R2":r2, "R3":r3, "R4":r4}), w

# --- 4. KHỞI TẠO & GIAO DIỆN (GIỮ NGUYÊN KHUNG V19) ---
if 'db' not in st.session_state:
    st.session_state.db = {"dau":[0]*10, "duoi":[0]*10, "tong":[0]*10, "last_gdb_full":"00000", "ky_quay":1, "history":[], "bang_b_points":[{"dau":1} for _ in range(120)], "ref_dau":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)}, "ref_duoi":{str(i):{"d":[0]*10,"u":[0]*10} for i in range(10)}, "weights":[25.0]*4}
if 'num1' not in st.session_state: st.session_state.num1 = 11
if 'num2' not in st.session_state: st.session_state.num2 = 37

db = st.session_state.db
st.markdown("<h3 style='text-align: center;'>🛡️ TUAN PHONG V19.5 MASTER</h3>", unsafe_allow_html=True)

c_day, c_gdb, c_ky = st.columns([1.2, 1.5, 1])
with c_day: day_in = st.text_input("Ngày:", value=datetime.now().strftime("%d/%m"))
with c_gdb: gdb_now = st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"])
with c_ky: ky_now = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

if st.button("🚀 CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True):
    if len(gdb_now) >= 5:
        df_old, _ = calculate_master(st.session_state.get('ai_auto_w', True))
        target = f"{int(gdb_now[-2:]):02d}"
        db["history"].insert(0, {"Ngày": day_in, "Kỳ": int(ky_now), "Số": target, "R_AI": int(stats_rank(df_old["TOTAL"])[df_old[df_old['SO']==target].index[0]]), "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]), "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]), "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]), "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])})
        db["last_gdb_full"], db["ky_quay"] = gdb_now, ky_now + 1
        st.rerun()

tab_dan, tab_log, tab_setup = st.tabs(["🎯 DÀN", "📊 NHẬT KÝ", "⚖️ AI"])
with tab_dan:
    is_ai = st.toggle("🤖 AI Mode", key="ai_auto_w", value=True)
    df_res, w_active = calculate_master(is_ai)
    c_n1, c_n2 = st.columns(2)
    st.session_state.num1 = c_n1.number_input("Dàn 1:", 1, 90, st.session_state.num1)
    st.session_state.num2 = c_n2.number_input("Dàn 2:", 1, 90, st.session_state.num2)
    ds = df_res.sort_values("TOTAL")["SO"].tolist()
    st.markdown(f"<div class='dan-box dan-1'>{', '.join(ds[:st.session_state.num1])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dan-box dan-2'>{', '.join(ds[:st.session_state.num2])}</div>", unsafe_allow_html=True)

with tab_log:
    if db["history"]: st.table(pd.DataFrame(db["history"]).head(20)[["Ngày", "Kỳ", "Số", "R_AI", "Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]])
with tab_setup:
    st.write(f"E1:{w_active[0]}% | E2:{w_active[1]}% | E3:{w_active[2]}% | E4:{w_active[3]}%")
    st.download_button("💾 Lưu File", json.dumps(st.session_state.db), "data.json", use_container_width=True)
    up = st.file_uploader("Nạp File", type="json")
    if up: st.session_state.db = json.load(up); st.rerun()
