from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text
from flask import make_response
from jinja2 import Environment
from urllib.parse import urlparse,parse_qs,urlencode,urlunparse
cart_bp = Blueprint('cart_bp', __name__, url_prefix='/cart', template_folder='templates')

conn = Connecttodb()


def calculate_total(CartList):
    try:
        return sum(float(item['Price']) for item in CartList if item['Price'] is not None)
    except (TypeError,ValueError) as e:
        print(e)
        return 0
@cart_bp.before_request # Before each request it will look for the values below
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

@cart_bp.route('/<username>',methods=["GET"])
def UserCart(username):
    if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
    try:
        conn.commit() #!Fresh connection
        
        CartList = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.color AS color,p.description as description,p.image_url,ca.quantity as quantity, ca.PID as PID,ca.ORDER_ID,(Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) as Inventory,
                CASE
					WHEN (Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) = 0 THEN 'OUT OF STOCK'
                    WHEN p.discount IS NULL OR p.discount_date < curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL and p.discount_date > curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND (ca.ORDER_ID is Null OR ca.ORDER_ID = 0)"""),{'ID': g.User['ID']}).mappings().fetchall()
        
        if CartList== []:
            return render_template('Cart.html')
        
        print(CartList)#!Debug
        total = calculate_total(CartList)
        
        print(total) #!Debug
       
        item_status = request.args.get('ItemStatus')
        
        return render_template('Cart.html',username=username,ItemStatus=item_status,CartList = CartList,total =total)
    except Exception as e:
        print(f'ERROR: {e}')
        return render_template('Cart.html',username=username,CartList = CartList,total = 0)
    
@cart_bp.route('/<username>', methods=['POST'])
def RemoveFromCart(username):
    try:
       
        ITEMID = request.form.get('RemovedItem') #* Gets Item ID
        
        conn.execute(text(
            """
                DELETE FROM cart WHERE ITEM_ID = :ITEMID"""),{'ITEMID':ITEMID}) #* REMOVES ITEM FROM CART
        conn.commit()
        
        CartList = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.color AS color,p.description as description,p.image_url,ca.quantity as quantity, ca.PID as PID,ca.ORDER_ID,(Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) as Inventory,
                CASE
					WHEN (Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) = 0 THEN 'OUT OF STOCK'
                    WHEN p.discount IS NULL OR p.discount_date < curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL and p.discount_date > curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null """),{'ID': g.User['ID']}).mappings().fetchall() #* Updated Cart List
        
        total = calculate_total(CartList)
        return redirect(request.referrer or url_for('Cart.html',username=username,CartList = CartList,total=total))
    except Exception as e:
        print(f'ERROR: {e}')
        return render_template('Cart.html',username=username,CartList = CartList)
    
@cart_bp.route('/add',methods=['POST'])
def addToCart():
    if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
    try:
        
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
            """)).mappings().first()  # ✅ changed from .first() to .fetchall()
        
        inventory = conn.execute(text("""
            SELECT color, amount FROM product_inventory
            """)).mappings().fetchall()#! Needed to then get the PID
        
        EMAIL = g.User['Email']
        ID = g.User['ID']
        PID = int(request.args.get('PID'))
        COLOR = request.form.get('Color')
        Matchingitem =conn.execute(text("""
                SELECT ca.ITEM_ID AS itemid, ca.color AS color,ca.quantity as quantity,ca.PID as PID,ca.ORDER_ID,(Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) as Inventory
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID 
                WHERE ca.CID = :ID AND ca.color = :color and ca.PID = :PID AND ca.ORDER_ID is Null"""),{'ID': g.User['ID'],'color':COLOR,'PID':PID}).mappings().fetchall()
        
        if Matchingitem:
            if Matchingitem[0]['quantity'] <= Matchingitem[0]['Inventory']:
                print('Updating')
            
                newQuantity = Matchingitem[0]['quantity'] +1
                print(newQuantity)
                conn.execute(text("""
                      UPDATE cart
                      SET quantity =:quantity
                      Where item_ID = :item_id"""),{'quantity':newQuantity,'item_id':Matchingitem[0]['itemid']})
                conn.commit()
            else:
                # !-----------------------------------------------
                # ! HAD TO LOOK THIS UP!
                # * THIS IS MY LIFE SAVER. request.referrer gets the URL of the page that MADE the request!!!!
                if request.referrer:   #* this is just so I can add a variable to the request.referrer
                    parsed = urlparse(request.referrer)
                    params = parse_qs(parsed.query)
                    params['status']= ["Can't add anymore"] #* adds new parameter
                    #* recreates url with the new parameters
                    newQuery = urlencode(params, doseq=True)
                    newURL = parsed._replace(query=newQuery).geturl()
                    return redirect(newURL)
                # !---------------------------------------------
        else:
            conn.execute(text(
            """
            INSERT INTO cart 
            (title,color,email,PID,CID)
            VALUES
            (:title,:color,:email,:PID,:CID)"""),
            {'title':request.form.get('Title'),'color':COLOR,'email':EMAIL,'PID':PID,'CID':ID})
            print('ITEMADDED')
    
        conn.commit()
        product = conn.execute(text("""
             SELECT 
                PID, title, CAST(price AS DECIMAL(10,2)) AS Price,
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
        """), {"pid": PID}).mappings().first()
        
        inventory = conn.execute(text("""
            SELECT color, amount
            FROM product_inventory
            WHERE PID = :pid
        """), {"pid": PID}).mappings().fetchall()

        images = conn.execute(text("""
            SELECT image
            FROM product_images
            WHERE PID = :pid
        """), {"pid": PID}).mappings().fetchall()
            
        print('INTO Customer')
        return redirect(request.referrer or url_for('ProductView',products=product, inventory=inventory,images=images, username=g.User['Name'])) # * Takes you to Product page
        
    except Exception as e:
        print(f'ERROR: {e}')
        return redirect(url_for('start'))
@cart_bp.route('/quantity-update/<username>', methods=["POST"])
def quantityUpdate(username):
    try:
        ITEMID = request.form.get('UpdatedItem')
        UPDATEDITEMPID= request.form.get('UpdatedItemPID')
        UPDATEDITEMCOLOR = request.form.get('UpdatedItemColor')
        ITEMQUANTITY = request.form.get('ItemQuantity')
        print('Updating')
        conn.execute(text("""
                      Update cart
                        set quantity = Case
                        WHEN quantity <= (Select amount from product_inventory WHERE PID = :PID and color = :color ) 
                        THEN :quantity
                        ELSE  quantity
                        END
                        Where item_ID = :item_id;
                      """),{'quantity':ITEMQUANTITY,'item_id':ITEMID,'PID':UPDATEDITEMPID,'color':UPDATEDITEMCOLOR})
        print(f"UPDATED ITEM ID:{ITEMID}\nNEW QUANTITY:{ITEMQUANTITY}\nUPDATEDITEMPID: {UPDATEDITEMPID}\nUPDATED ITEM COLOR: {UPDATEDITEMCOLOR}")
        conn.commit()
        
        # !-----------------------------------------------
        # ! HAD TO LOOK THIS UP!
        # * THIS IS MY LIFE SAVER. request.referrer gets the URL of the page that MADE the request!!!!
        if request.referrer:   #* this is just so I can add a variable to the request.referrer
            parsed = urlparse(request.referrer)
            params = parse_qs(parsed.query)
            params['status']= ['success'] #* adds new parameter
            #* recreates url with the new parameters
            newQuery = urlencode(params, doseq=True)
            newURL = parsed._replace(query=newQuery).geturl()
            return redirect(newURL)
        # !---------------------------------------------
        return redirect(url_for('ProductView',username=g.User['Name'])) 
    except Exception as e:
        print(f'Error: {e}')
@cart_bp.route('/checkout/<username>')
def GotoCheckout(username):
    try:
        print(session)
        # ?Should I have an autofill for card info?
        # userinfo = conn.execute(text("""
        #             Select """))
        CartList = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.color AS color,LEFT(p.description, 18) as description,p.image_url,ca.quantity as quantity, ca.PID as PID,ca.ORDER_ID,(Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) as Inventory,
                CASE
					WHEN (Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) = 0 THEN 'OUT OF STOCK'
                    WHEN p.discount IS NULL OR p.discount_date < curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date > curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null"""),{'ID': g.User['ID']}).mappings().fetchall()
        
        listofItemStock = tuple([item['Price'] for item in CartList])
        print(listofItemStock)
        if 'OUT OF STOCK' in listofItemStock:
            # !-----------------------------------------------
            # ! HAD TO LOOK THIS UP!
            # * THIS IS MY LIFE SAVER. request.referrer gets the URL of the page that MADE the request!!!!
            if request.referrer:   #* this is just so I can add a variable to the request.referrer
                parsed = urlparse(request.referrer)
                base_url = url_for('cart_bp.UserCart', username = g.User["Name"])
                params={'ItemStatus':["OUT OF STOCK"]} #* adds new parameter
                #* recreates url with the new parameters
                newQuery = urlencode(params, doseq=True)
                # newURL = parsed._replace(query=newQuery).geturl()
                return redirect(f"{base_url}?{newQuery}")
            # !---------------------------------------------
        print (CartList)
        total = calculate_total(CartList)
            
        print(total)
        return render_template('Checkout.html',username=username,CartList = CartList,total=total)
    except:
        return render_template('Checkout.html',username=username)