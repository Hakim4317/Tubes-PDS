# ==========================================
# 1. IMPORT LIBRARY
# ==========================================
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
import warnings

# Ignore future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# ==========================================
# 2. KONFIGURASI HALAMAN & DATA
# ==========================================
st.set_page_config(layout="wide")
st.title("Dashboard Analisis Penjualan Nike - USA")

# Membaca file CSV
try:
    df = pd.read_csv("data_hasil_scrapping.csv")
except:
    df = pd.read_csv("dataset keggle/data_hasil_scrapping.csv")

# Data Cleaning 
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

# ==========================================
# 3. BAGIAN 1: OVERVIEW DATA (TABEL RAPI)
# ==========================================
st.subheader("📊 Data Product Nike")
row, columns = df.shape
st.write(f'Listings terdiri atas **{row}** baris dan **{columns}** kolom')

# Konfigurasi kolom agar tampil dengan logo mata uang dan titik ribuan
st.dataframe(
    df, 
    use_container_width=True, 
    column_config={
        "Invoice Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
    }
)

# ==========================================
# TOP 3 PRODUK BERDASARKAN KATEGORI
# ==========================================
st.subheader("🏆 Top 2 Produk Berdasarkan Kategori Penjualan")

col1, col2, col3 = st.columns(3)

produk_total = (
    df.groupby("Product")["Units Sold"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

n = len(produk_total)
bagi = max(1, n // 3)

sangat_laku = produk_total.iloc[:bagi]
laku = produk_total.iloc[bagi:bagi*2]
kurang_laku = produk_total.iloc[bagi*2:]


with col1:
    st.markdown("### 🔥 Sangat Laku")
    st.dataframe(sangat_laku, use_container_width=True)

with col2:
    st.markdown("### 👍 Laku")
    st.dataframe(laku, use_container_width=True)

with col3:
    st.markdown("### ❄️ Kurang Laku")
    st.dataframe(kurang_laku, use_container_width=True)

# ==========================================
# 4. BAGIAN 2: ANALISIS PERWILAYAH & METRIK
# ==========================================
st.divider() 
st.subheader("🌎 Analisis Performa Penjualan Berdasarkan Wilayah")

# Grouping data untuk chart
regional_performance = df.groupby('Region')['Total Sales'].sum().sort_values(ascending=True)

col_chart, col_metric = st.columns([2, 1])

with col_chart:
    # Perbaikan Chart: Mengatur ukuran agar pas di dalam "kotak" Streamlit
    fig, ax = plt.subplots(figsize=(8, 5)) 
    colors = sns.color_palette("viridis", len(regional_performance))
    regional_performance.plot(kind='barh', color=colors, ax=ax)
    
    ax.set_title('Total Sales per Region (USD)', fontsize=12, pad=10)
    ax.set_xlabel('Total Sales (USD)', fontsize=10)
    ax.set_ylabel('Region', fontsize=10)
    
    # Anotasi angka di ujung bar dengan format ribuan
    for i, v in enumerate(regional_performance):
        ax.text(v, i, f' ${v:,.0f}', va='center', fontsize=9)
    
    plt.tight_layout() # Memastikan tidak ada label yang terpotong/keluar kotak
    st.pyplot(fig)

with col_metric:
    wilayah_tertinggi = regional_performance.idxmax()
    total_seluruh_usd = df["Total Sales"].sum()
    total_seluruh_idr = df["Total Sales IDR"].sum()
    
    st.metric("Wilayah Penjualan Tertinggi", wilayah_tertinggi)
    st.metric("Total Penjualan (USD)", f"$ {total_seluruh_usd:,.0f}")
    st.metric("Total Penjualan (IDR)", f"Rp {total_seluruh_idr:,.0f}")
    
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

# ==========================================
# 5. BAGIAN 3: PETA GIS (POPUP LENGKAP)
# ==========================================
st.divider()
st.subheader("📍 Peta Sebaran: Klik Marker untuk Detail Penjualan")

# Grouping data per State untuk Map
state_stats = df.groupby('State').agg({
    'Units Sold': 'sum',
    'Total Sales': 'sum'
}).reset_index()

# Titik tengah peta US
center_lat, center_lon = 37.0902, -95.7129
m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

# Definisi 5 Wilayah Polygon
regions = [
    {"name": "West", "coords": [[49.0, -125.0], [49.0, -111.0], [31.0, -111.0], [31.0, -125.0]], "color": "#90D743", "fill": "#a1c9ed"},
    {"name": "Southwest", "coords": [[42.0, -111.0], [42.0, -94.0], [25.5, -94.0], [31.0, -111.0]], "color": "#31688E", "fill": "#ffc08a"},
    {"name": "Midwest", "coords": [[49.0, -111.0], [49.0, -82.0], [37.0, -82.0], [37.0, -111.0]], "color": "#443983", "fill": "#98df8a"},
    {"name": "Northeast", "coords": [[47.5, -82.0], [47.5, -67.0], [38.0, -67.0], [38.0, -82.0]], "color": "#35B779", "fill": "#c5b0d5"},
    {"name": "Southeast", "coords": [[37.0, -94.0], [38.0, -75.0], [24.0, -80.0], [24.0, -94.0]], "color": "#21918C", "fill": "#ff9896"}
]

for reg in regions:
    folium.Polygon(
        locations=reg["coords"],
        color=reg["color"],
        weight=2,
        fill=True,
        fill_color=reg["fill"],
        fill_opacity=0.2,
        tooltip=reg["name"]
    ).add_to(m)

# Koordinat State Dasar
selected_State_Coords = {
    "California": [36.7783, -119.4179], "Texas": [31.9686, -99.9018],
    "New York": [43.2994, -74.2179], "Illinois": [40.6331, -89.3985],
    "Pennsylvania": [41.2033, -77.1945], "Nevada": [38.8026, -116.4194],
    "Colorado": [39.5501, -105.7821], "Washington": [47.7511, -120.7401],
    "Florida": [27.9944, -81.7603], "Minnesota": [46.7296, -94.6859],
    "Montana": [46.8797, -110.3626], "Tennessee": [35.5175, -86.5804],
    "Louisiana": [30.9843, -91.9623], "Virginia": [37.4316, -78.6569],
    "Wyoming": [43.07597, -107.2903], "Oregon": [43.8041, -120.5542],
    "Utah": [39.3200, -111.0937], "Iowa": [41.8780, -93.0977],
    "Michigan": [44.1822, -84.5068], "Missouri": [38.5739, -92.6038],
    "North Dakota": [47.5515, -101.0020], "Indiana": [40.2672, -86.1349],
    "Wisconsin": [44.5000, -89.5000], "Massachusetts": [42.4072, -71.3824],
    "New Hampshire": [43.1939, -71.5724], "Vermont": [44.0000, -72.6999],
    "Connecticut": [41.6032, -73.0877], "Delaware": [38.9108, -75.5277],
    "Maryland": [39.0458, -76.6413], "Rhode Island": [41.5801, -71.4774],
    "West Virginia": [38.5976, -80.4549], "New Jersey": [40.0583, -74.4057],
    "Maine": [45.2538, -69.4455], "Georgia": [32.1656, -82.9001],
    "Arizona": [34.0489, -111.0937], "Idaho": [44.0682, -114.7420],
    "New Mexico": [34.5199, -105.8701], "Ohio": [40.4173, -82.9071],
    "Kansas": [39.0119, -98.4842], "Nebraska": [41.4925, -99.9018],
    "South Dakota": [43.9695, -99.9018], "Alabama": [32.8067, -86.7911],
    "Mississippi": [32.3547, -89.3985], "Kentucky": [37.8393, -84.2700],
    "North Carolina": [35.7596, -79.0193], "South Carolina": [33.8361, -81.1637],
    "Oklahoma": [35.0078, -97.0929], "Arkansas": [34.9697, -92.3731]
}

# Tambah Marker
for index, row_data in state_stats.iterrows():
    s_name = row_data['State']
    if s_name in selected_State_Coords:
        u_sold = row_data['Units Sold']
        t_rev = row_data['Total Sales']
        
        popup_html = f"""
        <div style="font-family: Arial; width: 180px; font-size: 12px;">
            <h4 style="margin: 0 0 5px 0; color: #d32f2f;">{s_name}</h4>
            <hr style="margin: 5px 0;">
            <b>Units Sold:</b> {u_sold:,.0f}<br>
            <b>Revenue:</b> ${t_rev:,.0f}
        </div>
        """
        
        folium.Marker(
            location=selected_State_Coords[s_name],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=s_name,
            icon=folium.Icon(color="red", icon="shopping-cart", prefix="fa")
        ).add_to(m)

# Tampilkan Peta
st_folium(m, width="100%", height=600)