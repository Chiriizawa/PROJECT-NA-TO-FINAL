from flask import Flask, Blueprint, render_template, request, flash, session, redirect, url_for, current_app, jsonify
import mysql.connector
import base64
import re
import random
from flask_mail import Message
from flask_bcrypt import Bcrypt


customer = Blueprint('customer', __name__, template_folder="template") 

bcrypt = Bcrypt()



db_config = {
    'host':'localhost',
    'database':'onlinefood',
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
            cursor = conn.cursor(dictionary=True)  # Fetch as dict
            cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user:
                email_error = "Email not found. Please check your email."
            elif not bcrypt.check_password_hash(user['password'], password):
                password_error = "Incorrect password. Please try again."
            else:
                # Store temporary session data for verification
                session["temp_user_id"] = user['customer_id']
                session["verification_code"] = str(random.randint(100000, 999999))

                # Send verification email
                if send_verification_email(email, session["verification_code"]):
                    return redirect(url_for("customer.verify"))
                else:
                    flash("Failed to send verification email. Please try again.", "danger")

    return render_template("customerlogin.html", email_error=email_error, password_error=password_error)


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
            flash("Invalid verification code.", "danger")

    return render_template("verify.html")
@customer.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("customer.index"))

@customer.route('/SignUp', methods=['GET', 'POST'])
def signup():
    errors = {}

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
        elif not name.isalpha():
            errors['name'] = "Name must contain only letters."
        elif len(name) < 4:
            errors['name'] = "Name must be 4 or more characters."

        # Validate email
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

        # Validate contact
        if not contact:
            errors['contact'] = "Contact number is required."
        elif not contact.isdigit() or len(contact) != 11:
            errors['contact'] = "Contact number must be 11 digits."
        else:
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
        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        if errors:
            return render_template("customersignup.html", errors=errors)

        # Insert new customer into database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customer (name, email, contact, address, password) VALUES (%s, %s, %s, %s, %s)",
            (name, email, contact, address, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()


        return render_template("customersignup.html", errors={})

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

        # Store updated cart in session
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

    cursor.execute("SELECT customer_id, name, email, contact, address FROM customer WHERE customer_id = %s", (session['user'],))
    user = cursor.fetchone()

    cart_items = session.get('cart_items', [])
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    if not cart_items:
        flash("Your cart is empty. Please add items.", "warning")
        connection.close()
        return render_template('payment.html', cart_items=[], total_amount=0, user=user)

    if request.method == 'POST':
        payment_file = request.files.get('payment_ss')
        if not payment_file or payment_file.filename == '':
            flash("Payment screenshot is required.", "danger")
            return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user)

        payment_ss = payment_file.read()

        # ✅ Insert each item in cart as a separate order row
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

        flash("Order placed successfully!", "success")
        return redirect(url_for('customer.myorder'))

    connection.close()
    return render_template('payment.html', cart_items=cart_items, total_amount=total_amount, user=user)




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
                orders_dict[order_id]["items"].append({"name": row["item_name"], "quantity": row["quantity"]})

    connection.close()

    return jsonify(list(orders_dict.values()))


@customer.route('/api/myorders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s", ('Completed', order_id))
    connection.commit()
    connection.close()
    return jsonify({'message': 'Order status updated successfully'}), 200



@customer.route('/Account')
def account():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM customer')
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("account.html", data=data)
