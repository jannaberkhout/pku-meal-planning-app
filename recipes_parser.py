import bs4
import os

CSS_INGREDIENTS = "div.ingredienten li"
CSS_INFO_PERSONEN = "div.informatie.detail li.personen"
CSS_INFO_BEREIDINGSTIJD = "div.informatie.detail li.bereiding"
CSS_INFO_GERECHT = "div.informatie.detail li.gerecht"
CSS_INFO_CALORIEN = "div.informatie.detail li.calorieen"


def strip_text(element):
    return element.text


dir = 'recipes/'
for file_name in os.listdir(dir):
    with open(dir + file_name, 'r') as f:
        content = f.read()
    soup = bs4.BeautifulSoup(content)

    info = soup.select(CSS_INFO_CALORIEN)
    for i in info:
        print(i.text)

    # ingredients = soup.select(CSS_INGREDIENTS)
    # if not ingredients:
    #     continue
    #
    # for i in ingredients:
    #     print(i.text)
