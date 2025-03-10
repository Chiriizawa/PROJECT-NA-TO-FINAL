from flask import Flask, Blueprint, render_template

customer = Blueprint('customer', __name__, template_folder="template") 

@customer.route('/')
def index():
    return render_template("index.html")

@customer.route('/logIn')
def login():
    return render_template("customerlogin.html")

@customer.route('/SignUp')
def signup():
    return render_template("customersignup.html")

@customer.route('/Menu')
def menu():
    return render_template("Menu.html")

@customer.route('/Orders')
def orders():
    return render_template("orders.html")