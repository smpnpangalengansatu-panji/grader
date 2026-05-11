import streamlit as st
import pandas as pd
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Smart Grader SMP V3 - Panji", layout="wide")

st.title("📊 Smart Grader Panji")
st.markdown("""
Aplikasi ini kini dilengkapi dengan fitur **Batas Lantai Nilai**. 
Nilai yang terlalu rendah (outlier) tidak akan merusak skala nilai siswa lainnya.
""")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
buffer_template = io.BytesIO()
df_template = pd.DataFrame({
    'Nama Siswa': ['Siswa A', 'Siswa B', 'Siswa C', 'Siswa D'],
    'Nilai Asli': [80, 45, 42, 25] # Contoh Siswa D adalah outlier (25)
})
with pd.ExcelWriter(buffer_template, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False)

st.sidebar.download_button(
    label="📥 Download Template .xlsx",
    data=buffer_template.getvalue(),
    file_name="Template_Nilai_SMP.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- AREA UTAMA: UPLOAD & PENGATURAN ---
uploaded_file = st.file_uploader("Upload file Excel Anda", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        st.subheader("⚙️ Pengaturan Skala")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            kolom_nilai = st.selectbox("Kolom Nilai Asli", df.columns)
        with col2:
            target_min = st.number_input("Target Nilai Minimal", value=75)
        with col3:
            target_max = st.number_input("Target Nilai Maksimal", value=95)
        with col4:
            # FITUR BARU: Batas Lantai
            floor_value = st.number_input("Batas Lantai (Minimal Angka)", value=40, 
                                          help="Nilai asli di bawah angka ini akan dianggap sama dengan angka ini agar tidak merusak skala.")

        if st.button("🚀 Proses Nilai (Optimasi Outlier)"):
            # 1. Konversi ke numeric
            df[kolom_nilai] = pd.to_numeric(df[kolom_nilai], errors='coerce')
            df_clean = df.dropna(subset=[kolom_nilai]).copy()

            if not df_clean.empty:
                # 2. TERAPKAN FITUR ANTI-JOMPLANG (Clipping)
                # Nilai asli di bawah 'floor_value' akan dipaksa menjadi 'floor_value' untuk perhitungan skala
                df_clean['Nilai_Kalkulasi'] = df_clean[kolom_nilai].clip(lower=floor_value)
                
                min_kalkulasi = df_clean['Nilai_Kalkulasi'].min()
                max_kalkulasi = df_clean['Nilai_Kalkulasi'].max()

                def scale_nilai(x):
                    if max_kalkulasi == min_kalkulasi:
                        return float(target_min)
                    # Menggunakan Nilai_Kalkulasi untuk menentukan bobot
                    hasil = ((x - min_kalkulasi) / (max_kalkulasi - min_kalkulasi)) * (target_max - target_min) + target_min
                    return round(hasil, 0)

                # 3. Hitung Nilai Baru
                df_clean['Nilai_Baru'] = df_clean['Nilai_Kalkulasi'].apply(scale_nilai)
                
                # Hapus kolom pembantu agar tidak membingungkan saat di-download
                df_final = df_clean.drop(columns=['Nilai_Kalkulasi'])

                st.success(f"✅ Berhasil! Nilai di bawah {floor_value} telah disesuaikan agar sebaran tetap adil.")
                st.dataframe(df_final, use_container_width=True)

                # --- DOWNLOAD HASIL ---
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                
                st.download_button(
                    label="💾 Download Hasil Akhir (.xlsx)",
                    data=buffer_hasil.getvalue(),
                    file_name="Hasil_Nilai_Anti_Jomplang.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Data tidak valid.")
                
    except Exception as e:
        st.error(f"Error: {e}")