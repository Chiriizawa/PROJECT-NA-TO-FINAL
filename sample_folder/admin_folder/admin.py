import base64
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from flask_bcrypt import Bcrypt

admin = Blueprint('admin', __name__, template_folder="template")
bcrypt = Bcrypt()

db_config = {   
    'host': 'localhost',
    'database': 'craveon',
    'user': 'root',
    'password': '',
}   

def connect_db():
    return mysql.connector.connect(**db_config)

@admin.app_template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8') if data else ''

# --------- Login Required Decorator ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
def index():
    return render_template("admin_index.html")

@admin.route('/add-admin', methods=['GET'])
@login_required
def add_admin_page():
    return render_template('add_admin.html')


@admin.route('/add-admin', methods=['POST'])
@login_required
def add_admin():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        contact = request.form.get("contact", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "").strip()

        # ✅ Hash the password before inserting
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = connect_db()
            cursor = conn.cursor()

            # ✅ Insert hashed password into the database
            cursor.execute(
                "INSERT INTO admin (name, email, contact, address, password) VALUES (%s, %s, %s, %s, %s)",
                (name, email, contact, address, hashed_password)
            )

            conn.commit()
            cursor.close()
            conn.close()

            flash("Admin added successfully!", "success")
            return redirect(url_for("admin.index"))

        except Exception as e:
            flash(f"Error adding admin: {str(e)}", "danger")
            return redirect(url_for("admin.index"))



@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)  # Fetch as dictionary to access by column name

        # ✅ Fetch user by email
        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # ✅ Check if user exists and verify password using bcrypt
        if user and bcrypt.check_password_hash(user['password'], password):  # Ensure correct column name
            session["user"] = user['email']  # Store session with email
            flash("Login successful!", "success")
            return redirect(url_for("admin.index"))

        flash("Invalid credentials.", "danger")

    return render_template("admin_login.html")
    


@admin.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin.login"))

@admin.route('/Manage-Item', methods=['GET', 'POST'])
@login_required
def manageitem():
    if request.method == "POST":
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.files.get('image')

        if not name or not price or not image:
            flash("Missing form data.", "danger")
            return redirect(url_for('admin.manageitem'))

        image_data = image.read()

        try:
            connection = connect_db()
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO items (item_name, price, image) VALUES (%s, %s, %s)",
                (name, price, image_data)
            )

            connection.commit()
            cursor.close()
            connection.close()
            flash("Item added successfully!", "success")
            return redirect(url_for('admin.manageitem'))
        except Exception as e:
            return f"Error: {str(e)}", 500

    try:
        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute("SELECT item_id, item_name, price, image FROM items")
        items = cursor.fetchall()

        processed_items = []
        for item in items:
            item_id, item_name, price, image_data = item
            image_base64 = base64.b64encode(image_data).decode('utf-8') if image_data else None
            processed_items.append((item_id, item_name, price, image_base64))

        cursor.close()
        connection.close()
    except Exception as e:
        processed_items = []
        flash(f"Error fetching items: {str(e)}", "danger")

    return render_template("manage_item.html", items=processed_items)

@admin.route('/delete/<int:item_id>', methods=['GET'])
@login_required
def delete_item(item_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Item deleted successfully!", "success")
        return redirect(url_for('admin.manageitem'))
    except Exception as e:
        return f"Error deleting item: {str(e)}", 500

@admin.route('/edit-item/<int:item_id>', methods=['POST'])
@login_required
def edit_item(item_id):
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.files.get('image')

        try:
            connection = connect_db()
            cursor = connection.cursor()

            if image:
                image_data = image.read()
                cursor.execute(
                    "UPDATE items SET item_name=%s, price=%s, image=%s WHERE item_id=%s",
                    (name, price, image_data, item_id),
                )
            else:
                cursor.execute(
                    "UPDATE items SET item_name=%s, price=%s WHERE item_id=%s",
                    (name, price, item_id),
                )

            connection.commit()
            cursor.close()
            connection.close()
            flash("Item updated successfully!", "success")
            return redirect(url_for('admin.manageitem'))
        except Exception as e:
            return f"Error updating item: {str(e)}", 500

@admin.route('/Manage-Orders')
@login_required
def manageorders():
    return render_template('manage_order.html')

@admin.route('/Manage-Categories')
@login_required
def categories():
    return render_template("categories.html")

@admin.route('/Manage-Users')
@login_required
def users():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute('SELECT customer_id, name, email, contact, address, login_time FROM customer')
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manage_users.html', data=data)

@admin.route('/delete_order/<int:order_id>')
@login_required
def delete_order(order_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE order_id=%s", (order_id,))
    conn.commit()
    conn.close()
    flash("Order deleted successfully!", "success")
    return redirect(url_for('admin.manageorders')) 

@admin.route('/delete_user/<int:user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
        flash("user deleted successfully!", "success")
        return redirect(url_for('admin.users'))
    except Exception as e:
        return f"Error deleting item: {str(e)}", 500



@admin.route('/Manage-User', methods=['POST'])
@login_required
def edit_user():
    user_id = request.form['user_id']
    name = request.form['name']
    email = request.form['email']
    contact = request.form['contact']
    address = request.form['address']

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # ✅ Corrected table name and query
        sql = "UPDATE customer SET name=%s, email=%s, contact=%s, address=%s WHERE customer_id=%s"
        values = (name, email, contact, address, user_id)

        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()

        flash('User updated successfully!', 'success')
    except Exception as e:
        flash(f"Error updating user: {str(e)}", 'danger')

    # ✅ Redirecting back to user management page
    return redirect(url_for('admin.users'))
