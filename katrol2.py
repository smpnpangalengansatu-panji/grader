import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Smart Grader SMP V4 - Full Control", layout="wide")

st.title("📊 Smart Grader SMP V4.0 (Floor & Ceiling Control)")
st.markdown("Kendali penuh untuk hasil evaluasi yang adil dan proporsional.")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
df_template = pd.DataFrame({'Nama Siswa': ['Siswa A', 'Siswa B'], 'Nilai Asli': [85, 30]})
buffer_template = io.BytesIO()
with pd.ExcelWriter(buffer_template, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False)

st.sidebar.download_button("📥 Download Template .xlsx", data=buffer_template.getvalue(), file_name="Template_Nilai.xlsx")

# --- AREA UTAMA ---
uploaded_file = st.file_uploader("Upload file Excel Anda", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        st.subheader("⚙️ Pengaturan Batas Ekstrem (Outlier)")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            kolom_nilai = st.selectbox("Kolom Nilai", df.columns)
        with col2:
            target_min = st.number_input("Target Min", value=75)
        with col3:
            target_max = st.number_input("Target Max", value=95)
        with col4:
            floor_val = st.number_input("Batas Lantai (Min)", value=40)
        with col5:
            # FITUR BARU: Ceiling Value
            ceil_val = st.number_input("Batas Langit (Max)", value=85)

        if st.button("🚀 Proses Nilai"):
            df[kolom_nilai] = pd.to_numeric(df[kolom_nilai], errors='coerce')
            df_clean = df.dropna(subset=[kolom_nilai]).copy()

            if not df_clean.empty:
                # Penerapan Floor & Ceiling (Clipping)
                # Nilai di bawah floor_val jadi floor_val, di atas ceil_val jadi ceil_val
                df_clean['Nilai_Kalkulasi'] = df_clean[kolom_nilai].clip(lower=floor_val, upper=ceil_val)
                
                min_calc = df_clean['Nilai_Kalkulasi'].min()
                max_calc = df_clean['Nilai_Kalkulasi'].max()

                def scale_nilai(x):
                    if max_calc == min_calc: return float(target_min)
                    hasil = ((x - min_calc) / (max_calc - min_calc)) * (target_max - target_min) + target_min
                    return round(hasil, 0)

                df_clean['Nilai_Baru'] = df_clean['Nilai_Kalkulasi'].apply(scale_nilai)
                df_final = df_clean.drop(columns=['Nilai_Kalkulasi'])

                st.success(f"✅ Selesai! Menggunakan rentang asli {floor_val} - {ceil_val}")
                st.dataframe(df_final, use_container_width=True)

                # DOWNLOAD
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Nilai_Final_V4.xlsx")
                
    except Exception as e:
        st.error(f"Error: {e}")
