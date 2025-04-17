from globals import Blueprint, render_template, request,g,session

cart_bp = Blueprint('cart_bp', __name__, url_prefix='/cart', template_folder='templates')

@cart_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None

cart_bp.route('/order')
def UserCart():
    return render_template('Cart.html')