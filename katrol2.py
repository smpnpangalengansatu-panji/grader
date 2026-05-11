import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Smart Grader V7 - Bonus Feature", layout="wide")

st.title("📊 Smart Grader V7.0 (Fitur Bonus Nilai Atas)")
st.markdown("Fitur ini memungkinkan guru memberikan apresiasi lebih bagi siswa yang nilainya melampaui Batas Ceiling.")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
df_template = pd.DataFrame({'Nama Siswa': ['Siswa A', 'Siswa B', 'Siswa C'], 'Nilai Asli': [98, 80, 30]})
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
            rerata = int(temp_series.mean())
            rec_floor = int((temp_series.min() + rerata) / 2)
            rec_ceil = int(temp_series.quantile(0.90))

            st.info(f"💡 Statistik Kelas: Min **{temp_series.min()}**, Max **{temp_series.max()}**, Rerata **{rerata}**")
            
            col1, col2 = st.columns(2)
            with col1:
                target_min = st.number_input("Target Nilai Min (KKTP)", value=75)
                target_max = st.number_input("Target Nilai Max", value=95)
            with col2:
                floor_val = st.number_input("Batas Floor (Lantai)", value=rec_floor)
                ceil_val = st.number_input("Batas Ceiling (Langit)", value=rec_ceil)
            
            # FITUR BARU: Tambahan Nilai untuk Siswa di atas Ceiling
            st.subheader("🌟 Apresiasi Khusus")
            bonus_top = st.number_input("Tambahan Nilai untuk Siswa di atas Ceiling", value=2, 
                                        help="Siswa yang nilai aslinya > Ceiling akan diberikan nilai (Target Max + Bonus ini).")

            if st.button("🚀 Proses Penyesuaian Nilai"):
                df_clean = df.copy()
                df_clean[kolom_nilai] = pd.to_numeric(df_clean[kolom_nilai], errors='coerce')
                
                def hitung_final(x):
                    if pd.isna(x): return x
                    
                    # LOGIKA BARU: Jika nilai di atas atau sama dengan Ceiling
                    if x >= ceil_val:
                        # Nilai diberikan Target Max + Bonus manual
                        # Kita batasi agar tidak lewat 100 kecuali Anda mengizinkannya
                        return min(100, target_max + bonus_top)
                    
                    # Proses Scaling untuk nilai di bawah ceiling
                    x_calc = max(x, floor_val) # Terapkan Floor
                    
                    if ceil_val == floor_val:
                        return float(target_min)
                    
                    skala = ((x_calc - floor_val) / (ceil_val - floor_val)) * (target_max - target_min) + target_min
                    return round(skala, 0)

                df_clean['Nilai_Baru'] = df_clean[kolom_nilai].apply(hitung_final)
                
                st.success(f"✅ Berhasil! Siswa istimewa (> {ceil_val}) mendapatkan nilai apresiasi {target_max + bonus_top}.")
                st.dataframe(df_clean, use_container_width=True)

                # DOWNLOAD
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_clean.to_excel(writer, index=False)
                st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Hasil_Nilai_Bonus.xlsx")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
