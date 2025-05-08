from globals import Flask, redirect, url_for,render_template,session,g,Connecttodb,text,request,jsonify

import secrets
from datetime import datetime
from Auth.Login import login_bp
from Auth.Register import register_bp
from User.Admin.Admin import admin_bp
from User.Customer.Customer import customer_bp
from User.Vendor.Vendor import vendor_bp
from User.user import user_bp
from User.chat import chat_bp
from User.user_util.cart.cart import cart_bp
from User.user_util.search.search import search_bp
from User.user_util.PlaceOrder.PlaceOrder import OrderPlace_bp



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
app.register_blueprint(search_bp)
app.register_blueprint(OrderPlace_bp)

app.register_blueprint(admin_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(vendor_bp)


 
@app.route('/', methods=["GET"])
def start():
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
        return render_template('GuestHomepage.html', products=[],CurDate=CurDate,inventory=[])

    
@app.route('/Product-View')
def ProductView():
    try:
        conn.commit()
        CurDate = datetime.now().date()
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
            SELECT color, amount
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
        
        Review_Count = conn.execute(text("""
            SELECT COUNT(*) AS review_count
            FROM reviews
            WHERE PID = :pid
        """), {"pid": pid}).mappings().first()

        Avg_Rating = conn.execute(text("""
            SELECT COALESCE(AVG(rating), 0) AS average_rating
            FROM reviews
            WHERE PID = :pid
        """), {"pid": pid}).mappings().first()

        Rating_Distribution = conn.execute(text("""
            SELECT rating, COUNT(*) AS count
            FROM reviews
            WHERE PID = :pid
            GROUP BY rating
        """), {"pid": pid}).mappings().fetchall()

        # Convert rating distribution to a dictionary {rating: count}
        rating_counts = {row["rating"]: row["count"] for row in Rating_Distribution}
        
        # Calculate rating percentages
        total_reviews = Review_Count["review_count"] if Review_Count and Review_Count["review_count"] else 0
        rating_percentages = {star: (rating_counts.get(star, 0) / total_reviews * 100) if total_reviews > 0 else 0 for star in range(1, 6)}

        return render_template('Product.html', product=product, inventory=inventory, CurDate=CurDate, images=images, Reviews=Reviews, Review_Count=total_reviews, Avg_Rating=round(Avg_Rating["average_rating"], 1) if Avg_Rating else 0, Rating_Percentages=rating_percentages)

    except Exception as e:
        print("##############################################") 
        print("Error:", e)  
        print("##############################################") 
        return render_template('Product.html', product=None, inventory=[], images=[], Reviews=[],CurDate=CurDate, Review_Count=0, Avg_Rating=0, Rating_Percentages={})

@app.route('/api/inventory')
def GetInventory():
    pid=request.args.get('PID')
    color=request.args.get('color')
    inventory= conn.execute(text("""
        SELECT amount FROM product_inventory
        WHERE PID = :pid AND color = :color """),{'pid':pid,'color': color}).fetchone()
    
    return jsonify({'amount':inventory.amount if inventory else 0 })
    

@app.route('/Review', methods=["POST"])
def Review():
    try:
        if not g.User:
            return redirect(url_for('login_bp.Login'))

        pid = request.form.get('pid')
        rating = request.form.get('rating')
        title = request.form.get('title', '')
        review = request.form.get('description', '')
        cid = g.User.get('ID')

        # Ensure rating is an integer and properly handled
        if rating:
            rating = int(rating)
        else:
            rating = 0  # Default to 0 if no rating is selected
        conn.execute(text("""INSERT INTO reviews (CID, PID, rating, title, description) 
                             VALUES (:CID, :PID, :rating, :title, :description)"""), 
                     {"CID": cid, "PID": pid, "rating": rating, "title": title, "description": review})
        conn.commit()
        print(f"Redirecting to ProductView with PID: {pid}")  # Log the pid
        return redirect(url_for('ProductView', pid=pid))
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('ProductView', pid=request.form.get('pid')))



if __name__ == '__main__':
        app.run(debug=True)
