import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
url = "https://filmforgalmazok.hu/category/filmenkenti-osszesites/"

# Oldal letöltése és link keresése
try:
    res = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")
    xls_link = [a.get("href") for a in soup.find_all("a") if ".xls" in a.get("href", "")][0]
    
    # Fájl letöltése
    xls_data = requests.get(xls_link, headers=headers, timeout=30).content
    with open("adatok.xls", "wb") as f:
        f.write(xls_data)
except Exception as e:
    print(f"Letöltési hiba: {e}")
    exit(1)

# Mindent túlélő feldolgozás
try:
    # Beolvassuk a nyers táblázatot trükközés nélkül
    df = pd.read_excel("adatok.xls", header=None)
    output = []
    
    for _, row in df.iterrows():
        # Átalakítjuk a sor összes elemét tiszta szöveggé
        sor_értékek = [str(val).strip() for val in row.values if pd.notna(val)]
        
        # Ha a sor üres vagy a fejléc része, átugorjuk
        if len(sor_értékek) < 3 or "magyar" in sor_értékek[0].lower() or "összesen" in sor_értékek[0].lower():
            continue
            
        # Elmentjük a sor elemeit tisztán, a telefonos app majd szétválogatja
        film = {
            "nyers_adatok": sor_értékek
        }
        output.append(film)

    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Sikeres kimentés!")

except Exception as e:
    print(f"Végső hiba: {e}")
    exit(1)
