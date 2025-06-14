from flask import Flask, session, redirect, url_for, flash
from flask_mail import Mail
from sample_folder.__init__ import create_app

mail = Mail()

app = create_app()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'craveon129@gmail.com'
app.config['MAIL_PASSWORD'] = 'eorsaacreayfwlnw' 
app.config['MAIL_DEFAULT_SENDER'] = 'craveon129@gmail.com'

mail.init_app(app)

@app.before_request
def make_session_permanent():
    session.permanent = True 

@app.after_request
def add_no_cache_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)
