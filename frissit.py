import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
url = "https://filmforgalmazok.hu/category/filmenkenti-osszesites/"

# 1. Excel fájl megkeresése és letöltése
try:
    res = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")
    xls_link = [a.get("href") for a in soup.find_all("a") if ".xls" in a.get("href", "")][0]
    
    xls_data = requests.get(xls_link, headers=headers, timeout=30).content
    with open("adatok.xls", "wb") as f:
        f.write(xls_data)
    print("Fájl sikeresen letöltve.")
except Exception as e:
    print(f"Letöltési hiba: {e}")
    exit(1)

# 2. A teljes táblázat feldolgozása soronként
try:
    df = pd.read_excel("adatok.xls", header=None)
    output = []
    
    for idx, row in df.iterrows():
        try:
            # Átalakítjuk a sor elemeit szöveggé, kiszűrve az üres cellákat
            sor_értékek = [str(val).strip() for val in row.values if pd.notna(val)]
            
            # Ha a sor üres, vagy túl rövid, vagy a fejléc/összesítő része, kihagyjuk
            if len(sor_értékek) < 3:
                continue
            if "magyar" in sor_értékek[0].lower() or "összesen" in sor_értékek[0].lower() or "forgalmazó" in sor_értékek[0].lower():
                continue
                
            # Ha eljutott idáig, ez egy valódi film sor!
            output.append({
                "nyers_adatok": sor_értékek
            })
        except:
            # HA BÁRMI HIBA VAN EGY SORNÁL, NEM ÁLL LE, CSAK TOVÁBBLÉP A KÖVETKEZŐRE!
            continue

    # Mentés a telefonnak
    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Sikeres mentés! Összesen {len(output)} film került beolvasásra a mestertáblázatból.")

except Exception as e:
    print(f"Végső hiba: {e}")
    exit(1)
