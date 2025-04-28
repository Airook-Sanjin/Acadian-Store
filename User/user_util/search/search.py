from globals import Blueprint, render_template, request,g,session,redirect,url_for,Connecttodb,text
from datetime import datetime
search_bp = Blueprint('search_bp', __name__, url_prefix='/search', template_folder='templates')

conn = Connecttodb()
@search_bp.before_request # Before each request it will look for the values below
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
        
@search_bp.route("/Search",methods=["POST"])
def searchedItem():
    try:
        CurDate = datetime.now().date()
        SearchInp = request.form.get('Search')
        print(SearchInp.strip())
        Results = conn.execute(text("""
        Select p.PID, p.title, CAST(p.price AS DECIMAL(10,2)) AS price,
        price - (price * discount) AS discounted_price,
        p.description,p.warranty,p.discount,p.discount_date,p.availability,
	    p.VID,p.AID,p.image_url 
        from product as p LEFT JOIN vendor as v ON p.VID=v.VID 
                                    WHERE p.title LIKE :Searched"""),{'Searched':f'%{SearchInp.strip()}%'}).mappings().fetchall()
        print(Results)
        return render_template('search.html', products = Results,CurDate=CurDate)
    except Exception as e:
        print(f"ERROR: {e}")
        return render_template('search.html',products = SearchInp)