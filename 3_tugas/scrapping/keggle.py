import kagglehub
from kagglehub import KaggleDatasetAdapter

# 1. Gunakan dataset yang valid (ayushrakesh/nike-sales-data)
# 2. Nama file di dataset ini adalah 'nike_sales_data.csv'
dataset_handle = "ayushrakesh/nike-sales-data"
file_name = "nike_sales_data.csv"

try:
    df = kagglehub.dataset_load(
        KaggleDatasetAdapter.PANDAS,
        handle=dataset_handle,
        path=file_name
    )

    print("Berhasil memuat data!")
    print(df.head())
    
except Exception as e:
    print(f"Terjadi kesalahan: {e}")