from bs4 import BeautifulSoup
from dataclasses import dataclass
import requests as req
import json
import datetime



@dataclass
class Recipe:
    name: str
    url: str
    headline: str
    author: str
    image: list  #  list with order [@type, url, height, width, description]
    datePublished: str
    dateModified: str
    publisher: list  #  list with order [name, url]
    keywords: str
    cookTime: str
    prepTime: str
    totalTime: str
    recipeIngredient: list  #  list with order [ingredient 1, ingredient2...]
    recipeInstructions: list  #  list of tuples [(@type, instruction text),]
    rating: float
    recipeYield: str




def rec_link_consolidate(url):
    page = req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    links_pag = []
    rec_array = []
    for item in soup.find_all("a", class_="o-IndexPagination__a-Button"):
        links_pag.append("http:" + item.get('href'))
    for item2 in links_pag:
        page2 = req.get(item2)
        soup2 = BeautifulSoup(page2.content, 'html.parser')
        for item3 in soup2.find_all("li", class_="m-PromoList__a-ListItem"):
            rec_array.append("http:" + item3.a.get('href'))
    return rec_array


def rec_json_dict(url):
    page = req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    rec_json_tag = soup.find('script', type="application/ld+json")
    data = json.loads(rec_json_tag.text)
    if isinstance(data, list):
        site_dict = data[0]
    else:
        site_dict = data

    rec_url = 'Third option'
    if 'url' in site_dict.keys():
        rec_url = site_dict.get('url')
    elif 'mainEntityOfPage' in site_dict.keys():
        if '@id' in site_dict.get('mainEntityOfPage'):
            rec_url = site_dict.get('mainEntityOfPage').get('@id')
        else:
            rec_url = site_dict.get('mainEntityOfPage')
    else:
        return 'ERROR URL not found in json'

    rec_dict = Recipe(site_dict.get('name'), rec_url, site_dict.get('headline'), site_dict.get('author'), site_dict.get('image'), site_dict.get('datePublished'), site_dict.get('dateModified'), [site_dict.get('publisher').get('name'), site_dict.get('publisher').get('url')], site_dict.get('keywords'), site_dict.get('cookTime'), site_dict.get('prepTime'), site_dict.get('totalTime'), site_dict.get('recipeIngredient'), site_dict.get('recipeInstructions'), site_dict.get('aggregateRating').get('ratingValue'), site_dict.get('recipeYield'))
    return rec_dict




# abLinks = rec_link_consolidate("https://www.foodnetwork.com/recipes/alton-brown")
# print('type: ', type(abLinks))
# print(len(abLinks))


#dict1 = (rec_json_dict("https://www.foodnetwork.com/recipes/alton-brown/10-minute-apple-sauce-recipe-1950796"))
#print(dict1)

print(rec_json_dict('https://www.justonecookbook.com/zosui-japanese-rice-soup/#webpage'))






