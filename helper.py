import pandas as pd # type: ignore

# --- HELPER: kolomnamen normaliseren en decimale komma's ---
def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        'Naam': 'naam',
        'Eiwit (g) per 100 gram': 'protein_100g',
        'Energie (kcal) per 100 gram': 'kcal_100g',
        '1 VSE': 'vse_label',
        'Hoeveelheid gram/ml': 'hoeveelheid',
        'Eiwit (g) per VSE': 'protein_vse',
        'Energie (kcal) per VSE': 'kcal_vse',
        'Kleurgroep': 'kleurgroep',
        'Productgroep': 'productgroep'
    })

    # Zorg dat alle numerieke velden numeriek zijn (comma->dot)
    for col in ['protein_100g', 'kcal_100g', 'protein_vse', 'kcal_vse']:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors='raise').fillna(0)

    # Converteer Hoeveelheid gram/ml naar integer
    
    #Pak het eerste getal (met optionele decimalen) en zet komma om in punt
    num = df['hoeveelheid'].str.extract(r'(\d+(?:[.,]\d+)?)')[0].str.replace(',', '.', regex=False)
    df['hoeveelheid_per_vse'] = pd.to_numeric(num, errors='coerce')
    return df

# --- HELPER: maaltijdgroepen ---
ACCEPTABLE_VSE = {
    'ontbijt': ['1 portie','1 schaaltje','1 glas','1 snee','1 stuk'],
    'fruit':   ['1 stuk','1 schaaltje','1 handje','1 glas'],
    'lunch':   ['1 snee','1 stuk','1 bolletje','1 kop','2 stuks','1 portie'],
    'snack':   ['1 stuk','1 zakje','1 handje','2 stuks'],
    'avondeten':['2 opscheplepels','1 portie','1 stuk']
}

MEAL_GROUPS = {
    'ontbijt': [
        'Graanproducten, pappen en bindmiddelen',
        'Brood en crackers',
        'Melk/yoghurtdrank',
        'Melkproducten- Nagerechten',
        'Kaas',
        'Broodbeleg, hartig',
        'Broodbeleg, zoet'
    ],
    'fruit': ['Fruit'],
    'lunch': ['Brood en crackers', 
              'Salades', 
              'Soepen', 
              'Kaas',
              'Broodbeleg, hartig',
              'Broodbeleg, zoet'],
    'snack': ['Gebak en koek', 
              'Snacks', 
              'Noten, zaden en chips', 
              'Chocola'],
    'avondeten': ['Samengestelde gerechten', 
                  'Aardappelen en knolgewassen',
                  'Groenten en peulvruchten', 
                  'Vis', 
                  'Vlees en vleeswaren', 
                  'Vegetarische producten']
}

EXCLUDE_GROUPS = {'Vetten, oliën en hartige sauzen', 'Kruiden en specerijen', 'Dieetpreparaten'}


import re

#geeft per kandidaat tags voor combinatieregels
def component_tags(row) -> set[str]:
    g   = (row['productgroep'] or '').strip()
    nm  = (row['naam'] or '').strip().lower()
    vse = (row['vse_label'] or '').strip().lower()
    tags = set()

    # --- broodbasis ---
    if g == 'Brood en crackers' or \
       re.search(r'\b(pizzabodem)\b', nm):
        tags.add('bread_base')
        # brood telt ook als koolhydraat (voor diner)
        tags.add('carb')

    # --- broodbeleg (hartig/zoet/kaas) ---
    # prima indicator is VSE 'voor 1 snee' of smeer/spread in naam
    if g in {'Broodbeleg, hartig', 'Broodbeleg, zoet', 'Kaas'} or \
       ('voor 1 snee' in vse) or \
       re.search(r'\b(smeer|spread|heksenkaas|baba|pasta|tapena(de)?|tah(i|ini)nh?)\b', nm):
        tags.add('bread_spread')

    # --- groente ---
    if g == 'Groenten en peulvruchten':
        tags.add('veg')

    # --- koolhydraat ---
    if g in {'Aardappelen en knolgewassen', 'Graanproducten, pappen en bindmiddelen'}:
        tags.add('carb')

    # --- eiwitbron ---
    if g in {'Vis', 'Vlees en vleeswaren', 'Vegetarische producten', 'Eieren'}:
        tags.add('protein')

    # --- samengesteld gerecht ---
    if g == 'Samengestelde gerechten':
        tags.add('composed')

    return tags

def get_candidates(df: pd.DataFrame, slot_key: str, top_n: int = 200) -> pd.DataFrame:
    """Beperk tot realistische kandidaten per maaltijdslot."""
    groups = MEAL_GROUPS[slot_key]
    c = df[df['productgroep'].isin(groups)].copy()
    c = c[~c['productgroep'].isin(EXCLUDE_GROUPS)]
    c = c[c['vse_label'].isin(ACCEPTABLE_VSE[slot_key])]
    c = c[c['kcal_vse'] > 0]
    c['tags'] = c.apply(component_tags, axis=1)
    # Houd de laagste-eiwit opties om het oplossen makkelijker te maken
    c = c.sort_values('protein_vse').head(top_n).reset_index(drop=True) #vergroot top_n als je meer variatie wilt; verklein voor snellere solve‑tijden.
    return c

#maakt indexlijsten per component voor elk slot
def _build_index_by_tag(cands: pd.DataFrame):
    by = { 'bread_base': [], 'bread_spread': [], 'veg': [], 'carb': [], 'protein': [], 'composed': [] }
    for i, tags in enumerate(cands['tags']):
        for t in by.keys():
            if t in tags:
                by[t].append(i)
    return by


# Minima per slot (pas aan naar jouw voorkeur)
SLOT_MIN_PROTEIN = {
    'ontbijt': 0.3,   # gram
    'fruit':   0.0,
    'lunch':   0.5,
    'snack':   0.0,
    'avondeten': 1.0
}

SLOT_MIN_KCAL = {
    'ontbijt': 50,   # kcal
    'fruit':    50,
    'lunch':   100,
    'snack':   50,
    'avondeten': 200
}


def solve_plan_pulp(df: pd.DataFrame,
                    protein_limit: float,
                    kcal_limit: float,
                    min_serv: float,
                    max_serv: float,
                    unique_product: bool = True):
    import pulp

    slots = ['ontbijt', 'fruit', 'lunch', 'snack', 'avondeten']
    candidates = {s: get_candidates(df, s) for s in slots}

    prob = pulp.LpProblem('PKU_MealPlan', pulp.LpMaximize)
    y, s = {}, {}

    # Variabelen + constraints per slot
    for slot in slots:
        cands = candidates[slot]
        if len(cands) == 0:
            # Geen kandidaten -> maak model infeasible
            prob += 0 == 1
            continue

        for i in range(len(cands)):
            y[(slot,i)] = pulp.LpVariable(f'y_{slot}_{i}', lowBound=0, upBound=1, cat='Binary')
            s[(slot,i)] = pulp.LpVariable(f's_{slot}_{i}', lowBound=0, upBound=max_serv, cat='Continuous')
            # Link s aan y
            prob += s[(slot,i)] <= max_serv * y[(slot,i)]
            prob += s[(slot,i)] >= min_serv * y[(slot,i)]

        
    # --- NIEUW: aantal items per slot ---
        count = pulp.lpSum(y[(slot,i)] for i in range(len(cands)))
        if slot in ['fruit', 'snack']:
            # Exact 1 item
            prob += count == 1
        else:
            # Ontbijt/lunch/avondeten: minimaal 1, maximaal 3
            prob += count >= 1
            prob += count <= 3

        # --- NIEUW: slot-minima op eiwit en kcal ---
        slot_protein = pulp.lpSum(s[(slot,i)] * candidates[slot].loc[i, 'protein_vse']
                                  for i in range(len(cands)))
        slot_kcal    = pulp.lpSum(s[(slot,i)] * candidates[slot].loc[i, 'kcal_vse']
                                  for i in range(len(cands)))
        
# Alleen toevoegen als er een minimum is geconfigureerd
        if slot in SLOT_MIN_PROTEIN:
            prob += slot_protein >= SLOT_MIN_PROTEIN[slot]
        if slot in SLOT_MIN_KCAL:
            prob += slot_kcal    >= SLOT_MIN_KCAL[slot]


    # Daglimiet eiwit
    total_protein = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'protein_vse']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )
    prob += total_protein <= protein_limit


    # Totale kcal (voor doel en grenzen)
    total_kcal = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'kcal_vse']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )

    # Bovengrens kcal (optioneel)
    if kcal_limit is not None:
        prob += total_kcal <= kcal_limit
        prob += total_kcal >= kcal_limit*0.85


    # (Optioneel) voorkom hergebruik van exact hetzelfde product (over alle maaltijden)
    if unique_product: 
        name_occ = {}
        for slot in slots:
            for i, nm in enumerate(candidates[slot]['naam']):
                name_occ.setdefault(nm, []).append((slot, i))
        for nm, occ in name_occ.items():
            prob += pulp.lpSum(y[(slot,i)] for (slot,i) in occ if (slot,i) in y) <= 1


    # --- NIEUW: indices per tag per slot ---
    idx_by_slot = {slot: _build_index_by_tag(candidates[slot]) for slot in slots}

    # --- NIEUW: brood + beleg constraints (ontbijt & lunch) ---
    # Guard: voeg alleen toe als er ten minste brood of beleg kandidaten zijn
    for slot in ['ontbijt', 'lunch']:
        base_idx = idx_by_slot[slot]['bread_base']
        spread_idx = idx_by_slot[slot]['bread_spread']
        if len(base_idx) + len(spread_idx) == 0:
            continue  # niets te doen in dit slot

        BB   = pulp.lpSum(y[(slot,i)] for i in base_idx)
        SP   = pulp.lpSum(y[(slot,i)] for i in spread_idx)
        BB_s = pulp.lpSum(s[(slot,i)] for i in base_idx)
        SP_s = pulp.lpSum(s[(slot,i)] for i in spread_idx)

        # (1) ten minste evenveel beleg-items als brood-items
        prob += SP >= BB

        # (2) geen beleg zonder brood (big-M = 3, want max 3 items per slot)
        prob += SP <= 3 * BB

        # (3) servings koppeling: ~1 beleg per snee (marge toegestaan)
        prob += SP_s == BB_s

    # diner compositie (groente + carb + eiwit óf samengesteld) ---
    slot = 'avondeten'
    comp_idx = idx_by_slot[slot]['composed']
    veg_idx  = idx_by_slot[slot]['veg']
    carb_idx = idx_by_slot[slot]['carb']
    prot_idx = idx_by_slot[slot]['protein']

    # Voeg constraints toe alleen als er ten minste één kandidaat in de relevante sets zit,
    # om infeasibiliteit bij lege datasets te voorkomen.
    if len(comp_idx) + len(veg_idx) + len(carb_idx) + len(prot_idx) > 0:
        COMP  = pulp.lpSum(y[(slot,i)] for i in comp_idx)
        VEG   = pulp.lpSum(y[(slot,i)] for i in veg_idx)
        CARB  = pulp.lpSum(y[(slot,i)] for i in carb_idx)
        PROT  = pulp.lpSum(y[(slot,i)] for i in prot_idx)

        # component- of samengesteld gerecht
        if len(veg_idx) + len(comp_idx) > 0:
            prob += VEG   + COMP >= 1
        if len(carb_idx) + len(comp_idx) > 0:
            prob += CARB  + COMP >= 1
        if len(prot_idx) + len(comp_idx) > 0:
            prob += PROT  + COMP >= 1

        # (optioneel) minimale servings per component als er géén samengesteld gerecht is:
        VEG_s  = pulp.lpSum(s[(slot,i)] for i in veg_idx)
        CARB_s = pulp.lpSum(s[(slot,i)] for i in carb_idx)
        PROT_s = pulp.lpSum(s[(slot,i)] for i in prot_idx)

        M = 10  # big-M
        VEG_MIN, CARB_MIN, PROT_MIN = 0.5, 0.5, 0.5  # in VSE; pas aan naar wens
        if len(veg_idx) > 0:
            prob += VEG_s  >= VEG_MIN  - M * COMP
        if len(carb_idx) > 0:
            prob += CARB_s >= CARB_MIN - M * COMP
        if len(prot_idx) > 0:
            prob += PROT_s >= PROT_MIN - M * COMP

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    if status != 'Optimal':
        return None, {'status': status}

    # Output
    rows = []
    for slot in slots:
        cands = candidates[slot]
        for i in range(len(cands)):
            if pulp.value(y[(slot,i)]) and pulp.value(y[(slot,i)]) > 0.5:
                chosen = cands.loc[i]
                chosen_s = float(pulp.value(s[(slot,i)]))
                rows.append({
                    'Maaltijd': slot.capitalize(),
                    'Product': chosen['naam'],
                    '1 VSE': chosen['vse_label'],
                    'Hoeveelheid per VSE': chosen['hoeveelheid'],
                    'Hoeveelheid (g/ml)': round(chosen['hoeveelheid_per_vse'] * chosen_s,2),
                    'Aantal VSE': round(chosen_s, 2),
                    'Eiwit (g)': round(chosen['protein_vse'] * chosen_s, 2),
                    'Energie (kcal)': round(chosen['kcal_vse'] * chosen_s, 1),
                    'Kleurgroep': chosen['kleurgroep']
                })

    plan_df = pd.DataFrame(rows)
    totals = {
        'Status': status,
        'Totaal eiwit (g)': round(plan_df['Eiwit (g)'].sum(), 2),
        'Totaal energie (kcal)': round(plan_df['Energie (kcal)'].sum(), 1)
       }
    
    return plan_df, totals
 
if __name__ == "__main__":
    df = pd.read_csv("data/product_list.csv", sep=';')
    df  = prepare_df(df)
    plan_df, totals = solve_plan_pulp(df, protein_limit=10.0, min_serv=0.5, max_serv=2.0)
    if plan_df is None:
        print("Geen optimale oplossing:", totals)
    else:
        print(plan_df)
        print("\nTotals:", totals)
