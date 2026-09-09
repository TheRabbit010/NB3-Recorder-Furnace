import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import re
import io

# 1. ตั้งค่า Page Config
st.set_page_config(
    page_title="Recorder NB3 Furnace",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ปรับแต่ง CSS สำหรับ Dark Mode
st.markdown("""
    <style>
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            display: none !important;
        }
        [data-testid="stToolbar"] {
            display: none !important;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
        }
        .stMarkdown, h1, h2, h3, p, span, label {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] div.stButton > button {
            background-color: #21262d !important;
            color: #ffffff !important;
            border: 1px solid #F0B90B !important;
            font-weight: bold !important;
            width: 100% !important;
            padding: 8px 16px !important;
        }
        [data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #F0B90B !important;
            color: #000000 !important;
        }
        [data-testid="stFileUploader"] {
            background-color: #161b22 !important;
            border: 1.5px solid #F0B90B !important;
            border-radius: 8px !important;
            padding: 10px !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #1c2128 !important;
            border: 1px dashed #F0B90B !important;
            border-radius: 6px !important;
        }
        [data-testid="stFileUploader"] section div, 
        [data-testid="stFileUploader"] section span,
        [data-testid="stFileUploader"] section small {
            color: #e6edf3 !important;
        }
        [data-testid="stFileUploaderFileData"],
        [data-testid="stFileUploaderFileData"] > div,
        [data-testid="stFileUploaderFile"] {
            background-color: #21262d !important;
            border: 1px solid #F0B90B !important;
            border-radius: 6px !important;
        }
        [data-testid="stFileUploaderFileData"] *,
        [data-testid="stFileUploaderFile"] * {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        [data-testid="stExpander"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] details summary {
            background-color: #21262d !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] details summary * {
            color: #ffffff !important;
        }
        [data-testid="stDataFrame"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }
        div[data-testid="stDataFrame"] div[role="grid"] {
            background-color: #161b22 !important;
            color: #ffffff !important;
        }
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #21262d !important;
            color: #ffffff !important;
        }
        div[data-baseweb="input"] {
            background-color: #21262d !important;
            border: 1px solid #30363d !important;
            color: #ffffff !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="input"] input {
            background-color: #21262d !important;
            color: #ffffff !important;
        }
        div.stDownloadButton > button {
            background-color: #21262d !important;
            border: 1.5px solid #F0B90B !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease-in-out;
        }
        div.stDownloadButton > button, 
        div.stDownloadButton > button *,
        div.stDownloadButton > button p,
        div.stDownloadButton > button span {
            color: #ffffff !important;
            font-weight: bold !important;
            font-size: 15px !important;
        }
        div.stDownloadButton > button:hover {
            background-color: #F0B90B !important;
            border-color: #F0B90B !important;
        }
        div.stDownloadButton > button:hover,
        div.stDownloadButton > button:hover *,
        div.stDownloadButton > button:hover p,
        div.stDownloadButton > button:hover span {
            color: #000000 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 Recorder NB3 Furnace")

# 3. ฟังก์ชันสแกนและแกะข้อมูลบรรทัดต่อบรรทัดแบบยืดหยุ่นสูง
def parse_single_file(uploaded_file):
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    
    text_content = None
    encodings = ['cp932', 'shift_jis', 'utf-8-sig', 'utf-8', 'tis-620', 'latin1']
    for enc in encodings:
        try:
            text_content = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
            
    if text_content is None:
        text_content = raw_bytes.decode('utf-8', errors='ignore')

    lines = text_content.splitlines()
    
    endheader_cols = []
    data_rows = []
    
    date_regex = re.compile(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}')
    time_regex = re.compile(r'^\d{1,2}:\d{2}:\d{2}')

    curr_date = ""

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        if line_str.startswith("#EndHeader"):
            endheader_cols = [x.strip() for x in line_str.split(",")]
            continue

        if date_regex.match(line_str) and "," not in line_str:
            curr_date = line_str
            continue

        parts = [p.strip() for p in line_str.split(",")]
        
        if date_regex.search(parts[0]):
            data_rows.append(parts)
        elif time_regex.search(parts[0]):
            dt_str = f"{curr_date} {parts[0]}".strip() if curr_date else parts[0]
            data_rows.append([dt_str] + parts[1:])

    if not data_rows:
        return pd.DataFrame()

    data_df = pd.DataFrame(data_rows)

    def find_col_by_keyword(key_pattern):
        if endheader_cols:
            for c_idx, name in enumerate(endheader_cols):
                if re.search(key_pattern, name, re.IGNORECASE):
                    return c_idx
        return None

    df = pd.DataFrame()

    col0_str = data_df[0].astype(str).str.strip()
    df["DateTime"] = pd.to_datetime(col0_str, errors="coerce", dayfirst=True)

    def extract_series(col_idx, fallback_idx, min_val=-100.0, max_val=10000.0):
        target_idx = col_idx if col_idx is not None else fallback_idx
        if target_idx is not None and target_idx < data_df.shape[1]:
            s = pd.to_numeric(data_df[target_idx], errors="coerce")
            s = s.apply(lambda x: x if (pd.notna(x) and min_val <= x <= max_val) else None)
            return s
        return pd.Series([None] * len(data_df))

    # 1) Top Zone #1 - #7
    for i in range(1, 8):
        c = find_col_by_keyword(rf'1\)TH_CH{i}Max')
        fb = 2 + (i - 1) * 3
        df[f"Top Zone #{i}"] = extract_series(c, fb, min_val=0.0, max_val=1200.0)

    # 2) Bottom Zone #1 - #7
    for i in range(1, 8):
        c = find_col_by_keyword(rf'2\)TH_CH{i}Max')
        fb = 2 + (7 + i - 1) * 3
        df[f"Bottom Zone #{i}"] = extract_series(c, fb, min_val=0.0, max_val=1200.0)

    # 3) DRYOFF1-3
    dryoff_names = ["DRYOFF1", "DRYOFF2", "DRYOFF3"]
    for i in range(1, 4):
        c = find_col_by_keyword(rf'3\)TH_CH{i}Max')
        fb = 2 + (14 + i - 1) * 3
        df[dryoff_names[i-1]] = extract_series(c, fb, min_val=0.0, max_val=1000.0)

    # 4) Oxygen & N2 Flow
    c_o2_exit = find_col_by_keyword(r'3\)TH_CH4Max')
    df["Oxygen EXIT"] = extract_series(c_o2_exit, 2 + (17) * 3, min_val=0.0, max_val=2000.0)

    c_o2_ent = find_col_by_keyword(r'3\)TH_CH5Max')
    df["Oxygen ENTRANCE"] = extract_series(c_o2_ent, 2 + (18) * 3, min_val=0.0, max_val=2000.0)

    c_n2_exit = find_col_by_keyword(r'3\)TH_CH7Max')
    df["N2 Exit"] = extract_series(c_n2_exit, 2 + (20) * 3, min_val=0.0, max_val=20000.0)

    c_n2_ent = find_col_by_keyword(r'3\)TH_CH8Max')
    df["N2 Entrance"] = extract_series(c_n2_ent, 2 + (21) * 3, min_val=0.0, max_val=20000.0)

    # 5) Cool Water Temp
    c_cool = find_col_by_keyword(r'3\)TH_CH6Max')
    df["COOL WATER TEMP"] = extract_series(c_cool, 2 + (19) * 3, min_val=-50.0, max_val=200.0)

    valid_df = df.dropna(subset=["DateTime"]).reset_index(drop=True)
    return valid_df

def process_multiple_files(uploaded_files):
    combined_dfs = []
    for file in uploaded_files:
        single_df = parse_single_file(file)
        if not single_df.empty:
            combined_dfs.append(single_df)
    
    if not combined_dfs:
        return pd.DataFrame()

    full_df = pd.concat(combined_dfs, ignore_index=True)
    full_df = full_df.drop_duplicates(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
    return full_df

# ฟังก์ชันแปลง DataFrame เป็น Binary สำหรับดาวน์โหลดเป็นไฟล์ Excel (.xlsx)
def to_excel_bytes(dataframe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = dataframe.copy()
        if pd.api.types.is_datetime64_any_dtype(df_export["DateTime"]):
            df_export["DateTime"] = df_export["DateTime"].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_export.to_excel(writer, index=False, sheet_name='Furnace Data')
    output.seek(0)
    return output.getvalue()

# 4. ฟังก์ชันตกแต่งสไตล์กราฟ
def apply_industrial_style(fig, y_title, y_range=None, is_dual_axis=False):
    layout_args = dict(
        template="plotly_dark",
        plot_bgcolor="#161b22",
        paper_bgcolor="#0e1117",
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            font=dict(color="#FFFFFF", size=12, family="Arial Bold"),
            bgcolor="rgba(27, 31, 36, 0.95)",
            bordercolor="#F0B90B",
            borderwidth=1.5,
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        xaxis=dict(
            title=dict(text="Date & Time", font=dict(color="#FFFFFF", size=12)),
            tickfont=dict(color="#CCCCCC", size=10),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="#555555",
            type="date",
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="#FFFFFF", size=12)),
            tickfont=dict(color="#CCCCCC", size=10),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            linecolor="#555555",
        ),
        height=420,
        margin=dict(l=60, r=180, t=30, b=40),
    )
    if y_range and not is_dual_axis:
        layout_args["yaxis"]["range"] = y_range
        
    fig.update_layout(**layout_args)

# ส่วน Sidebar อัปโหลดไฟล์
st.sidebar.header("📁 เมนูอัปโหลดข้อมูล")

if st.sidebar.button("🧹 เคลียร์ข้อมูลไฟล์เก่าทั้งหมด"):
    st.cache_data.clear()
    st.rerun()

uploaded_files = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ Recorder NB3 (.csv) ได้มากกว่า 1 ไฟล์", 
    type=["csv"],
    accept_multiple_files=True
)

# 5. ส่วนแสดงผลหลัก
if uploaded_files:
    try:
        raw_df = process_multiple_files(uploaded_files)
        
        if raw_df.empty:
            st.error("⚠️ ไม่พบข้อมูลวันเวลา (DateTime) ที่ถูกต้องในไฟล์ที่อัปโหลด กรุณาตรวจสอบรูปแบบไฟล์ CSV")
        else:
            st.sidebar.success(f"รวมข้อมูลสำเร็จ {len(uploaded_files)} ไฟล์ ({len(raw_df)} แถว)")

            st.sidebar.markdown("---")
            st.sidebar.header("🎛️ Dynamic Controls")
            
            min_time = raw_df["DateTime"].min().to_pydatetime()
            max_time = raw_df["DateTime"].max().to_pydatetime()
            
            selected_time = st.sidebar.slider(
                "⏱️ ช่วงเวลา:",
                min_value=min_time,
                max_value=max_time,
                value=(min_time, max_time),
                format="MM-DD HH:mm"
            )
            
            df = raw_df[(raw_df["DateTime"] >= selected_time[0]) & (raw_df["DateTime"] <= selected_time[1])].copy()

            st.sidebar.subheader("📊 เลือกกลุ่มกราฟ")
            show_g1 = st.sidebar.checkbox("1. Top Zone Temp", value=True)
            show_g2 = st.sidebar.checkbox("2. Bottom Zone Temp", value=True)
            show_g3 = st.sidebar.checkbox("3. DRYOFF Temp", value=True)
            show_g4 = st.sidebar.checkbox("4. ppm Oxygen & N2 Flow", value=True)
            show_g5 = st.sidebar.checkbox("5. Cool Water Temp", value=True)

            # 1. Top Zone Temp (#1 - #7)
            if show_g1:
                st.subheader("1) Top Zone Temperature (#1 to #7)")
                fig1 = go.Figure()
                top_colors = ["#FF0000", "#008000", "#0000FF", "#8A2BE2", "#A52A2A", "#FFA500", "#9ACD32"]
                for i in range(1, 8):
                    fig1.add_trace(go.Scatter(
                        x=df["DateTime"], 
                        y=df[f"Top Zone #{i}"], 
                        name=f"Top Zone #{i}", 
                        mode="lines", 
                        line=dict(color=top_colors[i-1], width=2)
                    ))
                apply_industrial_style(fig1, "Temperature (°C)")
                st.plotly_chart(fig1, use_container_width=True)

            # 2. Bottom Zone Temp (#1 - #7)
            if show_g2:
                st.subheader("2) Bottom Zone Temperature (#1 to #7)")
                fig2 = go.Figure()
                bottom_colors = ["#E0FFFF", "#FF1493", "#808080", "#00FF00", "#008000", "#0000FF", "#8A2BE2"]
                for i in range(1, 8):
                    fig2.add_trace(go.Scatter(
                        x=df["DateTime"], 
                        y=df[f"Bottom Zone #{i}"], 
                        name=f"Bottom Zone #{i}", 
                        mode="lines", 
                        line=dict(color=bottom_colors[i-1], width=2)
                    ))
                apply_industrial_style(fig2, "Temperature (°C)")
                st.plotly_chart(fig2, use_container_width=True)

            # 3. DRYOFF1-3
            if show_g3:
                st.subheader("3) DRYOFF Temperature (DRYOFF1 to DRYOFF3)")
                fig3 = go.Figure()
                dry_colors = ["#FFA500", "#9ACD32", "#00ECFF"]
                dryoff_names = ["DRYOFF1", "DRYOFF2", "DRYOFF3"]
                for i in range(1, 4):
                    fig3.add_trace(go.Scatter(
                        x=df["DateTime"], 
                        y=df[dryoff_names[i-1]], 
                        name=dryoff_names[i-1], 
                        mode="lines", 
                        line=dict(color=dry_colors[i-1], width=2)
                    ))
                apply_industrial_style(fig3, "Temperature (°C)")
                st.plotly_chart(fig3, use_container_width=True)

            # 4. ppm Oxygen & N2 Flow Rate (Dual Axis)
            if show_g4:
                st.subheader("4) Oxygen EXIT/ENTRANCE & N2 Flow")
                fig4 = make_subplots(specs=[[{"secondary_y": True}]])
                
                # แกน Y ซ้าย: ppm Oxygen (Scale 0-200 ppm)
                fig4.add_trace(go.Scatter(
                    x=df["DateTime"], 
                    y=df["Oxygen EXIT"], 
                    name="Oxygen EXIT", 
                    mode="lines", 
                    line=dict(color="#FF80FF", width=2)
                ), secondary_y=False)
                
                fig4.add_trace(go.Scatter(
                    x=df["DateTime"], 
                    y=df["Oxygen ENTRANCE"], 
                    name="Oxygen ENTRANCE", 
                    mode="lines", 
                    line=dict(color="#A52A2A", width=2)
                ), secondary_y=False)

                # แกน Y ขวา: N2 Flow Rate (Scale 0-1000)
                fig4.add_trace(go.Scatter(
                    x=df["DateTime"], 
                    y=df["N2 Exit"], 
                    name="N2 Exit", 
                    mode="lines", 
                    line=dict(color="#ADD8E6", width=2, dash="dash")
                ), secondary_y=True)

                fig4.add_trace(go.Scatter(
                    x=df["DateTime"], 
                    y=df["N2 Entrance"], 
                    name="N2 Entrance", 
                    mode="lines", 
                    line=dict(color="#00FF00", width=2, dash="dash")
                ), secondary_y=True)

                apply_industrial_style(fig4, "Oxygen Level (ppm)", is_dual_axis=True)
                fig4.update_layout(
                    yaxis=dict(
                        title=dict(text="Oxygen Level (ppm) [0-200]", font=dict(color="#FFFFFF", size=12)),
                        range=[0, 200],
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.08)"
                    ),
                    yaxis2=dict(
                        title=dict(text="N2 Flow Rate [0-1000]", font=dict(color="#ADD8E6", size=12)),
                        tickfont=dict(color="#ADD8E6", size=10),
                        showgrid=False,
                        overlaying="y",
                        side="right",
                        linecolor="#ADD8E6",
                        range=[0, 1000]
                    )
                )
                st.plotly_chart(fig4, use_container_width=True)

            # 5. Cool Water Temp
            if show_g5:
                st.subheader("5) COOL WATER TEMP")
                fig5 = go.Figure()
                fig5.add_trace(go.Scatter(
                    x=df["DateTime"], 
                    y=df["COOL WATER TEMP"], 
                    name="COOL WATER TEMP", 
                    mode="lines", 
                    line=dict(color="#00ecff", width=2)
                ))
                apply_industrial_style(fig5, "Cool Water Temp (°C)")
                st.plotly_chart(fig5, use_container_width=True)

            # ส่วนตรวจสอบและเลือกดาวน์โหลด Excel
            with st.expander("📊 ตรวจสอบและเลือกดาวน์โหลดตารางข้อมูล Excel (.xlsx)"):
                st.dataframe(df)
                
                st.markdown("---")
                st.markdown("##### 📥 ตัวเลือกการดาวน์โหลดไฟล์ Excel")
                
                col_opt1, col_opt2 = st.columns([2, 1])
                with col_opt1:
                    custom_filename = st.text_input(
                        "ตั้งชื่อไฟล์ดาวน์โหลด:", 
                        value="combined_recorder_nb3_data.xlsx"
                    )
                    if not custom_filename.endswith('.xlsx'):
                        custom_filename += '.xlsx'
                        
                with col_opt2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    excel_bytes = to_excel_bytes(df)
                    st.download_button(
                        label="📊 ดาวน์โหลดไฟล์ Excel",
                        data=excel_bytes,
                        file_name=custom_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")

else:
    st.info("👈 กรุณาเลือกอัปโหลดไฟล์ (.csv) ที่เมนูด้านซ้าย สามารถเลือกอัปโหลดได้มากกว่า 1 ไฟล์")
