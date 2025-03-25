from flask import Flask, session, redirect, url_for, flash
from sample_folder.customers_folder.customer import customer
from sample_folder.admin_folder.admin import admin


def create_app():
    app = Flask(__name__)

    app.secret_key = 'ray' 

    app.register_blueprint(customer, url_prefix='/CraveOn')
    app.register_blueprint(admin, url_prefix='/Admin')

    @app.before_request
    def make_session_permanent():
        session.permanent = True 

    @app.after_request
    def add_no_cache_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
