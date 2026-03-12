import os
import pandas as pd
from pathlib import Path

class Olist:
    def get_data(self):
        """
        9 CSV dosyasını okur ve temizlenmiş isimlerle bir sözlük döndürür.
        """
        # Adresimizi tanımlıyoruz (Senin bilgisayarındaki gerçek yol)
        csv_path = Path("~/GitHub/s14-olistdata/csv").expanduser()
        
        # Klasördeki dosyaları listeliyoruz
        file_paths = list(csv_path.iterdir())
        
        # Sadece .csv uzantılı olanları alıyoruz
        file_paths = [f for f in file_paths if f.name.endswith('.csv')]
        
        # Dosya isimlerini temizliyoruz
        file_names = [f.name for f in file_paths]
        key_names = [
            name.replace('olist_', '').replace('_dataset.csv', '').replace('.csv', '') 
            for name in file_names
        ]
        
        # Sözlüğümüzü oluşturup içini dolduruyoruz
        data = {}
        for key, path in zip(key_names, file_paths):
            data[key] = pd.read_csv(path)
            
        return data

    def ping(self):
        return "pong"