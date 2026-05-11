import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Smart Grader V6 - Smart Protection", layout="wide")

st.title("📊 Smart Grader V6.0 (Perlindungan Nilai Tinggi)")
st.markdown("""
Aplikasi ini memastikan siswa yang nilainya sudah tinggi **tidak akan turun**. 
Siswa yang melampaui Target Maksimal akan dipertahankan nilai aslinya.
""")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
df_template = pd.DataFrame({'Nama Siswa': ['Siswa A', 'Siswa B', 'Siswa C'], 'Nilai Asli': [97, 80, 30]})
buffer_template = io.BytesIO()
with pd.ExcelWriter(buffer_template, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False)
st.sidebar.download_button("📥 Download Template .xlsx", data=buffer_template.getvalue(), file_name="Template_Nilai.xlsx")

# --- AREA UTAMA ---
uploaded_file = st.file_uploader("Upload file Excel Anda", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        kolom_nilai = st.selectbox("Pilih Kolom Nilai Asli", df.columns)
        
        temp_series = pd.to_numeric(df[kolom_nilai], errors='coerce').dropna()
        
        if not temp_series.empty:
            # Rekomendasi
            rerata = temp_series.mean()
            rec_floor = int((temp_series.min() + rerata) / 2)
            rec_ceil = int(temp_series.quantile(0.90))

            st.info(f"💡 Saran: Floor **{rec_floor}**, Ceiling **{rec_ceil}**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                target_min = st.number_input("Target Nilai Min", value=75)
            with col2:
                target_max = st.number_input("Target Nilai Max", value=95)
            with col3:
                floor_val = st.number_input("Batas Floor", value=rec_floor)
            with col4:
                ceil_val = st.number_input("Batas Ceiling", value=rec_ceil)

            if st.button("🚀 Proses Penyesuaian Nilai"):
                df_clean = df.copy()
                df_clean[kolom_nilai] = pd.to_numeric(df_clean[kolom_nilai], errors='coerce')
                
                def hitung_final(x):
                    if pd.isna(x): return x
                    
                    # LOGIKA PERLINDUNGAN: Jika nilai sudah di atas Target Max, JANGAN DIUBAH
                    if x >= target_max:
                        return x
                    
                    # Proses Scaling untuk nilai lainnya
                    # 1. Terapkan Floor & Ceiling pada input sementara
                    x_calc = max(min(x, ceil_val), floor_val)
                    
                    # 2. Hitung skala
                    # Kita gunakan ceil_val dan floor_val sebagai patokan min-max kalkulasi
                    if ceil_val == floor_val:
                        return float(target_min)
                    
                    skala = ((x_calc - floor_val) / (ceil_val - floor_val)) * (target_max - target_min) + target_min
                    return round(skala, 0)

                df_clean['Nilai_Baru'] = df_clean[kolom_nilai].apply(hitung_final)
                
                st.success("✅ Nilai diproses. Siswa dengan nilai sangat tinggi tetap dipertahankan!")
                st.dataframe(df_clean, use_container_width=True)

                # DOWNLOAD
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_clean.to_excel(writer, index=False)
                st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Hasil_Nilai_V6.xlsx")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
