from flask import Flask, Blueprint, render_template, request, flash, session, redirect, url_for, current_app
import mysql.connector
import base64
import re
from flask_mail import Message
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

    return render_template('index.html', items=formatted_items)

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
            
            return redirect(url_for("customer.index"))

        flash("Invalid credentials.", "danger")

    return render_template("customerlogin.html")

@customer.route("/logout")
def logout():
    session.pop("user", None)
  #  flash("Logged out successfully!", "success")
    return redirect(url_for("customer.index"))

@customer.route('/SignUp', methods=['GET', 'POST'])
def signup():
    errors = {}  # Store individual field errors

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        # Validate name
        if not name:
            errors['name'] = "Name is required."

        # Validate email
        if not email:
            errors['email'] = "Email is required."
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors['email'] = "Invalid email format."

        # Validate contact
        if not contact:
            errors['contact'] = "Contact number is required."
        elif not contact.isdigit() or len(contact) != 11:
            errors['contact'] = "Contact number must be 11 digits."
        else:
            # Check if contact number is already registered
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customer WHERE contact = %s", (contact,))
            existing_contact = cursor.fetchone()
            cursor.close()
            conn.close()

            if existing_contact:
                errors['contact'] = "Contact number already registered. Please use a different one."


        # Validate address
        if not address:
            errors['address'] = "Address is required."

        # Validate password
        if not password:
            errors['password'] = "Password is required."
        elif len(password) < 8:
            errors['password'] = "Password must be at least 8 characters."

        # Validate confirm password
        if not confirm_password:
            errors['confirm_password'] = "Confirm password is required."
        elif password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        # Check if email already exists
        if not errors.get('email'):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            cursor.close()
            conn.close()

            if existing_user:
                errors['email'] = "Email already registered. Please log in."

        # If there are errors, re-render form with errors
        if errors:
            return render_template("customersignup.html", errors=errors)

        # Insert user if no errors
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customer (name, email, contact, address, password) VALUES (%s, %s, %s, %s, %s)",(name, email, contact, address, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Sign-up successful! Please log in.", "success")
        return redirect(url_for('customer.login'))

    return render_template("customersignup.html", errors={})

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

@customer.route('/verify-account')
def verify():
    try:
        mail = current_app.extensions.get('mail') 

        if not mail:
            return "ERROR: Mail extension not initialized!"

        message = Message(
            subject="Holabels",
            recipients=["@gmail.com"],
            sender=current_app.config['MAIL_USERNAME'] 
        )
        message.body = "HELLLOO"

        mail.send(message)
        return "MESSAGE SENT SUCCESSFULLY"
    except Exception as e:
        return f"FAILED TO SEND MESSAGE: {str(e)}"