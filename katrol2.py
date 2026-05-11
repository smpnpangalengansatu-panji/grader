import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Smart Grader SMP V5 - Auto Suggest", layout="wide")

st.title("📊 Smart Grader SMP V5.0 (Smart Recommendation)")
st.markdown("Aplikasi akan memberikan rekomendasi batas Floor & Ceiling secara otomatis berdasarkan data Anda.")
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
        
        # Pembersihan awal untuk mencari rekomendasi
        all_cols = df.columns.tolist()
        kolom_nilai = st.selectbox("Pilih Kolom Nilai Asli", all_cols)
        
        # Konversi sementara untuk hitung statistik
        temp_series = pd.to_numeric(df[kolom_nilai], errors='coerce').dropna()
        
        if not temp_series.empty:
            # HITUNG REKOMENDASI STATISTIK
            rec_floor = int(temp_series.quantile(0.10)) # Persentil 10
            rec_ceil = int(temp_series.quantile(0.90))  # Persentil 90
            
            st.info(f"💡 **Rekomendasi Sistem:** Berdasarkan data Anda, Batas Lantai (Floor) yang ideal adalah **{rec_floor}** dan Batas Langit (Ceiling) adalah **{rec_ceil}**.")
            
            st.subheader("⚙️ Pengaturan Parameter")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                target_min = st.number_input("Target Nilai Min", value=75)
            with col2:
                target_max = st.number_input("Target Nilai Max", value=95)
            with col3:
                floor_val = st.number_input("Batas Lantai (Floor)", value=rec_floor)
                st.caption(f"Saran: {rec_floor}")
            with col4:
                ceil_val = st.number_input("Batas Langit (Ceiling)", value=rec_ceil)
                st.caption(f"Saran: {rec_ceil}")

            if st.button("🚀 Proses Penyesuaian Nilai"):
                df[kolom_nilai] = pd.to_numeric(df[kolom_nilai], errors='coerce')
                df_clean = df.dropna(subset=[kolom_nilai]).copy()

                # Proses Clipping
                df_clean['Nilai_Kalkulasi'] = df_clean[kolom_nilai].clip(lower=floor_val, upper=ceil_val)
                
                min_calc = df_clean['Nilai_Kalkulasi'].min()
                max_calc = df_clean['Nilai_Kalkulasi'].max()

                def scale_nilai(x):
                    if max_calc == min_calc: return float(target_min)
                    hasil = ((x - min_calc) / (max_calc - min_calc)) * (target_max - target_min) + target_min
                    return round(hasil, 0)

                df_clean['Nilai_Baru'] = df_clean['Nilai_Kalkulasi'].apply(scale_nilai)
                df_final = df_clean.drop(columns=['Nilai_Kalkulasi'])

                st.success("✅ Nilai berhasil diproses dengan rekomendasi cerdas.")
                st.dataframe(df_final, use_container_width=True)

                # DOWNLOAD
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Hasil_Nilai_Smart.xlsx")
        else:
            st.warning("Kolom yang dipilih tidak berisi angka.")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
