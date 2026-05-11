import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Smart Grader V7.1", layout="wide")

st.title("📊 Smart Grader V7.1")
st.markdown("""
Pada versi ini, siswa yang melampaui batas **Ceiling** akan mendapatkan nilai: 
**Nilai Asli + Bonus** (Tanpa mengikuti rumus katrol).
""")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
df_template = pd.DataFrame({'Nama Siswa': ['Siswa A', 'Siswa B', 'Siswa C'], 'Nilai Asli': [97, 80, 35]})
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
            rec_ceil = 85 # Default ceiling untuk memisahkan kelompok istimewa

            st.info(f"💡 Info Kelas: Min **{temp_series.min()}**, Max **{temp_series.max()}**, Rerata **{rerata}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎯 Target Katrol (Nilai Bawah-Tengah)")
                target_min = st.number_input("Target Nilai Min (KKTP)", value=75)
                target_max = st.number_input("Target Nilai Max (Batas Atas Katrol)", value=95)
                floor_val = st.number_input("Batas Floor (Lantai)", value=rec_floor)
            with col2:
                st.subheader("🌟 Aturan Kelompok Istimewa")
                ceil_val = st.number_input("Batas Ceiling (Titik Pisah)", value=rec_ceil, 
                                          help="Siswa di atas angka ini tidak dikatrol, tapi ditambah bonus.")
                bonus_manual = st.number_input("Bonus Manual untuk Siswa Istimewa", value=2, 
                                             help="Nilai Akhir = Nilai Asli + Bonus ini.")

            if st.button("🚀 Proses Penyesuaian Nilai"):
                df_clean = df.copy()
                df_clean[kolom_nilai] = pd.to_numeric(df_clean[kolom_nilai], errors='coerce')
                
                def hitung_final(x):
                    if pd.isna(x): return x
                    
                    # LOGIKA BARU: JIKA DI ATAS CEILING
                    if x > ceil_val:
                        # Nilai Asli + Bonus Manual
                        return min(100, x + bonus_manual)
                    
                    # LOGIKA KATROL UNTUK DI BAWAH/SAMA DENGAN CEILING
                    x_calc = max(x, floor_val) # Terapkan Floor
                    
                    if ceil_val == floor_val:
                        return float(target_min)
                    
                    # Proses Scaling menggunakan range [floor_val s/d ceil_val] ke [target_min s/d target_max]
                    skala = ((x_calc - floor_val) / (ceil_val - floor_val)) * (target_max - target_min) + target_min
                    return round(skala, 0)

                df_clean['Nilai_Baru'] = df_clean[kolom_nilai].apply(hitung_final)
                
                st.success(f"✅ Berhasil! Siswa di atas {ceil_val} diberikan bonus manual +{bonus_manual}.")
                st.dataframe(df_clean, use_container_width=True)

                # DOWNLOAD
                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_clean.to_excel(writer, index=False)
                st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Hasil_Nilai_Final.xlsx")
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
