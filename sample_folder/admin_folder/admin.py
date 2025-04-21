import base64
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, make_response
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

def make_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def connect_db():
    return mysql.connector.connect(**db_config)

@admin.app_template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8') if data else ''

@admin.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("SELECT SUM(total_amount) FROM orders")
    total_sales = cursor.fetchone()[0] or 0 

    cursor.execute("SELECT COUNT(*) FROM customer")
    total_customers = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    response = make_response(render_template(
        'admin_index.html',
        total_sales=total_sales,
        total_customers=total_customers,
    ))
    return response

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('admin.index'))

    emailmsg = ''
    passwordmsg = ''
    msg = ''
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email != 'admin123@gmail.com':
            emailmsg = 'Email is incorrect!'

        if password != 'admin':
            passwordmsg = 'Password is incorrect!'

        if not emailmsg and not passwordmsg:
            try:
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()
                cursor.execute("INSERT INTO admin (email, password) VALUES(%s, %s)", (email, password))
                connection.commit()
                session['user'] = email
                return redirect(url_for('admin.index'))
            except mysql.connector.Error as e:
                msg = f"Adding data failed! Error: {str(e)}"
            finally:
                cursor.close()
                connection.close()
        else:
            msg = emailmsg or passwordmsg

    response = make_response(render_template('admin_login.html', msg=msg, emailmsg=emailmsg, passwordmsg=passwordmsg))
    return make_header(response)

@admin.route('/logout')
def adminlogout():
    session.pop('user', None)
    response = make_response(redirect(url_for('admin.login')))
    response = make_header(response)
    return response

@admin.route('/Manage-Item', methods=['GET', 'POST'])
def manageitem():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Fetch all categories for dropdown
        cursor.execute("SELECT category_id, category_name FROM category")
        categories = cursor.fetchall()

        if request.method == "POST":
            name = request.form.get('name')
            price = request.form.get('price')
            category_id = request.form.get('category_id')
            image = request.files.get('image')

            if not name or not price or not image or not category_id:
                flash("Missing form data.", "danger")
                return redirect(url_for('admin.manageitem'))

            image_data = image.read()

            try:
                cursor.execute(
                    "INSERT INTO items (item_name, price, image, category_id) VALUES (%s, %s, %s, %s)",
                    (name, price, image_data, category_id)
                )
                connection.commit()
                flash("Item added successfully!", "success")
                return redirect(url_for('admin.manageitem'))
            except Exception as e:
                flash(f"Error inserting item: {str(e)}", "danger")
                return redirect(url_for('admin.manageitem'))

        # Use LEFT JOIN to include all items, even without valid category
        cursor.execute("""
            SELECT items.item_id, items.item_name, items.price, items.image,items.category_id, category.category_name
            FROM items
            LEFT JOIN category ON items.category_id = category.category_id
        """)
        items = cursor.fetchall()

        processed_items = []
        for item in items:
            item_id, item_name, price, image_data, category_id, category_name = item
            image_base64 = base64.b64encode(image_data).decode('utf-8') if image_data else None
            processed_items.append((item_id, item_name, price, image_base64, category_id, category_name or "Uncategorized"))

        cursor.close()
        connection.close()

    except Exception as e:
        processed_items = []
        categories = []
        flash(f"Error: {str(e)}", "danger")

    return render_template("manage_item.html", items=processed_items, categories=categories)


@admin.route('/delete/<int:item_id>', methods=['GET'])
def delete_item(item_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Ensure the item exists before attempting to delete it
        cursor.execute("SELECT item_id FROM items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()

        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for('admin.manageitem'))

        cursor.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Item deleted successfully!", "success")
        return redirect(url_for('admin.manageitem'))
    except Exception as e:
        return f"Error deleting item: {str(e)}", 500

@admin.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
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
            flash(f"Error updating item: {str(e)}", "danger")
            return redirect(url_for('admin.manageitem'))

    # GET method to fetch existing item data
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT item_name, price, image FROM items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        cursor.close()
        connection.close()

        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for('admin.manageitem'))

        item_name, price, image_data = item
        image_base64 = base64.b64encode(image_data).decode('utf-8') if image_data else None
        return render_template("edit_item.html", item_id=item_id, item_name=item_name, price=price, image=image_base64)

    except Exception as e:
        flash(f"Error fetching item data: {str(e)}", "danger")
        return redirect(url_for('admin.manageitem'))

@admin.route('/Manage-User', methods=['GET'])
def users():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customer")
        users = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template("manage_users.html", users=users)
    except Exception as e:
        flash(f"Error fetching users: {str(e)}", "danger")
        return render_template("manage_users.html", users=[])
    
@admin.route('/delete-user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
        flash("User deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "danger")

    return redirect(url_for('admin.users'))

@admin.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        address = request.form.get('address')

        try:
            cursor.execute("""
                UPDATE customer 
                SET name = %s, email = %s, contact = %s, address = %s 
                WHERE customer_id = %s
            """, (name, email, contact, address, user_id))
            connection.commit()
            flash("User updated successfully!", "success")
            return redirect(url_for('admin.users'))
        except Exception as e:
            flash(f"Error updating user: {str(e)}", "danger")

    cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.users'))

    return render_template("edit_user.html", user=user)

@admin.route('/Manage-Categories', methods=['GET', 'POST'])
def categories():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    connection = connect_db()
    cursor = connection.cursor()

    if request.method == 'POST':
        category_name = request.form.get('category_name', '').strip()

        if category_name:
            try:
                cursor.execute("INSERT INTO category (category_name) VALUES (%s)", (category_name,))
                connection.commit()
                flash("Category added successfully!", "success")
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")

    cursor.execute("SELECT category_id, category_name FROM category")
    category_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("categories.html", categories=category_list)

@admin.route('/Manage-Orders')
def manageorders():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    return render_template("manage_order.html")

@admin.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user' not in session:
        return redirect(url_for('admin.login'))

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT 
            o.order_id,
            o.total_amount,
            o.order_date,
            o.order_status,
            o.payment_ss,
            c.name AS customer_name,
            c.contact AS customer_contact,
            c.address AS customer_address,
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

    for row in result:
        order_id = row['order_id']
        payment_ss_base64 = base64.b64encode(row['payment_ss']).decode('utf-8') if row['payment_ss'] else None

        if order_id not in orders_dict:
            orders_dict[order_id] = {
                "order_id": order_id,
                "name": row["customer_name"],
                "contact": row["customer_contact"],
                "address": row["customer_address"],
                "total_amount": row["total_amount"],
                "order_date": row["order_date"].strftime('%a, %d %b %Y %H:%M:%S GMT') if row["order_date"] else "N/A",
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

@admin.route('/api/deleteorders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    connection = connect_db()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM order_item WHERE order_id = %s", (order_id,))
        connection.commit()

        # Now delete the order
        query = "DELETE FROM orders WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        connection.commit()

        connection.close()

        return jsonify({"message": "Order deleted successfully."}), 200
    except Exception as e:
        connection.rollback()
        connection.close()
        print(f"Error deleting order: {e}") 
        return jsonify({"error": str(e)}), 500

@admin.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders 
        SET order_status = 'Approved' 
        WHERE order_id = %s AND order_status = 'Pending'
    """, (order_id,))

    conn.commit()

    if cursor.rowcount == 0:
        return jsonify({'message': 'Order not found or already approved'}), 404

    cursor.close()
    conn.close()

    return jsonify({'message': 'Order status updated to Approved'}), 200

@admin.route('/api/cancelorders/<int:order_id>', methods=['PUT'])
def cancel_order(order_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders 
        SET order_status = 'Cancelled' 
        WHERE order_id = %s AND order_status = 'Pending'
    """, (order_id,))

    conn.commit()
    
    if cursor.rowcount == 0:
        return jsonify({'message': 'Order not found or cannot be canceled (not in Pending status)'}), 404

    cursor.close()
    conn.close()
    return jsonify({'message': 'Order status updated to Cancelled'}), 200
