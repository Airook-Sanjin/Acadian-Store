from flask import Blueprint, render_template

customer_bp = Blueprint('customer_bp', __name__, url_prefix='/cust')

@customer_bp.route('/User')
def UserHomePage():
    return 'User Page'
