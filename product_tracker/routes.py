from flask import render_template, url_for, redirect, current_app, jsonify, flash
from product_tracker import app, mysql
from product_tracker.forms import AddProductForm
import secrets, os

# Endpoint for getting products, either by category or all of them
@app.route('/products')
@app.route('/products/<category>')
def products(category=None):
    _, cursor = create_db_connection()
    if category is None:
        cursor.execute("SELECT * FROM Product")
    else:
        try:
            cursor.execute("SELECT * "
                           "FROM Product pdt "
                           "INNER JOIN Category cat ON pdt.CategoryId = cat.Id "
                           "WHERE cat.Name = %s", (category))
        except BaseException as error:
            print(error)
            cursor.close()
            return render_template('error.html')
    products = cursor.fetchall()
    cursor.close()

    return render_template('products.html', products=products, category=category)

# Endpoint for deleting a product with an Id
@app.route('/delete-product/<id>')
def delete_product(id):
    connection, cursor = create_db_connection()
    try:
        cursor.execute("DELETE "
                       "FROM Product "
                       "WHERE Id = %s", (int(id)))
    except BaseException as error:
        print(error)
        cursor.close()
        return render_template('error.html')
    connection.commit()
    cursor.close()
    flash('Product deleted!', 'danger')
    return redirect(url_for('products'))

# Endpoint for adding a product
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    connection, cursor = create_db_connection()

    categories = get_dropdown_categories(cursor)
    form = AddProductForm()
    form.category.choices = categories
    if form.validate_on_submit():
        file_name = save_image(form.image.data)
        try:
            cursor.execute("INSERT INTO "
                           "Product (Name, Description, Price, CategoryId, Image) "
                           "VALUES (%s, %s, %s, %s, %s)", 
                           (form.product_name.data, form.product_description.data, 
                           form.price.data, form.category.data, file_name))
        except BaseException as error:
            print(error)
            cursor.close()
            return render_template('error.html')
        connection.commit()
        cursor.close()
        flash('Product added!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html', form=form)

# Endpoint for getting the analytics
@app.route('/analytics')
def analytics():
    _, cursor = create_db_connection()

    # Get sales of each category
    categories_labels, categories_data = get_category_sales(cursor)
    default_category = 'fruits'

    return render_template('analytics.html',
                            categories_labels=categories_labels, 
                            categories_data=categories_data,
                            default_category=default_category)

# Endpoint for getting the sales of all products in a given category
@app.route('/product-sales/<category>')
def product_sales(category):
    _, cursor = create_db_connection()

    # Get sales of each prodcut in a given category
    products_labels, products_data = get_product_sales(cursor, category)

    return jsonify(products_labels=products_labels, products_data=products_data)

# Endpoint for getting the prices data for a given product (to be used in a chart)
@app.route('/comparisson-search/<product>')
def comparisson_search(product):
    _, cursor = create_db_connection()

    # Get sales of a product across its different prices
    prices_labels, prices_data = get_product_prices_sales(cursor, product)
    return jsonify(prices_labels=prices_labels, prices_data=prices_data)

# Helper method to create the connection and cursor for the database
def create_db_connection():
    connection = mysql.connect()
    cursor = connection.cursor()
    return connection, cursor

# Helper method for storing the image in the static folder of the project
def save_image(image):
    random_hex = secrets.token_hex(8)
    _, extension = os.path.splitext(image.filename)
    file_name = random_hex + extension
    image_path = os.path.join(current_app.root_path, 'static/product_images', file_name)
    image.save(image_path)

    return file_name

# Helper method for getting the total sales of a product across its different prices
def get_product_prices_sales(cursor, product):
    cursor.execute("SELECT pch.Price AS Price, "
                   "TRUNCATE(SUM(pch.Price*pch.Quantity), 2) AS Sales "
                   "FROM Product pdt "
                   "INNER JOIN Purchase pch ON pdt.Id = pch.ProductId "
                   "WHERE pdt.Name = %s "
                   "GROUP BY pch.Price", (product))
    results = cursor.fetchall()
    # Create two arrays for the chart, one for the lables (product prices) and one for the
    # chart's data (product sales)
    prices_labels = []
    prices_data = []
    for result in results:
        prices_labels.append(result['Price'])
        prices_data.append(result['Sales'])

    return prices_labels, prices_data

# Helper method for getting the total sales for each product in a given category
def get_product_sales(cursor, category):
    cursor.execute("SELECT pdt.Name AS Product, "
                   "TRUNCATE(SUM(pch.Price*pch.Quantity), 2) AS Sales "
                   "FROM Category cat "
                   "INNER JOIN Product pdt ON cat.Id = pdt.CategoryId "
                   "INNER JOIN Purchase pch ON pdt.Id = pch.ProductId "
                   "WHERE cat.Name = %s"
                   "GROUP BY pch.ProductId", (category))
    results = cursor.fetchall()
    # Create two arrays for the chart, one for the lables (product names) and one for the
    # chart's data (product sales)
    products_labels = []
    products_data = []
    for result in results:
        products_labels.append(result['Product'])
        products_data.append(result['Sales'])
    
    return products_labels, products_data

# Helper method for getting the total sales for each category
def get_category_sales(cursor):
    cursor.execute("SELECT cat.Name AS Category, "
                   "TRUNCATE(SUM(pch.Price*pch.Quantity), 2) AS Sales "
                   "FROM Category cat "
                   "INNER JOIN Product pdt ON cat.Id = pdt.CategoryId "
                   "INNER JOIN Purchase pch ON pdt.Id = pch.ProductId "
                   "GROUP BY cat.Id")
    results = cursor.fetchall()
    # Create two arrays for the chart, one for the lables (category names) and one for the
    # chart's data (category sales)
    categories_labels = []
    categories_data = []
    for result in results:
        categories_labels.append(result['Category'])
        categories_data.append(result['Sales'])
    
    return categories_labels, categories_data

# Helper method for getting the categories in the right format for a dropdown menu
def get_dropdown_categories(cursor):
    results = get_categories(cursor)
    # The query result is returned as an array of dicts, need to convert it to an array
    # tuples for the dropdown menu
    categories = []
    for result in results:
        categories.append((result['Id'], result['Name'].capitalize()))
    return categories

# Helper method for getting the available categories from the DB
def get_categories(cursor):
    cursor.execute("SELECT * FROM Category")
    return cursor.fetchall()

