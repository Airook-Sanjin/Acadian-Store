from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text

cart_bp = Blueprint('cart_bp', __name__, url_prefix='/cart', template_folder='templates')

conn = Connecttodb()
@cart_bp.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None

@cart_bp.route('/<username>')
def UserCart(username):
    CartList = conn.execute(text(
        """
            SELECT ca.ITEM_ID AS itemid, ca.title AS title, ca.size AS size, ca.color AS color, p.description as description 
            FROM cart AS ca LEFT JOIN CUSTOMER AS cu ON ca.CID = cu.CID LEFT JOIN product as p on ca.PID = p.PID
            WHERE ca.CID = :ID """),{'ID': g.User['ID']}).mappings().fetchall()
    print (CartList)
    
    if not g.User:
        return redirect(url_for('login_bp.Login'))
    return render_template('Cart.html',username=username,CartList = CartList)