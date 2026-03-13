
from typing import Dict, List

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


# Slot-specifieke maxima als percentage van daglimieten ---
# Deze percentages worden vermenigvuldigd met protein_limit en kcal_limit.
# Pas naar wens aan; hieronder een verdeling die vaak goed werkt.
SLOT_MAX_PROTEIN_PCT = {
    'ontbijt': 0.20,
    'fruit':   0.10,
    'lunch':   0.25,
    'snack':   0.15,
    'avondeten': 0.30  # voorbeeld: 30% voor diner
}

SLOT_MAX_KCAL_PCT = {
    'ontbijt': 0.20,
    'fruit':   0.10,
    'lunch':   0.25,
    'snack':   0.15,
    'avondeten': 0.30  # voorbeeld: 30% voor diner
}

# --- HELPER: maaltijdgroepen ---
ACCEPTABLE_VSE = {
    'ontbijt': ['1 portie','1 schaaltje','1 glas','1 snee','1 stuk'],
    'fruit':   ['1 stuk','1 schaaltje','1 handje','1 glas'],
    'lunch':   ['1 snee','1 stuk','1 bolletje','1 kop','2 stuks','1 portie'],
    'snack':   ['1 stuk','1 zakje','1 handje','2 stuks'],
    'avondeten':['2 opscheplepels','1 portie','1 stuk']
}

MEAL_GROUPS: Dict[str, List[str]] = {
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