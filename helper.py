import pandas as pd # type: ignore

# --- HELPER: kolomnamen normaliseren en decimale komma's ---
def prepare_df_for_solver(df: pd.DataFrame) -> pd.DataFrame:
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
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Verwijder rijen zonder geldige per-VSE waarden
    df = df[df['protein_vse'].notnull() & df['kcal_vse'].notnull()]
    return df


# --- HELPER: maaltijdgroepen en VSE-geschiktheid ---
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
        'Melkproducten- Nagerechten'
    ],
    'fruit': ['Fruit'],
    'lunch': ['Brood en crackers', 'Salades', 'Samengestelde gerechten', 'Soepen'],
    'snack': ['Gebak en koek', 'Snacks', 'Noten, zaden en chips', 'Chocola'],
    'avondeten': ['Samengestelde gerechten', 'Aardappelen en knolgewassen',
                  'Groenten en peulvruchten', 'Vis', 'Vlees en vleeswaren', 'Vegetarische producten']
}

EXCLUDE_GROUPS = {'Vetten, oliën en hartige sauzen', 'Kruiden en specerijen', 'Dieetpreparaten'}


def get_candidates(df: pd.DataFrame, slot_key: str, top_n: int = 50) -> pd.DataFrame:
    """Beperk tot realistische kandidaten per maaltijdslot."""
    groups = MEAL_GROUPS[slot_key]
    c = df[df['productgroep'].isin(groups)].copy()
    c = c[~c['productgroep'].isin(EXCLUDE_GROUPS)]
    c = c[c['vse_label'].isin(ACCEPTABLE_VSE[slot_key])]
    c = c[c['kcal_vse'] > 0]
    # Houd de laagste-eiwit opties om het oplossen makkelijker te maken
    c = c.sort_values('protein_vse').head(top_n).reset_index(drop=True)
    return c




def solve_plan_pulp(df: pd.DataFrame,
                    protein_limit: float,
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

        # >>> HIER de nieuwe 'meerdere producten' constraint <<<
        prob += pulp.lpSum(y[(slot,i)] for i in range(len(cands))) <= 2
        #prob += cands[i] in brood and cands[j] in beleg

    # Daglimiet eiwit
    total_protein = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'protein_vse']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )
    prob += total_protein <= protein_limit

    # (Optioneel) voorkom hergebruik van exact hetzelfde product (over alle maaltijden)
    if unique_product:
        name_occ = {}
        for slot in slots:
            for i, nm in enumerate(candidates[slot]['naam']):
                name_occ.setdefault(nm, []).append((slot, i))
        for nm, occ in name_occ.items():
            prob += pulp.lpSum(y[(slot,i)] for (slot,i) in occ if (slot,i) in y) <= 1

    # Doel: maximaliseer kcal
    total_kcal = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'kcal_vse']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )
    prob += total_kcal

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
                    'VSE gram/ml': chosen['hoeveelheid'],
                    'Servings (VSE)': round(chosen_s, 2),
                    'Eiwit (g)': round(chosen['protein_vse'] * chosen_s, 2),
                    'Energie (kcal)': round(chosen['kcal_vse'] * chosen_s, 1),
                    'Productgroep': chosen['productgroep'],
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
    df  = prepare_df_for_solver(df)
    solve_plan_pulp(df, protein_limit=10.0, min_serv=0.5, max_serv=2.0)