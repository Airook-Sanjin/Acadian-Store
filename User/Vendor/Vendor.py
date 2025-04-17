
from flask import Blueprint, render_template, request,g,session
from dbconnect import Connecttodb  # Import the updated Connecttodb function
from sqlalchemy import text
from globals import redirect, url_for


vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vendor', template_folder='templates')
@vendor_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
# @vendor_bp.route('/Home', methods=["GET"])
# def VendorHomePage():
#     return render_template('VendorHomepage.html')

###########################################################
# IF YOU DO NOT SEE IN DATABASE BECAUSE I HAVE NO COMMITS #
###########################################################

@vendor_bp.route('/AddProduct', methods=["GET"])
def VendorViewProducts():
    try:
        # Get database connection
        conn = Connecttodb()

        # Fetch all products to display
        AllProducts = conn.execute(text("SELECT * FROM product")).fetchall()
        print(AllProducts)  # Debugging: Print the fetched products

        return render_template('VendorHomepage.html', AllProducts=AllProducts, message="Successfully added", success=True)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('VendorHomepage.html', AllProducts=[], message="Failed to add product.", success=False)
    
@vendor_bp.route('/AddProduct', methods=["POST"])
def VendorAddProduct():
    try:
        # Get database connection
        conn = Connecttodb()

        # Get form data
        TITLE = request.form.get("title")
        PRICE = request.form.get("price")
        DESCRIPTION = request.form.get("description")
        WARRANTY = request.form.get("warranty")
        DISCOUNT = request.form.get("discount")
        DISCOUNT_DATE = request.form.get("discount_date")
        AVAILABILITY = request.form.get("availability")
        VID = request.form.get("VID")
        IMAGE = request.form.get("URL")

        # Handle empty discount and discount_date
        DISCOUNT = DISCOUNT if DISCOUNT else None
        DISCOUNT_DATE = DISCOUNT_DATE if DISCOUNT_DATE else None

        # Insert product into the database
        conn.execute(text("""
            INSERT INTO product (title, price, description, warranty, discount, discount_date, availability, VID, image_url)
            VALUES (:title, :price, :description, :warranty, :discount, :discount_date, :availability, :VID, :image_url)
        """), {
            'title': TITLE,
            'price': PRICE,
            'description': DESCRIPTION,
            'warranty': WARRANTY,
            'discount': DISCOUNT,
            'discount_date': DISCOUNT_DATE,
            'availability': AVAILABILITY,
            'VID': VID,
            'image_url': IMAGE
        })

        # Commit the changes to the database
        # conn.commit()

        # Redirect to the ViewProducts route to display the updated product list
        return redirect(url_for('login_bp.vendor_bp.VendorAddProduct', success=True))
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('login_bp.vendor_bp.VendorAddProduct', success=False))