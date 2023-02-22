from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
from flask_wtf.csrf import CSRFProtect
import os
from flask_mongoengine import MongoEngine
import googlemaps

app = Flask('CMF Delivery API', static_folder='static')
csrf = CSRFProtect(app)

# If RUNNING_IN_PRODUCTION is defined as an environment variable, then we're running on Azure
if not 'RUNNING_IN_PRODUCTION' in os.environ:
   # Local development, where we'll use environment variables.
   print("Loading config.development and environment variables from .env file.")
   app.config.from_object('azureproject.development')
else:
   # Production, we don't load environment variables from .env file but add them as environment variables in Azure.
   print("Loading config.production.")
   app.config.from_object('azureproject.production')

gmaps = googlemaps.Client(key=app.config.get('GOOGLEMAPS_APIKEY'))

app.config['MONGODB_SETTINGS'] = {
    'host': app.config.get('MONGO_URI'),
    'connect': False,
}

mgdb = MongoEngine(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/",methods=['GET'])
def home():
    return jsonify({"name": app.name , "version":app.config.get('API_VERSION')})

import routes.pedido

"""
@app.route('/add', methods=['POST'])
@csrf.exempt
def add_restaurant():
    from models import Restaurant
    try:
        name = request.values.get('restaurant_name')
        street_address = request.values.get('street_address')
        description = request.values.get('description')
        if (name == "" or description == "" ):
            raise RequestException()
    except (KeyError, RequestException):
        # Redisplay the restaurant entry form.
        return render_template('create_restaurant.html', 
            message='Restaurant not added. Include at least a restaurant name and description.')
    else:
        restaurant = Restaurant()
        restaurant.name = name
        restaurant.street_address = street_address
        restaurant.description = description
        db.session.add(restaurant)
        db.session.commit()

        return redirect(url_for('details', id=restaurant.id))
"""
"""
@app.context_processor
def utility_processor():
    def star_rating(id):
        from models import Review
        reviews = Review.query.where(Review.restaurant==id)

        ratings = []
        review_count = 0;        
        for review in reviews:
            ratings += [review.rating]
            review_count += 1

        avg_rating = round(sum(ratings)/len(ratings), 2) if ratings else 0
        stars_percent = round((avg_rating / 5.0) * 100) if review_count > 0 else 0
        return {'avg_rating': avg_rating, 'review_count': review_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)
"""


if __name__ == '__main__':
   app.run()
