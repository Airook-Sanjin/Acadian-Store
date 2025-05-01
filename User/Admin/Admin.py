
from globals import Blueprint,render_template,g,session,Connecttodb,text
from datetime import datetime
from User.chat import chat_bp

admin=Blueprint('admin',__name__, url_prefix='/admin',template_folder='templates',static_folder='static',static_url_path='/static') # * init blueprint
admin.register_blueprint(chat_bp)
conn= Connecttodb()
@admin.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None


@admin.route('/Home')
def AdminHomePage():
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
            SELECT color, amount
            FROM product_inventory
        """)).mappings().fetchall()

        conn.commit()
        return render_template('GuestHomepage.html', products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('GuestHomepage.html', products=[],CurDate=CurDate, inventory=[])