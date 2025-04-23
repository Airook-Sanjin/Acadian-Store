
from globals import Blueprint, render_template,redirect,url_for,session,g,text,Connecttodb

from User.chat import chat_bp


customer_bp = Blueprint('customer_bp', __name__, url_prefix='/cust', template_folder='templates')
customer_bp.register_blueprint(chat_bp)




conn=Connecttodb() # Connects to DB

@customer_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@customer_bp.route('/Home', methods=["GET"]) # Customer homepage
def CustomerHomePage():
    try:
        products = conn.execute(text("""
                SELECT 
                    PID, title, price, description,
                    warranty, discount, availability, image_url
                FROM product
            """)).mappings().fetchall()  # ✅ changed from .first() to .fetchall()

        inventory = conn.execute(text("""
            SELECT size, color, amount            FROM product_inventory
            """)).mappings().fetchall()
        return render_template('CustomerHomepage.html',products=products, inventory=inventory)
    except Exception as e:
        return render_template('CustomerHomepage.html',products=[], inventory=[])

# def AddToCart():
    

