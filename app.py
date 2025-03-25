from flask import Flask, session, redirect, url_for, flash
from flask_mail import Mail
from sample_folder.__init__ import create_app

mail = Mail()

# ✅ Create app instance
app = create_app()

# ✅ Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'craveon129@gmail.com'
app.config['MAIL_PASSWORD'] = 'eorsaacreayfwlnw'  # Consider using environment variables for security
app.config['MAIL_DEFAULT_SENDER'] = 'craveon129@gmail.com'

# ✅ Initialize mail
mail.init_app(app)

# ✅ Set session to be permanent (until user logs out)
@app.before_request
def make_session_permanent():
    session.permanent = True  # Session persists until user logs out

# ✅ Prevent caching to disable back after logout
@app.after_request
def add_no_cache_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)
