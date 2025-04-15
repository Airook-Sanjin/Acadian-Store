from flask import Blueprint, render_template

vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vend', template_folder='templates')

@vendor_bp.route('/Home')
def VendorHomePage():
    return render_template('VendorHomepage.html')