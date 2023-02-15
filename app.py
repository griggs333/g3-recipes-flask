from asyncio import new_event_loop
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import validators, StringField, IntegerField, DateField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired
from dataclasses import dataclass
import requests as req
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import isodate
from loguru import logger

import gunicorn_conf
import scrape
import format
import dbquery



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



class RecipeForm(FlaskForm):
    name = StringField('Recipe Name', [validators.Length(min=4, max=100)])
    url = StringField('Recipe URL', [validators.Length(min=4, max=100)])
    headline = StringField('Recipe Headline', [validators.Length(min=4, max=100)])
    author_name = StringField('Author Name', [validators.Length(min=4, max=100)])
    author_url = StringField('Author URL', [validators.Length(min=4, max=100)])
    description = TextAreaField('Description', [validators.Length(min=4, max=100)])
    image = StringField('Image URL', [validators.Length(min=4, max=100)])
    image_description = TextAreaField('Image Description', [validators.Length(min=0, max=100)])
    datePublished = DateField('Date Published')
    dateModified = DateField('Date Modified')
    publisher_name = StringField('Source Name', [validators.Length(min=4, max=100)])
    publisher_url = StringField('Source URL', [validators.Length(min=4, max=100)])
    keywords = StringField('keywords', [validators.Length(min=4, max=100)])
    cookTimeHr = IntegerField('Cook Time Hours', [validators.Length(min=0, max=100)])
    cookTimeMin = IntegerField('Cook Time Minutes', [validators.Length(min=0, max=60)])
    prepTimeHr = IntegerField('Prep Time Hours', [validators.Length(min=0, max=100)])
    prepTimeMin = IntegerField('Prep Time Minutes', [validators.Length(min=0, max=60)])
    totalTimeHr = IntegerField('Total Time Hours', [validators.Length(min=0, max=100)])
    totalTimeMin = IntegerField('Total Time Minutes', [validators.Length(min=0, max=60)])
    recYield = StringField('Yield', [validators.Length(min=4, max=100)])
    recServings = StringField('Yield', [validators.Length(min=4, max=100)])
    rating = StringField('Site Rating', [validators.Length(min=4, max=100)])
    ingredients = TextAreaField('Ingredients', [validators.Length(min=4, max=100)])
    instructions = TextAreaField('Instructions', [validators.Length(min=4, max=100)])
    category = StringField('Category', choices=['Appetizer', 'Main', 'Sides', 'Dessert', 'Snack', 'Condiment', 'Dip', 'Dressing', 'Spice Mix', 'Marinade', 'Sauce'])
    cuisine = StringField('Cuisine', [validators.Length(min=4, max=50)])
    notes = TextAreaField('Notes', [validators.Length(min=4, max=500)])
    custom = StringField('Custom', [validators.Length(min=4, max=100)])



class RecDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=True)
    headline = db.Column(db.String(100), nullable=True)
    author_name = db.Column(db.String(50), nullable=True)
    author_url = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    datePublished = db.Column(db.Date, nullable=True)
    dateModified = db.Column(db.Date, nullable=True)
    publisher_name = db.Column(db.String(50), nullable=True)
    publisher_url = db.Column(db.String, nullable=True)
    keywords = db.Column(db.String(200), nullable=True)
    cookTime = db.Column(db.String(30), nullable=True)
    prepTime = db.Column(db.String(30), nullable=True)
    totalTime = db.Column(db.String(30), nullable=True)
    recYield = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.String(4), nullable=True)
    ingredients = db.Column(db.String, nullable=True)
    instructions = db.Column(db.String, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    cuisine = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.String, nullable=True)
    custom = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<Recipe %r>' % self.id

with app.app_context():
    db.create_all()

@app.route('/', methods={'POST', 'GET'} )
def index():
    return render_template('index.html')

@app.route('/main', methods={'POST', 'GET'} )
def main_table():
    author_filter = request.args.get('author', default='None', type=str)
    source_filter = request.args.get('source', default='None', type=str)
    cuisine_filter = request.args.get('cuisine', default='None', type=str)

    if author_filter != 'None':
        cookbook = RecDB.query.filter_by(author_name=author_filter).all()
    elif source_filter != 'None':
        cookbook = RecDB.query.filter_by(publisher_name=source_filter).all()
    elif cuisine_filter != 'None':
        cookbook = RecDB.query.filter_by(cuisine=cuisine_filter).all()
    else:
        cookbook = RecDB.query.order_by(RecDB.id).all()

    a_list = dbquery.author_filter_list(cookbook)
    s_list = dbquery.source_filter_list(cookbook)
    cu_list = dbquery.cuisine_filter_list(cookbook)



    return render_template('main_table.html', cookbook=cookbook, authors_list=a_list, sources_list=s_list, cuisines_list=cu_list)

@app.route('/recipe_view/<int:id>')
def recipe_view(id):
    cookbook = RecDB.query.order_by(RecDB.id).all()
    recipe_to_view = RecDB.query.get_or_404(id)
    ingredients = eval(str(recipe_to_view.ingredients),{})
    instructions = eval(str(recipe_to_view.instructions),{})
    # publisher = eval(str(recipe_to_view.publisher),{})
    # author = eval(str(recipe_to_view.author),{})

    image = eval(str(recipe_to_view.image),{})
    if image:
        if isinstance(image, list):
            if isinstance(image[-1], dict):
                image = image[-1]
            elif isinstance(image[-1], str):
                image = {'url': image[0]}
        elif isinstance(image, dict):
            image = image
        else:
            image = None


    if recipe_to_view.recYield[0] == '[':
        recYield = eval(recipe_to_view.recYield, {})
    else:
        recYield = recipe_to_view.recYield

    # if isinstance(instructions, list):
    #     instructions = instructions[0]

    return render_template('nav_test.html', recipe=recipe_to_view, cookbook = cookbook, image=image, ingredients = ingredients, instructions = instructions, recYield=recYield)


@app.route('/delete/<int:id>')
def delete(id):
    recipe_to_delete = RecDB.query.get_or_404(id)

    try:
        db.session.delete(recipe_to_delete)
        db.session.commit()
        return redirect('/main')
    except:
            return 'Problem deleting'

# @app.route('/administration', methods={'POST', 'GET'} )
# def administration():
#
#     return render_template('administration.html')

@app.route('/update/<string:url>', methods = ['POST', 'GET'])
def update(url):
    if request.method == "POST":
        recipe_url = request.form['url']
        rec_dict = scrape.rec_json_dict(recipe_url)

        new_recipe = RecDB(
            name=str(rec_dict.name),
            url=str(recipe_url),
            headline=str(rec_dict.headline),
            author_name=str(rec_dict.author['name']),
            author_url=str(rec_dict.author['url']),
            description=str(rec_dict.description),
            image=str(rec_dict.image),
            datePublished=rec_dict.datePublished,
            dateModified=rec_dict.dateModified,
            publisher_name = str(rec_dict.publisherName),
            publisher_url=str(rec_dict.publisherUrl),
            keywords=str(rec_dict.keywords),
            cookTime=str(rec_dict.cookTime),
            prepTime=str(rec_dict.prepTime),
            totalTime=str(rec_dict.totalTime),
            recYield= str(rec_dict.recipeYield),
            rating= str(rec_dict.rating),
            ingredients=str(rec_dict.recipeIngredient),
            instructions=str(rec_dict.recipeInstructions),
            category= str(rec_dict.recipeCategory),
            cuisine=str(rec_dict.recipeCuisine),
            notes = str(''),
            custom = str('')
        )

        try:
            db.session.add(new_recipe)
            db.session.commit()
            return redirect('/main')
        except:
            return 'There was an issue adding the recipe'
    else:
        return redirect('/main')
    
# @app.route('/add_recipe/<string:url>', methods = ['POST', 'GET'])
# def add_recipe(url):
#     if request.method == "POST":
#         recipe_url = request.form['url']
#         #recipe_form_id = request.form['form_id']
#         rec_dict = scrape.rec_json_dict(recipe_url)
#
#         new_recipe = RecDB(
#             name=str(rec_dict.name),
#             url=str(recipe_url),
#             headline=str(rec_dict.headline),
#             author=str(rec_dict.author),
#             description=str(rec_dict.description),
#             image=str(type(rec_dict.image)),
#             datePublished= str(rec_dict.datePublished),
#             dateModified=str(rec_dict.dateModified),
#             publisher = str(rec_dict.publisher),
#             keywords=str(rec_dict.keywords),
#             cookTime=str(rec_dict.cookTime),
#             prepTime=str(rec_dict.prepTime),
#             totalTime=str(rec_dict.totalTime),
#             recYield= str(rec_dict.recipeYield),
#             rating= str(rec_dict.rating),
#             ingredients=str(rec_dict.recipeIngredient),
#             instructions=str(rec_dict.recipeInstructions),
#             category= str(rec_dict.recipeCategory),
#             cuisine=str(rec_dict.recipeCuisine),
#             notes = str('')
#         )
#
#         ingredients = eval(str(new_recipe.ingredients),{})
#         instructions = eval(str(new_recipe.instructions),{})
#         publisher = eval(str(new_recipe.publisher),{})
#
#         return render_template('add_recipe.html', recipe=new_recipe, recipetype= type(new_recipe), publisher=publisher, ingredients=ingredients, instructions=instructions)
#
#     else:
#         return redirect('/administration/')


# @app.route('/add_recipe/<string:url>', methods = ['POST', 'GET'])
# def add_recipe(url):
#     if request.method == "POST":
#         recipe_url = request.form['url']
#         #recipe_form_id = request.form['form_id']
#         rec_dict = scrape.rec_json_dict(recipe_url)
#
#         new_recipe = RecDB(
#             name=str(rec_dict.name),
#             url=str(recipe_url),
#             headline=str(rec_dict.headline),
#             author_name=str(rec_dict.author['name']),
#             author_url=str(rec_dict.author['url']),
#             description=str(rec_dict.description),
#             image=str(rec_dict.image),
#             datePublished=rec_dict.datePublished,
#             dateModified=rec_dict.dateModified,
#             publisher_name = str(rec_dict.publisherName),
#             publisher_url=str(rec_dict.publisherUrl),
#             keywords=str(rec_dict.keywords),
#             cookTime=str(rec_dict.cookTime),
#             prepTime=str(rec_dict.prepTime),
#             totalTime=str(rec_dict.totalTime),
#             recYield= str(rec_dict.recipeYield),
#             rating= str(rec_dict.rating),
#             ingredients=str(rec_dict.recipeIngredient),
#             instructions=str(rec_dict.recipeInstructions),
#             category= str(rec_dict.recipeCategory),
#             cuisine=str(rec_dict.recipeCuisine),
#             notes = str(''),
#             custom = str('')
#         )
#
#         ingredients = eval(str(new_recipe.ingredients),{})
#         instructions = eval(str(new_recipe.instructions),{})
#         # publisher = eval(str(new_recipe.publisher),{})
#
#         return render_template('add_recipe2.html', recipe=new_recipe, recipetype= type(new_recipe), publisher_name=new_recipe.publisher_name, publisher_url=new_recipe.publisher_url, ingredients=ingredients, instructions=instructions)
#
#     else:
#         return redirect('/administration/')

# @app.route('/commit_recipe/<string:recipe>', methods = ['POST', 'GET'])
# def commit_recipe(recipe):
#     form = RecipeForm(request.POST)
#     if request.method == "POST" and form.validate():
#         recName = form.name.data
#         recUrl = form.url.data
#         recDescription = form.description.data
#         recDatePublished = form.datePublished.data
#         recData = [recName, recUrl, recDescription, recDatePublished]
#
#
#
#         # try:
#         #     db.session.add(new_recipe)
#         #     db.session.commit()
#         #     return redirect('/')
#         # except:
#         #     return 'There was an issue adding the recipe'
#     else:
#         return redirect('/administration')
#
#     print(recData)


# @app.route('/nav_test/<string:rec_id>', methods={'POST', 'GET'} )
# def nav_test(rec_id):
#     if request.method == "POST":
#         id = int(request.form['rec_id'])
#
#     recipe_to_view = RecDB.query.get_or_404(id)
#     ingredients = eval(str(recipe_to_view.ingredients), {})
#     instructions = eval(str(recipe_to_view.instructions), {})
#     publisher = eval(str(recipe_to_view.publisher), {})
#     author = eval(str(recipe_to_view.author), {})
#
#     if recipe_to_view.recYield[0] == '[':
#         recYield = eval(recipe_to_view.recYield, {})
#     else:
#         recYield = recipe_to_view.recYield
#
#     return render_template('nav_test.html', recYield=recYield, recipe=recipe_to_view, author=author, publisher=publisher, ingredients=ingredients, instructions=instructions)


@app.route('/favorites')
def favorites():
    favorites = RecDB.query.filter(RecDB.custom.contains('favorite')).all()
    return render_template('favorites.html', cookbook=favorites)


@app.route('/source_list')
def source_list():
    cookbook = RecDB.query.order_by(RecDB.id).all()
    sources_list = []

    for recipe in cookbook:
        source = [recipe.publisher_name, recipe.publisher_url]
        if source not in sources_list:
            sources_list.append(source)

    return render_template('source_list.html', sources_list=sources_list)

@app.route('/by_source/<string:source>')
def by_source(source):
    by_source = RecDB.query.filter(RecDB.publisher_name.contains(source)).all()

    return render_template('by_source.html', cookbook=by_source)


@app.route('/author_list')
def author_list():
    cookbook = RecDB.query.order_by(RecDB.id).all()

    authors_list = []
    for recipe in cookbook:
        author = [recipe.author_name, recipe.author_url]
        if author not in authors_list:
            authors_list.append(author)

    return render_template('author_list.html', authors_list=authors_list)


@app.route('/by_author/<string:author>')
def by_author(author):
    by_author = RecDB.query.filter(RecDB.author_name.contains(author)).all()

    return render_template('by_author.html', cookbook=by_author)




if __name__== "__main__":
    app.run(host='0.0.0.0', port= gunicorn_conf.PORT, debug=gunicorn_conf.DEBUG_MODE)