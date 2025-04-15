from flask import Blueprint, render_template, request
from dbconnect import Connecttodb  # Import the updated Connecttodb function
from sqlalchemy import text

register_bp = Blueprint('register_bp', __name__, url_prefix='/auth', template_folder='templates', static_folder='static')

@register_bp.route('/register', methods=["GET"])
def register_who():
    # Get the type of registration from the query parameter
    reg_type = request.args.get('type', 'customer')  # Default to 'customer' if no type is provided
    return render_template('Register.html', reg_type=reg_type)

###########################################################
# IF YOU DO NOT SEE IN DATABASE BECAUSE I HAVE NO COMMITS #
###########################################################

@register_bp.route('/register/customer', methods=["POST"])
def register_view_customer():
    try:
        # Get database connection
        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")
        
        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO customer (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        return render_template('Register.html', message="Registered successfully!", success=True)
    except Exception as e:
        print(f"Error during registration: {e}")
        return render_template('Register.html', message="Registration failed. Please try again.", success=False)
    
@register_bp.route('/register/vendor', methods=["POST"])
def register_view_vendor():
    try:
        # Get database connection
        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")
        
        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO vendor (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        return render_template('Register.html', message="Registered successfully!", success=True)
    except Exception as e:
        print(f"Error during registration: {e}")
        return render_template('Register.html', message="Registration failed. Please try again.", success=False)
    
@register_bp.route('/register/admin', methods=["POST"])
def register_view_admin():
    try:
        # Get database connection
        conn = Connecttodb()

        EMAIL = request.form.get("email")
        USERNAME = request.form.get("username")
        FULL_NAME = request.form.get("full_name")
        PASSWORD = request.form.get("password")
        
        conn.execute(text("""INSERT INTO users (email, username, name, password) 
                              VALUES (:email, :username, :name, :password)"""),
                     {'email': EMAIL, 'username': USERNAME, 'name': FULL_NAME, 'password': PASSWORD})
        
        conn.execute(text("""INSERT INTO admin (email) 
                              VALUES (:email)"""), {'email': EMAIL})
        
        return render_template('Register.html', message="Registered successfully!", success=True)
    except Exception as e:
        print(f"Error during registration: {e}")
        return render_template('Register.html', message="Registration failed. Please try again.", success=False)