import subprocess
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__) # create a Flask app instance
CORS(app) # Enable CORS to accept cross origin requests
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db' # set up the Flask application to use a SQLite database named database.db
db = SQLAlchemy(app)

class ProductResult(db.Model):
    """ SQLAlchemy model class ProductResult represents a table in a database """
    id = db.Column(db.Integer, primary_key=True) # define primary key
    name = db.Column(db.String(1000)) # to store name of the product(max 1000 characters)   
    img = db.Column(db.String(1000)) # to store image 
    url = db.Column(db.String(1000)) # to store the URL
    price = db.Column(db.Float) # to store the price(Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # stores the creation timestamp
    search_text = db.Column(db.String(255)) # to store search text used to retrieve the product
    source = db.Column(db.String(255)) # stores the source of the product

    def __init__(self, name, img, url, price, search_text, source):
        self.name = name
        self.url = url
        self.img = img
        self.price = price
        self.search_text = search_text
        self.source = source

class TrackedProducts(db.Model):
    """ Represents the TrackedProducts table in the database """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tracked = db.Column(db.Boolean, default=True)

    def __init__(self, name, tracked=True):
        self.name = name
        self.tracked = tracked


@app.route('/results', methods=['POST']) # specify that this route(/results) only accepts POST requests.
def submit_results():
    """ Function that submits result to the database """
    results = request.json.get('data') # get results from data                       
    search_text = request.json.get("search_text") # get search_text from request
    source = request.json.get("source") # get source from request

    # loop over results , create ProductResult class and add to database
    for result in results:
        product_result = ProductResult(
            name=result['name'],
            url=result['url'],
            img=result["img"],
            price=result['price'],
            search_text=search_text,
            source=source
        )
        db.session.add(product_result)

    db.session.commit()
    response = {'message': 'Received data successfully'}
    return jsonify(response), 200

@app.route('/unique_search_texts', methods=['GET'])
def get_unique_search_texts():
    """ function that retrieves a list of unique search texts from a database 
        and return them as a JSON response. """
    unique_search_texts = db.session.query(
        ProductResult.search_text).distinct().all()
    unique_search_texts = [text[0] for text in unique_search_texts]
    return jsonify(unique_search_texts)

@app.route('/results')
def get_product_results():
    """ function to fetch product results from the ProductResult table 
        based on the search text and format them to include a price 
        history for each product """
    search_text = request.args.get('search_text') # Extracts the search_text from the query parameters of the request
    results = ProductResult.query.filter_by(search_text=search_text).order_by(
        ProductResult.created_at.desc()).all() # Orders the results by the 'created_at' timestamp in descending order (most recent first)

    product_dict = {} # for storing formatted product results
    for result in results:
        url = result.url # url is used as a unique identifier
        if url not in product_dict:
            product_dict[url] = {
                'name': result.name,
                'url': result.url,
                "img": result.img,
                "source": result.source,
                "created_at": result.created_at,
                'priceHistory': []
            }
        product_dict[url]['priceHistory'].append({
            'price': result.price,
            'date': result.created_at
        })

    formatted_results = list(product_dict.values())

    return jsonify(formatted_results)

@app.route('/all-results', methods=['GET'])
def get_results():
    """ Function to fetch all product results from the ProductResult table 
        and return them as a JSON response. """
    results = ProductResult.query.all()
    product_results = []
    for result in results:
        product_results.append({
            'name': result.name,
            'url': result.url,
            'price': result.price,
            "img": result.img,
            'date': result.created_at,
            "created_at": result.created_at,
            "search_text": result.search_text,
            "source": result.source
        })

    return jsonify(product_results)

@app.route('/start-scraper', methods=['POST'])
def start_scraper():
    """ Funtion to start a web scraper with a specified URL and search 
        text, running it asynchronously in a separate Python process. """
    url = request.json.get('url')
    search_text = request.json.get('search_text')

    # Run scraper asynchronously in a separate Python process
    command = f"python ./scraper/__init__.py {url} \"{search_text}\" /results"
    subprocess.Popen(command, shell=True)

    response = {'message': 'Scraper started successfully'}
    return jsonify(response), 200

@app.route('/add-tracked-product', methods=['POST'])
def add_tracked_product():
    """ Function to add a new tracked product to the TrackedProducts table
        and return a confirmation message along with the new product's ID."""
    name = request.json.get('name')
    tracked_product = TrackedProducts(name=name)
    db.session.add(tracked_product)
    db.session.commit()

    response = {'message': 'Tracked product added successfully',
                'id': tracked_product.id}
    return jsonify(response), 200

@app.route('/tracked-product/<int:product_id>', methods=['PUT'])
def toggle_tracked_product(product_id):
    """ Function to toggle the tracking status (tracked field) of a 
        product identified by product_id in the TrackedProducts table. """
    tracked_product = TrackedProducts.query.get(product_id)
    if tracked_product is None:
        response = {'message': 'Tracked product not found'}
        return jsonify(response), 404

    tracked_product.tracked = not tracked_product.tracked
    db.session.commit()

    response = {'message': 'Tracked product toggled successfully'}
    return jsonify(response), 200

@app.route('/tracked-products', methods=['GET'])
def get_tracked_products():
    """ Function that gets all the tracked products """
    tracked_products = TrackedProducts.query.all()

    results = []
    for product in tracked_products:
        results.append({
            'id': product.id,
            'name': product.name,
            'created_at': product.created_at,
            'tracked': product.tracked
        })

    return jsonify(results), 200

@app.route("/update-tracked-products", methods=["POST"])
def update_tracked_products():
    """ 
        function that triggers the web scraper for each tracked product 
        in the database and return a response indicating the scraping 
        process has started.
    """
    tracked_products = TrackedProducts.query.all()
    url = "https://amazon.ca"

    product_names = []
    for tracked_product in tracked_products:
        name = tracked_product.name
        if not tracked_product.tracked: # continue if a product is not a tracked product
            continue

        command = f"python ./scraper/__init__.py {url} \"{name}\" /results"
        subprocess.Popen(command, shell=True)
        product_names.append(name)

    response = {'message': 'Scrapers started successfully',
                "products": product_names}
    return jsonify(response), 200
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # creates all database tables defined in the models
    app.run()
