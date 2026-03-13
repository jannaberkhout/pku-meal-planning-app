
# PKU meal planner
PKU-patiënten moeten dagelijks hun eiwitinname nauwkeurig monitoren. Deze app kan worden gebruikt om een dagplanning te maken die voldoet aan de ingestelde eiwit dag-limieten. 

In de app zijn er twee methodes om een dagplanning te maken:

## 1.) Handmatig (maak een eigen dagplanning)
 - Kies een maaltijd (ontbijt, lunch, avondeten)
 - filter op productgroep, naam, kleurcategorie
 - voer hoeveel gram/ml van het product (default = 1 VSE)
 - zet een daglimiet voor eiwit 
 - voeg het product toe aan de dagplanning

 ### output
 - totaal aantal kcal en eiwit voor het product
 - progress bar voor daglimiet eiwit + restant eiwit over
 - tabel met dagplanning + totalen (download de dagplanning als .xlsx file)

 ## 2.) PuLP-ILP Solver (Doe een voorstel)

Een compacte, uitbreidbare planner die per dag **ontbijt, fruit, lunch, snack en avondeten** voorstelt op basis van `product_list.csv`. De planner:

- respecteert een **daglimiet eiwit** (`protein_limit`),
- werkt met een **kcal-doel** (`kcal_limit`) en ondergrens (85%),
- hanteert **slot-minima** (eiwit/kcal) en **slot-maxima als percentage van de daglimieten** (eiwit/kcal),
- dwingt **brood + beleg** (1:1 servings) en **diner-compositie** (groente + carb + eiwitbron *óf* een samengesteld gerecht),
- zorgt voor **exact 1** fruit én **exact 1** snack

> Ontworpen om flexibel te zijn: alle regels zijn configurabel via Python (`config.py`).

---

## Inhoud
- [Installatie](#installatie)
- [Data](#data)
- [Snel starten](#snel-starten)
- [Configuratie](#configuratie)
- [Sanity-check](#sanity-check)
- [Belangrijkste constraints](#belangrijkste-constraints)
- [CLI (optioneel)](#cli-optioneel)
- [Output](#output)
- [Architectuur & bestanden](#architectuur--bestanden)
- [Troubleshooting](#troubleshooting)

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

De helper `prepare_df(...)` normaliseert kolomnamen en zet decimale komma's om naar punten.

---

## Configuratie

Je kunt de configuratie van de solver op deze manier beheren:

### `config.py` 
Alle variabelen in één module. Voorbeelden:

```python
# config.py (fragment)
MEAL_GROUPS = {
    'ontbijt': ['Graanproducten, pappen en bindmiddelen','Brood en crackers',
                'Melk/yoghurtdrank','Melkproducten- Nagerechten','Kaas',
                'Broodbeleg, hartig','Broodbeleg, zoet'],
    'fruit': ['Fruit'],
    'lunch':  [...],
    'snack':  [...],
    'avondeten': [...]
}

EXCLUDE_GROUPS = {'Vetten, oliën en hartige sauzen','Kruiden en specerijen','Dieetpreparaten'}

ACCEPTABLE_VSE = {
    'ontbijt': ['1 portie','1 schaaltje','1 glas','1 snee','1 stuk'],
    'fruit':   ['1 stuk','1 schaaltje','1 handje','1 glas'],
    'lunch':   ['1 snee','1 stuk','1 bolletje','1 kop','2 stuks','1 portie'],
    'snack':   ['1 stuk','1 zakje','1 handje','2 stuks'],
    'avondeten':['2 opscheplepels','1 portie','1 stuk']
}

SLOT_MIN_PROTEIN = {'ontbijt':0.3,'fruit':0.0,'lunch':0.5,'snack':0.0,'avondeten':1.0}
SLOT_MIN_KCAL    = {'ontbijt':150,'fruit':50,'lunch':300,'snack':100,'avondeten':350}
SLOT_MAX_PROTEIN_PCT = {'ontbijt':0.20,'fruit':0.10,'lunch':0.25,'snack':0.15,'avondeten':0.30}
SLOT_MAX_KCAL_PCT    = {'ontbijt':0.20,'fruit':0.10,'lunch':0.25,'snack':0.15,'avondeten':0.30}
```


---

## Belangrijkste constraints

- **Fruit/snack**: elk **exact 1** item.
- **Ontbijt/lunch/avondeten**: **min 1, max 3** items.
- **Brood + beleg**: aantal servings **exact 1:1**.
- **Avondeten**: **veg + carb + protein** *óf* **composed** (volledig gerecht).
- **Slot‑minima**: `SLOT_MIN_PROTEIN`, `SLOT_MIN_KCAL`.
- **Slot‑maxima** (percentueel): `SLOT_MAX_PROTEIN_PCT * protein_limit`, `SLOT_MAX_KCAL_PCT * kcal_limit`.
- **Daglimieten**: `total_protein ≤ protein_limit`, `total_kcal ≤ kcal_limit` én `total_kcal ≥ 0.85 * kcal_limit`.
- **Unique product** (optioneel): geen hergebruik van dezelfde `Naam` in de dag.

---

## Output

De solver schrijft standaard een tabel met o.a.:

```text
Maaltijd,Product,1 VSE,VSE gram/ml,Servings (VSE),Eiwit (g),Energie (kcal),Productgroep,Kleurgroep
Ontbijt,Jelly aardbei (dr. Oetker) bereid,1 portie,150 gram,1.00,0.00,90.0,Melkproducten- Nagerechten,groen
Fruit,Appelmoes (blik/ pot),1 schaaltje,200 gram,1.00,0.40,152.0,Fruit,groen
...
```

Daarnaast print de solver een `Totals`‑samenvatting met **totaal eiwit/kcal** en de gebruikte limieten.

---

## Architectuur & bestanden

- `config.py` : configuratie (groepen, VSE, minima/maxima)
- `helper.py`: PuLP solver (constraints + doelstelling), helpers
- `data/product_list.csv`: brondata
- `pku_app.py`: streamlit app (interface en handmatige aanmaak van dagplanning)

---

## Troubleshooting

- **Infeasible**: verlaag slot‑minima, verhoog daglimieten, of versoepel brood+beleg (bandbreedte i.p.v. 1:1).
- **Te weinig variatie**: verhoog `top_n` in `get_candidates`, zet `unique_product=False` (tijdelijk).
- **Kcal‑ondergrens (85%) niet haalbaar**: controleer som van `SLOT_MAX_KCAL_PCT` (bijv. ≥ 0.85) en verhoog evt. percentages.
- **Geen kandidaten in een slot**: controleer `MEAL_GROUPS` en `ACCEPTABLE_VSE` (VSE‑labels moeten overeenkomen met je dataset).

---

## Licentie

Vrij te gebruiken
de app wordt gehost op https://pku-app.streamlit.app/


## Disclaimer

Deze applicatie wordt aangeboden **zoals hij is** ("as is"). Gebruik is **op eigen risico**. Hoewel er zorg is besteed aan de juistheid en volledigheid, kan de software **fouten of onnauwkeurigheden** bevatten en worden **geen garanties** gegeven voor prestaties, resultaten of geschiktheid voor een bepaald doel.

De maker/beheerder is **niet aansprakelijk** voor enige directe, indirecte, incidentele, bijzondere of gevolgschade die voortvloeit uit het gebruik, het niet kunnen gebruiken, of de resultaten van het gebruik van deze applicatie, dataset(s) of bijbehorende documentatie. Door de applicatie te gebruiken, ga je akkoord met deze voorwaarden.
