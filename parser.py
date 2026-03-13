import bs4
import os
from recipe import Ingredient, Recipe
import re
import pandas as pd

CSS_INGREDIENTS = "div.ingredienten li"
CSS_INFO_PERSONEN = "div.informatie.detail li.personen"
CSS_INFO_BEREIDINGSTIJD = "div.informatie.detail li.bereiding"
CSS_INFO_INSTRUCTIES = "span[itemprop='recipeInstructions']"
CSS_INFO_RECEPTCAT = "div.informatie.detail li.gerecht"
CSS_INFO_CALORIEN = "div.informatie.detail li.calorieen"
CSS_PROTEIN = 'td[itemprop="proteinContent"]'
CSS_H1 = "h1"

rows = []
dir = 'recipes/'
for file_name in os.listdir(dir):
    with open(dir + file_name, 'r') as f:
        content = f.read()
    soup = bs4.BeautifulSoup(content, features="html.parser")

    name = soup.select_one(CSS_H1)
    if not name:
        continue 
    name = name.text
    cal_str = soup.select_one(CSS_INFO_CALORIEN).text
    calories = int(re.findall(r'\d+', cal_str)[0])
    protein = int(re.findall(r'\d+', soup.select_one(CSS_PROTEIN).text)[0])
    n_persons = int(re.findall(r'\d+', soup.select_one(CSS_INFO_PERSONEN).text)[0])
    preptime = soup.select_one(CSS_INFO_BEREIDINGSTIJD).text
    instructions = soup.select_one(CSS_INFO_INSTRUCTIES).text
    receptcat = soup.select_one(CSS_INFO_RECEPTCAT).text
    ingredients = [ingredient.text for ingredient in soup.select(CSS_INGREDIENTS)]

    #rec = Recipe(name=name, n_persons= n_persons, preptime= preptime, ingredients=ingredients, instructions = instructions, protein=protein, calories=calories, receptcat= receptcat) 
    #print(rec)
    

# voeg rij toe voor DataFrame
    rows.append({
        "name": name,
        "ingredients": ingredients,     # string zodat df het netjes weergeeft
        "instructions": instructions,
        "preptime": preptime,
        "n_persons": n_persons,
        "calories": calories,
        "protein": protein
    })

# maak DataFrame in één keer
df = pd.DataFrame(rows, columns=["name", "ingredients", "instructions", "preptime", "n_persons", "calories", "protein"])

pd.to_pickle(df, "data/veggie_recipes_struct.pkl")