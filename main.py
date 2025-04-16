from flask import Flask, redirect, url_for
import secrets
from Auth.Login import login_bp
from Auth.Register import register_bp
from User.Admin.Admin import admin
from User.Customer.Customer import customer_bp
from User.Vendor.Vendor import vendor_bp
from User.user import user_bp
from User.chat import chat_bp



app = Flask(__name__,template_folder='templates',static_folder='static') #* This makes it easier to set base templates
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module
# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)

app.register_blueprint(chat_bp)

app.register_blueprint(admin)
app.register_blueprint(user_bp)


@app.route('/')
def start():
    return redirect(url_for("login_bp.Login"))

if __name__ == '__main__':
        app.run(debug=True)  