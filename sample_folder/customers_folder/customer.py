from flask import Flask, Blueprint, render_template, request, flash, session, redirect, url_for
import mysql.connector
import base64
from flask_bcrypt import Bcrypt

customer = Blueprint('customer', __name__, template_folder="template") 
bcrypt = Bcrypt()


db_config = {
    'host':'localhost',
    'database':'craveon',
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

@customer.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[5], password):
            session["user"] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for("customer.index"))

    #  flash("Invalid credentials. Please try again.", "danger")

    return render_template("customerlogin.html")

@customer.route("/logout")
def logout():
    session.pop("user", None)
  #  flash("Logged out successfully!", "success")
    return redirect(url_for("customer.index"))

@customer.route('/SignUp', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        if not name or not email or not contact or not address or not password or not confirm_password:
            return redirect(url_for('customer.signup'))

        if password != confirm_password:
            return redirect(url_for('customer.signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            #flash("Email already registered. Please log in.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('customer.signup'))

        cursor.execute("INSERT INTO customer (name, email, contact, address, password) VALUES (%s, %s, %s, %s, %s)", 
        (name, email, contact, address, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('customer.login'))

    return render_template("customersignup.html")

@customer.route('/Menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('customer.login'))
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT item_id, item_name, price, image FROM items")
    items = cursor.fetchall()
    connection.close()

    formatted_items = []
    for item_id, name, price, img in items:
        if isinstance(img, bytes):
            img_base64 = base64.b64encode(img).decode('utf-8')
        else:
            img_base64 = None 

        formatted_items.append((item_id, name, price, img_base64))

    return render_template('Menu.html', items=formatted_items)

@customer.route('/Orders', methods=['GET', 'POST'])
def orders():
    if 'user' not in session:
        return redirect(url_for('customer.login')) 

    cart_items = []
    index = 0
    while f'item_name_{index}' in request.form:
        cart_items.append({
            'name': request.form[f'item_name_{index}'],
            'price': float(request.form[f'item_price_{index}']),
            'quantity': int(request.form[f'item_quantity_{index}'])
        })
        index += 1

    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT name, email, contact, address FROM customer")
    users = cursor.fetchall()
    connection.close()

    return render_template('orders.html', cart_items=cart_items, total_amount=total_amount, users=users)

@customer.route('/Account')
def account():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute('SELECT name, email, contact, address FROM customer')
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("account.html", data=data)