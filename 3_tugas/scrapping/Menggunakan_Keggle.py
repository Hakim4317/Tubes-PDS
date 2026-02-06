import kaggle

kaggle.api.authenticate()
kaggle.api.dataset_download_files('hamizanhibatullah407/analisis-penjualan-produk-nike-u-s-2020-2021', path='.', unzip=True)