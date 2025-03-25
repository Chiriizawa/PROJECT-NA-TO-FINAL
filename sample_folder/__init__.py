from flask import Flask, session, redirect, url_for, flash
from sample_folder.customers_folder.customer import customer
from sample_folder.admin_folder.admin import admin


def create_app():
    app = Flask(__name__)

    # ✅ Secret key for session security
    app.secret_key = 'ray'  # Use a more secure key in production

    # ✅ Register Blueprints
    app.register_blueprint(customer, url_prefix='/CraveOn')
    app.register_blueprint(admin, url_prefix='/Admin')

    # ✅ Set session to be permanent (until user logs out)
    @app.before_request
    def make_session_permanent():
        session.permanent = True  # Session lasts until logout

    # ✅ Prevent caching to avoid back navigation after logout
    @app.after_request
    def add_no_cache_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
