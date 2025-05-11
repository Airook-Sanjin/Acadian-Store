from flask import Blueprint, render_template, request
from dbconnect import Connecttodb  # Import the updated Connecttodb function
from sqlalchemy import text

register_bp = Blueprint('register_bp', __name__, url_prefix='/auth', template_folder='templates', static_folder='static')

@register_bp.route('/register', methods=["GET"])
def register_who():
    # Get the type of registration from the query parameter
    reg_type = request.args.get('type', 'customer')  # Default to 'customer' if no type is provided
    return render_template('Register.html', reg_type=reg_type)

@register_bp.route('/register/customer', methods=["POST"])
def register_view_customer():
    try:

        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")

        if not EMAIL or not USERNAME or not FULL_NAME or not PASSWORD:
            return render_template('Register.html', message="All fields are required.", success=False)

        existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {'email': EMAIL}).fetchone()
        if existing_user:
            return render_template('Register.html', message="Email is already registered.", success=False)

        # Insert into users and customer tables
        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO customer (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        conn.commit()
        
        return render_template('Register.html', message="Registered successfully!", success=True)
    except Exception as e:
        error_message = str(e)
        print(f"Error during registration: {error_message}")
        if "Duplicate entry" in error_message:
            return render_template('Register.html', message="This email is already in use.", success=False)
        elif "cannot be null" in error_message:
            return render_template('Register.html', message="A required field is missing.", success=False)
        else:
            return render_template('Register.html', message="An unexpected error occurred. Please try again.", success=False)

@register_bp.route('/register/vendor', methods=["POST"])
def register_view_vendor():
    try:

        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")

        if not EMAIL or not USERNAME or not FULL_NAME or not PASSWORD:
            return render_template('Register.html', message="All fields are required.", success=False)

        existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {'email': EMAIL}).fetchone()
        if existing_user:
            return render_template('Register.html', message="Email is already registered.", success=False)
        
        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO vendor (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        conn.commit()
        
        return render_template('Register.html', message="Registered successfully!", success=True)
    except Exception as e:
        error_message = str(e)
        print(f"Error during registration: {error_message}")
        if "Duplicate entry" in error_message:
            return render_template('Register.html', message="This email is already in use.", success=False)
        elif "cannot be null" in error_message:
            return render_template('Register.html', message="A required field is missing.", success=False)
        else:
            return render_template('Register.html', message="An unexpected error occurred.", success=False)

@register_bp.route('/register/admin', methods=["POST"])
def register_view_admin():
    try:

        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")

        if not EMAIL or not USERNAME or not FULL_NAME or not PASSWORD:
            return render_template('Register.html', message="All fields are required.", success=False)

        
        existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {'email': EMAIL}).fetchone()
        if existing_user:
            return render_template('Register.html', message="Email is already registered.", success=False)


        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO admin (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        conn.commit()
        
        return render_template('Register.html', message="Registered successfully.", success=True)
    except Exception as e:
        print(f"Error during registration: {e}")
        message = "An error occurred during registration."