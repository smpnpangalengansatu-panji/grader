import streamlit as st
import pandas as pd
import io
import numpy as np

st.set_page_config(page_title="Smart Grader V11 - Lebar Rentang", layout="wide")

st.title("📊 Smart Grader SMP V11.0 (Kendali Lebar Rentang Data)")
st.markdown("""
Pada versi ini, Anda bisa menentukan **lebar interval (jarak nilai)** tiap kelompok hingga maksimal **30 poin data**.
Sistem akan otomatis menyesuaikan jumlah kelompoknya.
""")
st.divider()

# --- SIDEBAR: DOWNLOAD TEMPLATE ---
st.sidebar.header("Langkah 1: Persiapan")
df_template = pd.DataFrame({
    'Nama Siswa': ['Andi', 'Budi', 'Cici', 'Dedi', 'Eri', 'Fani', 'Gani', 'Hani'], 
    'Nilai Asli': [97, 80, 55, 52, 48, 25, 12, 50]
})
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
        
        # Bersihkan data non-angka
        df[kolom_nilai] = pd.to_numeric(df[kolom_nilai], errors='coerce')
        df_clean = df.dropna(subset=[kolom_nilai]).copy()
        
        if not df_clean.empty:
            total_siswa = len(df_clean)
            
            # MEMBUAT TABS AGAR RAPI
            tab1, tab2 = st.tabs(["📊 Analisis Nilai Awal", "⚙️ Proses Katrol & Bonus"])
            
            # ----------------------------------------------------
            # TAB 1: ANALISIS DISTRIBUSI & DETAIL KELOMPOK
            # ----------------------------------------------------
            with tab1:
                st.subheader("📋 Ringkasan Statistik Kelas")
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                with metrics_col1:
                    st.metric("Total Data Siswa", f"{total_siswa} Orang")
                with metrics_col2:
                    st.metric("Rata-rata Kelas", f"{int(df_clean[kolom_nilai].mean())}")
                with metrics_col3:
                    st.metric("Nilai Terendah", f"{int(df_clean[kolom_nilai].min())}")
                with metrics_col4:
                    st.metric("Nilai Tertinggi", f"{int(df_clean[kolom_nilai].max())}")
                
                st.divider()
                st.subheader("⚙️ Atur Lebar Rentang Kelompok")
                
                # FITUR BARU: Slider untuk menentukan LEBAR INTERVAL (maksimal 30)
                lebar_rentang = st.slider(
                    "Tentukan lebar interval nilai tiap kelompok (poin data):", 
                    min_value=5, 
                    max_value=30, 
                    value=15,
                    step=5,
                    help="Misal dipilih 30, maka kelompok akan dibuat per 30 angka (0-30, 31-60, dst)."
                )
                
                # Membuat bins dinamis dari 0 sampai 100 berdasarkan lebar_rentang
                bins = list(range(0, 101, lebar_rentang))
                if bins[-1] != 100:
                    bins.append(100) # Memastikan angka 100 tetap masuk hitungan
                
                # Membuat label rentang otomatis secara rapi
                labels = []
                for i in range(len(bins)-1):
                    start = bins[i] if i == 0 else bins[i] + 1
                    end = bins[i+1]
                    if start > end: # Menghindari error jika sisa pembagian terlalu kecil
                        start = end
                    labels.append(f"{start} - {end}")
                
                # Mengelompokkan data berdasarkan bins baru
                df_clean['Rentang_Kustom'] = pd.cut(df_clean[kolom_nilai], bins=bins, labels=labels, include_lowest=True)
                
                # Menghitung frekuensi tiap kelompok kustom
                distribusi = df_clean['Rentang_Kustom'].value_counts().reindex(labels).reset_index()
                distribusi.columns = ['Rentang Nilai', 'Jumlah Siswa']
                
                # Isi otomatis kolom kosong dengan angka 0
                distribusi['Jumlah Siswa'] = distribusi['Jumlah Siswa'].fillna(0).astype(int)
                
                distribusi['Persentase'] = (distribusi['Jumlah Siswa'] / total_siswa * 100).round(1)
                distribusi['Persentase'] = distribusi['Persentase'].apply(lambda x: f"{x}%")
                
                # Tampilkan tabel distribusi baru
                st.table(distribusi)
                
                # --- FITUR INTERAKTIF: DRILL DOWN SISWA ---
                st.subheader("🔍 Detail Anggota Kelompok")
                kelompok_pilihan = st.selectbox("Pilih Rentang Nilai untuk Melihat Daftar Nama Siswa:", labels)
                
                siswa_terfilter = df_clean[df_clean['Rentang_Kustom'] == kelompok_pilihan].drop(columns=['Rentang_Kustom'])
                
                if not siswa_terfilter.empty:
                    st.success(f"Menampilkan {len(siswa_terfilter)} siswa di rentang nilai {kelompok_pilihan}:")
                    st.dataframe(siswa_terfilter, use_container_width=True)
                else:
                    st.info(f"Tidak ada siswa yang berada di rentang nilai {kelompok_pilihan}.")
            
            # ----------------------------------------------------
            # TAB 2: PROSES KATROL
            # ----------------------------------------------------
            with tab2:
                rerata = int(df_clean[kolom_nilai].mean())
                rec_floor = int((df_clean[kolom_nilai].min() + rerata) / 2)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 🎯 Batas Target Akhir Rapor")
                    target_min = st.number_input("Target Nilai Min (KKTP)", value=75)
                    target_max = st.number_input("Target Nilai Max (Batas Atas Katrol)", value=95)
                    floor_val = st.number_input("Batas Floor (Lantai)", value=rec_floor)
                with col2:
                    st.markdown("#### 🌟 Aturan Kelompok Istimewa")
                    ceil_val = st.number_input("Batas Ceiling (Titik Pisah)", value=85)
                    bonus_manual = st.number_input("Bonus Manual Kelompok Istimewa", value=2)

                if st.button("🚀 Eksekusi dan Ambil Nilai Baru"):
                    def hitung_final(x):
                        if pd.isna(x): return x
                        
                        if x > ceil_val:
                            return min(100, x + bonus_manual)
                        
                        x_calc = max(x, floor_val)
                        
                        if ceil_val == floor_val:
                            return float(target_min)
                        
                        skala = ((x_calc - floor_val) / (ceil_val - floor_val)) * (target_max - target_min) + target_min
                        return round(skala, 0)

                    df_final = df_clean.drop(columns=['Rentang_Kustom']).copy()
                    df_final['Nilai_Baru'] = df_final[kolom_nilai].apply(hitung_final)
                    
                    st.success("✅ Nilai Berhasil Disesuaikan!")
                    st.dataframe(df_final, use_container_width=True)

                    # DOWNLOAD
                    buffer_hasil = io.BytesIO()
                    with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                        df_final.to_excel(writer, index=False)
                    st.download_button("💾 Download Hasil (.xlsx)", data=buffer_hasil.getvalue(), file_name="Hasil_Nilai_Final.xlsx")
        else:
            st.warning("File Excel tidak mendeteksi kolom berisi angka.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
