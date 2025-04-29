from flask import Flask, Blueprint, render_template, request, flash, session, redirect, url_for, current_app, jsonify, make_response
import mysql.connector
import base64
import re
import random
from flask_mail import Message
from flask_bcrypt import Bcrypt


customer = Blueprint('customer', __name__, template_folder="template") 

bcrypt = Bcrypt()

def make_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

db_config = {
    'host':'localhost',
    'database':'foodordering',
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
    if 'user' in session:
        return redirect(url_for('customer.index'))  

    email_error = None
    password_error = None
    errors = {}

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Email validation
        if not email:
            errors['email'] = "Email is required."
        else:
            # Regular expression for email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors['email'] = "Invalid email format."
            else:
                # Check if email already exists in the database
                conn = connect_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
                existing_email = cursor.fetchone()
                cursor.close()
                conn.close()

                if not existing_email:
                    errors['email'] = "Email not found. Please check your email or register if you don't have an account."

        # Password validation
        if not password:
            password_error = "Password is required."

        # If there are no errors, proceed with the login process
        if not errors and not password_error:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user['password'], password):
                # Store the user's email in session
                session["user_email"] = user['email']  # Store the logged-in user's email in the session
                session["temp_user_id"] = user['customer_id']
                session["verification_code"] = str(random.randint(100000, 999999))

                if send_verification_email(email, session["verification_code"]):
                    return redirect(url_for("customer.verify"))
                else:
                    flash("Failed to send verification email. Please try again.", "danger")
            else:
                password_error = "Incorrect password. Please try again."

            cursor.close()
            conn.close()

    response = make_response(render_template("customerlogin.html", email_error=errors.get('email'), password_error=password_error))
    return response


def send_verification_email(email, code):
    try:
        mail = current_app.extensions.get('mail')

        if not mail:
            return False

        message = Message(
            subject="Your Verification Code",
            recipients=[email],
            sender=current_app.config['MAIL_USERNAME'],
            body=f"Your verification code is: {code}"
        )

        mail.send(message)
        return True
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {str(e)}")
        return False
    
@customer.route("/Verify-Account", methods=['GET', 'POST'])
def verify():
    if "user" in session:
        return redirect(url_for('customer.index'))
    if "verification_code" not in session or "temp_user_id" not in session:
        return redirect(url_for('customer.login'))

    error_message = None

    if request.method == "POST":
        entered_code = "".join([
            request.form.get("code1", ""), request.form.get("code2", ""),
            request.form.get("code3", ""), request.form.get("code4", ""),
            request.form.get("code5", ""), request.form.get("code6", "")
        ])

        if entered_code == session.get("verification_code"):
            session["user"] = session.pop("temp_user_id") 
            session.pop("verification_code", None)  
            return redirect(url_for("customer.index"))
        else:
            error_message = "Invalid verification code."

    response = make_response(render_template("verify.html", error_message=error_message))
    return response

@customer.route("/logout")
def customerlogout():
    session.pop("user", None)
    return redirect(url_for("customer.index"))

@customer.route('/SignUp', methods=['GET', 'POST'])
def signup():
    errors = {}

    if request.method == 'POST':
        firstname = request.form.get('firstname', '').strip()
        middlename = request.form.get('middlename', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        contact = request.form.get('contact', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm-password', '').strip()

        # Name Validation
        if not firstname:
            errors['firstname'] = "First name is required."
        elif not firstname.isalpha():
            errors['firstname'] = "First name must contain only letters."

        if not middlename and middlename != '':
            errors['middlename'] = "Middle name is required."
        elif middlename and not middlename.isalpha():
            errors['middlename'] = "Middle name must contain only letters."

        if not surname:
            errors['surname'] = "Surname is required."
        elif not surname.isalpha():
            errors['surname'] = "Surname must contain only letters."

        # Email Validation
        if not email:
            errors['email'] = "Email is required."
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors['email'] = "Invalid email format."
            else:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
                existing_email = cursor.fetchone()
                cursor.close()
                conn.close()

                if existing_email:
                    errors['email'] = "Email already registered. Please use a different one."

        # Contact Validation
        if not contact:
            errors['contact'] = "Contact number is required."
        elif not contact.isdigit():
            errors['contact'] = "Contact number must contain only digits."
        elif len(contact) != 10:
            errors['contact'] = "Contact number must be exactly 10 digits."
        else:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customer WHERE contact = %s", (contact,))
            existing_contact = cursor.fetchone()
            cursor.close()
            conn.close()

            if existing_contact:
                errors['contact'] = "Contact number already registered. Please use a different one."

        # Password Validation
        if not password:
            errors['password'] = "Password is required."
        elif len(password) < 8:
            errors['password'] = "Password must be at least 8 characters."

        if not confirm_password:
            errors['confirm_password'] = "Please confirm your password."
        elif password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        if errors:
            return render_template("customersignup.html", errors=errors)

        # Create full name
        full_name = f"{firstname} {middlename} {surname}".strip()  # Strip middle name if empty
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Get address values (region, province, municipality, barangay) from the form
        region = request.form.get('region', '')
        province = request.form.get('province', '')
        municipality = request.form.get('municipality', '')
        barangay = request.form.get('barangay', '')

        # Concatenate address values into one string
        full_address = f"{region}, {province}, {municipality}, {barangay}".strip(", ")

        conn = connect_db()
        cursor = conn.cursor()

        # Insert into 'customer' table (name, address, email, contact, password)
        cursor.execute(
            "INSERT INTO customer (name, email, contact, address, password) VALUES (%s, %s, %s, %s, %s)",
            (full_name, email, contact, full_address, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return render_template("customersignup.html", errors={})

    return render_template("customersignup.html", errors={})

@customer.route('/Forgot-Password', methods=['GET', 'POST'])
def forgot_password():
    if 'user' in session:
        return redirect(url_for('customer.login'))  

    email_error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            email_error = "Email is required."
        else:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user:
                email_error = "Email not found. Please check your email."
            else:
                session["reset_user_id"] = user['customer_id']
                session["reset_verification_code"] = str(random.randint(100000, 999999))

                if send_verification_email(email, session["reset_verification_code"]):
                    return redirect(url_for("customer.verify_reset"))
                else:
                    email_error = "Failed to send verification email. Try again later."

    return render_template("forgotpassword.html", email_error=email_error)


@customer.route('/Verify-Reset', methods=['GET', 'POST'])
def verify_reset():
    if "user" in session:
        return redirect(url_for('customer.login'))

    if "reset_verification_code" not in session or "reset_user_id" not in session:
        return redirect(url_for('customer.forgot_password'))

    error_message = None

    if request.method == "POST":
        entered_code = "".join([
            request.form.get("code1", ""), request.form.get("code2", ""),
            request.form.get("code3", ""), request.form.get("code4", ""),
            request.form.get("code5", ""), request.form.get("code6", "")
        ])

        if entered_code == session.get("reset_verification_code"):
            session.pop("reset_verification_code", None)
            return redirect(url_for("customer.reset_password"))
        else:
            error_message = "Invalid verification code."

    return render_template("verifyreset.html", error_message=error_message)

@customer.route('/Reset-Password', methods=['GET', 'POST'])
def reset_password():
    if "reset_user_id" not in session:
        return redirect(url_for("customer.login"))

    password_error = None

    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            password_error = "Both password fields are required."
        elif new_password != confirm_password:
            password_error = "Passwords do not match."
        elif len(new_password) < 8:
            password_error = "Password must be at least 8 characters long."
        else:
            # Hash the password before saving
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

            # Update password in database
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customer SET password = %s WHERE customer_id = %s",
                (hashed_password, session["reset_user_id"])
            )
            conn.commit()
            cursor.close()
            conn.close()

            # Clear reset session data
            session.pop("reset_user_id", None)

            return redirect(url_for("customer.login"))

    return render_template("resetpassword.html", password_error=password_error)


@customer.route('/Menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('customer.login'))

    connection = connect_db()
    cursor = connection.cursor()

    # Fetch items with category name
    cursor.execute("""
        SELECT i.item_id, i.item_name, i.price, i.image, c.category_name 
        FROM items i
        JOIN category c ON i.category_id = c.category_id
    """)
    items = cursor.fetchall()

    # Fetch categories
    cursor.execute("SELECT category_id, category_name FROM category")
    categories = cursor.fetchall()

    connection.close()

    # Format items (encode images)
    formatted_items = []
    for item_id, name, price, img, category_name in items:
        if isinstance(img, bytes):
            img_base64 = base64.b64encode(img).decode('utf-8')
        else:
            img_base64 = None
        formatted_items.append((item_id, name, price, img_base64, category_name))  # Important: category_name

    return render_template('Menu.html', items=formatted_items, categories=categories)


@customer.route('/Orders', methods=['GET', 'POST'])
def orders():
    if 'user' not in session:
        return redirect(url_for('customer.login'))

    cart_items = session.get('cart_items', [])

    if request.method == 'POST':
        item_index = 0
        while f'item_name_{item_index}' in request.form:
            new_item = {
                'item_id': request.form.get(f'item_id_{item_index}', ''),
                'name': request.form[f'item_name_{item_index}'],
                'price': float(request.form[f'item_price_{item_index}']),
                'quantity': int(request.form[f'item_quantity_{item_index}']),
                'image_url': request.form.get(f'item_image_{item_index}', '')
            }

            existing = next((item for item in cart_items if item['item_id'] == new_item['item_id']), None)
            if existing:
                existing['quantity'] += new_item['quantity']
            else:
                cart_items.append(new_item)

            item_index += 1

        
        session['cart_items'] = cart_items

    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT name, email, contact, address FROM customer WHERE customer_id = %s", (session['user'],))
    users = cursor.fetchone()
    connection.close()

    if not cart_items:
        flash("Your cart is empty. Please add items.", "warning")

    return render_template('orders.html', cart_items=cart_items, total_amount=total_amount, users=users)

import traceback

@customer.route('/api/insert_item', methods=['POST'])
def insert_item():
    try:
        # Retrieve cart items from the incoming request
        cart_items = request.json.get('cart_items', [])
        if not cart_items:
            return jsonify({"message": "Cart is empty."}), 400

        connection = connect_db()
        cursor = connection.cursor()

        # Insert each cart item into the order_item table
        for item in cart_items:
            item_id = item['item_id']
            quantity = item['quantity']
            
            # Insert the item into the order_item table
            cursor.execute("""
                INSERT INTO order_item (item_id, quantity)
                VALUES (%s, %s)
            """, (item_id, quantity))

        connection.commit()
        connection.close()

        return jsonify({"message": "Order items inserted successfully!"}), 200

    except Exception as e:
        # Log the error message and stack trace
        print("Error occurred:", str(e))
        print("Stack trace:", traceback.format_exc())

        connection.rollback()
        connection.close()
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@customer.route('/Payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session:
        return redirect(url_for('customer.login'))

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    # Fetch customer details
    cursor.execute("SELECT customer_id, name, email, contact, address FROM customer WHERE customer_id = %s ORDER BY customer_id DESC LIMIT 1", (session['user'],))
    user = cursor.fetchone()

    # Fetch cart items from session
    cart_items = session.get('cart_items', [])
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    message = None
    message_type = None

    if not cart_items:
        message = "Your cart is empty. Please add items."
        message_type = "warning"
        connection.close()
        return render_template('payment.html', cart_items=[], total_amount=0, user=user, message=message, message_type=message_type)

    if request.method == 'POST':
        # Get payment screenshot
        payment_file = request.files.get('payment_ss')
        if not payment_file or payment_file.filename == '':
            message = "Payment screenshot is required."
            message_type = "danger"
            return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user, message=message, message_type=message_type)

        # Read the payment screenshot file
        payment_ss = payment_file.read()

        # Insert order into the 'orders' table for each cart item
        for item in cart_items:
            item_id = item.get('item_id') or item.get('id')
            quantity = item['quantity']

            cursor.execute("""
                INSERT INTO orders (customer_id, item_id, quantity, total_amount, order_status, payment_ss)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user['customer_id'],
                item_id,
                quantity,
                total_amount,
                'Pending',  # Order status is initially 'Pending'
                payment_ss  # Storing the payment screenshot as binary data
            ))

        # Commit the changes to the database
        connection.commit()
        connection.close()

        # Clear the cart items from session after the order is placed
        session['cart_items'] = []

        # Redirect to Thank You page
        return redirect(url_for('customer.thankyou'))

    connection.close()
    return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user, message=message, message_type=message_type)


@customer.route('/api/customer_details', methods=['GET'])
def api_customer_details():
    if 'user' not in session:
        return jsonify({'message': 'User not logged in'}), 401

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT customer_id, name, email, contact, address FROM customer WHERE customer_id = %s LIMIT 1", (session['user'],))
    user = cursor.fetchone()

    connection.close()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user)

import base64

@customer.route('/api/recent_orders', methods=['GET'])
def recent_orders():
    if 'user' not in session:
        return jsonify({'message': 'User not logged in'}), 401

    # Connect to the database
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    # Fetch the most recent orders for the logged-in customer
    cursor.execute("""
    SELECT oi.item_id, i.item_name, oi.quantity, i.price, 
           (oi.quantity * i.price) AS total_price
    FROM order_item oi
    JOIN items i ON oi.item_id = i.item_id
    ORDER BY oi.order_item_id DESC
    LIMIT 5
""")

    recent_orders = cursor.fetchall()

    connection.close()

    if not recent_orders:
        return jsonify({'message': 'No recent orders found'}), 404

    # Return the recent orders in JSON format
    return jsonify(recent_orders)


@customer.route('/MyOrders', methods=['GET'])
def myorder():
    highlight_order_id = request.args.get('highlight_order_id')
    return render_template("myorder.html", highlight_order_id=highlight_order_id)

@customer.route('/api/myorders', methods=['GET'])
def my_orders():
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT 
        o.order_id,
        c.name AS customer_name,
        o.total_amount,
        o.order_date,
        o.order_status,
        o.payment_ss,
        i.item_name,
        o.quantity
    FROM orders o
    LEFT JOIN customer c ON o.customer_id = c.customer_id
    LEFT JOIN items i ON o.item_id = i.item_id
    ORDER BY o.order_date DESC;
    """
    cursor.execute(query)
    result = cursor.fetchall()

    orders_dict = {}

    if result:
        for row in result:
            order_id = row['order_id']
            payment_ss_base64 = None
            if row['payment_ss']:
                payment_ss_base64 = base64.b64encode(row['payment_ss']).decode('utf-8')

            if order_id not in orders_dict:
                orders_dict[order_id] = {
                    "order_id": order_id,
                    "name": row["customer_name"],
                    "total_amount": row["total_amount"],
                    "order_date": row["order_date"],
                    "status": row["order_status"],
                    "payment_ss": payment_ss_base64,
                    "items": []
                }

            if row["item_name"]:
                orders_dict[order_id]["items"].append({
                    "name": row["item_name"],
                    "quantity": row["quantity"]
                })
    connection.close()

    return jsonify(list(orders_dict.values()))

@customer.route('/Thankyou')
def thankyou():
    return render_template("thankyou.html")

@customer.route('/Account', methods=['GET'])
def account():
    return render_template("account.html")

@customer.route('/api/account', methods=['GET'])
def account_api():
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    email = session.get('user_email')  # Retrieve the user's email from the session
    if not email:
        return jsonify({'error': 'Email not found in session'}), 400

    # Fetch user data from the database
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email, contact, address FROM customer WHERE email = %s", (email,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user_data:
        return jsonify({'error': 'User not found'}), 404

    # Return the user data as a JSON response
    return jsonify(user_data)



