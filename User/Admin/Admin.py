
from globals import Blueprint,render_template,g,session,Connecttodb,text,request,checkAndUpdateOrder
from datetime import datetime
from User.chat import chat_bp
from threading import Timer
from globals import redirect, url_for

admin_bp=Blueprint('admin_bp',__name__, url_prefix='/admin',template_folder='templates',static_folder='static',static_url_path='/static') # * init blueprint
admin_bp.register_blueprint(chat_bp)
conn= Connecttodb()
@admin_bp.before_request # Before each request it will look for the values below
def load_user():
   
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None


@admin_bp.route('/Home')
def AdminHomePage():
    try:
        checkAndUpdateOrder()
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
        return render_template('AdminHomepage.html', products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        print(f"Error adding product: {e}")

        return render_template('AdminHomepage.html', products=[],CurDate=CurDate, inventory=[])
    
    
# /////////////////////////////////////////////////////// #
# //                                                   // #
# //                      ADMIN                        // #
# //                                                   // #
# /////////////////////////////////////////////////////// #
@admin_bp.route('/AdminView', methods=["GET"])
def AdminViewAccounts():
    try:
        UnAuthorizedAdmins = conn.execute(text("""
           SELECT  
                a.*,  
                u.* 
            FROM admin AS a  
            LEFT JOIN users AS u ON a.email = u.email  
            WHERE a.Authorization = 'denied';
        """)).mappings().fetchall()
        
        UnAuthorizedVendor = conn.execute(text("""
           SELECT  
                v.*,  
                u.* 
            FROM vendor AS v  
            LEFT JOIN users AS u ON v.email = u.email  
            WHERE v.Authorization = 'denied';
        """)).mappings().fetchall()

        conn.commit()
        return render_template('PendingAccount.html', UnAuthorizedAdmins=UnAuthorizedAdmins, UnAuthorizedVendor=UnAuthorizedVendor)
    except Exception as e:
        print(f"Error viewing accounts: {e}")
        return render_template('PendingAccount.html')
    
@admin_bp.route('/AdminView', methods=["POST"])
def AdminChangeAccountsAuth():
    try:
        conn = Connecttodb()
        VID = request.form.get("VID")
        AID = request.form.get("AID")
        if VID:
            print(VID)
            changeVendorAuth = conn.execute(text("""
               Update vendor 
               SET Authorization = 'granted' 
               WHERE VID = :VID;
            """),{'VID':VID}) 
        if AID:
            print(AID)
            changeAdminAuth = conn.execute(text("""
               Update admin 
               SET Authorization = 'granted' 
               WHERE AID = :AID;
            """),{'AID':AID})
        conn.commit()
        return redirect(url_for('admin_bp.AdminViewAccounts'))
    except Exception as e:
        print(f"Error Authorizing account: {e}")
        return redirect(url_for('admin_bp.AdminViewAccounts'))

# //////////////////////////////////////////////////////////////// #
# //                                                            // #
# //                      VENDOR PRODUCT                        // #
# //                                                            // #
# //////////////////////////////////////////////////////////////// #
@admin_bp.route('/AddProduct', methods=["GET"])
def AdminViewProducts():
    try:
        conn = Connecttodb()
        CurDate = datetime.now().date()
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
            GROUP BY 
                p.PID, p.title, p.price, p.discount, p.description, 
                p.warranty, p.discount_date, p.availability, p.VID, 
                p.AID, p.image_url, p.category,inv_summary.color, inv_summary.amount
        """)).mappings().fetchall()

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

        return render_template('AdminEditProduct.html', AllProducts=AllProducts, CurDate=CurDate, message="Successfully added", success=True)

    except Exception as e:
        print(f"Error: {e}")
        return render_template('AdminEditProduct.html', AllProducts=[], CurDate=CurDate, message="Failed to add product.", success=False)
    
@admin_bp.route('/AddProduct', methods=["POST"])
def AdminAddProduct():
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
        AID = g.User['ID']
        IMAGE = request.form.get("URL")
        CATEGORY = request.form.get("category")
        COLOR = request.form.get('Color')
        AMOUNT = request.form.get('Amount')

        # Handle empty discount, discount_date, and warranty
        DISCOUNT = float(DISCOUNT) / 100 if DISCOUNT else None
        DISCOUNT_DATE = DISCOUNT_DATE if DISCOUNT_DATE else None
        WARRANTY = WARRANTY if WARRANTY else None

        conn.execute(text("""
            INSERT INTO product (title, price, description, warranty, discount, discount_date, availability, AID, image_url, category)
            VALUES (:title, :price, :description, :warranty, :discount, :discount_date, :availability, :AID, :image_url, :category)
        """), {
            'title': TITLE,
            'price': PRICE,
            'description': DESCRIPTION,
            'warranty': WARRANTY,
            'discount': DISCOUNT,
            'discount_date': DISCOUNT_DATE,
            'availability': AVAILABILITY,
            'AID': AID,
            'image_url': IMAGE,
            'category': CATEGORY
        })

        PID = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        conn.execute(text("""
            INSERT INTO product_inventory (color, amount, PID)
            VALUES (:color, :amount, :PID)
        """), {
            'color': COLOR,
            'amount': AMOUNT,
            'PID': PID
        })

        conn.commit()

        return redirect(url_for('admin_bp.AdminViewProducts', message="Product added successfully", success=True))
    except Exception as e:
        print(f"ERROR ADDING PRODUCT: {e}")
        return redirect(url_for('admin_bp.AdminViewProducts', message="Product failed to add", success=False))

@admin_bp.route('/editProduct', methods=['POST'])
def AdminEditProduct():
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
        return redirect(url_for('admin_bp.AdminViewProducts', message="Product updated successfully", success=True))
    except Exception as e:
        print(f"ERROR UPDATING PRODUCT: {e}")
        return redirect(url_for('admin_bp.AdminViewProducts', message="Product update failed", success=False))

@admin_bp.route('/EditInventory', methods=["POST"])
def AdminEditInventory():
    try:
        PID = request.form.get("PID")
        IMG_ID = request.form.get("image_ids")
        Color = request.form.get("Color")
        Amount = request.form.get("Amount")

        conn = Connecttodb()

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
        return redirect(url_for('admin_bp.AdminViewProducts', message="Inventory saved successfully", success=True))
    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('admin_bp.AdminViewProducts', message="Failed to save inventory", success=False))

@admin_bp.route('/deleteProduct', methods=['POST'])
def AdminDeleteProduct():
    try:
        pid = request.form.get('PID')
        print("######################################")
        print("######################################")
        print('working...', pid)
        print("######################################")
        print("######################################")

        conn = Connecttodb()

        # Disable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Perform deletions
        conn.execute(text("DELETE FROM product_inventory WHERE PID = :pid"), {'pid': pid})
        conn.execute(text("DELETE FROM product_images WHERE PID = :pid"), {'pid': pid})
        conn.execute(text("DELETE FROM product WHERE PID = :pid"), {'pid': pid})

        # Re-enable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        conn.commit()

        return redirect(url_for('admin_bp.AdminViewProducts', message="Product deleted successfully", success=True))

    except Exception as e:
        print(f"ERROR DELETING PRODUCT: {e}")
        print("######################################")
        print("######################################")
        print('nope...')
        print("######################################")
        print("######################################")
        return redirect(url_for('admin_bp.AdminViewProducts', message="Product delete failed", success=False))


@admin_bp.route('/AddImages', methods=["POST"])
def AdminAddImages():
    try:
        image_url = request.form.get("image_url")
        pid = request.form.get("PID")

        if not pid or not image_url:
            print(f"Missing product ID or image URL. PID: {pid}, Image URL: {image_url}")
            return redirect(url_for("vendor_bp.AdminViewProducts"))

        conn = Connecttodb()
        conn.execute(text(""" 
            INSERT INTO product_images (PID, image) VALUES (:pid, :image)
        """), {"pid": pid, "image": image_url})

        conn.commit()
        print("Image added successfully.")
        return redirect(url_for("admin_bp.AdminViewProducts"))

    except Exception as e:
        print(f"Error adding image: {e}")
        print("Failed to add image.")
        return redirect(url_for("admin_bp.AdminViewProducts"))

@admin_bp.route('/editProductImages', methods=['POST'])
def AdminEditProductImages():
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

        return redirect(url_for('admin_bp.AdminViewProducts', message="Product image updated successfully", success=True))

    except Exception as e:
        print(f"ERROR UPDATING PRODUCT IMAGE: {e}")
        return redirect(url_for('admin_bp.AdminViewProducts', message="Product image update failed", success=False))
    
@admin_bp.route('/Profile',methods=["GET","POST"])
def GetProfileInfo():
    try:
        customer_data = conn.execute(text("""
            SELECT u.email as Email,u.username as User,u.name as Name FROM users AS u LEFT JOIN admin as a ON u.email = a.email
            WHERE a.AID = :ID
        """), {'ID': g.User['ID']}).mappings().first()
        
        return render_template("Adminprofile.html", customer_data=customer_data)
    except Exception as e:
        print(f"Error: {e}")
        return render_template("Adminprofile.html",customer_data=customer_data)


@admin_bp.route('/ClaimHistory', methods=["GET"])
def claimHistory():
    print("ViewProfile route hit!")

    request_type = request.args.get("type")  # 'return', 'refund', 'warranty'

    try:
        result = conn.execute(text("SELECT * FROM chatroom_admin")).mappings()
        chatroom = [dict(row) for row in result]

        # Deduplicate
        seen_chat_ids = set()
        unique_chatroom = []
        for request_row in chatroom:
            if request_row["CHAT_ID"] not in seen_chat_ids:
                seen_chat_ids.add(request_row["CHAT_ID"])
                unique_chatroom.append(request_row)
                
        if request_type == "return":
            unique_chatroom = [r for r in unique_chatroom if r.get("returns") == "YES"]
        elif request_type == "refund":
            unique_chatroom = [r for r in unique_chatroom if r.get("refund") == "YES"]
        elif request_type == "warranty":
            unique_chatroom = [r for r in unique_chatroom if r.get("warranty_claim") == "YES"]

        print("Filtered Chatroom Length:", len(unique_chatroom))

        return render_template("Adminclaims.html", chatroom=unique_chatroom)
    
    except Exception as e:
        print("Error fetching data:", e)
        return render_template("Adminclaims.html", chatroom=[])

def update_status(chat_id, status):
    try:
        conn.execute(text("""
            UPDATE chatroom_admin
            SET request_status = :status
            WHERE CHAT_ID = :chat_id
        """), {"status": status, "chat_id": chat_id})
        conn.commit()
    except Exception as e:
        print(f"Error updating to {status}:", e)

@admin_bp.route('/UpdateClaimStatus', methods=["POST"])
def updateClaimStatus():
    chat_id = request.form.get("chat_id")
    new_status = request.form.get("status")
    # Status flow: pending -> rejected/confirmed -> processing -> complete

    try:
        # Step 1: Update to confirmed or rejected
        conn.execute(text("""
            UPDATE chatroom_admin
            SET request_status = :new_status
            WHERE CHAT_ID = :chat_id
        """), {"new_status": new_status, "chat_id": chat_id})
        conn.commit()

        # Step 2: If confirmed, schedule automatic transitions
        if new_status == "confirmed":
            Timer(180, update_status, args=(chat_id, "processing")).start()  # processing after 3 mins = 180 both start at the same time
            Timer(360, update_status, args=(chat_id, "complete")).start()   # complete after 6 mins = 360


    except Exception as e:
        print("Error updating status:", e)

    return redirect(url_for('admin_bp.claimHistory'))





    