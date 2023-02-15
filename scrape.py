import format
import requests as req
from bs4 import BeautifulSoup
import json
import isodate
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Recipe:
    name: str
    url: str
    headline: str
    author: str
    description: str
    image: list  #  list with order [@type, url, height, width, description]
    datePublished: datetime
    dateModified: datetime
    publisherName: str
    publisherUrl: str
    keywords: str
    cookTime: datetime
    prepTime: datetime
    totalTime: datetime
    recipeIngredient: list  #  list with order [ingredient 1, ingredient2...]
    recipeInstructions: list  #  list of tuples [(@type, instruction text),]
    rating: float
    recipeYield: str
    recipeCategory: str
    recipeCuisine: str



def rec_json_dict(url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    page = req.get(url, headers=hdr)
    soup = BeautifulSoup(page.content, 'html.parser')
    rec_json_tag = soup.find('script', type="application/ld+json")
    data = json.loads(rec_json_tag.text)
    if isinstance(data, list):
        site_dict = data[0]
    else:
        site_dict = data

    if 'name' in site_dict.keys():
        rec_name = site_dict.get('name')
    elif 'headline' in site_dict.keys():
        rec_name = site_dict.get('headline')
    else:
        rec_name = "Name Unknown"


    if 'url' in site_dict.keys():
        rec_url = site_dict.get('url')
    elif 'mainEntityOfPage' in site_dict.keys():
        if isinstance(site_dict.get('mainEntityOfPage'), dict):
            if '@id' in site_dict.get('mainEntityOfPage').keys():
                rec_url = site_dict.get('mainEntityOfPage').get('@id')
        else:
            rec_url = site_dict.get('mainEntityOfPage')

    else:
        #return 'ERROR URL not found in json'
        rec_url = url

    if 'author' in site_dict.keys():
        if isinstance(site_dict['author'], list):
            site_dict['author'] = site_dict.get('author')[0]

        if isinstance(site_dict['author'], dict):
            if 'URL' in site_dict['author'].keys():
                site_dict['author']['url'] = site_dict['author']['URL']

    if 'publisher' in site_dict.keys():
        rec_publisher_name = site_dict.get('publisher').get('name')
        rec_publisher_url = site_dict.get('publisher').get('url')
    else:
        rec_publisher_name = "Publisher unknown"
        rec_publisher_url ="/"

    if 'recipeCuisine' in site_dict.keys():
        if isinstance(site_dict['recipeCuisine'], list):
            if len(site_dict['recipeCuisine']) == 1:
                site_dict['recipeCuisine'] = site_dict['recipeCuisine'][0]


    if 'aggregateRating' in site_dict.keys():
        rec_rating = site_dict.get('aggregateRating').get('ratingValue')
    else:
        rec_rating = "Rating unknown"

    iso_dates = ['dateModified', 'datePublished']
    iso_times = ['prepTime', 'cookTime', 'totalTime']
    for items in iso_dates:
        if isinstance(site_dict.get(items), str):
            site_dict[items] = isodate.parse_date(site_dict.get(items))
        else:
            site_dict[items] = None

    for items in iso_times:
        if isinstance(site_dict.get(items), str):
            site_dict[items] = format.format_timedelta(isodate.parse_duration(site_dict.get(items)))
        else:
            site_dict[items] = None


    rec_dict = Recipe(name= rec_name, url= rec_url, headline= site_dict.get('headline'), author= site_dict.get('author'), image= site_dict.get('image'), datePublished= site_dict.get('datePublished'), dateModified= site_dict.get('dateModified'), publisherName= rec_publisher_name, publisherUrl= rec_publisher_url, keywords= site_dict.get('keywords'), cookTime= site_dict.get('cookTime'), prepTime= site_dict.get('prepTime'), totalTime= site_dict.get('totalTime'), recipeIngredient= site_dict.get('recipeIngredient'), recipeInstructions= site_dict.get('recipeInstructions'), rating= rec_rating, recipeYield= site_dict.get('recipeYield'), description= site_dict.get('description'), recipeCategory= site_dict.get('recipeCategory'), recipeCuisine= site_dict.get('recipeCuisine'))
    #print(rec_dict.dateModified, rec_dict.datePublished, rec_dict.prepTime, rec_dict.cookTime, rec_dict.totalTime)

    return rec_dict