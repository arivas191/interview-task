from flask import Flask
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
import os

app = Flask(__name__)

# Configure the application's secret key
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

# Configure the database connection to MySQL
mysql = MySQL(cursorclass=DictCursor)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'product_tracker'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

from product_tracker import routes