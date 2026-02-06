# import library yang dibutuhkan
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# import library untuk ignore future warning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Membaca file excel
df = pd.read_csv("dataset keggle/data_hasil_scrapping.csv")

# pengecekan apakah ada list yang duplikat
sama = df[df.duplicated()]

# Data Cleaning (Mengecek apakah ada data yang sama atau kosong)
df = df.drop_duplicates()
df.columns = df.columns.str.strip()
df['State'] = df['State'].str.strip().str.title()

# Perhitungan Kolom IDR
kurs = 16900
df["Total Sales IDR"] = df["Total Sales"] * kurs
df["price per unit IDR"] = df["Price per Unit"] * kurs

# Membuat kolom kategori berdasarkan Units Sold
df["kategori"] = df["Units Sold"].apply(
    lambda x: "Kurang Laku" if x < 50
    else "Laku" if x <= 80
    else "Sangat Laku" 
)

# perbaikan jika ada spasi 
df.columns = df.columns.str.strip()

# membuat judul
st.set_page_config(layout="wide")
st.title("isi list dan kolom dari dataset Nike")

#.Tampilkan isi dataframe di streamlit
st.subheader("Data Product Nike")

# dimensi dataset
row, columns = df.shape
st.write(f'Listings terdiri atas {row} baris dan {columns} kolom')

# menampilkan dataframe
st.dataframe(df, column_config={
    "Waktu Transaksi": st.column_config.DateColumn(format="DD/MM/YYYY") #Membuat  tanggal sesuai urutan
})

# cek jumlah data unik pada State
state_unique = df['Region'].nunique()
print(f'Jumlah data unik pada kolom Wilayah: {state_unique}')

