
from globals import Blueprint, render_template, request,g,session,Connecttodb,text

from User.chat import chat_bp
from globals import redirect, url_for


vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vendor', template_folder='templates')

vendor_bp.register_blueprint(chat_bp)

# Get database connection
conn = Connecttodb()


@vendor_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@vendor_bp.route('/Home', methods=["GET"])
def VendorHomePage():
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

###########################################################
# IF YOU DO NOT SEE IN DATABASE BECAUSE I HAVE NO COMMITS #
###########################################################

@vendor_bp.route('/AddProduct', methods=["GET"])
def VendorViewProducts():
    try:
        # Get database connection
        conn = Connecttodb()

        # Fetch all products to display
        AllProducts = conn.execute(text("""SELECT 
                                PID,
                                title,
                                CAST(price AS DECIMAL(10,2)) AS price,
                                (price * discount) as saving_discount,
                                price - (price * discount) AS discounted_price,
                                description,
                                warranty,
                                discount,
                                discount_date,
                                availability,
                                VID,
                                AID,
                                image_url
                            FROM product 
                            """)).fetchall()
        # print(AllProducts)  # Debugging: Print the fetched products

        return render_template('AddProduct.html', AllProducts=AllProducts, message="Successfully added", success=True)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('AddProduct.html', AllProducts=[], message="Failed to add product.", success=False)
    
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

        DISCOUNT = float(DISCOUNT)/100
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
        conn.commit()
        return render_template('AddProduct.html', message="Added product successfully.", success=True)
    except Exception as e:
        print(f"ERROR ADDING PRODUCT: {e}")
        return render_template('AddProduct.html', message="Product failed to add.", success=False)

###########################################################
# IF YOU DO NOT SEE IN DATABASE BECAUSE I HAVE NO COMMITS #
###########################################################
@vendor_bp.route('/AddInventory', methods=["POST"])
def AddInventory():
    try:
        # Get form data
        PID = request.form.get("PID")
        Color = request.form.get("Color")
        Size = request.form.get("Size")
        Amount = request.form.get("Amount")

        # Insert inventory data into the database
        conn = Connecttodb()
        conn.execute(text("""
            INSERT INTO product_inventory (PID, color, size, amount)
            VALUES (:product_id, :color, :size, :amount)
        """), {
            'product_id': PID,
            'color': Color,
            'size': Size,
            'amount': Amount
        })
        conn.commit()

        return redirect(url_for('vendor_bp.VendorViewProducts', message="Inventory added successfully", success=True))
    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Failed to add inventory", success=False))
    
@vendor_bp.route('/AddImages', methods=["POST"])
def AddImages():
    try:
        PID = request.form.get("PID")
        image_url = request.form.get("image_url")

        conn = Connecttodb()
        conn.execute(text("""
            INSERT INTO product_images (PID, image)
            VALUES (:product_id, :image)
        """), {
            'product_id': PID,
            'image': image_url
        })
        conn.commit()
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Image added successfully", success=True))

    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Failed to add image", success=False))
