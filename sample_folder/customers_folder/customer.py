from flask import Flask, Blueprint, render_template, request, flash, session, redirect, url_for
import mysql.connector
import base64
from flask_bcrypt import Bcrypt

customer = Blueprint('customer', __name__, template_folder="template") 
bcrypt = Bcrypt()


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

@customer.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[4], password):
            session["user"] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for("customer.index"))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template("customerlogin.html")

@customer.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("customer.index"))

@customer.route('/SignUp', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        if not name or not email or not address or not password or not confirm_password:
            return redirect(url_for('customer.signup'))

        if password != confirm_password:
            return redirect(url_for('customer.signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('customer.signup'))

        cursor.execute("INSERT INTO users (name, email, address, password) VALUES (%s, %s, %s, %s)", 
        (name, email, address, hashed_password))
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
    cursor.execute("SELECT id, item_name, price, quantity, image FROM test_items")
    items = cursor.fetchall()
    connection.close()

    formatted_items = []
    for id, name, price, qty, img in items:
        if isinstance(img, bytes):
            img_base64 = base64.b64encode(img).decode('utf-8')
        else:
            img_base64 = None 

        formatted_items.append((id, name, price, qty, img_base64))

    return render_template('Menu.html', items=formatted_items)



@customer.route('/Orders')
def orders():
    if 'user' not in session:
        return redirect(url_for('customer.login'))  # Redirect to Login
    return render_template('orders.html')