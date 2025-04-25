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

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email:
            email_error = "Email is required."
        elif not password:
            password_error = "Password is required."
        else:
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user:
                email_error = "Email not found. Please check your email."
            elif not bcrypt.check_password_hash(user['password'], password):
                password_error = "Incorrect password. Please try again."
            else:
                session["temp_user_id"] = user['customer_id']
                session["verification_code"] = str(random.randint(100000, 999999))

                if send_verification_email(email, session["verification_code"]):
                    return redirect(url_for("customer.verify"))
                else:
                    flash("Failed to send verification email. Please try again.", "danger")

    response = make_response(render_template("customerlogin.html", email_error=email_error, password_error=password_error))
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


from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()  # Make sure this is initialized in your app setup

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
            # ✅ Hash the password before saving
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

@customer.route('/Payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session:
        return redirect(url_for('customer.login'))

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT customer_id, name, email, contact, address FROM customer WHERE customer_id = %s ORDER BY customer_id DESC LIMIT 1", (session['user'],))
    user = cursor.fetchone()

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
        payment_file = request.files.get('payment_ss')
        if not payment_file or payment_file.filename == '':
            message = "Payment screenshot is required."
            message_type = "danger"
            return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user, message=message, message_type=message_type)

        payment_ss = payment_file.read()

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
                'Pending',
                payment_ss
            ))

        connection.commit()
        connection.close()

        session['cart_items'] = []

        return redirect(url_for('customer.myorder', message="Order placed successfully!", message_type="success"))

    connection.close()
    return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user, message=message, message_type=message_type)

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

@customer.route('/Account')
def account():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM customer')
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("account.html", data=data)
