
from globals import Blueprint,render_template,g,session,Connecttodb,text
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
        products = conn.execute(text("""
                SELECT 
                    PID, title, price, description,
                    warranty, discount, availability, image_url
                FROM product
            """)).mappings().fetchall()  # ✅ changed from .first() to .fetchall()

        inventory = conn.execute(text("""
            SELECT size, color, amount            FROM product_inventory
            """)).mappings().fetchall()
        return render_template('AdminHomepage.html',products=products, inventory=inventory)
    except Exception as e:
        return render_template('AdminHomepage.html',products=[], inventory=[])