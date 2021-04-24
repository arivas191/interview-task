from flask import render_template, url_for, flash, redirect, request, session
from product_tracker import app, mysql
from product_tracker.forms import AddProductForm

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
        try:
            cursor.execute("INSERT INTO "
                           "Product (Name, Description, Price, CategoryId) "
                           "VALUES (%s, %s, %s, %s)", 
                           (form.product_name.data, form.product_description.data, 
                           form.price.data, form.category.data))
        except BaseException as error:
            print(error)
            cursor.close()
            return render_template('error.html')
        connection.commit()
        cursor.close()
        return redirect(url_for('products'))
    return render_template('add_product.html', form=form)

# Endpoint for getting the analytics
def analytics():
    
#Helper method for getting the available categories from the DB
def get_categories(cursor):
    cursor.execute("SELECT * FROM Category")
    return cursor.fetchall()

# Helper method for creating a connection and subsequently the cursor
def create_cursor():
    connection = mysql.connect()
    return connection.cursor()

