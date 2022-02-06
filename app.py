from asyncio import new_event_loop
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
import requests as req
from bs4 import BeautifulSoup
import json
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

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


def rec_json_dict(url):
    page = req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    rec_json_tag = soup.find('script', type="application/ld+json")
    data = json.loads(rec_json_tag.text)
    if isinstance(data, list):
        site_dict = data[0]
    else:
        site_dict = data

    print(site_dict, type(site_dict))

    if 'name' in site_dict.keys():
        rec_name = site_dict.get('name')
    elif 'headline' in site_dict.keys():
        rec_name = site_dict.get('headline')
    else:
        rec_name = "Name Unknown"

    rec_url = 'Third option'

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

    if 'publisher' in site_dict.keys():
        rec_publisher_name = site_dict.get('publisher').get('name')
        rec_publisher_url = site_dict.get('publisher').get('url')
    else:
        rec_publisher_name = "Publisher unknown"
        rec_publisher_url ="/"

    if 'aggregateRating' in site_dict.keys():
        rec_rating = site_dict.get('aggregateRating').get('ratingValue')
    else:
        rec_rating = "Rating unknown"

    rec_dict = Recipe(rec_name, rec_url, site_dict.get('headline'), site_dict.get('author'), site_dict.get('image'), site_dict.get('datePublished'), site_dict.get('dateModified'), [rec_publisher_name, rec_publisher_url], site_dict.get('keywords'), site_dict.get('cookTime'), site_dict.get('prepTime'), site_dict.get('totalTime'), site_dict.get('recipeIngredient'), site_dict.get('recipeInstructions'), rec_rating, site_dict.get('recipeYield'))
    return rec_dict


class RecDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    publisher = db.Column(db.String(200), nullable=True)
    time = db.Column(db.String(200), nullable=True)
    recYield = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.String(10), nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<Recipe %r>' % self.id


@app.route('/', methods={'POST', 'GET'} )
def index():
    cookbook = RecDB.query.order_by(RecDB.id).all()
    return render_template('index.html', cookbook=cookbook)

@app.route('/recipe_view/<int:id>')
def recipe_view(id):
    cookbook = RecDB.query.order_by(RecDB.id).all()
    recipe_to_view = RecDB.query.get_or_404(id)
    ingredients = eval(str(recipe_to_view.ingredients))
    instructions = eval(str(recipe_to_view.instructions))

    #publisher = ['temp', 'temp2']
    publisher = eval(str(recipe_to_view.publisher))
    print(type(recipe_to_view.publisher), recipe_to_view.publisher)

    # print(instr_slice, instructions, type(instructions))
    for items in instructions:
        print (type(items), items, end='\n')

    return render_template('view_recipe.html', recipe=recipe_to_view, cookbook = cookbook, ingredients = ingredients, instructions = instructions, publisher=publisher)


@app.route('/delete/<int:id>')
def delete(id):
    recipe_to_delete = RecDB.query.get_or_404(id)

    try:
        db.session.delete(recipe_to_delete)
        db.session.commit()
        return redirect('/')
    except:
            return 'Problem deleting'

@app.route('/update/<string:url>', methods = ['POST', 'GET'])
def update(url):
    if request.method == "POST":
        recipe_url = request.form['url']
        rec_dict = rec_json_dict(recipe_url)

        new_recipe = RecDB(name=str(rec_dict.name), url=str(recipe_url), image=str(type(rec_dict.image)), publisher = str(rec_dict.publisher),time=str(rec_dict.totalTime), recYield= str(rec_dict.recipeYield), rating= str(rec_dict.rating), ingredients=str(rec_dict.recipeIngredient), instructions=str(rec_dict.recipeInstructions))
        print(new_recipe)
        # new_recipe = RecDB(name = rec_dict.name, url = recipe_url, image = str(type(rec_dict.image)), time = rec_dict.totalTime, recYield = rec_dict.recipeYield, rating = rec_dict.rating, ingredients = str(rec_dict.recipeIngredient), instructions = str(rec_dict.recipeInstructions))
        #new_recipe = RecDB(name = rec_dict.name, url = recipe_url, image = str(type(rec_dict.image)))
        try:
            db.session.add(new_recipe)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding the recipe'
    else:
        return redirect('/')
    







if __name__== "__main__":
    app.run(debug=True)