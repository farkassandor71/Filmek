import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

# Álcázott böngésző fejlécek (User-Agent), hogy embernek tűnjön a robot
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "hu,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

url = "https://filmforgalmazok.hu/category/filmenkenti-osszesites/"

# Hibatűrő letöltés: 5 alkalommal újrapróbálkozik, ha a szerver lassan válaszolna
response = None
for i in range(5):
    try:
        print(f"Kapcsolódási kísérlet a weboldalhoz ({i+1}/5)...")
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            print("Sikeres csatlakozás!")
            break
    except requests.exceptions.RequestException as e:
        print(f"Hiba történt: {e}")
        time.sleep(5) # Vár 5 másodpercet a következő próbálkozás előtt

if not response or response.status_code != 200:
    print("Nem sikerült elérni a filmforgalmazók oldalt. A szerver blokkolja a kérést.")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

xls_link = None
for link in soup.find_all("a"):
    href = link.get("href", "")
    if ".xls" in href:
        xls_link = href
        break

if not xls_link:
    print("Nem található .xls fájl az oldalon.")
    exit(1)

print(f"Legfrissebb fájl megtalálva: {xls_link}")

# Az .xls fájl letöltése az álcázott fejléccel
try:
    xls_data = requests.get(xls_link, headers=headers, timeout=30).content
    with open("adatok.xls", "wb") as f:
        f.write(xls_data)
    print("Excel fájl sikeresen letöltve.")
except Exception as e:
    print(f"Nem sikerült letölteni az Excel fájlt: {e}")
    exit(1)

# Az .xls beolvasása és tisztítása
try:
    df = pd.read_excel("adatok.xls", skiprows=3)
    df = df.dropna(subset=[df.columns[0]]) # Üres sorok törlése
    
    output = []
    for _, row in df.iterrows():
        try:
            # Csak akkor adjuk hozzá, ha a bemutató dátuma vagy a cím értelmes szöveg
            m_cim = str(row.iloc[0]).strip()
            if m_cim.lower() in ["magyar cím", "nan", ""] or "összesen" in m_cim.lower():
                continue
                
            film = {
                "magyar_cim": m_cim,
                "eredeti_cim": str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
                "bemutato": str(row.iloc[2]).split()[0] if pd.notna(row.iloc[2]) else "",
                "nezoszam": int(row.iloc[3]) if pd.notna(row.iloc[3]) and str(row.iloc[3]).replace('.','').replace(' ','').isdigit() else 0,
                "bevetel": int(row.iloc[4]) if pd.notna(row.iloc[4]) and str(row.iloc[4]).replace('.','').replace(' ','').isdigit() else 0
            }
            output.append(film)
        except Exception as e:
            continue

    # Mentés JSON formátumba
    with open("adatok.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Sikeres adatfrissítés! {len(output)} film feldolgozva. adatok.json elkészült.")

except Exception as e:
    print(f"Hiba a fájl feldolgozása közben: {e}")
    exit(1)
