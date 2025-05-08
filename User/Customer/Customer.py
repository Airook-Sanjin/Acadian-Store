
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
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        
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
            SELECT color, amount
            FROM product_inventory
        """)).mappings().fetchall()
        
        return render_template('CustomerHomepage.html',products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('CustomerHomepage.html',products=[],CurDate=CurDate, inventory=[])


@customer_bp.route('/Profile',methods=["POST"])
def GetProfileInfo():
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        
        return redirect(url_for('customer_bp.ViewProfile'))
    except Exception as e:
        print(f"Error POST: {e}")
        return redirect(url_for('customer_bp.ViewProfile'))

@customer_bp.route('/Profile',methods=["GET"])
def ViewProfile():
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
         
        customer_data = conn.execute(text("""
            SELECT u.email as Email,u.username as User,u.name as Name  FROM users AS u LEFT JOIN customer as c ON u.email = c.email
            WHERE c.CID = :ID
        """), {'ID': g.User['ID']}).mappings().first()
        
        OrderHistory= conn.execute(text("""
            SELECT o.ORDER_ID as OID,o.amount as amount,o.total as total,o.status as status FROM cart AS ca Inner JOIN orders as o ON ca.ORDER_ID= o.ORDER_ID
            Where CID = :ID Group by o.ORDER_ID,o.total,o.amount,o.status; """),{'ID': g.User['ID']})
        print(session)
        print(g.User)
        
        return render_template('Custprofile.html', customer_data=customer_data,OrderHistory=OrderHistory)
        
        
    except Exception as e:
        print(f"Error GET: {e}")
        return render_template('Custprofile.html',customer_data=[],OrderHistory=[])