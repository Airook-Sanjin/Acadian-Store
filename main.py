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

        conn.commit()
        return render_template('GuestHomepage.html', products=products, inventory=inventory)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('GuestHomepage.html', products=[], inventory=[])

    
@app.route('/Product-View')
def ProductView():
    try:
        pid = request.args.get('pid')
        
        product = conn.execute(text("""
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
            WHERE PID = :pid
        """), {"pid": pid}).mappings().first()
        
        inventory = conn.execute(text("""
            SELECT size, color, amount
            FROM product_inventory
            WHERE PID = :pid
        """), {"pid": pid}).mappings().fetchall()

        images = conn.execute(text("""
            SELECT image
            FROM product_images
            WHERE PID = :pid
        """), {"pid": pid}).mappings().fetchall()
        
        Reviews = conn.execute(text("""
            SELECT *
            FROM reviews
            WHERE PID = :pid
        """), {"pid": pid}).mappings().fetchall()
        
        # print("Specific Product:", specific_product)  # Debugging output
        return render_template('Product.html', product=product, inventory=inventory, images=images, Reviews=Reviews)
    except Exception as e:
        print("Error:", e)  # Print the actual error
        return render_template('Product.html', product=None, inventory=[], images=[], Reviews=[])
    
# @app.route('/View-Reviews')
# def ProductReviews():
#     try:
#         pid = request.args.get('pid')
#         conn.commit()
#         return render_template('Product.html', product=None, inventory=[], images=[])
#     except Exception as e:
#         print("Error:", e)  # Print the actual error
#         return render_template('Product.html', product=None, inventory=[], images=[])

app.route('/Review', methods=["POST"])
def Review():
    try:
        pid = request.args.get('pid') # take from page
        rating = request.args.get('rating')
        title = request.args.get('title')
        review = request.args.get('description')
        cid = g.User['ID']
        
        conn.execute(text("""Insert into reviews (CID, PID, rating, title, description) 
                          values (:CID, :PID, :rating, :title, :description)"""), 
                        {"CID": cid, 
                        "PID": pid,
                        "rating": rating,
                        "title": title,
                        "description": review})
        
        # conn.commit()
        return render_template('Product.html', product=None, inventory=[], images=[])
    except Exception as e:
        print("Error:", e)  # Print the actual error
        return render_template('Product.html', product=None, inventory=[], images=[])

    


if __name__ == '__main__':
        app.run(debug=True)  