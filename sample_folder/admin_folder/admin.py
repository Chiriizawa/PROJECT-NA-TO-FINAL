import base64
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from flask_bcrypt import Bcrypt

admin = Blueprint('admin', __name__, template_folder="template")
bcrypt = Bcrypt()

db_config = {   
    'host': 'localhost',
    'database': 'foodordering',
    'user': 'root',
    'password': '',
}   

def connect_db():
    return mysql.connector.connect(**db_config)

@admin.app_template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8') if data else ''

@admin.route('/')
def index():
    connection = connect_db()
    cursor = connection.cursor()

    # Fetch total sales from orders
    cursor.execute("SELECT SUM(total_price) FROM orders")
    total_sales = cursor.fetchone()[0] or 0  # If NULL, set to 0

    # Fetch total number of customers
    cursor.execute("SELECT COUNT(*) FROM customer")
    total_customers = cursor.fetchone()[0]


    connection.close()

    return render_template(
        'admin_index.html',
        total_sales=total_sales,
        total_customers=total_customers,
    )

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)  # Fetch as dictionary to access by column name

        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

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
def manageorders():
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT 
        o.order_id,
        c.name AS customer_name,
        o.total_amount,
        o.order_date,
        o.order_status AS status,  
        i.item_name,
        o.quantity 
        FROM orders o
        LEFT JOIN customer c ON o.customer_id = c.customer_id
        LEFT JOIN items i ON o.item_id = i.item_id
        ORDER BY o.order_date DESC;
    """
    cursor.execute(query)
    result = cursor.fetchall()

    orders = {}

    if result:  
        for row in result:
            order_id = row['order_id']
            if order_id not in orders:
                orders[order_id] = {
                    "order_id": order_id,
                    "name": row["customer_name"],
                    "total_amount": row["total_amount"],
                    "order_date": row["order_date"],
                    "status": row["status"],
                    "items": []
                }
            if row["item_name"]:
                orders[order_id]["items"].append({"name": row["item_name"], "quantity": row["quantity"]})

    connection.close()

    # Convert dictionary values to list
    orders_list = list(orders.values()) if orders else []


    return render_template("manage_order.html", orders=orders_list)



@admin.route('/Manage-Categories')
def categories():
    return render_template("categories.html")

@admin.route('/Manage-Users')
def users():

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM customer")
    users = cursor.fetchall()
    connection.close()

    return render_template('manage_users.html', users=users)


@admin.route('/delete_order/<int:order_id>')
def delete_order(order_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE order_id=%s", (order_id,))
    conn.commit()
    conn.close()
    flash("Order deleted successfully!", "success")
    return redirect(url_for('admin.manageorders')) 

@admin.route('/delete_user/<int:user_id>', methods=['GET'])
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
def edit_user():
    user_id = request.form['user_id']
    name = request.form['name']
    email = request.form['email']
    contact = request.form['contact']
    address = request.form['address']

    try:
        conn = connect_db()
        cursor = conn.cursor()

        sql = "UPDATE customer SET name=%s, email=%s, contact=%s, address=%s WHERE customer_id=%s"
    except Exception as e:
        flash(f"Error updating user: {str(e)}", 'danger')

    return redirect(url_for('admin.users'))
