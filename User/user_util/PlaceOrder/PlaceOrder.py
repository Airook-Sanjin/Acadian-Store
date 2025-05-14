from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text,CheckOrderDelivered,checkAndUpdateOrder
from datetime import datetime

OrderPlace_bp = Blueprint('OrderPlace_bp', __name__, url_prefix='/order', template_folder='templates')



@OrderPlace_bp.before_request # Before each request it will look for the values below
def load_user():
   
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None

@OrderPlace_bp.route('/OrderPlaced', methods=["POST"])
def placeOrder():
    conn=None
    try:
        conn = Connecttodb()
        conn.begin()
        
        checkAndUpdateOrder()
        CheckOrderDelivered()
        
        
        
        total = request.form.get('Total')
        
        CurTime = datetime.now()
        print(str(CurTime)[0:19])
        # * Get ItemIDs without an ORDER_ID
        ItemIDTable = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.color AS color,p.description as description,p.image_url,p.VID as VID,ca.quantity as quantity, ca.PID as PID,ca.ORDER_ID,(Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) as Inventory,
                CASE
					WHEN (Select amount from product_inventory WHERE PID = ca.PID and color = ca.color ) = 0 THEN 'OUT OF STOCK'
                    WHEN p.discount IS NULL OR p.discount_date > curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date < curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
	            FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
	            WHERE ca.CID = :ID AND (ca.ORDER_ID is Null or ca.ORDER_ID = 0) """),{'ID': g.User['ID']}).mappings().fetchall()
        listofitemid = tuple([item['itemid'] for item in ItemIDTable])
        
        print(listofitemid)
        # * Get Count of cart items
        CartQuantity = conn.execute(text("""
            SELECT COALESCE(SUM(quantity), 0) as CartQuantity
            FROM cart
            WHERE CID = :ID 
            AND ORDER_ID IS NULL
        """), {'ID': g.User['ID']}).mappings().fetchone()
    
        if not CartQuantity or CartQuantity['CartQuantity'] == 0:
            raise ValueError("Cart is empty")
        
        ADDRESS = request.form.get('Address1')
        CITY= request.form.get('City')
        STATE = request.form.get('State')
        ZIP = request.form.get('ZIP')
        EMAIL = request.form.get('Email')
        
        if not all([ADDRESS, CITY, STATE, ZIP, total]):
            raise ValueError("Missing required fields")
        # print(CartQuantity['CartQuantity'])
        # print(CartQuantity) #!DEBUG
        
        # * Creates new OrderID
        conn.execute(text("""
                INSERT INTO orders
	                (date,total,amount,ContactInfo)
                VALUES
	                (now(),:total, :quantity,:ContactInfo);"""),{'total':total,'quantity':int(CartQuantity['CartQuantity']),'ContactInfo':f'{ADDRESS},{CITY},{STATE},{ZIP}'})
        
        # * Gets Recent OrderID
        RecentOrder=conn.execute(text("""
                SELECT max(ORDER_ID) as ID from orders""")).mappings().fetchone()
        
        conn.commit()
        #* Sends money to the proper Vendor
        for item in list(ItemIDTable):
            # conn.execute(text("""
            #     Update vendor set balance = balance + :Price
            #     Where VID = :VID"""),{'VID':item['VID'],'Price':item['Price']})
            
             # * UPDATES PRODUCT INV
        
            conn.execute(text("""
            update product_inventory
            SET amount = amount - :quantity
            WHERE PID = :pid AND color = :color """),{'quantity':item['quantity'],'pid':item['PID'],'color': item['color']})
        
        # * Updates Cart items
        conn.execute(text("""
                Update cart
                set ORDER_ID = :recent
                Where CID = :cid AND (ORDER_ID IS NULL OR ORDER_ID = 0) AND ITEM_ID in :itemids;"""),
                {'cid':g.User['ID'],'itemids':listofitemid,'recent':RecentOrder['ID']}) # Sets ORDER ID to the correct items
        conn.commit()
        
       
        session['recentOrderId'] = RecentOrder['ID']
        print(session['recentOrderId'])
        return redirect(url_for('OrderPlace_bp.ShowOrder'))
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error: {e}')
        return redirect(url_for('OrderPlace_bp.ShowOrder'))
    finally:
        if conn:
            conn.close()
@OrderPlace_bp.route('/OrderPlaced', methods=["GET"])
def ShowOrder():
    conn=None
    try:
        conn = Connecttodb()
        conn.begin()
        
        checkAndUpdateOrder()
        CheckOrderDelivered()
        ADDRESS = request.form.get('Address1')
        CITY= request.form.get('City')
        STATE = request.form.get('State')
        ZIP = request.form.get('ZIP')
        EMAIL = request.form.get('Email')
       
        query = """SELECT ca.title AS ItemTitle,p.PID as PID,
            CASE
                WHEN p.discount IS NULL OR p.discount_date < curdate() THEN p.price * ca.quantity
	            WHEN p.discount IS NOT NULL OR p.discount_date > curdate() THEN (p.price - (p.price * p.discount)) * ca.quantity 
            END AS ItemPrice,
            p.image_url as ItemImage,date(ca.DateShipped) as DateShipped,ca.ItemStatus as ItemStatus, ca.email as CustEmail,ca.quantity AS ItemQuantity, o.ORDER_ID AS ORDERID, o.date AS DatePlaced,DATE(o.date) as DatePlaced,date(date_add(ca.DateShipped, interval 5 DAY)) as DeliveryDate,
            o.status AS Status,o.ContactInfo as ContactInfo, o.amount AS OrderQuantity,o.total as Total from orders AS o 
            INNER JOIN cart AS ca ON o.ORDER_ID = ca.ORDER_ID
            LEFT JOIN product AS p ON ca.PID = p.PID"""
            
        recentOrder = session.get('recentOrderId')
        OID = request.args.get('ORDER_ID')
        print(f"RECENT : {recentOrder}")
        print(f'OID: {OID}')
        
        if recentOrder and not OID :
            query +=" WHERE ca.ORDER_ID = :recent"
            params = {'recent':recentOrder}
            print("RECENT OID")
        else:
            query+= " WHERE ca.ORDER_ID = :OID"
            params = {'OID':OID}
            print("REG OID")
        #* ORDER HISTORY
        OrderHistory = conn.execute(text(query),params).mappings().fetchall() #! Change this back to :recent
        conn.commit()
        return render_template('OrderPlaced.html',OrderHistory= OrderHistory)
    except Exception as e:
        if conn:
            conn.rollback()
        print(f'Error: {e}')
        return render_template('OrderPlaced.html', OrderHistory=[])
    finally:
        if conn:
            conn.close()