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
        
        listofitemid = tuple([item['itemid'] for item in CartList])
        print(listofitemid)
        # * Get Count of cart items
        CartQuantity = conn.execute(text(
            """
                SELECT sum(ca.quantity) as CartQuantity, ca.ORDER_ID as OrderID 
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID
                Group By ca.ORDER_ID;"""),{'ID': g.User['ID']}).mappings().fetchone()
    
        print(CartQuantity['CartQuantity'])
        print(CartQuantity) #!DEBUG
        
        # * Creates new OrderID
        conn.execute(text("""
                INSERT INTO orders
	                (date,total,amount)
                VALUES
	                (now(),:total, :quantity);"""),{'total':total,'quantity':int(CartQuantity['CartQuantity'])})
        
        Order=conn.execute(text("""
                Select ORDER_ID from order"""))
        
        # conn.commit()
        # * Updates Cart items
        conn.execute(text("""
                Update cart
                set ORDER_ID = 7
                Where ITEM_ID in :itemids;"""),{'itemids':listofitemid})
        
        
        return render_template('OrderPlaced.html')
    except Exception as e:
        print(f'Error: {e}')
        return render_template('OrderPlaced.html')
    