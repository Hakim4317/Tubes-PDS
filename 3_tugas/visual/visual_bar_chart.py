# import library yang dibutuhkan
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# import library untuk ignore future warning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Membaca file CSV yang baru
df = pd.read_csv("dataset keggle/data_hasil_scrapping.csv")

# pengecekan apakah ada list yang duplikat dan menghapusnya
df = df.drop_duplicates()

# perbaikan jika ada spasi pada nama kolom
df.columns = df.columns.str.strip()

# Mengambil data kolom redion dan Total Sales
regional_performance = df.groupby('Region')['Total Sales'].sum().sort_values(ascending=True)

# menambahkan judul
st.header("Analisis Performa Penjualan Berdasarkan Wilayah")

# Membuat visualisasi menggumanak mathlotib
fig, ax = plt.subplots(figsize=(10, 6))

# Membuat horizontal bar chart
colors = sns.color_palette("viridis", len(regional_performance))
regional_performance.plot(kind='barh', color=colors, ax=ax)

# Menambahkan label dan judul
ax.set_title('Total Sales per Region', fontsize=14, pad=15)
ax.set_xlabel('Total Sales (USD)', fontsize=12)
ax.set_ylabel('Region', fontsize=12)

# Menambahkan anotasi nilai di ujung bar
for i, v in enumerate(regional_performance):
    ax.text(v, i, f' {v:,.0f}', va='center', fontsize=10)

# Menyesuaikan tata letak agar tidak terpotong
plt.tight_layout()

# Tampilkan di Streamlit
st.pyplot(fig)

# Tampilkan data ringkasan dalam bentuk metrik
col1, col2 = st.columns(2)
with col1:
    wilayah_tertinggi = regional_performance.idxmax()
    st.metric("Wilayah Penjualan Tertinggi", wilayah_tertinggi)
with col2:
    total_seluruh = regional_performance.sum()
    st.metric("Total Penjualan Keseluruhan", f"${total_seluruh:,.0f}")

# Menampilkan data mentah hasil grouping
if st.checkbox("Tampilkan Detail Data Wilayah"):
    tabel = regional_performance.sort_values(ascending=False).reset_index()
    tabel.columns = ["Region", "Total Sales"]
    tabel["Total Sales"] = tabel["Total Sales"].map(lambda x: f"${x:,.0f}")
    st.dataframe(
        tabel.style.set_properties(**{
            'text-align': 'center'
        })
    )