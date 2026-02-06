from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

api.dataset_download_files(
    "krishnavamsis/nike-sales",
    path="nike_dataset",
    unzip=True
)

print("Download selesai, cek folder nike_dataset")
