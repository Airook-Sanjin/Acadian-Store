
from globals import Blueprint, render_template,redirect,url_for,session,g,text,Connecttodb
from datetime import datetime
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
        CurDate = datetime.now().date()
        products = conn.execute(text("""
           SELECT 
                PID, title, CAST(price AS DECIMAL(10,2)) AS price,
                (price * discount) as saving_discount,
                price - (price * discount) AS discounted_price,
                description,
                warranty,
                discount, discount_date,
                availability,
                VID,
                AID,
                image_url
                FROM product 
        """)).mappings().fetchall()  # changed from .first() to .fetchall()

        inventory = conn.execute(text("""
            SELECT size, color, amount
            FROM product_inventory
        """)).mappings().fetchall()
        
        return render_template('CustomerHomepage.html',products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        return render_template('CustomerHomepage.html',products=[],CurDate=CurDate, inventory=[])

# def AddToCart():
    

