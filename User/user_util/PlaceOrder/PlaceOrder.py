from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text

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

