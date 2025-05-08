
from globals import Blueprint,render_template,g,session,Connecttodb,text
from datetime import datetime
from User.chat import chat_bp

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
                *
                FROM vendor
                Where Authorization = 'denied' 
        """)).mappings().fetchall()

        # inventory = conn.execute(text("""
        #     SELECT color, amount
        #     FROM product_inventory
        # """)).mappings().fetchall()

        conn.commit()
        return render_template('PendingAccount.html', UnAuthorizedAdmins=UnAuthorizedAdmins, UnAuthorizedVendor=UnAuthorizedVendor)
    except Exception as e:
        print(f"Error adding product: {e}")
        return render_template('PendingAccount.html')








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
                p.AID, p.image_url, inv_summary.color, inv_summary.amount
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

        return render_template('editProduct.html', AllProducts=AllProducts, CurDate=CurDate, message="Successfully added", success=True)

    except Exception as e:
        print(f"Error: {e}")
        return render_template('editProduct.html', AllProducts=[], CurDate=CurDate, message="Failed to add product.", success=False)
