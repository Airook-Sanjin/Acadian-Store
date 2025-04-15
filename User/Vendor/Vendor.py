
from flask import Blueprint, render_template, request,g,session
from dbconnect import Connecttodb  # Import the updated Connecttodb function
from sqlalchemy import text
from User.chat import chat_bp
vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vendor', template_folder='templates')

vendor_bp.register_blueprint(chat_bp)


@vendor_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@vendor_bp.route('/Home')
def VendorHomePage():
    return render_template('VendorHomepage.html')
  

@vendor_bp.route('/AddProduct', methods=["GET", "POST"])
def VendorAddProductPage():
    try:
        # Get database connection
        conn = Connecttodb()
        
        
        TITLE = request.form.get("title")
        PRICE = request.form.get("price")
        DESCRIPTION = request.form.get("description")
        WARRANTY = request.form.get("warranty")
        DISCOUNT = request.form.get("discount")
        DISCOUNT_DATE = request.form.get("discount_date")
        AVAILABILITY = request.form.get("availability")
        VID = request.form.get("VID")
        
        # Handle empty discount and discount_date
        DISCOUNT = DISCOUNT if DISCOUNT else None
        DISCOUNT_DATE = DISCOUNT_DATE if DISCOUNT_DATE else None
        
        conn.execute(text("""
                INSERT INTO product (title, price, description, warranty, discount, discount_date, availability, VID)
                VALUES (:title, :price, :description, :warranty, :discount, :discount_date, :availability, :VID)
            """), {
                'title': TITLE,
                'price': PRICE,
                'description': DESCRIPTION,
                'warranty': WARRANTY,
                'discount': DISCOUNT,
                'discount_date': DISCOUNT_DATE,
                'availability': AVAILABILITY,
                'VID': VID
            })
        
        # conn.commit()
        return render_template('AddProduct.html', message="Added product successfully.", success=True)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('AddProduct.html', message="Product failed to add.", success=False)

