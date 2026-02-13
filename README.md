
# PKU meal planner
PKU-patiënten moeten dagelijks hun eiwitinname nauwkeurig monitoren. Deze app kan worden gebruikt om een dagplanning te maken die voldoet aan de ingestelde eiwit dag-limieten. 

In de app kun je zo een dagplanning te maken:

 - Kies een maaltijd (ontbijt, lunch, avondeten)
 - filter op productgroep, naam, kleurcategorie
 - voer hoeveel gram/ml van het product (default = 1 VSE)
 - zet een daglimiet voor eiwit 
 - voeg het product toe aan de dagplanning

 ### output
 - totaal aantal kcal en eiwit voor het product
 - progress bar voor daglimiet eiwit + restant eiwit over
 - tabel met dagplanning + totalen (download de dagplanning als .xlsx file)

---

## Inhoud
- [Installatie](#installatie)
- [Data](#data)
- [Architectuur & bestanden](#architectuur--bestanden)
- [Licentie](#licentie)
- [Disclaimer](#disclaimer)

---

## Installatie

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
run de app lokaal via je terminal:
```bash
streamlit run pku_app.py
```

## Data

Gebruik de bijgevoegde CSV of een CSV zoals `product_list.csv` met ten minste deze kolommen (zie data/product_list.csv):

- `Naam`, `Eiwit (g) per VSE`, `Energie (kcal) per VSE`, `1 VSE`, `Hoeveelheid gram/ml`, `Kleurgroep`, `Productgroep`

---


## Architectuur & bestanden

- `data/product_list.csv`: brondata
- `pku_app.py`: streamlit app (interface en handmatige aanmaak van dagplanning)

---

## Licentie

Vrij te gebruiken
de app wordt gehost op https://pku-app.alwaysbelearning.nl/


## Disclaimer

Deze applicatie wordt aangeboden **zoals hij is** ("as is"). Gebruik is **op eigen risico**. Hoewel er zorg is besteed aan de juistheid en volledigheid, kan de software **fouten of onnauwkeurigheden** bevatten en worden **geen garanties** gegeven voor prestaties, resultaten of geschiktheid voor een bepaald doel.

De maker/beheerder is **niet aansprakelijk** voor enige directe, indirecte, incidentele, bijzondere of gevolgschade die voortvloeit uit het gebruik, het niet kunnen gebruiken, of de resultaten van het gebruik van deze applicatie, dataset(s) of bijbehorende documentatie. Door de applicatie te gebruiken, ga je akkoord met deze voorwaarden.
