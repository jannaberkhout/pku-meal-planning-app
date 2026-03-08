import bs4
import os
from recipe import Ingredient, Recipe
import re

CSS_INGREDIENTS = "div.ingredienten li"
CSS_INFO_PERSONEN = "div.informatie.detail li.personen"
CSS_INFO_BEREIDINGSTIJD = "div.informatie.detail li.bereiding"
CSS_INFO_GERECHT = "div.informatie.detail li.gerecht"
CSS_INFO_CALORIEN = "div.informatie.detail li.calorieen"

CSS_PROTEIN = 'td[itemprop="proteinContent"]'
CSS_H1 = "h1"

dir = 'recipes/'
for file_name in os.listdir(dir):
    with open(dir + file_name, 'r') as f:
        content = f.read()
    soup = bs4.BeautifulSoup(content)

    name = soup.select_one(CSS_H1)
    if not name:
        continue 
    name = name.text
    cal_str = soup.select_one(CSS_INFO_CALORIEN).text
    calories = int(re.findall(r'\d+', cal_str)[0])
    protein = int(re.findall(r'\d+', soup.select_one(CSS_PROTEIN).text)[0])

    ingredients = []
    ingredient_elements = soup.select(CSS_INGREDIENTS)
    if not ingredient_elements:
        continue

    for i in ingredient_elements:
        ingredients.append(Ingredient(name=i.text))

    rec = Recipe(name=name, ingredients=ingredients, protein=protein, calories=calories) 
    print(rec)
