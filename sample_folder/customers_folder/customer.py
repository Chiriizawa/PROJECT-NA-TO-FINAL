from flask import Flask, Blueprint, render_template, request
import mysql.connector
import base64

customer = Blueprint('customer', __name__, template_folder="template") 

db_config = {
    'host':'localhost',
    'database':'test',
    'user':'root',
    'password':'',
}

def connect_db():
    return mysql.connector.connect(**db_config)

conn = connect_db()
cursor = conn.cursor()

@customer.app_template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8') if data else ''


@customer.route('/')
def index():
    return render_template("index.html")

@customer.route('/login', methods=['POST'])
def login():
    return render_template("index.html")

@customer.route('/SignUp')
def signup():
    return render_template("customersignup.html")

@customer.route('/Menu')
def menu():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id, item_name, price, quantity, image FROM test_items")
    items = cursor.fetchall()
    connection.close()

    # Ensure `img` is a byte object before encoding
    formatted_items = []
    for id, name, price, qty, img in items:
        if isinstance(img, bytes):  # Check if image is a BLOB
            img_base64 = base64.b64encode(img).decode('utf-8')
        else:
            img_base64 = None  # Use default image if not a valid BLOB

        formatted_items.append((id, name, price, qty, img_base64))

    return render_template('Menu.html', items=formatted_items)

@customer.route('/Orders')
def orders():
    return render_template('orders.html')