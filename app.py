from asyncio import new_event_loop
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
import requests as req
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import isodate
from loguru import logger


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recDB.db'
db = SQLAlchemy(app)

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
    publisher: list  #  list with order [name, url]
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

def format_timedelta(delta: timedelta) -> str:
    """Formats a timedelta duration to %H:%M:%S format"""
    seconds = int(delta.total_seconds())

    secs_in_a_hour = 3600
    secs_in_a_min = 60

    hours, seconds = divmod(seconds, secs_in_a_hour)
    minutes, seconds = divmod(seconds, secs_in_a_min)

    if hours >= 1:
        time_fmt = f"{hours} hr {minutes} min"
    else:
        time_fmt = f"{minutes} min"

    return time_fmt


def rec_json_dict(url):
    page = req.get(url)
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

    if 'author' in site_dict.keys():
        if isinstance(site_dict['author'], list):
            site_dict['author'] = site_dict.get('author')[0]

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

    iso_dates = ['dateModified', 'datePublished']
    iso_times = ['prepTime', 'cookTime', 'totalTime']
    for items in iso_dates:
        if isinstance(site_dict.get(items), str):
            site_dict[items] = isodate.parse_date(site_dict.get(items))
        else:
            site_dict[items] = None

    for items in iso_times:
        if isinstance(site_dict.get(items), str):
            site_dict[items] = format_timedelta(isodate.parse_duration(site_dict.get(items)))
        else:
            site_dict[items] = None

    # site_dict['recipeYield'] = eval(site_dict['recipeYield'])

    # if 'recipeYield' in site_dict.keys():
    #     if isinstance(site_dict['recipeYield'], list):
    #         site_dict['recipeYield'] = f"Serves: {site_dict['recipeYield'][0]} &emsp; Makes: {site_dict['recipeYield'][1]}"


    rec_dict = Recipe(name= rec_name, url= rec_url, headline= site_dict.get('headline'), author= site_dict.get('author'), image= site_dict.get('image'), datePublished= site_dict.get('datePublished'), dateModified= site_dict.get('dateModified'), publisher= [rec_publisher_name, rec_publisher_url], keywords= site_dict.get('keywords'), cookTime= site_dict.get('cookTime'), prepTime= site_dict.get('prepTime'), totalTime= site_dict.get('totalTime'), recipeIngredient= site_dict.get('recipeIngredient'), recipeInstructions= site_dict.get('recipeInstructions'), rating= rec_rating, recipeYield= site_dict.get('recipeYield'), description= site_dict.get('description'), recipeCategory= site_dict.get('recipeCategory'), recipeCuisine= site_dict.get('recipeCuisine'))
    #print(rec_dict.dateModified, rec_dict.datePublished, rec_dict.prepTime, rec_dict.cookTime, rec_dict.totalTime)

    return rec_dict


class RecDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=True)
    headline = db.Column(db.String(100), nullable=True)
    author = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    datePublished = db.Column(db.Date, nullable=True)
    dateModified = db.Column(db.Date, nullable=True)
    publisher = db.Column(db.String(200), nullable=True)
    keywords = db.Column(db.String(200), nullable=True)
    cookTime = db.Column(db.String(30), nullable=True)
    prepTime = db.Column(db.String(30), nullable=True)
    totalTime = db.Column(db.String(30), nullable=True)
    recYield = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.String(10), nullable=True)
    ingredients = db.Column(db.String, nullable=True)
    instructions = db.Column(db.String, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    cuisine = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.String, nullable=True)
    custom = db.Column(db.String, nullable=True)

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
    ingredients = eval(str(recipe_to_view.ingredients),{})
    instructions = eval(str(recipe_to_view.instructions),{})
    publisher = eval(str(recipe_to_view.publisher),{})
    author = eval(str(recipe_to_view.author),{})

    print(recipe_to_view.recYield, type(recipe_to_view.recYield))

    if recipe_to_view.recYield[0] == '[':
        recYield = eval(recipe_to_view.recYield, {})
    else:
        recYield = recipe_to_view.recYield

    return render_template('view_recipe.html', recipe=recipe_to_view, cookbook = cookbook, author=author, ingredients = ingredients, instructions = instructions, publisher=publisher, recYield=recYield)


@app.route('/delete/<int:id>')
def delete(id):
    recipe_to_delete = RecDB.query.get_or_404(id)

    try:
        db.session.delete(recipe_to_delete)
        db.session.commit()
        return redirect('/')
    except:
            return 'Problem deleting'

@app.route('/administration', methods={'POST', 'GET'} )
def administration():

    return render_template('administration.html')

@app.route('/update/<string:url>', methods = ['POST', 'GET'])
def update(url):
    if request.method == "POST":
        recipe_url = request.form['url']
        rec_dict = rec_json_dict(recipe_url)

        new_recipe = RecDB(
            name=str(rec_dict.name),
            url=str(recipe_url),
            headline=str(rec_dict.headline),
            author=str(rec_dict.author),
            description=str(rec_dict.description),
            image=str(type(rec_dict.image)),
            datePublished=rec_dict.datePublished,
            dateModified=rec_dict.dateModified,
            publisher = str(rec_dict.publisher),
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
            return redirect('/')
        except:
            return 'There was an issue adding the recipe'
    else:
        return redirect('/')
    
@app.route('/add_recipe/<string:url>', methods = ['POST', 'GET'])
def add_recipe(url):
    if request.method == "POST":
        recipe_url = request.form['url']
        #recipe_form_id = request.form['form_id']
        rec_dict = rec_json_dict(recipe_url)

        new_recipe = RecDB(
            name=str(rec_dict.name),
            url=str(recipe_url),
            headline=str(rec_dict.headline),
            author=str(rec_dict.author),
            description=str(rec_dict.description),
            image=str(type(rec_dict.image)),
            datePublished= str(rec_dict.datePublished),
            dateModified=str(rec_dict.dateModified),
            publisher = str(rec_dict.publisher),
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
            notes = str('')
        )

        ingredients = eval(str(new_recipe.ingredients),{})
        instructions = eval(str(new_recipe.instructions),{})
        publisher = eval(str(new_recipe.publisher),{})

        return render_template('add_recipe.html', recipe=new_recipe, recipetype= type(new_recipe), publisher=publisher, ingredients=ingredients, instructions=instructions)

    else:
        return redirect('/administration/')



@app.route('/commit_recipe/<string:recipe>', methods = ['POST', 'GET'])
def commit_recipe(recipe):
    if request.method == "POST":
        new_recipe = eval(request.form['recipe'],{})

        try:
            db.session.add(new_recipe)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding the recipe'
    else:
        return redirect('/')

@app.route('/nav_test/<string:rec_id>', methods={'POST', 'GET'} )
def nav_test(rec_id):
    if request.method == "POST":
        id = int(request.form['rec_id'])

    recipe_to_view = RecDB.query.get_or_404(id)
    ingredients = eval(str(recipe_to_view.ingredients), {})
    instructions = eval(str(recipe_to_view.instructions), {})
    publisher = eval(str(recipe_to_view.publisher), {})
    author = eval(str(recipe_to_view.author), {})

    if recipe_to_view.recYield[0] == '[':
        recYield = eval(recipe_to_view.recYield, {})
    else:
        recYield = recipe_to_view.recYield

    return render_template('nav_test.html', recYield=recYield, recipe=recipe_to_view, author=author, publisher=publisher, ingredients=ingredients, instructions=instructions)


@app.route('/favorites')
def favorites():
    favorites = RecDB.query.filter(RecDB.custom.contains('favorite')).all()
    return render_template('favorites.html', cookbook=favorites)


@app.route('/source_list')
def source_list():
    cookbook = RecDB.query.order_by(RecDB.id).all()
    sources_list = []

    for recipe in cookbook:
        source = eval(recipe.publisher, {})
        if source not in sources_list:
            sources_list.append(source)

    return render_template('source_list.html', sources_list=sources_list)

@app.route('/by_source/<string:source>')
def by_source(source):
    by_source = RecDB.query.filter(RecDB.publisher.contains(source)).all()

    return render_template('by_source.html', cookbook=by_source)


@app.route('/author_list')
def author_list():
    cookbook = RecDB.query.order_by(RecDB.id).all()

    authors_list = []
    for recipe in cookbook:
        author = [eval(recipe.author,{})['name'], eval(recipe.author,{})['url']]
        if author not in authors_list:
            authors_list.append(author)

    return render_template('author_list.html', authors_list=authors_list)


@app.route('/by_author/<string:author>')
def by_author(author):
    by_author = RecDB.query.filter(RecDB.author.contains(author)).all()

    return render_template('by_author.html', cookbook=by_author)




if __name__== "__main__":
    app.run(debug=True)