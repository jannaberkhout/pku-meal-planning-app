import pandas as pd


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



import numpy as np
import pandas as pd

def get_candidates(df: pd.DataFrame, slot_key: str, top_n: int = 200) -> pd.DataFrame:
    """Beperk tot realistische kandidaten per maaltijdslot."""

    # Work on a copy to avoid side effects
    df = df.copy()

    # Ensure receptcat is a list of clean strings per row.
    # If any entries are single strings, convert to one-item lists.
    def normalize_cats(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return []
        if isinstance(x, list):
            return [s.strip() for s in x if isinstance(s, str)]
        if isinstance(x, str):
            # If accidentally stored as "a, b, c"
            return [s.strip() for s in x.split(",") if s.strip()]
        # Unknown type → treat as empty
        return []

    df['receptcat'] = df['receptcat'].apply(normalize_cats)

    # Keep rows where slot_key is present in the list of categories
    c = df[df['receptcat'].apply(lambda cats: slot_key in cats)].copy()

    # Keep valid calories > 0
    c = c[pd.to_numeric(c['calories'], errors='coerce') > 0].copy()

    # Make sure protein is numeric as well
    c['protein'] = pd.to_numeric(c['protein'], errors='coerce')

    # Vectorized protein/calorie ratio; 0 if calories <= 0 or cal is NaN
    cal = c['calories'].to_numpy(dtype=float)
    prot = c['protein'].to_numpy(dtype=float)
    pc_ratio = np.divide(prot, cal, out=np.zeros_like(prot, dtype=float), where=(cal > 0) & np.isfinite(cal))
    c['pc_ratio'] = pc_ratio

    # Sort and take the lowest protein/calorie options
    c = c.sort_values('pc_ratio', kind='mergesort').head(top_n).reset_index(drop=True)

    return c


def solve_plan_pulp(df: pd.DataFrame,
                    protein_limit: float,
                    kcal_limit: float,
                    min_serv: float,
                    max_serv: float,
                    unique_product: bool = True):
    import pulp

    slots = ['tussendoor', 'lunch', 'ontbijt', 'hoofdgerecht']

    required_picks = {'ontbijt': 1, 'lunch': 1, 'tussendoor': 2, 'hoofdgerecht': 1}

    candidates = {s: get_candidates(df, s) for s in slots}


    # Early validation: ensure each required slot has at least 1 candidate
    empty_slots = [s for s in slots if len(candidates[s]) < required_picks[s]]
    if empty_slots:
        raise ValueError(
            f"No candidates available for required slot(s): {', '.join(empty_slots)}. "
            f"Please adjust filters or provide recipes for these categories."
        )


    prob = pulp.LpProblem('PKU_MealPlan', pulp.LpMaximize)
    y, s = {}, {}

    # Variabelen + constraints per slot
    
    for slot in slots:
        cands = candidates[slot]
        for i in range(len(cands)):
            y[(slot, i)] = pulp.LpVariable(f'y_{slot}_{i}', lowBound=0, upBound=1, cat='Binary')
            s[(slot, i)] = pulp.LpVariable(f's_{slot}_{i}', lowBound=0, upBound=max_serv, cat='Continuous')
            # Link: s == 0 when y == 0, s in [min_serv, max_serv] when y == 1
            prob += s[(slot, i)] <= max_serv * y[(slot, i)]
            prob += s[(slot, i)] >= min_serv * y[(slot, i)]

        # ✅ precies 1 recept per slot
        prob += pulp.lpSum(y[(slot, i)] for i in range(len(cands))) == required_picks[slot]



    # Daglimiet eiwit
    total_protein = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'protein']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )
    prob += total_protein <= protein_limit


    # Totale kcal (voor doel en grenzen)
    total_kcal = pulp.lpSum(
        s[(slot,i)] * candidates[slot].loc[i, 'calories']
        for slot in slots for i in range(len(candidates[slot]))
        if (slot,i) in s
    )

    # Bovengrens kcal (optioneel)
    if kcal_limit is not None:
        prob += total_kcal <= kcal_limit
        prob += total_kcal >= kcal_limit*0.5


    # (Optioneel) voorkom hergebruik van exact hetzelfde product (over alle maaltijden)
    if unique_product: 
        name_occ = {}
        for slot in slots:
            for i, nm in enumerate(candidates[slot]['name']):
                name_occ.setdefault(nm, []).append((slot, i))
        for nm, occ in name_occ.items():
            prob += pulp.lpSum(y[(slot,i)] for (slot,i) in occ if (slot,i) in y) <= 1


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
                    'Recept': chosen['name'],
                    'url': chosen['url'],
                    'Personen': chosen['n_persons'],
                    'Aantal VSE': round(chosen_s, 2),
                    'Eiwit (g)': round(chosen['protein'] * chosen_s, 2),
                    'Energie (kcal)': round(chosen['calories'] * chosen_s, 1),
                })

    plan_df = pd.DataFrame(rows)
    totals = {
        'Status': status,
        'Totaal eiwit (g)': round(plan_df['Eiwit (g)'].sum(), 2),
        'Totaal energie (kcal)': round(plan_df['Energie (kcal)'].sum(), 1)
       }
    
    return plan_df, totals

 
if __name__ == "__main__":
    df = pd.read_pickle("data/veggie_recipes_struct.pkl")
    plan_df, totals = solve_plan_pulp(df, protein_limit=10.0, kcal_limit=1000, min_serv=0.1, max_serv=2.0)
    if plan_df is None:
        print("Geen optimale oplossing:", totals)
    else:
        print(plan_df)
        print("\nTotals:", totals)
