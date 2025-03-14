import base64
from flask import Blueprint, render_template, request, redirect, url_for
import mysql.connector

admin = Blueprint('admin', __name__, template_folder="template")

db_config = {
    'host': 'localhost',
    'database': 'test',
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
        quantity = request.form.get('quantity')
        image = request.files.get('image')

        if not name or not price or not quantity or not image:
            return "Missing form data", 400
        
        image_data = image.read()
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO test_items (item_name, price, quantity, image) VALUES (%s, %s, %s, %s)",
                (name, price, quantity, image_data)
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
        cursor.execute("SELECT id, item_name, price, quantity, image FROM test_items")
        items = cursor.fetchall()
        cursor.close()
        connection.close()
    except Exception:
        items = []
    
    return render_template("manage_item.html", items=items)

@admin.route('/delete/<int:item_id>', methods=['GET'])
def delete_item(item_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM test_items WHERE id = %s", (item_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('admin.manageitem'))
    except Exception as e:
        return f"Error deleting item: {str(e)}", 500
    
@admin.route('/edit-item', methods=['POST'])
def edit_item():
    item_id = request.form.get('item_id')
    name = request.form.get('name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')

    if not item_id or not name or not price or not quantity:
        return "Missing form data", 400

    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE test_items SET item_name = %s, price = %s, quantity = %s WHERE id = %s",
            (name, price, quantity, item_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('admin.manageitem'))
    except Exception as e:
        return f"Error: {str(e)}", 500

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
        cursor.execute('SELECT * FROM customers')
        data = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('manage_users.html')
