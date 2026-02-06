import streamlit as st 
import pandas as pd
import time
import matplotlib.pyplot as plt
import io

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


st.set_page_config(layout="wide")
st.title("👟 Nike Advanced Scraping Dashboard")


# =========================
# Helper
# =========================

def clean_price(text):
    num = ''.join(c for c in text if c.isdigit())
    return int(num) if num else 0


def auto_scroll(driver, times=4):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)


# =========================
# Scraper
# =========================

def scrape_nike(max_pages):

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    all_products = []

    for page in range(max_pages):

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
                img = card.find_element(By.TAG_NAME, "img").get_attribute("src")

                all_products.append([name, price_text, price, link, img])

            except:
                pass

        time.sleep(2)

    driver.quit()

    df = pd.DataFrame(
        all_products,
        columns=["Nama", "Harga Text", "Harga Angka", "Link", "Gambar"]
    )

    return df


# =========================
# UI Controls
# =========================

pages = st.slider("Jumlah halaman", 1, 5, 2)
keyword = st.text_input("Filter nama produk (optional)")

if st.button("🚀 Mulai Scraping"):

    with st.spinner("Scraping Nike..."):
        df = scrape_nike(pages)

    st.success(f"Total produk: {len(df)}")

    # =========================
    # Filter Search
    # =========================
    if keyword:
        df = df[df["Nama"].str.contains(keyword, case=False)]

    st.dataframe(df[["Nama", "Harga Text", "Link"]], use_container_width=True)


    # =========================
    # Grafik Harga
    # =========================
    st.subheader("📊 Grafik Distribusi Harga")

    fig, ax = plt.subplots()
    ax.hist(df["Harga Angka"], bins=10)
    st.pyplot(fig)


    # =========================
    # Preview gambar
    # =========================
    st.subheader("Preview Produk")

    cols = st.columns(4)
    for i, row in df.head(8).iterrows():
        with cols[i % 4]:
            st.image(row["Gambar"], width=150)
            st.write(row["Nama"])
            st.write(row["Harga Text"])


    # =========================
    # EXPORT BUTTONS (SEJAJAR)
    # =========================
    st.subheader("⬇ Export Data")

    col1, col2 = st.columns(2)

    # ===== CSV =====
    csv_data = df.to_csv(index=False).encode("utf-8")
    with col1:
        st.download_button(
            "⬇ Download CSV",
            csv_data,
            file_name="nike_scraped.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ===== Excel =====
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)

    with col2:
        st.download_button(
            "⬇ Download Excel",
            excel_buffer,
            file_name="nike_scraped.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
