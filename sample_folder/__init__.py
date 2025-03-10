from flask import Flask
from sample_folder.customers_folder.customer import customer
from sample_folder.admin_folder.admin import admin


def create_app():
    app = Flask(__name__)
    
    app.secret_key = 'ray'
    
    app.register_blueprint(customer, url_prefix='/CraveOn')
    app.register_blueprint(admin, url_prefix='/Admin')
    
    return app