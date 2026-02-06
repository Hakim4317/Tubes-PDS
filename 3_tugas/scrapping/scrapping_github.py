import requests

url = "https://raw.githubusercontent.com/ham407/Analisis-Penjualan-Produk-Nike-U.S.-Tahun-2020---2021/main/Nike%20Dataset.csv"

# Minta (request) data ke internet
res = requests.get(url)

# Mengecek apakah berhasil (angka 200 melambangkan berhasil)
if res.status_code == 200:
    # Buka file baru di komputer (mode 'wb' = write binary)
    with open("nike_dataset_scrapping.csv", "wb") as file:
        file.write(res.content)
    print("Berhasil! File tersimpan dengan nama 'nike_dataset_scrapping.csv'")
else:
    print("Gagal mendownload.")