import base64
from flask import Blueprint, render_template, request, redirect, url_for
import mysql.connector
import base64

admin = Blueprint('admin', __name__, template_folder="template")

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

@admin.route("/")
def index():

    return render_template("admin_index.html")

@admin.route('/Manage-Item', methods=['GET', 'POST'])
def manageitem():
    if request.method == "POST":
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.files.get('image')

        if not name or not price or not image:
            return "Missing form data", 400

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
    except Exception:
        processed_items = []

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
        return redirect(url_for('admin.manageitem'))
    except Exception as e:
        return f"Error deleting item: {str(e)}", 500
    
@admin.route('/edit-item', methods=['POST'])
def edit_item():
    return

@admin.route('/Manage-Orders')
def manageorders():
    return render_template("manage_order.html")

@admin.route('/Manage-Categories')
def categories():
    return render_template("categories.html")

@admin.route('/Manage-Users')
def users():
    
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute('SELECT customer_id, name, email, contact, address, login_time FROM customer')
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manage_users.html', data=data)