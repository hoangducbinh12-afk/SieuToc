import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import scipy.stats as stats

# --- 1. GIAO DIỆN ---
st.set_page_config(page_title="V14.8 SIN-DYNAMIC", layout="wide")
st.markdown("""<style>
    .main-box { background-color: #ffffff; color: #1e293b; padding: 12px; border-radius: 10px; font-family: 'JetBrains Mono'; font-size: 0.82rem; border: 2px solid #3b82f6; font-weight: 700; text-align: center; }
    .stTable td { font-weight: bold !important; text-align: center !important; font-size: 11px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. QUY LUẬT ---
def get_root_val(s):
    try:
        t = sum(int(x) for x in str(s) if x.isdigit())
        while t > 9: t = sum(int(x) for x in str(t))
        return t
    except: return 1

def build_ma_tran_120(gdb_str):
    g_str = str(gdb_str).strip()
    if not g_str or len(g_str) < 5: return []
    digits = [int(d) for d in g_str[-5:]]
    return [[(d + i)%10 for d in digits] for i in range(24)] # Đơn giản hóa ma trận 120

def create_blank_station():
    return {
        "dau": [0]*10, "duoi": [0]*10, "tong": [0]*10, "hieu": [0]*10, "cham": [0]*10,
        "bang_b_points": [{"dau":1,"duoi":1,"tong":1} for _ in range(120)],
        "last_gdb_full": "00000", "ky_quay": 1, "history": [], "use_root": True,
        "weights": [25.0, 25.0, 25.0, 25.0],
        "ref_dau": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_duoi": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)},
        "ref_tong": {str(i): {"dau":[0]*10,"duoi":[0]*10,"tong":[0]*10} for i in range(10)}
    }

if 'multi_db' not in st.session_state:
    st.session_state.multi_db = {"MB": create_blank_station()}

# --- 3. THUẬT TOÁN HÌNH SIN CẢI TIẾN ---
def get_dynamic_sin_weights(st_name):
    st_db = st.session_state.multi_db[st_name]
    hist = st_db["history"]
    if len(hist) < 5: return [25.0, 25.0, 25.0, 25.0]
    
    eng_keys = ["Rank_E1", "Rank_E2", "Rank_E3", "Rank_E4"]
    raw_w = []
    for k in eng_keys:
        ranks = [h[k] for h in hist[:10]] # Xét chu kỳ 10 kỳ
        avg = np.mean(ranks)
        std = np.std(ranks)
        
        # Chiến thuật bắt đáy: Nếu Rank trung bình đang tệ (>60) nhưng dao động hẹp (đang nén)
        # -> Tăng mạnh trọng số để đón đầu cú nổ hình sin
        if avg > 55 and std < 20: 
            score = 40.0
        # Nếu đang quá đỏ (Rank < 20) -> Chuẩn bị chu kỳ dạt -> Hạ xuống
        elif avg < 20:
            score = 15.0
        else:
            score = 25.0
        raw_w.append(score)
    
    total = sum(raw_w)
    return [round((w/total)*100, 2) for w in raw_w]

def calculate_master_v148(st_name):
    st_db = st.session_state.multi_db[st_name]
    last_gdb = st_db["last_gdb_full"]
    curr_n = int(last_gdb[-2:]) if len(str(last_gdb))>=2 else 0
    
    # ÉP BUỘC TÍNH TRỌNG SỐ TRƯỚC
    st_db["weights"] = get_dynamic_sin_weights(st_name)
    
    e1, e2, e3, e4 = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    
    # Engine 3
    ma_tran = build_ma_tran_120(last_gdb)
    list_e3 = [0]*10
    if ma_tran:
        for n in range(10):
            list_e3[n] = sum(st_db["bang_b_points"][i]["dau"] for i in range(len(ma_tran)) if ma_tran[i]==n)

    for i in range(100):
        d, u, t = i//10, i%10, (i//10+i%10)%10
        e1[i] = st_db["dau"][d] + st_db["duoi"][u] + st_db["tong"][t]
        e2[i] = get_root_val(last_gdb) + get_root_val(i)
        e3[i] = list_e3[d] + list_e3[u] + list_e3[t]
        for m, k in [("ref_dau",str(curr_n//10)), ("ref_duoi",str(curr_n%10)), ("ref_tong",str((curr_n//10+curr_n%10)%10))]:
            if k in st_db[m]: e4[i] += st_db[m][k]["dau"][d] + st_db[m][k]["duoi"][u]

    def rk(scores, rev=False): return stats.rankdata(-scores if rev else scores, method='average')
    df = pd.DataFrame({"SO": [f"{k:02d}" for k in range(100)], 
                       "R1":rk(e1), "R2":rk(e2), "R3":rk(e3,True), "R4":rk(e4,True)})
    
    w = st_db["weights"]
    df["DIEM_TONG"] = (df["R1"]*w[0] + df["R2"]*w[1] + df["R3"]*w[2] + df["R4"]*w[3])/100
    return df

def process_v148():
    st_name = st.session_state.current_station
    st_db = st.session_state.multi_db[st_name]
    raw = st.session_state.gdb_in.strip()
    if len(raw)<5: return
    n = int(raw[-2:]); target = f"{n:02d}"
    df_old = calculate_master_v148(st_name)
    
    st_db["history"].insert(0, {
        "Kỳ": int(st_db["ky_quay"]), "GĐB": raw, "Số": target,
        "Rank_AI": int(stats.rankdata(df_old["DIEM_TONG"], method='min')[df_old[df_old['SO']==target].index[0]]),
        "Rank_E1": int(df_old.loc[df_old['SO']==target, 'R1'].values[0]),
        "Rank_E2": int(df_old.loc[df_old['SO']==target, 'R2'].values[0]),
        "Rank_E3": int(df_old.loc[df_old['SO']==target, 'R3'].values[0]),
        "Rank_E4": int(df_old.loc[df_old['SO']==target, 'R4'].values[0])
    })
    
    dv, duv, tv = n//10, n%10, (n//10+n%10)%10
    for i in range(10):
        st_db["dau"][i] = 0 if i==dv else st_db["dau"][i]+1
        st_db["duoi"][i] = 0 if i==duv else st_db["duoi"][i]+1
        st_db["tong"][i] = 0 if i==tv else st_db["tong"][i]+1
    
    if len(st_db["history"]) >= 2:
        c = int(st_db["history"][1]["Số"]); n_n = int(st_db["history"][0]["Số"])
        for m, k in [("ref_dau",str(c//10)), ("ref_duoi",str(c%10)), ("ref_tong",str((c//10+c%10)%10))]:
            st_db[m][k]["dau"][n_n//10]+=1; st_db[m][k]["duoi"][n_n%10]+=1
            
    st_db["last_gdb_full"], st_db["ky_quay"] = raw, st_db["ky_quay"]+1

# --- 4. GIAO DIỆN ---
st.title("🛡️ SIN-DYNAMIC V14.8")
with st.sidebar:
    st.session_state.current_station = st.selectbox("ĐÀI:", list(st.session_state.multi_db.keys()))
    if st.button("🔴 RESET"): st.session_state.clear(); st.rerun()
    up = st.file_uploader("📂 Nạp .Json", type="json")
    if up and st.button("✅ XÁC NHẬN"): st.session_state.multi_db = json.load(up); st.rerun()

db = st.session_state.multi_db[st.session_state.current_station]
c1, c2 = st.columns([3,1])
with c1: st.text_input("GĐB Vừa Ra:", value=db["last_gdb_full"], key="gdb_in")
with c2: db["ky_quay"] = st.number_input("Kỳ:", value=int(db["ky_quay"]), step=1)

st.button("🚀 CẬP NHẬT", on_click=process_v148, type="primary", use_container_width=True)

# Lệnh này sẽ kích hoạt hàm tính weights
df_m = calculate_master_v148(st.session_state.current_station)

t1, t2, t3 = st.tabs(["🎯 DÀN AI", "⚖️ ĐỐI TRỌNG SIN", "📋 NHẬT KÝ"])
with t1:
    danh_sach = df_m.sort_values("DIEM_TONG")["SO"].tolist()
    st.subheader("Dàn mỏng (36 số):")
    st.markdown(f"<div class='main-box'>{' '.join(danh_sach[:36])}</div>", unsafe_allow_html=True)
    st.subheader("Dàn tiêu chuẩn (51 số):")
    st.markdown(f"<div class='main-box' style='border-color:#10b981'>{' '.join(danh_sach[:51])}</div>", unsafe_allow_html=True)
with t2:
    st.subheader("📊 Trọng số Hình Sin thời gian thực")
    st.write("Nếu dữ liệu lịch sử > 5 kỳ, các con số dưới đây sẽ tự động nhảy:")
    st.table(pd.DataFrame({"Engine": ["E1 (Khan)", "E2 (Root)", "E3 (Tịnh Tiến)", "E4 (Phản Xạ)"], "%": db["weights"]}).set_index("Engine").T)
    st.download_button("💾 LƯU DỮ LIỆU", json.dumps(st.session_state.multi_db), "DATA_DYNAMIC.json", use_container_width=True)
with t3:
    if db["history"]:
        df_h = pd.DataFrame(db["history"])
        st.table(df_h[['Kỳ', 'GĐB', 'Số', 'Rank_AI', 'Rank_E1', 'Rank_E2', 'Rank_E3', 'Rank_E4']])
        st.line_chart(df_h["Rank_AI"])
