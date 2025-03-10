from flask import Flask, Blueprint, render_template

admin = Blueprint('admin', __name__, template_folder="template")

@admin.route("/")
def index():
    return render_template("admin_index.html")

@admin.route('/Manage-Item')
def manageitem():
    return render_template("manage_item.html")

@admin.route('/Manage-Orders')
def manageorders():
    return render_template("manage_order.html")

@admin.route('/Manage-Categories')
def categories():
    return render_template("categories.html")

@admin.route('/Manage-Users')
def users():
    return render_template('users.html')