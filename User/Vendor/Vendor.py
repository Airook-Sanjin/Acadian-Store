from flask import Blueprint, render_template
from User.chat import chat_bp

vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vend', template_folder='templates')
vendor_bp.register_blueprint(chat_bp)

@vendor_bp.route('/Home')
def VendorHomePage():
    return render_template('VendorHomepage.html')