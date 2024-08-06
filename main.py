from flask import Flask, request, jsonify
from flask import json
from flask_pymongo import PyMongo
from flask_cors import CORS
from pymongo import TEXT, MongoClient
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://127.0.0.1:27017/pspi"
CORS(app)
mongo = PyMongo(app)
mongo.db.products.create_index([("name", TEXT)])


@app.route("/search", methods=["GET"])
def search():
    # BEGIN CODE HERE

    name = request.args.get('name', '')

    products = mongo.db.products.find({"name": {"$regex": name, "$options": "i"}})

    # descending order
    sorted_products = sorted(products, key=lambda p: p['price'], reverse=True)

    # μετατροπη σε φορματ json που θελουμε
    result = [
        {
            "id": str(product["_id"]),
            "name": product["name"],
            "production_year": product["production_year"],
            "price": product["price"],
            "color": product["color"],
            "size": product["size"],
        }
        for product in sorted_products
    ]

    return jsonify(result)


# END CODE HERE


@app.route("/add-product", methods=["POST"])
def add_product():
    # BEGIN CODE HERE

    data = request.get_json()
    # print("Data:", data)

    # παιρνουμε product info
    name = data.get("name")
    production_year = data.get("production_year")
    price = data.get("price")
    color = data.get("color")
    size = data.get("size")

    # ελεγχουμε αν το προιον υπαρχει ηδη
    existing_product = mongo.db.products.find_one({"name": name})

    if existing_product:  # αν υπαρχει update, else add
        mongo.db.products.update_one(
            {"name": name},
            {
                "$set": {
                    "production_year": production_year,
                    "price": price,
                    "color": color,
                    "size": size,
                }
            },
        )
        return jsonify({"message": "Product updated successfully"})
    else:
        mongo.db.products.insert_one(
            {
                "name": name,
                "production_year": production_year,
                "price": price,
                "color": color,
                "size": size,
            }
        )
        return jsonify({"message": "Product added successfully"})

    # END CODE HERE


@app.route("/crawler", methods=["GET"])
def crawler():
    # BEGIN CODE HERE

    semester = request.args.get("semester", type=int)
    if semester is None:
        return jsonify({"error": "semester required"}), 400

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    # browser = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver", options=options)
    browser = webdriver.Chrome(options=options)

    browser.get('https://qa.auth.gr/el/x/studyguide/600000438/current')

    # βρισκουμε το συγκεκριμενο table
    semester_table = browser.find_element(By.ID, f"exam{semester}")

    # με εξεταση του πηγαιου κωδικα των tables, μπορουμε να διαπιστωσουμε πως στοιχεια οπως το tr και το td.title
    # μας βοηθουν να βρουμε συγκεκριμενα τα στοιχεια που θελουμε.
    course_names = []
    table_rows = semester_table.find_elements(By.CSS_SELECTOR, "tr")
    for row in table_rows:
        title_elements = row.find_elements(By.CSS_SELECTOR, "td.title")
        if title_elements:
            course_names.append(title_elements[0].text)

    browser.quit()

    return str(course_names), 200, {"Content-Type": "text/plain; charset=utf-8"}


# END CODE HERE


'''
---COMMENTS ΓΙΑ ΤΟ FILTERING---
Αφού πάρει το input product σχηματίζει ενα vector αυτού του προϊόντος,
με βάση τα χαρακτηριστικά "production_year", "price", "color" και "size".
Αυτό το vector κανονικοποιείται και "περνάει" one-hot encoding για τα κατηγορικά χαρακτηριστικά "color" και "size".

Για το "production_year", η τιμή κανονικοποιείται αφαιρώντας το 2000 και διαιρώντας με το 30.
Αυτό υποθέτει ότι το εύρος του "production_year" είναι περίπου μεταξύ 2000 και 2030.
Αυτή η κανονικοποίηση βοηθάει στο να φέρει το χαρακτηριστικό σε μικρότερο εύρος (μεταξύ 0 και 1), 
κανοντας έτσι ευκολότερη τη σύγκρισή του με άλλα χαρακτηριστικά.

Παρομοίως, το "price" κανονικοποιείται διαιρώντας με το 200,
γεγονός που υποθέτει ότι η τιμή των προϊόντων είναι περίπου μικρότερη ή γύρω στο 200 (επιλέχθηκε τυχαία, λειτουργεί καλά με αρκετά παραδειγματά)

Το "color" και το "size" είναι κατηγορικά χαρακτηριστικά. 
Κωδικοποιούνται χρησιμοποιώντας one-hot encoding, το οποίο μετατρέπει αυτά τα κατηγορικά χαρακτηριστικά σε δυαδικά (0 ή 1).
Για κάθε πιθανή τιμή του κατηγορικού χαρακτηριστικού, προστίθεται ένα νέο δυαδικό χαρακτηριστικό στο vector.
'''


@app.route("/content-based-filtering", methods=["POST"])
def content_based_filtering():
    # BEGIN CODE HERE

    input_product = request.get_json()

    product_info = [(input_product["production_year"] - 2000) / 30,
                    input_product["price"] / 200]  # κανονικοποίηση του "production_year" και του "price"

    for i in range(1, 4):
        if input_product["color"] == i:
            product_info.append(1)
        else:
            product_info.append(0)

    for i in range(1, 5):
        if input_product["size"] == i:
            product_info.append(1)
        else:
            product_info.append(0)

    input_vector = np.array(product_info)

    # παιρνουμε ολα τα προιοντα απο το database
    products = mongo.db.products.find({})

    similar_products = []
    similarity_threshold = 0.7

    for product in products:

        product_info = [(product["production_year"] - 2000) / 30, product[
            "price"] / 200]  # κανονικοποίηση του "production_year" και του "price" των products απο το database

        for i in range(1, 4):
            if product["color"] == i:
                product_info.append(1)
            else:
                product_info.append(0)

        for i in range(1, 5):
            if product["size"] == i:
                product_info.append(1)
            else:
                product_info.append(0)

        product_vector = np.array(product_info)

        # υπολογιζουμε το cosine similarity μεταξυ του input product and του τρεχοντος product
        dot_product = np.dot(input_vector, product_vector)
        norm_a = np.linalg.norm(input_vector)
        norm_b = np.linalg.norm(product_vector)
        similarity = dot_product / (norm_a * norm_b)

        print(f"Product: {product['name']}, Similarity: {similarity}")

        if similarity > similarity_threshold:
            similar_products.append(product["name"])

    return jsonify(similar_products)

    # END CODE HERE


if __name__ == '__main__':
    app.run(debug=True)
