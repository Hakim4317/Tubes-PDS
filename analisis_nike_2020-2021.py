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
import time
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Ignore future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# ==========================================
# FUNGSI HELPER SCRAPING
# ==========================================
def clean_price(text):
    num = ''.join(c for c in text if c.isdigit())
    return int(num) if num else 0

def auto_scroll(driver, times=4):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

def scrape_nike(max_pages):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    all_products = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page in range(max_pages):
        status_text.caption(f"Sedang memproses halaman {page + 1} dari {max_pages}...")
        url = f"https://www.nike.com/w/mens-shoes-nik1zy7ok?offset={page*24}"
        driver.get(url)

        time.sleep(4)
        auto_scroll(driver)

        cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card")

        for card in cards:
            try:
                name = card.find_element(By.CSS_SELECTOR, ".product-card__title").text
                price_text = card.find_element(By.CSS_SELECTOR, ".product-price").text
                price = clean_price(price_text)
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                try:
                    img = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                except:
                    img = ""
                all_products.append([name, price_text, price, link, img])
            except:
                pass
        
        progress_bar.progress((page + 1) / max_pages)

    driver.quit()
    progress_bar.empty()
    status_text.empty()

    df_res = pd.DataFrame(all_products, columns=["Nama", "Harga Text", "Harga Angka", "Link", "Gambar"])
    return df_res

# ==========================================
# KONFIGURASI HALAMAN & DATA LOAD
# ==========================================
st.set_page_config(layout="wide", page_title="Nike Analytics Suite")
st.title("Dashboard Analisis Product Nike")

# Load Data Historis
try:
    df = pd.read_csv("data_hasil_scrapping.csv")
except:
    try:
        df = pd.read_csv("dataset keggle/data_hasil_scrapping.csv")
    except:
        st.error("File CSV tidak ditemukan.")
        df = pd.DataFrame()

# Data Cleaning
if not df.empty:
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip()
    if 'State' in df.columns:
        df['State'] = df['State'].str.strip().str.title()

    # Hitung Kurs
    kurs = 16900
    if "Total Sales" in df.columns:
        df["Total Sales IDR"] = df["Total Sales"] * kurs
    if "Price per Unit" in df.columns:
        df["price per unit IDR"] = df["Price per Unit"] * kurs

    # Kategori
    if "Units Sold" in df.columns:
        df["kategori"] = df["Units Sold"].apply(
            lambda x: "Kurang Laku" if x < 50 else "Laku" if x <= 80 else "Sangat Laku" 
        )

# ==========================================
# BAGIAN 1: LIVE SCRAPER PANEL
# ==========================================
st.divider()
st.subheader("🕵️ Live Data Scrapping Nike.com")
st.caption("Ambil data produk terbaru secara real-time.")

with st.expander("Buka Panel Scrapping", expanded=False):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        pages_in = st.number_input("Jumlah Halaman", 1, 5, 1)
    with c2:
        key_in = st.text_input("Filter Untuk Cari Product")
    with c3:
        st.write("")
        st.write("")
        btn_start = st.button("🚀 Mulai Scraping", use_container_width=True)

    if btn_start:
        with st.spinner("Sedang scraping..."):
            df_s = scrape_nike(pages_in)
        
        if not df_s.empty:
            if key_in:
                df_s = df_s[df_s["Nama"].str.contains(key_in, case=False)]
            
            st.success(f"Berhasil mengambil {len(df_s)} produk!")
            
            t1, t2, t3 = st.tabs(["📄 Data Tabel", "📊 Grafik Harga", "🖼️ Preview"])
            
            with t1:
                st.dataframe(df_s, use_container_width=True)
                csv = df_s.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "nike_live.csv", "text/csv")
            
            with t2:
                fig, ax = plt.subplots()
                ax.hist(df_s["Harga Angka"], color="orange")
                st.pyplot(fig)
            
            with t3:
                cols = st.columns(4)
                for i, r in df_s.head(8).iterrows():
                    with cols[i%4]:
                        if r["Gambar"]: st.image(r["Gambar"])
                        st.caption(f"{r['Nama']} - {r['Harga Text']}")

# ==========================================
# BAGIAN 2: ANALISIS DATA NIKE KEGGLE.COM
# ==========================================
st.divider()
st.subheader("🧑‍💻 Analisis Data Nike Keggle.com")

with st.expander("Panel Cari Produk", expanded=True):
    
    # --- FITUR SEARCH DENGAN BUTTON ---
    col_input, col_btn = st.columns([3, 1])
    
    with col_input:
        query_historis = st.text_input(
            "Cari Nama Produk", 
            placeholder="Masukkan nama produk dari kolom Product...",
            key="input_search_hist"
        )
    
    with col_btn:
        st.write("") # Spacer
        st.write("") 
        btn_search_hist = st.button("🔍 Cari Produk", use_container_width=True)

    # Inisialisasi DataFrame untuk ditampilkan
# Inisialisasi DataFrame untuk ditampilkan
if not df.empty:

    df_display = df.copy()

    # filter kalau ada keyword
    if query_historis:
        mask = (
            df["Product"]
            .astype(str)
            .str.lower()
            .str.contains(query_historis.lower(), na=False)
        )
        df_display = df[mask]

        st.info(f"Ditemukan **{len(df_display)}** data untuk kata kunci: '{query_historis}'")

    # =========================
    # TABS SELALU TAMPIL (LUAR IF)
    # =========================
    tab_overview, tab_top, tab_region, tab_map = st.tabs([
        "📊 Overview Data",
        "🏆 Top Produk",
        "🌎 Analisis Wilayah",
        "📍 Peta Sebaran (GIS)"
    ])


    # 1. Overview
    with tab_overview:
            st.write(f"Menampilkan **{df_display.shape[0]}** baris data.")
            st.dataframe(
                df_display, 
                use_container_width=True,
                column_config={"Invoice Date": st.column_config.DateColumn(format="DD/MM/YYYY")}
            )

        # 2. Top Produk
    with tab_top:
            st.markdown("#### Top Produk Berdasarkan Kategori")
            produk_total = (
                df_display.groupby("Product")["Units Sold"]
                .sum().sort_values(ascending=False).reset_index()
            )
            if not produk_total.empty:
                n = len(produk_total)
                bagi = max(1, n // 3)
                c_top1, c_top2, c_top3 = st.columns(3)
                with c_top1:
                    st.success("🔥 **Sangat Laku**")
                    st.dataframe(produk_total.iloc[:bagi], use_container_width=True, hide_index=True)
                with c_top2:
                    st.warning("👍 **Laku**")
                    st.dataframe(produk_total.iloc[bagi:bagi*2], use_container_width=True, hide_index=True)
                with c_top3:
                    st.error("❄️ **Kurang Laku**")
                    st.dataframe(produk_total.iloc[bagi*2:], use_container_width=True, hide_index=True)

        # 3. Analisis Wilayah
    with tab_region:
            st.markdown("#### Performa Penjualan Regional")
            if not df_display.empty:
                regional_perf = df_display.groupby('Region')['Total Sales'].sum().sort_values(ascending=True)
                rc1, rc2 = st.columns([2, 1])
                with rc1:
                    fig_reg, ax_reg = plt.subplots(figsize=(8, 4))
                    colors = sns.color_palette("viridis", len(regional_perf))
                    regional_perf.plot(kind='barh', color=colors, ax=ax_reg)
                    st.pyplot(fig_reg)
                with rc2:
                    st.metric("Total Sales (USD)", f"${df_display['Total Sales'].sum():,.0f}")
                    st.metric("Total Sales (IDR)", f"Rp {df_display['Total Sales IDR'].sum():,.0f}")

        # 4. Peta GIS
    with tab_map:
            st.markdown("#### Peta Sebaran Penjualan")
            state_stats = df_display.groupby('State').agg({'Units Sold': 'sum', 'Total Sales': 'sum'}).reset_index()
            m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
            
            selected_State_Coords = {
                "California": [36.7783, -119.4179], "Texas": [31.9686, -99.9018], "New York": [43.2994, -74.2179], 
                "Illinois": [40.6331, -89.3985], "Pennsylvania": [41.2033, -77.1945], "Nevada": [38.8026, -116.4194],
                "Colorado": [39.5501, -105.7821], "Washington": [47.7511, -120.7401], "Florida": [27.9944, -81.7603], 
                "Minnesota": [46.7296, -94.6859], "Montana": [46.8797, -110.3626], "Tennessee": [35.5175, -86.5804],
                "Louisiana": [30.9843, -91.9623], "Virginia": [37.4316, -78.6569], "Wyoming": [43.07597, -107.2903], 
                "Oregon": [43.8041, -120.5542], "Utah": [39.3200, -111.0937], "Iowa": [41.8780, -93.0977],
                "Michigan": [44.1822, -84.5068], "Missouri": [38.5739, -92.6038], "North Dakota": [47.5515, -101.0020], 
                "Indiana": [40.2672, -86.1349], "Wisconsin": [44.5000, -89.5000], "Massachusetts": [42.4072, -71.3824],
                "New Hampshire": [43.1939, -71.5724], "Vermont": [44.0000, -72.6999], "Connecticut": [41.6032, -73.0877], 
                "Delaware": [38.9108, -75.5277], "Maryland": [39.0458, -76.6413], "Rhode Island": [41.5801, -71.4774],
                "West Virginia": [38.5976, -80.4549], "New Jersey": [40.0583, -74.4057], "Maine": [45.2538, -69.4455], 
                "Georgia": [32.1656, -82.9001], "Arizona": [34.0489, -111.0937], "Idaho": [44.0682, -114.7420],
                "New Mexico": [34.5199, -105.8701], "Ohio": [40.4173, -82.9071], "Kansas": [39.0119, -98.4842], 
                "Nebraska": [41.4925, -99.9018], "South Dakota": [43.9695, -99.9018], "Alabama": [32.8067, -86.7911],
                "Mississippi": [32.3547, -89.3985], "Kentucky": [37.8393, -84.2700], "North Carolina": [35.7596, -79.0193], 
                "South Carolina": [33.8361, -81.1637], "Oklahoma": [35.0078, -97.0929], "Arkansas": [34.9697, -92.3731]
            }

            for index, row_data in state_stats.iterrows():
                s_name = row_data['State']
                if s_name in selected_State_Coords:
                    folium.Marker(
                        location=selected_State_Coords[s_name],
                        popup=f"{s_name}: {row_data['Units Sold']} Sold",
                        icon=folium.Icon(color="red")
                    ).add_to(m)
            st_folium(m, width="100%", height=500)
else:
    st.error("Data historis kosong.")