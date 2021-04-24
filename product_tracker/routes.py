from flask import render_template, url_for, redirect, request, session, json, current_app
from product_tracker import app, mysql
from product_tracker.forms import AddProductForm
import secrets, os

# Endpoint for getting products, either by category or all of them
@app.route('/products')
@app.route('/products/<category>')
def products(category=None):
    connection = mysql.connect()
    cursor = connection.cursor()
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
    connection = mysql.connect()
    cursor = connection.cursor()
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
    return redirect(url_for('products'))

# Endpoint for adding a product
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    connection = mysql.connect()
    cursor = connection.cursor()
    results = get_categories(cursor)
    # The query result is returned as an array of dicts, need to convert it to an array
    # tuples for the dropdown menu
    categories = []
    for result in results:
        categories.append((result['Id'], result['Name'].capitalize()))
    form = AddProductForm()
    form.category.choices = categories
    if form.validate_on_submit():
        file_name = ''
        if form.image.data:
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
        return redirect(url_for('products'))
    return render_template('add_product.html', form=form)

# Helper method for storing the image in the static folder of the project
def save_image(image):
    random_hex = secrets.token_hex(8)
    _, extension = os.path.splitext(image.filename)
    file_name = random_hex + extension
    image_path = os.path.join(current_app.root_path, 'static/product_images', file_name)
    image.save(image_path)

    return file_name

# Endpoint for getting the analytics
@app.route('/analytics')
@app.route('/analytics/<category>')
def analytics(category='fruits'):
    connection = mysql.connect()
    cursor = connection.cursor()
    
    # Get the available categories to display them in a dropdown menu
    categories_results = get_categories(cursor)
    categories = []
    for result in categories_results:
        categories.append(result['Name'])

    labels, data = get_category_sales(cursor, category)
    return render_template('analytics.html', labels=json.dumps(labels), data=json.dumps(data), 
                            categories=categories, current_category=category)

# Helper method for getting the total sales for each product in every category
def get_category_sales(cursor, category):
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
    product_labels = []
    product_data = []
    for result in results:
        product_labels.append(result['Product'])
        product_data.append(result['Sales'])
    
    return product_labels, product_data

#Helper method for getting the available categories from the DB
def get_categories(cursor):
    cursor.execute("SELECT * FROM Category")
    return cursor.fetchall()

# Helper method for creating a connection and subsequently the cursor
def create_cursor():
    connection = mysql.connect()
    return connection.cursor()

