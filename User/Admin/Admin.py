
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
    Allproducts = conn.execute(text(
         """SELECT p.PID as PID,p.title as title, p.price as price,p.description as description,inv.amount as amount,p.warranty as warranty,p.discount as discount,p.availability as availability,p.image_url as image FROM product as p
           LEFT JOIN product_images as pi on p.PID = pi.PID
           LEFT JOIN product_inventory as inv on pi.PID = inv.PID""")).mappings().fetchall()
    return render_template('AdminHomepage.html',Allproducts=Allproducts)