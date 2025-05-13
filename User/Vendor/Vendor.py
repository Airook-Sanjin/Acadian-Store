
from globals import Blueprint, render_template, request,g,session,Connecttodb,text,checkAndUpdateOrder,CheckOrderDelivered
from datetime import datetime
from User.chat import chat_bp
from globals import redirect, url_for




vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/vendor', template_folder='templates',static_folder='static',static_url_path='/static')

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
                p.category,
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
                p.AID, p.image_url,p.category, inv_summary.color, inv_summary.amount;
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
        CATEGORY = request.form.get("category")
        VID = g.User['ID']
        IMAGE = request.form.get("URL")

        # Handle empty discount, discount_date, and warranty
        DISCOUNT = float(DISCOUNT) / 100 if DISCOUNT else None
        DISCOUNT_DATE = DISCOUNT_DATE if DISCOUNT_DATE else None
        WARRANTY = WARRANTY if WARRANTY else None

        # Insert product into the database
        conn.execute(text("""
            INSERT INTO product (title, price, description, warranty, discount, discount_date, availability, VID, image_url, category)
            VALUES (:title, :price, :description, :warranty, :discount, :discount_date, :availability, :VID, :image_url, :category)
        """), {
            'title': TITLE,
            'price': PRICE,
            'description': DESCRIPTION,
            'warranty': WARRANTY,
            'discount': DISCOUNT,
            'discount_date': DISCOUNT_DATE,
            'availability': AVAILABILITY,
            'category': CATEGORY,
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


    
@vendor_bp.route('/EditInventory', methods=["POST"])
def editInventory():
    try:
        PID = request.form.get("PID")
        IMG_ID = request.form.get("image_ids")
        Color = request.form.get("Color")
        Amount = request.form.get("Amount")

        PID = int(PID)
        
        conn = Connecttodb()
        print(PID)
        is_main = IMG_ID == 'main'

        # Check if inventory exists
        if is_main:
            inventory_exists = conn.execute(text("""
                SELECT 1 FROM product_inventory
                WHERE PID = :pid AND IMG_ID IS NULL AND color = :color
            """), {
                'pid': PID,
                'color': Color
            }).first()
        else:
            inventory_exists = conn.execute(text("""
                SELECT 1 FROM product_inventory
                WHERE PID = :pid AND IMG_ID = :img_id AND color = :color
            """), {
                'pid': PID,
                'img_id': IMG_ID,
                'color': Color
            }).first()

        # Perform update or insert depending on existence
        if inventory_exists:
            if is_main:
                conn.execute(text("""
                    UPDATE product_inventory
                    SET amount = :amount
                    WHERE PID = :pid AND IMG_ID IS NULL AND color = :color
                """), {
                    'pid': PID,
                    'color': Color,
                    'amount': Amount
                })
            else:
                conn.execute(text("""
                    UPDATE product_inventory
                    SET amount = :amount
                    WHERE PID = :pid AND IMG_ID = :img_id AND color = :color
                """), {
                    'pid': PID,
                    'img_id': IMG_ID,
                    'color': Color,
                    'amount': Amount
                })
        else:
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
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Inventory saved successfully", success=True))

    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Failed to save inventory", success=False))




@vendor_bp.route('/AddImages', methods=["POST"])
def AddImages():
    try:
        image_url = request.form.get("image_url")
        pid = request.form.get("PID")

        if not pid or not image_url:
            print(f"Missing product ID or image URL. PID: {pid}, Image URL: {image_url}")
            return redirect(url_for("vendor_bp.VendorViewProducts"))

        conn = Connecttodb()
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
        
        if vid:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.execute(text("DELETE FROM product WHERE PID = :pid and VID = :vid"), {'vid': vid, 'pid': pid})
            conn.execute(text("DELETE FROM product_images WHERE PID = :pid"), {'pid': pid})
            conn.execute(text("DELETE FROM product_inventory WHERE PID = :pid"), {'pid': pid})
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product Deleted successfully", success=True))
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

        # Debugging: print out received data
        print(f"PID: {pid}, Image ID: {img_id}, Image URL: {image_url}")

        # Basic validation
        if not pid or not img_id or not image_url:
            raise ValueError("Missing form data")

        # Make sure img_id is a single number
        if '|' in img_id or '||' in img_id:
            raise ValueError(f"Invalid img_id received: {img_id}")

        conn = Connecttodb()
        conn.execute(text("""UPDATE product_images SET
            image = :image_url
            WHERE PID = :pid AND img_id = :img_id"""), {
            'image_url': image_url,
            'img_id': img_id,
            'pid': pid
        })
        conn.commit()

        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product image updated successfully", success=True))

    except Exception as e:
        print(f"ERROR UPDATING PRODUCT IMAGE: {e}")
        return redirect(url_for('vendor_bp.VendorViewProducts', message="Product image update failed", success=False))


    
@vendor_bp.route('/Profile',methods=["POST"])
def GetProfileInfo():
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))

        return redirect(url_for('vendor_bp.ViewProfile'))
    except Exception as e:
        print(f"Error POST: {e}")
        return redirect(url_for('vendor_bp.ViewProfile'))

@vendor_bp.route('/Shippingitem',methods=['POST'])
def ShipItem():
    try:
        ITEMID = request.form.get('ItemID')
        # updating Cart.ItemStatus
        conn.execute(text("""UPDATE cart 
            SET ItemStatus = 'Shipping',DateShipped = Curdate()
            WHERE item_ID = :ItemID"""),{'ItemID':ITEMID})
        return redirect(request.referrer)
    except Exception as e :
        print(f"ERROR :{e}")
        
        return redirect(request.referrer) or render_template('Vendorprofile.html',customer_data=[],GroupedOrders=[])
        
@vendor_bp.route('/Rejectingitem',methods=['POST'])
def RejectItem():
    try:
        ITEMID = request.form.get('ItemID')
        # updating Cart.ItemStatus
        conn.execute(text("""UPDATE cart 
            SET ItemStatus = 'Rejected'
            WHERE item_ID = :ItemID"""),{'ItemID':ITEMID})
        return redirect(request.referrer)
    except Exception as e :
        print(f"ERROR :{e}")
        
        return redirect(request.referrer) or render_template('Vendorprofile.html',customer_data=[],GroupedOrders=[])

@vendor_bp.route('/Profile',methods=["GET"])
def ViewProfile():
    try:
        conn.commit()
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        checkAndUpdateOrder()
        CheckOrderDelivered()
        customer_data = conn.execute(text("""
            SELECT u.email as Email,u.username as User,u.name as Name FROM users AS u LEFT JOIN vendor as v ON u.email = v.email
            WHERE v.VID = :ID
        """), {'ID': g.User['ID']}).mappings().first()
        
       
        print(session)
        print(g.User)
        
        return render_template('Vendorprofile.html',customer_data=customer_data)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('Vendorprofile.html',customer_data=[])
    
@vendor_bp.route('/RecievedOrder',methods=["POST"])
def GetProfileOrderHistory():
    conn.commit()
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        checkAndUpdateOrder()
        CheckOrderDelivered()
        return redirect(url_for('vendor_bp.VendRecievedOrders'))
    except Exception as e:
        print(f"Error POST: {e}")
        return redirect(url_for('vendor_bp.VendRecievedOrders'))

@vendor_bp.route('/RecievedHistory',methods=["GET"])
def VendRecievedOrders():
    
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        checkAndUpdateOrder()
        CheckOrderDelivered()
        PlacedOrders= conn.execute(text("""
            select o.ORDER_ID as OID,o.total as total, o.status as OrderStatus,o.DateShipped as DateShipped,date(date_add(o.DateShipped, interval 5 DAY)) as DeliveryDate, ca.ITEM_ID as ItemID, p.title as Itemtitle, ca.color as ItemColor,ca.quantity as ItemQuantity,
            CASE
            	WHEN p.discount IS NULL OR p.discount_date > curdate() THEN p.price * ca.quantity
            	WHEN p.discount IS NOT NULL OR p.discount_date < curdate() THEN (p.price - (p.price * p.discount)) * ca.quantity 
            END AS ItemPrice, ca.ItemStatus AS ItemStatus, ca.CID as CustID,Date(ca.DateShipped) as DateShipped, v.email as CustEmail FROM cart AS ca 
            LEFT JOIN orders as o on ca.ORDER_ID = o.ORDER_ID 
            LEFT JOIN product as p on ca.PID =p.PID 
            LEFT JOIN vendor as v on p.VID = v.VID
            LEFT JOIN users as u on v.email = u.email
            WHERE v.VID = :ID and o.ORDER_ID is Not Null
            Order By o.ORDER_ID; """),{'ID': g.User['ID']}).mappings().fetchall()
        GroupedOrders={} #* Dictionary to keep all the values of PlacedOrder
        for row in PlacedOrders:
            OrderId = row['OID'] #* Extracts order ID
            if OrderId not in GroupedOrders:
                GroupedOrders[OrderId]={
                    "OrderId":OrderId,
                    "OrderStatus":row['OrderStatus'],
                    "OrderDateShipped":row['DateShipped'],
                    "OrderTotal":row['total'],
                    "Items":[]
                }
            # * 
            GroupedOrders[OrderId]["Items"].append({
                "ItemID":row['ItemID'],
                "ItemTitle":row['Itemtitle'],
                "ItemColor":row['ItemColor'],
                "ItemQuantity":row['ItemQuantity'],
                "ItemPrice":row['ItemPrice'],
                "ItemStatus":row['ItemStatus'],
                "DateShipped":row['DateShipped']
                
                })
        GroupedOrdersList = list(GroupedOrders.values())
        print(f"Grouped Orders: {GroupedOrdersList}")
            
        
        return render_template('VendRecievedOrders.html', GroupedOrders=GroupedOrdersList)
        
        
    except Exception as e:
        print(f"Error GET: {e}")
        return render_template('VendRecievedOrders.html',GroupedOrders=[])