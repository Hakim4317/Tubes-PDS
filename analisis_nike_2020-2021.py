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
import requests
from bs4 import BeautifulSoup

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
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    all_products = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page in range(max_pages):

        status_text.caption(f"Sedang memproses halaman {page + 1} dari {max_pages}...")

        offset = page * 24
        url = f"https://www.nike.com/w/mens-shoes-nik1zy7ok?offset={offset}"

        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            cards = soup.select("div.product-card")

            for card in cards:
                try:
                    name = card.select_one(".product-card__title").get_text(strip=True)
                    price_text = card.select_one(".product-price").get_text(strip=True)
                    price = clean_price(price_text)

                    link = card.select_one("a")["href"]
                    if not link.startswith("http"):
                        link = "https://www.nike.com" + link

                    img_tag = card.select_one("img")
                    img = img_tag["src"] if img_tag else ""

                    all_products.append([name, price_text, price, link, img])

                except:
                    pass

        except:
            st.warning(f"Gagal ambil halaman {page+1}")

        progress_bar.progress((page + 1) / max_pages)
        time.sleep(1)

    progress_bar.empty()
    status_text.empty()

    df_res = pd.DataFrame(
        all_products,
        columns=["Nama", "Harga Text", "Harga Angka", "Link", "Gambar"]
    )

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
    df["Invoice Date"] = pd.to_datetime(
        df["Invoice Date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

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

with st.expander("Panel Cari Produk", expanded=False):
    
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

            show_table = st.checkbox("📋 Tampilkan tabel detail per wilayah")

            if show_table:
                regional_table = (
                df_display
                .groupby("Region")
                .agg({
                    "Units Sold": "sum",
                    "Total Sales": "sum",
                    "Total Sales IDR": "sum"
                })
                .reset_index()
                .sort_values("Total Sales", ascending=False)
            )

                st.dataframe(regional_table, use_container_width=True)

        

        # 4. Peta GIS

    with tab_map:

        st.markdown("#### 📍 Peta Sebaran Penjualan USA")

        if not df_display.empty:

            state_stats = df_display.groupby('State').agg({
                'Units Sold': 'sum',
                'Total Sales': 'sum'
            }).reset_index()

            # ===============================
            # MAP BASE
            # ===============================
            center_lat, center_lon = 37.0902, -95.7129

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=4,
                tiles="cartodbpositron"   # lebih clean & modern
            )

            # ===============================
            # REGION POLYGON (rapih + soft color)
            # ===============================
            regions = [
                {"name": "West", "coords": [[49,-125],[49,-111],[31,-111],[31,-125]], "color":"#2ecc71"},
                {"name": "Midwest", "coords": [[49,-111],[49,-82],[37,-82],[37,-111]], "color":"#3498db"},
                {"name": "Northeast", "coords": [[47.5,-82],[47.5,-67],[38,-67],[38,-82]], "color":"#9b59b6"},
                {"name": "Southwest", "coords": [[42,-111],[42,-94],[25.5,-94],[31,-111]], "color":"#f39c12"},
                {"name": "Southeast", "coords": [[37,-94],[38,-75],[24,-80],[24,-94]], "color":"#e74c3c"},
            ]

            for reg in regions:
                folium.Polygon(
                    locations=reg["coords"],
                    color=reg["color"],
                    weight=3,            # garis lebih tebal
                    fill=True,
                    fill_color=reg["color"],
                    fill_opacity=0.15,   # lembut transparan
                    tooltip=f"Region: {reg['name']}"
                ).add_to(m)

            # ===============================
            # KOORDINAT STATE
            # ===============================
            selected_State_Coords = {
                "California":[36.77,-119.41],"Texas":[31.96,-99.90],"New York":[43.29,-74.21],
                "Illinois":[40.63,-89.39],"Pennsylvania":[41.20,-77.19],"Nevada":[38.80,-116.41],
                "Colorado":[39.55,-105.78],"Washington":[47.75,-120.74],"Florida":[27.99,-81.76],
                "Minnesota":[46.72,-94.68],"Montana":[46.87,-110.36],"Tennessee":[35.51,-86.58],
                "Louisiana":[30.98,-91.96],"Virginia":[37.43,-78.65],"Oregon":[43.80,-120.55],
                "Utah":[39.32,-111.09],"Iowa":[41.87,-93.09],"Michigan":[44.18,-84.50],
                "Missouri":[38.57,-92.60],"Ohio":[40.41,-82.90],"Georgia":[32.16,-82.90],
                "Arizona":[34.04,-111.09],"Kansas":[39.01,-98.48]
            }

            # ===============================
            # MARKER (card popup seperti gambar 2)
            # ===============================
            for _, row in state_stats.iterrows():

                s_name = row["State"]

                if s_name in selected_State_Coords:

                    units = row["Units Sold"]
                    sales = row["Total Sales"]

                    popup_html = f"""
                    <div style="
                        font-family: Arial;
                        width: 190px;
                        font-size: 13px;
                    ">
                        <h4 style="margin-bottom:6px;color:#e74c3c;">
                            {s_name}
                        </h4>
                        <b>Units Sold:</b> {units:,.0f}<br>
                        <b>Revenue:</b> ${sales:,.0f}
                    </div>
                    """

                    folium.Marker(
                        location=selected_State_Coords[s_name],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=s_name,
                        icon=folium.Icon(
                            color="red",
                            icon="shopping-cart",
                            prefix="fa"
                        )
                    ).add_to(m)

            st_folium(m, width="100%", height=650)

        else:
            st.info("Tidak ada data untuk ditampilkan.")

