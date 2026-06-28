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

# Weboldal elérése
response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, "html.parser")

xls_link = None
for link in soup.find_all("a"):
    if ".xls" in link.get("href", ""):
        xls_link = link.get("href")
        break

if not xls_link:
    print("Nem található .xls fájl.")
    exit(1)

# Fájl letöltése
xls_data = requests.get(xls_link, headers=headers, timeout=30).content
with open("adatok.xls", "wb") as f:
    f.write(xls_data)

def tiszta_szam(ertek):
    if pd.isna(ertek): return 0
    szoveg = str(ertek).replace('.', '').replace(' ', '').replace('\xa0', '').replace('Ft', '').strip()
    return int(szoveg) if szoveg.isdigit() else 0

try:
    # Beolvassuk a táblázatot úgy, hogy megkeressük, hol kezdődik a valódi fejléc
    raw_df = pd.read_excel("adatok.xls", header=None)
    
    header_row_index = 0
    for idx, row in raw_df.iterrows():
        row_str = str(row.values).lower()
        if "magyar cím" in row_str or "magyar cim" in row_str:
            header_row_index = idx
            break
            
    # Újraolvasás a pontos fejlécindex alapján
    df = pd.read_excel("adatok.xls", skiprows=header_row_index)
    
    # Oszlopok neveinek megtisztítása a biztonság kedvéért
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Megkeressük az oszlopokat név alapján (így ha elmozdulnak, akkor is működik)
    col_magyar = [c for c in df.columns if "magyar" in c][0]
    col_eredeti = [c for c in df.columns if "eredeti" in c or "gyári" in c][0]
    col_bemutato = [c for c in df.columns if "bemutató" in c or "bemutato" in c][0]
    col_nezoszam = [c for c in df.columns if "néző" in c or "nező" in c or "összes" in c and "néz" in c][0]
    col_bevetel = [c for c in df.columns if "bevétel" in c or "bevetel" in c][0]

    output = []
    for _, row in df.iterrows():
        m_cim = str(row[col_magyar]).strip()
        if m_cim.lower() in ["magyar cím", "nan", ""] or "összesen" in m_cim.lower():
            continue
            
        film = {
            "magyar_cim": m_cim,
            "eredeti_cim": str(row[col_eredeti]).strip() if pd.notna(row[col_eredeti]) else "",
            "bemutato": str(row[col_bemutato]).split()[0] if pd.notna(row[col_bemutato]) else "",
            "nezoszam": tiszta_szam(row[col_nezoszam]),
            "bevetel": tiszta_szam(row[col_bevetel])
        }
        output.append(film)

    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Sikeres frissítés! {len(output)} film mentve.")

except Exception as e:
    print(f"Hiba az oszlopok feldolgozásakor: {e}")
    exit(1)
