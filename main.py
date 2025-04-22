from globals import Flask, redirect, url_for,render_template,session,g,Connecttodb,text,request
import secrets
from Auth.Login import login_bp
from Auth.Register import register_bp
from User.Admin.Admin import admin
from User.Customer.Customer import customer_bp
from User.Vendor.Vendor import vendor_bp
from User.user import user_bp
from User.chat import chat_bp
from User.user_util.cart.cart import cart_bp



app = Flask(__name__,template_folder='templates',static_folder='static') #* This makes it easier to set base templates


app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn = Connecttodb()

@app.before_request # Before each request it will look for the values below
def load_user():
    try:
        conn.execute(text('SELECT 1')).fetchone()
    except Exception:
        print("Reconnecting to DB....")
        conn=Connecttodb()
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        

 # Get database connection

# Register blueprints  #! ORDER MATTERS
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)

app.register_blueprint(user_bp)
app.register_blueprint(cart_bp) 
app.register_blueprint(chat_bp)

app.register_blueprint(admin)
app.register_blueprint(customer_bp)
app.register_blueprint(vendor_bp)


 
@app.route('/', methods=["GET"])
def start():
    try:
        Allproducts = conn.execute(text(
        """SELECT p.PID as PID,p.title as title, p.price as price,p.description as description,inv.amount as amount,p.warranty as warranty,p.discount as discount,p.availability as availability,p.image_url as image FROM product as p
           LEFT JOIN product_images as pi on p.PID = pi.PID
           LEFT JOIN product_inventory as inv on pi.PID = inv.PID""")).mappings().fetchall() #* Gets all products
        # print(Allproducts)

        # resets connection  to db for the next request
        conn.commit()
        return render_template('GuestHomepage.html',Allproducts = Allproducts)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('GuestHomepage.html',Allproducts = [])
    
@app.route('/Product-View')
def ProductView():
    try:
        pid = request.args.get('pid')
        specific_product = conn.execute(text(
        """SELECT 
            p.PID as PID,
            p.title as title, 
            p.price as price,
            p.description as description,
            inv.amount as amount,
            p.warranty as warranty,
            p.discount as discount,
            p.availability as availability,
            p.image_url as image
            FROM product as p
            LEFT JOIN product_images as pi ON p.PID = pi.PID
            LEFT JOIN product_inventory as inv ON pi.PID = inv.PID
            WHERE p.PID = :pid"""), {"pid": pid}).mappings().fetchall()
        print("Specific Product:", specific_product)  # Debugging output
        return render_template('Product.html', specific_product=specific_product)
    except Exception as e:
        print("Error:", e)  # Print the actual error
        return render_template('Product.html', specific_product=[])

    


if __name__ == '__main__':
        app.run(debug=True)  