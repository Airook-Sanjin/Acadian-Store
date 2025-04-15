from flask import Blueprint, render_template,g,session

vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vend', template_folder='templates')

@vendor_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@vendor_bp.route('/Home')
def VendorHomePage():
    return render_template('VendorHomepage.html')