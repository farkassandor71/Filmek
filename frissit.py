import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

# 1. Weboldal letöltése és a legfrissebb .xls link megkeresése
url = "http://www.filmforgalmazok.hu/category/filmenkenti-osszesites/"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

xls_link = None
for link in soup.find_all("a"):
    href = link.get("href", "")
    if ".xls" in href:
        xls_link = href
        break

if not xls_link:
    print("Nem található .xls fájl az oldalon.")
    exit()

print(f"Legfrissebb fájl megtalálva: {xls_link}")

# 2. Az .xls fájl letöltése
xls_data = requests.get(xls_link, headers=headers).content
with open("adatok.xls", "wb") as f:
    f.write(xls_data)

# 3. Az .xls beolvasása és tisztítása (Pandas segítségével)
# Feltételezzük, hogy az első pár sor fejléc, és a táblázat később kezdődik
try:
    df = pd.read_excel("adatok.xls", skiprows=3) # Ha nem stimmel a sor, ezen igazítunk
    
    # Oszlopok átnevezése a kényelmes használathoz (A filmforgalmazók struktúrája alapján)
    # Feltételezzük a standard sorrendet: Magyar cím, Eredeti cím, Bemutató, Néző, Bevétel
    # Mivel az oszlopnevek változhatnak, index alapján azonosítjuk őket:
    df = df.dropna(subset=[df.columns[0]]) # Üres sorok kiszűrése
    
    output = []
    for _, row in df.iterrows():
        try:
            film = {
                "magyar_cim": str(row.iloc[0]).strip(),
                "eredeti_cim": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
                "bemutato": str(row.iloc[2]).split()[0] if pd.notna(row.iloc[2]) else "",
                "nezoszam": int(row.iloc[3]) if pd.notna(row.iloc[3]) and str(row.iloc[3]).isdigit() else 0,
                "bevetel": int(row.iloc[4]) if pd.notna(row.iloc[4]) and str(row.iloc[4]).isdigit() else 0
            }
            output.append(film)
        except Exception as e:
            continue

    # 4. Mentés JSON formátumba
    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Sikeres adatfrissítés! adatok.json elkészült.")

except Exception as e:
    print(f"Hiba a fájl feldolgozása közben: {e}")
