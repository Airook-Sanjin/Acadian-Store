from flask import Blueprint, render_template,session,g

customer_bp = Blueprint('customer_bp', __name__, url_prefix='/cust', template_folder='templates')

@customer_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@customer_bp.route('/Home')
def CustomerHomePage():
    return render_template('CustomerHomepage.html')
