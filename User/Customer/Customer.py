
from globals import Blueprint, render_template,redirect,url_for,session,g,text,Connecttodb,checkAndUpdateOrder,CheckOrderDelivered
from datetime import datetime
from User.chat import chat_bp


customer_bp = Blueprint('customer_bp', __name__, url_prefix='/cust', template_folder='templates',static_folder='static',static_url_path='/static')
customer_bp.register_blueprint(chat_bp)




conn=Connecttodb() # Connects to DB

@customer_bp.before_request # Before each request it will look for the values below
def load_user():
   
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
        
@customer_bp.route('/Home', methods=["GET"]) # Customer homepage
def CustomerHomePage():
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        checkAndUpdateOrder()
        conn.commit()
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
        
        return render_template('CustomerHomepage.html',products=products,CurDate=CurDate, inventory=inventory)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('CustomerHomepage.html',products=[],CurDate=CurDate, inventory=[])


@customer_bp.route('/Profile',methods=["POST"])
def GetProfileInfo():
    conn.commit()
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        
        return redirect(url_for('customer_bp.ViewProfile'))
    except Exception as e:
        print(f"Error POST: {e}")
        return redirect(url_for('customer_bp.ViewProfile'))

@customer_bp.route('/Profile',methods=["GET"])
def ViewProfile():
    
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        
        customer_data = conn.execute(text("""
            SELECT u.email as Email,u.username as User,u.name as Name  FROM users AS u LEFT JOIN customer as c ON u.email = c.email
            WHERE c.CID = :ID
        """), {'ID': g.User['ID']}).mappings().first()
        
        print(session)
        print(g.User)
        
        return render_template('Custprofile.html', customer_data=customer_data)
        
        
    except Exception as e:
        print(f"Error GET: {e}")
        return render_template('Custprofile.html',customer_data=[],OrderHistory=[])
    
@customer_bp.route('/OrderHistory',methods=["POST"])
def GetProfileOrderHistory():
    conn.commit()
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        
        return redirect(url_for('customer_bp.ViewOrderHistory'))
    except Exception as e:
        print(f"Error POST: {e}")
        return redirect(url_for('customer_bp.ViewOrderHistory'))

@customer_bp.route('/OrderHistory',methods=["GET"])
def ViewOrderHistory():
    conn.commit()
    try:
        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        checkAndUpdateOrder()
        CheckOrderDelivered()
        
        
        # OrderHistory= conn.execute(text("""
        #     SELECT o.ORDER_ID as OID,o.amount as amount,o.total as total,o.status as status FROM cart AS ca Inner JOIN orders as o ON ca.ORDER_ID= o.ORDER_ID
        #     Where ca.CID = :ID Group by o.ORDER_ID,o.total,o.amount,o.status; """),{'ID': g.User['ID']}).mappings().fetchall()
        # print(session)
        # print(g.User)
        
        # !-------------------------TEST-----------------------
        OrderHistory= conn.execute(text("""
            select o.ORDER_ID as OID,o.total as OrderTotal, o.status as OrderStatus,o.amount as OrderAmount,p.image_url as ItemIMG, ca.ITEM_ID as ItemID, p.title as Itemtitle, ca.color as ItemColor,ca.quantity as ItemQuantity,
            CASE
            	WHEN p.discount IS NULL OR p.discount_date > curdate() THEN p.price * ca.quantity
            	WHEN p.discount IS NOT NULL OR p.discount_date < curdate() THEN (p.price - (p.price * p.discount)) * ca.quantity 
            END AS ItemPrice, ca.ItemStatus AS ItemStatus, ca.CID as CustID,Date(ca.DateShipped) as DateShipped, v.email as CustEmail FROM cart AS ca 
            LEFT JOIN orders as o on ca.ORDER_ID = o.ORDER_ID 
            LEFT JOIN product as p on ca.PID =p.PID 
            LEFT JOIN vendor as v on p.VID = v.VID
            LEFT JOIN users as u on v.email = u.email
            WHERE ca.CID = :ID and o.ORDER_ID is Not Null
            Order By o.ORDER_ID; """),{'ID': g.User['ID']}).mappings().fetchall()
        GroupedOrderHistory={} #* Dictionary to keep all the values of PlacedOrder
        for row in OrderHistory:
            OrderId = row['OID'] #* Extracts order ID
            if OrderId not in GroupedOrderHistory:
                GroupedOrderHistory[OrderId]={
                    "OrderId":OrderId,
                    "OrderStatus":row['OrderStatus'],
                    "OrderTotal":row['OrderTotal'] or 0,
                    "OrderAmount":row['OrderAmount'] or 0,
                    "Items":[]
                }
            # * 
            GroupedOrderHistory[OrderId]["Items"].append({
                "ItemID":row['ItemID'],
                "ItemIMG":row['ItemIMG'],
                "ItemTitle":row['Itemtitle'],
                "ItemColor":row['ItemColor'],
                "ItemQuantity":row['ItemQuantity'],
                "ItemPrice":row['ItemPrice'] or 0,
                "ItemStatus":row['ItemStatus'],
                "DateShipped":row['DateShipped']
                
                })
        GroupedOrderHistoryList = list(GroupedOrderHistory.values())
        # !----------------------------------------------------
        
        return render_template('CustOrderHistory.html', OrderHistory=GroupedOrderHistoryList)
        
        
    except Exception as e:
        print(f"Error GET: {e}")
        return render_template('CustOrderHistory.html',OrderHistory=[])