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

@OrderPlace_bp.route('/OrderPlaced')
def placeOrder():
    try:
        total = request.args.get('total')
        
        CurTime = datetime.now()
        print(str(CurTime)[0:19])
        # * Get ItemIDs without an ORDER_ID
        ItemIDTable = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid,ca.ORDER_ID as OrderID
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null """),{'ID': g.User['ID']}).mappings().fetchall()
        listofitemid = tuple([item['itemid'] for item in ItemIDTable])
        print(listofitemid)
        # * Get Count of cart items
        CartQuantity = conn.execute(text(
            """
                SELECT sum(ca.quantity) as CartQuantity, ca.ORDER_ID as OrderID 
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID AND ca.ORDER_ID is Null
                Group By ca.ORDER_ID"""),{'ID': g.User['ID']}).mappings().fetchone()
    
        print(CartQuantity['CartQuantity'])
        print(CartQuantity) #!DEBUG
        
        # * Creates new OrderID
        conn.execute(text("""
                INSERT INTO orders
	                (date,total,amount)
                VALUES
	                (now(),:total, :quantity);"""),{'total':total,'quantity':int(CartQuantity['CartQuantity'])})
        conn.commit()
        # * Gets Recent OrderID
        RecentOrder=conn.execute(text("""
                SELECT max(ORDER_ID) as recent from orders""")).mappings().fetchone()
        
        conn.commit()
        # * Updates Cart items
        conn.execute(text("""
                Update cart
                set ORDER_ID = :recent
                Where CID = :cid AND (ORDER_ID IS NULL OR ORDER_ID = 0) AND ITEM_ID in :itemids;"""),
                {'cid':g.User['ID'],'itemids':listofitemid,'recent':RecentOrder['recent']})
        conn.commit()
        
        return render_template('OrderPlaced.html')
    except Exception as e:
        print(f'Error: {e}')
        return render_template('OrderPlaced.html')
    