from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text
from flask import make_response
cart_bp = Blueprint('cart_bp', __name__, url_prefix='/cart', template_folder='templates')

conn = Connecttodb()

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
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color,p.description as description,p.image_url,ca.quantity as quantity, ca.PID as PID,ca.ORDER_ID,
                CASE
                    WHEN p.discount IS NULL OR p.discount_date > curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date < curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND (ca.ORDER_ID is Null OR ca.ORDER_ID = 0)"""),{'ID': g.User['ID']}).mappings().fetchall()
        
        if CartList== []:
            return render_template('EmptyCart.html')
        
        total = 0
        
        print(CartList)#!Debug
        for item in CartList:
            total+=float(item['Price'])
            print(item)#!Debug
            print (f'PIDs:{item['PID'],item['size'],item['color']}')
            
        print(total) #!Debug
        return render_template('Cart.html',username=username,CartList = CartList,total =total)
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
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color,p.description as description,p.image_url,ca.quantity as quantity,ca.ORDER_ID,
                CASE
                    WHEN p.discount IS NULL OR p.discount_date > curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date < curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null """),{'ID': g.User['ID']}).mappings().fetchall() #* Updated Cart List
        
        total = 0
        for item in CartList:
            total+=float(item['Price'])
            
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
            SELECT size, color, amount FROM product_inventory
            """)).mappings().fetchall()#! Needed to then get the PID
        
        EMAIL = g.User['Email']
        ID = g.User['ID']
        PID = int(request.args.get('PID'))
        SIZE = request.form.get('Size')
        COLOR = request.form.get('Color')
        Matchingitem =conn.execute(text("""
                SELECT ca.ITEM_ID AS itemid,ca.size AS size, ca.color AS color,ca.quantity as quantity,ca.PID as PID,ca.ORDER_ID
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.size = :size AND ca.color = :color and ca.PID = :PID AND ca.ORDER_ID is Null"""),{'ID': g.User['ID'],'size':SIZE,'color':COLOR,'PID':PID}).mappings().fetchall()
        print(Matchingitem)
        if Matchingitem:
            print('Updating')
            
            newQuantity = Matchingitem[0]['quantity'] +1
            print(newQuantity)
            conn.execute(text("""
                      UPDATE cart
                      SET quantity =:quantity
                      Where item_ID = :item_id"""),{'quantity':newQuantity,'item_id':Matchingitem[0]['itemid']})
            conn.commit()
            
        else:
            conn.execute(text(
            """
            INSERT INTO cart 
            (title,size,color,email,PID,CID)
            VALUES
            (:title,:size,:color,:email,:PID,:CID)"""),
            {'title':request.form.get('Title'),'size':SIZE,'color':COLOR,'email':EMAIL,'PID':PID,'CID':ID})
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
            SELECT size, color, amount
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
        print('Updating')
        conn.execute(text("""
                      UPDATE cart
                      SET quantity =:quantity
                      Where item_ID = :item_id"""),{'quantity':request.form.get('quantity'),'item_id':request.form.get('UpdatedItem')})
        conn.commit()
        
        return redirect(request.referrer) # * THIS IS MY LIFE SAVER. request.referrer gets the URL of the page that MADE the request!!!!
    except Exception as e:
        print(f'Error: {e}')
@cart_bp.route('/checkout/<username>')
def GotoCheckout(username):
    try:
        # ?Should I have an autofill for card info?
        # userinfo = conn.execute(text("""
        #             Select """))
        CartList = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color,p.description as description,p.image_url,ca.quantity as quantity,ca.ORDER_ID,
                CASE
                    WHEN p.discount IS NULL OR p.discount_date > curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date < curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null"""),{'ID': g.User['ID']}).mappings().fetchall()
        print (CartList)
        total = 0
        for item in CartList:
            total+=float(item['Price'])
            
        print(total)
        return render_template('Checkout.html',username=username,CartList = CartList,total=total)
    except:
        return render_template('Checkout.html',username=username)