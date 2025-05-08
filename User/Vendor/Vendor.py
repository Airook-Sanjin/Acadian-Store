
from globals import Blueprint, render_template, request,g,session,Connecttodb,text
from datetime import datetime
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
        return render_template('VendorHomepage.html', products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('VendorHomepage.html', products=[],CurDate=CurDate, inventory=[])

@vendor_bp.route('/AddProduct', methods=["GET"])
def VendorViewProducts():
    try:
        conn = Connecttodb()
        CurDate = datetime.now().date()
        vid = g.User['ID']
        # Fetch all products
        AllProducts = conn.execute(text(""" 
            SELECT 
                p.PID AS product_id,
                p.title,
                CAST(p.price AS DECIMAL(10,2)) AS price,
                (p.price * p.discount) AS saving_discount,
                p.price - (p.price * p.discount) AS discounted_price,
                p.description,
                p.warranty,
                p.discount,
                p.discount_date,
                p.availability,
                p.VID,
                p.AID,
                p.image_url,
                GROUP_CONCAT(DISTINCT pi.image ORDER BY pi.IMG_ID SEPARATOR '|') AS additional_images,
                GROUP_CONCAT(DISTINCT pi.IMG_ID ORDER BY pi.IMG_ID SEPARATOR '|') AS image_ids,
                inv_summary.color,
                inv_summary.amount
            FROM product AS p
            LEFT JOIN product_images AS pi ON p.PID = pi.PID
            LEFT JOIN (
                SELECT  
                    PID,
                    GROUP_CONCAT(DISTINCT color ORDER BY color SEPARATOR '|') AS color,
                    SUM(amount) AS amount
                FROM product_inventory
                GROUP BY PID
            ) AS inv_summary ON p.PID = inv_summary.PID
            WHERE p.VID = :vid
            GROUP BY 
                p.PID, p.title, p.price, p.discount, p.description, 
                p.warranty, p.discount_date, p.availability, p.VID, 
                p.AID, p.image_url, inv_summary.color, inv_summary.amount;
        """),{'vid': vid}).mappings().fetchall()

        AllProducts = [dict(product) for product in AllProducts]

        for product in AllProducts:
            image_urls = product['additional_images'].split('|') if product['additional_images'] else []
            image_ids = product['image_ids'].split('|') if product['image_ids'] else []

            inventory = conn.execute(text("SELECT * FROM product_inventory WHERE PID = :pid"), {
                'pid': product['product_id']
            }).mappings().fetchall()

            product['additional_images'] = list(zip(image_urls, image_ids))
            product['inventory_map'] = {str(row.IMG_ID): {'color': row.color, 'amount': row.amount} for row in inventory if row.IMG_ID}
            product['main_inventory'] = [dict(row) for row in inventory if row.IMG_ID is None]

        return render_template('editProduct.html', AllProducts=AllProducts, CurDate=CurDate, message="Successfully added", success=True)

    except Exception as e:
        print(f"Error: {e}")
        return render_template('editProduct.html', AllProducts=[], CurDate=CurDate, message="Failed to add product.", success=False)
    
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
        VID = g.User['ID']
        IMAGE = request.form.get("URL")

        # Handle empty discount, discount_date, and warranty
        DISCOUNT = float(DISCOUNT) / 100 if DISCOUNT else None
        DISCOUNT_DATE = DISCOUNT_DATE if DISCOUNT_DATE else None
        WARRANTY = WARRANTY if WARRANTY else None

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

        # Redirect to GET route that loads and displays all products
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product added successfully", success=True))
    except Exception as e:
        print(f"ERROR ADDING PRODUCT: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product failed to add", success=False))

@vendor_bp.route('/AddInventory', methods=["POST"])
def AddInventory():
    try:
        PID = request.form.get("PID")
        IMG_ID = request.form.get("image_ids")  # This is 'main' if no IMG_ID
        Color = request.form.get("Color")
        Amount = request.form.get("Amount")

        conn = Connecttodb()

        is_main = IMG_ID == 'main'

        # Check if the inventory already exists
        if is_main:
            inventory_exists = conn.execute(text("""
                SELECT 1 FROM product_inventory
                WHERE PID = :pid AND
                      IMG_ID IS NULL AND
                      color = :color
            """), {
                'pid': PID,
                'color': Color
            }).first()
        else:
            inventory_exists = conn.execute(text("""
                SELECT 1 FROM product_inventory
                WHERE PID = :pid AND
                      IMG_ID = :img_id AND
                      color = :color
            """), {
                'pid': PID,
                'img_id': IMG_ID,
                'color': Color
            }).first()

        if inventory_exists:
            print("Inventory already exists for this image/color combination.")
            return redirect(url_for('vendor_bp.VendorViewProducts', messageinv="Inventory already exists", successinv=False))

        # Insert new inventory
        if is_main:
            conn.execute(text("""
                INSERT INTO product_inventory (PID, color, amount)
                VALUES (:pid, :color, :amount)
            """), {
                'pid': PID,
                'color': Color,
                'amount': Amount
            })
        else:
            conn.execute(text("""
                INSERT INTO product_inventory (PID, IMG_ID, color, amount)
                VALUES (:pid, :img_id, :color, :amount)
            """), {
                'pid': PID,
                'img_id': IMG_ID,
                'color': Color,
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
        conn = Connecttodb()
        image_url = request.form.get("image_url")
        pid = request.form.get("image_PID")

        if not pid or not image_url:
            print("Missing product ID or image URL.")
            return redirect(url_for("vendor_bp.VendorViewProducts"))

        conn.execute(text("""
            INSERT INTO product_images (PID, image) VALUES (:pid, :image)
        """), {"pid": pid, "image": image_url})

        conn.commit()
        print("Image added successfully.")
        return redirect(url_for("vendor_bp.VendorViewProducts"))

    except Exception as e:
        print(f"Error adding image: {e}")
        print("Failed to add image.")
        return redirect(url_for("vendor_bp.VendorViewProducts"))



# ////////////////////////////////////////////////////////////// #
# //                                                          // #
# //                      EDIT PRODUCT                        // #
# //                                                          // #
# ////////////////////////////////////////////////////////////// #

@vendor_bp.route('/editProduct', methods=['POST'])
def VendorEditProduct():
    try:
        pid = request.form.get('PID')
        title = request.form.get('title')
        price = request.form.get('price')
        description = request.form.get('description')
        image_url = request.form.get('URL')
        warranty = request.form.get('warranty') if request.form.get('add_warranty') == 'yes' else None
        discount = float(request.form.get('discount')) / 100 if request.form.get('add_discount') == 'yes' else None
        discount_date = request.form.get('discount_date') if request.form.get('add_discount') == 'yes' else None
        availability = request.form.get('availability')
        vid = request.form.get('VID')

        conn = Connecttodb()
        conn.execute(text("""
            UPDATE product SET
                title = :title,
                price = :price,
                description = :description,
                image_url = :image_url,
                warranty = :warranty,
                discount = :discount,
                discount_date = :discount_date,
                availability = :availability,
                VID = :vid
            WHERE PID = :pid
        """), {
            'title': title,
            'price': price,
            'description': description,
            'image_url': image_url,
            'warranty': warranty,
            'discount': discount,
            'discount_date': discount_date,
            'availability': availability,
            'vid': vid,
            'pid': pid
        })
        conn.commit()
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product updated successfully", success=True))
    except Exception as e:
        print(f"ERROR UPDATING PRODUCT: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product update failed", success=False))
    
    
@vendor_bp.route('/deleteProduct', methods=['POST'])
def VendorDeleteProduct():
    try:
        pid = request.form.get('PID')
        vid = g.User['ID']
        print("######################################")
        print("######################################")
        print('working...', pid, vid)
        print("######################################")
        print("######################################")
        conn = Connecttodb()
        conn.execute(text("""
            DELETE FROM product WHERE PID = :pid and VID = :vid
        """), {
            'vid': vid,
            'pid': pid
        })
        conn.commit()
        return redirect(url_for('admin_bp.VendorViewProducts', message="Product Deleted successfully", success=True))
    except Exception as e:
        print(f"ERROR DELETING PRODUCT: {e}")
        print("######################################")
        print("######################################")
        print('nope...')
        print("######################################")
        print("######################################")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product Delete failed", success=False))


@vendor_bp.route('/editProductImages', methods=['POST'])
def VendorEditProductImages():
    try:
        pid = request.form.get('PID')
        img_id = request.form.get('image_ids')
        image_url = request.form.get('image_url')

        # Basic validation
        if not pid or not img_id or not image_url:
            raise ValueError("Missing form data")

        # Make sure img_id is a single number
        if '|' in img_id or '||' in img_id:
            raise ValueError(f"Invalid img_id received: {img_id}")

        conn = Connecttodb()
        conn.execute(text("""
            UPDATE product_images SET
                image = :image_url
            WHERE PID = :pid AND img_id = :img_id
        """), {
            'image_url': image_url,
            'img_id': img_id,
            'pid': pid
        })
        conn.commit()

        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product image updated successfully", success=True))

    except Exception as e:
        print(f"ERROR UPDATING PRODUCT IMAGE: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product image update failed", success=False))

@vendor_bp.route('/AddInventory', methods=["POST"])
def editInventory():
    try:
        # Get form data
        PID = request.form.get("PID")
        IMG_ID = request.form.get("image_ids")
        Color = request.form.get("Color")
        Amount = request.form.get("Amount")

        # Insert inventory data into the database
        # IMG_ID
        conn = Connecttodb()
        if IMG_ID == 'main':
            conn.execute(text("""
                update INTO product_inventory (PID, color, amount)
                VALUES (:pid, :color, :amount)
            """), {
                'pid': PID,
                'color': Color,
                'amount': Amount
            })
        else:
            conn.execute(text("""
                update INTO product_inventory (PID, IMG_ID ,color, amount)
                VALUES (:pid, :img_id, :color, :amount)
            """), {
                'pid': PID,
                'img_id': IMG_ID,
                'color': Color,
                'amount': Amount
            })
        conn.commit()

        return redirect(url_for('vendor_bp.VendorViewProducts', message="Inventory added successfully", success=True))
    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Failed to add inventory", success=False))