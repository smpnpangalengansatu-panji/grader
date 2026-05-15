import streamlit as st
import pandas as pd
import io
import os

# --- KONFIGURASI LOGO SEKOLAH ---
FILE_LOGO = "logo.png" 
URL_LOGO_DEFAULT = "https://cdn-icons-png.flaticon.com/512/5322/5322031.png" # Ikon Edukasi/Sekolah

if os.path.exists(FILE_LOGO):
    logo_sekolah = FILE_LOGO
else:
    logo_sekolah = URL_LOGO_DEFAULT

# --- CONFIGURASI HALAMAN LURUS & LUAS ---
st.set_page_config(
    page_title="Aplikasi SIPADAN - Sistem Internal", 
    page_icon=logo_sekolah,
    layout="wide", 
    initial_sidebar_state="collapsed" # Sidebar otomatis sembunyi agar halaman luas
)

# --- HEADER BRANDING: SIPADAN ---
col_logo, col_judul = st.columns([1, 10])

with col_logo:
    st.image(logo_sekolah, width=95)

with col_judul:
    st.title("Aplikasi SIPADAN ")
    st.subheader("Sistem Penyesuaian Angka Dan Analisis Nilai")
    st.markdown("*“Menyelaraskan capaian nilai peserta didik secara objektif, adil, dan merata.”*")

st.caption("🔒 **Private & Secure:** Dashboard evaluasi internal sekolah. Semua data hanya diproses di memori lokal browser Anda. -- Created by : iman 2026 --")
st.divider()

# --- SIDEBAR (UNTUK DOWNLOAD TEMPLATE - TERSEMBUNYI NYAMAN) ---
st.sidebar.header("📋 File Template")
st.sidebar.markdown("Silakan unduh template jika format Excel Anda belum sesuai.")

df_7a = pd.DataFrame({
    'Nama Siswa': ['Andi 7A', 'Budi 7A', 'Cici 7A', 'Dedi 7A'], 
    'Nilai Asli': [95, 80, 55, 30]
})
df_7b = pd.DataFrame({
    'Nama Siswa': ['Eri 7B', 'Fani 7B', 'Gani 7B', 'Hani 7B'], 
    'Nilai Asli': [88, 75, 45, 12]
})

buffer_template = io.BytesIO()
with pd.ExcelWriter(buffer_template, engine='openpyxl') as writer:
    df_7a.to_excel(writer, sheet_name="Kelas 7A", index=False)
    df_7b.to_excel(writer, sheet_name="Kelas 7B", index=False)

st.sidebar.download_button("📥 Download Template Multi-Sheet", data=buffer_template.getvalue(), file_name="Template_SIPADAN.xlsx")

# --- AREA UTAMA: UPLOAD DATA ---
uploaded_file = st.file_uploader("Upload file Excel Nilai Siswa (Bisa berisi banyak Sheet/Kelas)", type=["xlsx"])

if uploaded_file:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        daftar_sheet = excel_file.sheet_names
        
        st.success(f"📂 SIPADAN mendeteksi {len(daftar_sheet)} kelas: {', '.join(daftar_sheet)}")
        
        kelas_aktif = st.selectbox("🎯 Pilih Kelas yang Ingin Diselaraskan & Dianalisis:", daftar_sheet)
        
        df = pd.read_excel(uploaded_file, sheet_name=kelas_aktif)
        kolom_nilai = st.selectbox(f"Pilih Kolom Nilai Asli ({kelas_aktif})", df.columns)
        
        df[kolom_nilai] = pd.to_numeric(df[kolom_nilai], errors='coerce')
        df_clean = df.dropna(subset=[kolom_nilai]).copy()
        
        if not df_clean.empty:
            total_siswa = len(df_clean)
            
            # Pengorganisasian halaman dengan Tabs agar rapi dan scannable
            tab1, tab2, tab3 = st.tabs(["📊 Analisis Kelompok", "📈 Grafik Komparasi", "⚙️ Penyesuaian Angka & Download"])
            
            with tab1:
                st.subheader(f"🗂️ Analisis Sebaran Nilai Awal - {kelas_aktif}")
                lebar_rentang = st.slider("Tentukan lebar interval nilai tiap kelompok:", min_value=5, max_value=30, value=20, step=5)
                
                bins = list(range(0, 101, lebar_rentang))
                if bins[-1] != 100: bins.append(100)
                labels = [f"{bins[i] if i==0 else bins[i]+1} - {bins[i+1]}" for i in range(len(bins)-1)]
                
                df_clean['Rentang_Kustom'] = pd.cut(df_clean[kolom_nilai], bins=bins, labels=labels, include_lowest=True)
                distribusi = df_clean['Rentang_Kustom'].value_counts().reindex(labels).reset_index()
                distribusi.columns = ['Rentang Nilai', 'Jumlah Siswa']
                distribusi['Jumlah Siswa'] = distribusi['Jumlah Siswa'].fillna(0).astype(int)
                distribusi['Persentase'] = (distribusi['Jumlah Siswa'] / total_siswa * 100).round(1).apply(lambda x: f"{x}%")
                
                st.table(distribusi)
                
                kelompok_pilihan = st.selectbox("Intip Nama Siswa di Rentang:", labels)
                siswa_terfilter = df_clean[df_clean['Rentang_Kustom'] == kelompok_pilihan].drop(columns=['Rentang_Kustom'])
                st.dataframe(siswa_terfilter, use_container_width=True)

            with tab3:
                st.subheader("⚙️ Parameter Penyesuaian Nilai (Floor & Ceiling)")
                rerata = int(df_clean[kolom_nilai].mean())
                rec_floor = int((df_clean[kolom_nilai].min() + rerata) / 2)
                
                col1, col2 = st.columns(2)
                with col1:
                    target_min = st.number_input("Target Nilai Min (KKTP)", value=75, key=f"tmin_{kelas_aktif}")
                    target_max = st.number_input("Target Nilai Max", value=95, key=f"tmax_{kelas_aktif}")
                    floor_val = st.number_input("Batas Batbawah (Floor)", value=rec_floor, key=f"floor_{kelas_aktif}")
                with col2:
                    ceil_val = st.number_input("Batas Batatas (Ceiling)", value=85, key=f"ceil_{kelas_aktif}")
                    bonus_manual = st.number_input("Bonus Penyelarasan Atas", value=2, key=f"bonus_{kelas_aktif}")

            def hitung_final(x):
                if pd.isna(x): return x
                if x > ceil_val: return min(100, x + bonus_manual)
                x_calc = max(x, floor_val)
                if ceil_val == floor_val: return float(target_min)
                skala = ((x_calc - floor_val) / (ceil_val - floor_val)) * (target_max - target_min) + target_min
                return round(skala, 0)

            df_final = df_clean.drop(columns=['Rentang_Kustom']).copy()
            df_final['Nilai_Baru'] = df_final[kolom_nilai].apply(hitung_final)

            with tab2:
                st.subheader(f"📈 Simulasi Hasil Penyesuaian Angka ({kelas_aktif})")
                df_chart = df_final.set_index(df_final.columns[0])[[kolom_nilai, 'Nilai_Baru']]
                df_chart.columns = ['Nilai Asli Ujian', 'Nilai Penyesuaian Rapor']
                st.bar_chart(df_chart, use_container_width=True)

            with tab3:
                st.divider()
                st.success(f"Matriks penyesuaian angka selesai dihitung untuk {kelas_aktif}.")
                st.dataframe(df_final, use_container_width=True)

                buffer_hasil = io.BytesIO()
                with pd.ExcelWriter(buffer_hasil, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button(f"💾 Download Hasil SIPADAN - {kelas_aktif} (.xlsx)", data=buffer_hasil.getvalue(), file_name=f"Hasil_SIPADAN_{kelas_aktif}.xlsx")
                
        else:
            st.warning("Kolom yang Anda pilih tidak mendeteksi angka nilai yang valid.")
            
    except Exception as e:
        st.error(f"Sistem mendeteksi kesalahan teknis format: {e}")
