
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
    Allproducts = conn.execute(text(
         """SELECT p.PID as PID,p.title as title, p.price as price,p.description as description,inv.amount as amount,p.warranty as warranty,p.discount as discount,p.availability as availability,p.image_url as image FROM product as p
           LEFT JOIN product_images as pi on p.PID = pi.PID
           LEFT JOIN product_inventory as inv on pi.PID = inv.PID""")).mappings().fetchall()
    return render_template('CustomerHomepage.html',Allproducts=Allproducts)

# def AddToCart():
    

