from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text
from datetime import datetime

OrderPlace_bp = Blueprint('OrderPlace_bp', __name__, url_prefix='/order', template_folder='templates')

conn = Connecttodb()

@OrderPlace_bp.before_request # Before each request it will look for the values below
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

@OrderPlace_bp.route('/OrderPlaced', methods=["POST"])
def placeOrder():
    try:
        total = request.form.get('Total')
        
        CurTime = datetime.now()
        print(str(CurTime)[0:19])
        # * Get ItemIDs without an ORDER_ID
        ItemIDTable = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid,p.VID as VID,ca.ORDER_ID as OrderID,
                CASE
                    WHEN p.discount IS NULL OR p.discount_date > curdate() then p.price * ca.quantity
	                WHEN p.discount IS NOT NULL OR p.discount_date < curdate() then (p.price - (p.price * p.discount)) * ca.quantity 
                END as Price
	            FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
	            WHERE ca.CID = :ID AND (ca.ORDER_ID is Null or ca.ORDER_ID = 0) """),{'ID': g.User['ID']}).mappings().fetchall()
        listofitemid = tuple([item['itemid'] for item in ItemIDTable])
        print(listofitemid)
        # * Get Count of cart items
        CartQuantity = conn.execute(text(
            """
                SELECT sum(ca.quantity) as CartQuantity, ca.ORDER_ID as OrderID 
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null
                Group By ca.ORDER_ID"""),{'ID': g.User['ID']}).mappings().fetchone()
    
        # print(CartQuantity['CartQuantity'])
        # print(CartQuantity) #!DEBUG
        
        # * Creates new OrderID
        conn.execute(text("""
                INSERT INTO orders
	                (date,total,amount)
                VALUES
	                (now(),:total, :quantity);"""),{'total':total,'quantity':int(CartQuantity['CartQuantity'])})
        conn.commit()
        # * Gets Recent OrderID
        RecentOrder=conn.execute(text("""
                SELECT max(ORDER_ID) as ID from orders""")).mappings().fetchone()
        
        conn.commit()
        #* Sends money to the proper Vendor
        for item in list(ItemIDTable):
            conn.execute(text("""
                Update vendor set balance = balance + :Price
                Where VID = :VID;"""),{'VID':item['VID'],'Price':item['Price']})
        
        # * Updates Cart items
        conn.execute(text("""
                Update cart
                set ORDER_ID = :recent
                Where CID = :cid AND (ORDER_ID IS NULL OR ORDER_ID = 0) AND ITEM_ID in :itemids;"""),
                {'cid':g.User['ID'],'itemids':listofitemid,'recent':RecentOrder['ID']}) # Sets ORDER ID to the correct items
        conn.commit()
        session['recentOrderId'] = RecentOrder['ID']
        return redirect(url_for('OrderPlace_bp.ShowOrder'))
    except Exception as e:
        print(f'Error: {e}')
        return redirect(url_for('OrderPlace_bp.ShowOrder'))
@OrderPlace_bp.route('/OrderPlaced', methods=["GET"])
def ShowOrder():
    try:
        recentOrder = session.get('recentOrderId')
        
        #* ORDER HISTORY
        OrderHistory = conn.execute(text("""
            SELECT ca.title AS ItemTitle,
            CASE
                WHEN p.discount IS NULL OR p.discount_date > curdate() THEN p.price * ca.quantity
	            WHEN p.discount IS NOT NULL OR p.discount_date < curdate() THEN (p.price - (p.price * p.discount)) * ca.quantity 
            END AS ItemPrice,
            p.image_url as ItemImage, ca.email as CustEmail,ca.quantity AS ItemQuantity, o.ORDER_ID AS ORDERID, o.date AS DatePlaced,o.date AS DatePlaced,DATE(date_add(o.date, interval 5 DAY)) as DeliveryDate,
            o.status AS Status, o.amount AS OrderQuantity,o.total as Total from orders AS o 
            LEFT JOIN cart AS ca ON o.ORDER_ID = ca.ORDER_ID
            LEFT JOIN product AS p ON ca.PID = p.PID WHERE ca.ORDER_ID = :recent"""),
                {'recent':recentOrder}).mappings().fetchall() #! Change this back to :recent
        return render_template('OrderPlaced.html',OrderHistory= OrderHistory)
    except Exception as e:
        print(f'Error: {e}')
        return render_template('OrderPlaced.html', OrderHistory=[])