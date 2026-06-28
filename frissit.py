import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://filmforgalmazok.hu/category/filmenkenti-osszesites/"

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, "html.parser")

xls_link = None
for link in soup.find_all("a"):
    if ".xls" in link.get("href", ""):
        xls_link = link.get("href")
        break

xls_data = requests.get(xls_link, headers=headers, timeout=30).content
with open("adatok.xls", "wb") as f:
    f.write(xls_data)

def tiszta_szam(ertek):
    if pd.isna(ertek): return 0
    szoveg = str(ertek).replace('.', '').replace(' ', '').replace('\xa0', '').replace('Ft', '').strip()
    return int(szoveg) if szoveg.isdigit() else 0

try:
    # Beolvassuk a táblázatot (kihagyva az első 3 üres/fejléc sort)
    df = pd.read_excel("adatok.xls", skiprows=3)
    
    # KINYOMTATJUK AZ OSZLOPOKAT A HIBAKERESÉSHEZ
    print("--- AZ EXCEL TÁBLÁZAT VALÓDI OSZLOPAI ---")
    for i, col in enumerate(df.columns):
        print(f"Index {i}: {col}")
    print("-----------------------------------------")
    
    df = df.dropna(subset=[df.columns[0]])
    output = []
    for _, row in df.iterrows():
        m_cim = str(row.iloc[0]).strip()
        if m_cim.lower() in ["magyar cím", "nan", ""] or "összesen" in m_cim.lower():
            continue
            
        film = {
            "magyar_cim": m_cim,
            "eredeti_cim": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
            "bemutato": str(row.iloc[2]).split()[0] if pd.notna(row.iloc[2]) else "",
            "nezoszam": tiszta_szam(row.iloc[3]),
            "bevetel": tiszta_szam(row.iloc[4])
        }
        output.append(film)

    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Kész! {len(output)} film mentve.")

except Exception as e:
    print(f"Hiba: {e}")
