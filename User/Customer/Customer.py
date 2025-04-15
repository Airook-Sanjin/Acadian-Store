from flask import Blueprint, render_template

customer_bp = Blueprint('customer_bp', __name__, url_prefix='/cust', template_folder='templates')

@customer_bp.route('/Home')
def CustomerHomePage():
    return render_template('CustomerHomepage.html')
