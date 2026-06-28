import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
url = "https://filmforgalmazok.hu/category/filmenkenti-osszesites/"

# 1. Letöltés
try:
    res = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")
    xls_link = [a.get("href") for a in soup.find_all("a") if ".xls" in a.get("href", "")][0]
    
    xls_data = requests.get(xls_link, headers=headers, timeout=30).content
    with open("adatok.xls", "wb") as f:
        f.write(xls_data)
    print("Fájl letöltve.")
except Exception as e:
    print(f"Letöltési hiba: {e}")
    exit(1)

# Számtisztító funkció
def tiszta_szam(ertek):
    if pd.isna(ertek): return 0
    szoveg = str(ertek).strip()
    if ',' in szoveg: szoveg = szoveg.split(',')[0]
    if '.' in szoveg: szoveg = szoveg.split('.')[0]
    szoveg = szoveg.replace(' ', '').replace('\xa0', '').replace('Ft', '').strip()
    return int(szoveg) if szoveg.isdigit() else 0

# Hónapok magyarosítása
honapok = {
    1: "január", 2: "február", 3: "március", 4: "április", 5: "május", 6: "június",
    7: "július", 8: "augusztus", 9: "szeptember", 10: "október", 11: "november", 12: "december"
}
ma = datetime.now()
aktualis_datum = f"{ma.year}. {honapok[ma.month]}"

# 2. Precíz feldolgozás
try:
    df = pd.read_excel("adatok.xls", skiprows=1)
    filmek_listaja = []
    
    for _, row in df.iterrows():
        try:
            m_cim = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            
            if m_cim == "" or m_cim.lower() in ["cím", "cim", "nan"] or "összesen" in m_cim.lower():
                continue
            
            film = {
                "magyar_cim": m_cim,
                "eredeti_cim": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "",
                "forgalmazo": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "Ismeretlen",
                "bemutato": str(row.iloc[4]).split()[0] if pd.notna(row.iloc[4]) else "Nincs adat",
                "bevetel": tiszta_szam(row.iloc[5]),
                "nezoszam": tiszta_szam(row.iloc[6])
            }
            filmek_listaja.append(film)
        except:
            continue

    # Új struktúra: elmentjük a dátumot ÉS a filmeket is egy közös csomagba
    vegso_adatok = {
        "frissitve": aktualis_datum,
        "filmek": filmek_listaja
    }

    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(vegso_adatok, f, ensure_ascii=False, indent=2)
    print(f"Sikeres mentés! Dátum: {aktualis_datum}, {len(filmek_listaja)} film feldolgozva.")

except Exception as e:
    print(f"Feldolgozási hiba: {e}")
    exit(1)
