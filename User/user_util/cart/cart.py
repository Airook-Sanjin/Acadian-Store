from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text

cart_bp = Blueprint('cart_bp', __name__, url_prefix='/cart', template_folder='templates')

conn = Connecttodb()
@cart_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None

@cart_bp.route('/<username>',methods=["GET"])
def UserCart(username):
    try:
        CartList = conn.execute(text(
            """
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color, p.description as description 
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID """),{'ID': g.User['ID']}).mappings().fetchall()
        print (CartList)

        if not g.User: #* Handles if signed in or not
            return redirect(url_for('login_bp.Login'))
        return render_template('Cart.html',username=username,CartList = CartList)
    except Exception as e:
        print(f'ERROR: {e}')
        return render_template('Cart.html',username=username,CartList = CartList)
    
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
                SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color, p.description as description 
                FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
                WHERE ca.CID = :ID """),{'ID': g.User['ID']}).mappings().fetchall() #* Updated Cart List
        
        return render_template('Cart.html',username=username,CartList = CartList)
    except Exception as e:
        print(f'ERROR: {e}')
        return render_template('Cart.html',username=username,CartList = CartList)
    
@cart_bp.route('/add',methods=['POST'])
def addToCart():
    try:
        EMAIL = g.User['Email']
        ID = g.User['ID']
        PID = request.form.get('PID')
        conn.execute(text(
            """
            INSERT INTO cart 
            (title,size,color,email,PID,CID)
            VALUES
            (:title,:size,:color,:email,:PID,:CID)"""),
            {'title':request.form.get('Title'),'size':request.form.get('Size'),'color':request.form.get('Color'),'email':EMAIL,'PID':PID,'CID':ID})
        print("item ADDED")
        conn.commit()
        if g.User['Role']=='customer': #* checks role
            
            print('INTO Customer')
            return redirect(url_for('customer_bp.CustomerHomePage', username=g.User['Name'])) # * Takes you to Customer page
        
        elif g.User['Role']=='admin': #* checks role
            print('INTO Admin')

            return redirect(url_for('admin.AdminHomePage', username=g.User['Name'])) # * Takes you to admin page

        elif g.User['Role']=='vendor': #* checks role

            print('INTO VENDOR')
            return redirect(url_for('vendor_bp.VendorHomePage', username=g.User['Name'])) # * Takes you to vendor page

    except Exception as e:
        print(f'ERROR: {e}')
        return redirect(url_for('start'))
    