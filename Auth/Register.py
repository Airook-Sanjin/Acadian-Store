from flask import Blueprint, render_template, request
from dbconnect import Connecttodb
from sqlalchemy import text
from werkzeug.security import generate_password_hash

register_bp = Blueprint('register_bp', __name__, url_prefix='/auth', template_folder='templates', static_folder='static')

@register_bp.route('/register', methods=["GET"])
def register_who():
    reg_type = request.args.get('type', 'customer')
    return render_template('Register.html', reg_type=reg_type)

def handle_register_user(email, username, full_name, password, user_type):
    conn = Connecttodb()

    if not email or not username or not full_name or not password:
        return render_template('Register.html', message="All fields are required.", success=False)

    existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {'email': email}).fetchone()
    if existing_user:
        return render_template('Register.html', message="Email is already registered.", success=False)

    # Hash the password securely
    hashed_password = generate_password_hash(password)

    # Insert user
    conn.execute(text("""
        INSERT INTO users (email, username, name, password)
        VALUES (:email, :username, :name, :password)
    """), {
        'email': email,
        'username': username,
        'name': full_name,
        'password': hashed_password
    })

    # Insert into the specific role table
    conn.execute(text(f"INSERT INTO {user_type} (email) VALUES (:email)"), {'email': email})
    conn.commit()
    return render_template('Register.html', message="Registered successfully!", success=True)

@register_bp.route('/register/customer', methods=["POST"])
def register_view_customer():
    try:
        return handle_register_user(
            request.form.get("email"),
            request.form.get("username"),
            request.form.get("full_name"),
            request.form.get("password"),
            user_type="customer"
        )
    except Exception as e:
        return render_template('Register.html', message=f"Error: {str(e)}", success=False)

@register_bp.route('/register/vendor', methods=["POST"])
def register_view_vendor():
    try:
        return handle_register_user(
            request.form.get("email"),
            request.form.get("username"),
            request.form.get("full_name"),
            request.form.get("password"),
            user_type="vendor"
        )
    except Exception as e:
        return render_template('Register.html', message=f"Error: {str(e)}", success=False)

@register_bp.route('/register/admin', methods=["POST"])
def register_view_admin():
    try:
        return handle_register_user(
            request.form.get("email"),
            request.form.get("username"),
            request.form.get("full_name"),
            request.form.get("password"),
            user_type="admin"
        )
    except Exception as e:
        return render_template('Register.html', message=f"Error: {str(e)}", success=False)
