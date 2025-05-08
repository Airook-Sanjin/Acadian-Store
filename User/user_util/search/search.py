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
        CategoryChoice = request.form.get('Category','')
        PriceMin = request.form.get('MinPrice', type =float )
        PriceMax = request.form.get('MaxPrice', type =float)
        InvChoice = request.form.get('Inv','')
        SearchText = request.form.get('Search','')
        
        
        print(CategoryChoice)
        print(InvChoice)
        print(SearchText.strip())
        print(PriceMax)
        print(PriceMin)
        # print(CategoryChoice)
        
        session['CategoryChoice'] = CategoryChoice 
        session['InvChoice'] = InvChoice 
            
        if SearchText:
            session['SearchedTerm'] = SearchText.strip()
            
        
            
        if  PriceMin is not None or PriceMax is not None:
            session['PriceMin'] = PriceMin if PriceMin is not None else 0
            session['PriceMax'] = PriceMax if PriceMax is not None else 1000
        return redirect(url_for('search_bp.SeeResults'))
    except Exception as e:
        print(f"ERROR: {e}")
        return redirect(url_for('search_bp.SeeResults'))
@search_bp.route("/Search",methods=["GET"])
def SeeResults():
    try:
        CategoryChoice = session.get('CategoryChoice', '')
        InvChoice = session.get('InvChoice', '')
        PriceMin = session.get('PriceMin', 0) 
        PriceMax = session.get('PriceMax', 1000) 
        searchedItem = session.get('SearchedTerm', '')
        # InvChoice = session.get('InvChoice', '%') 
        CurDate = datetime.now().date()
        
        currentSearch= searchedItem
        currentInv= InvChoice
        currentCategory= CategoryChoice
        currentMin= PriceMin
        currentMax= PriceMax
        
        
        
        Query = """Select p.PID, p.title, CAST(p.price AS DECIMAL(10,2)) AS price,
        price - (price * discount) AS discounted_price,
        p.description,p.warranty,p.discount,p.discount_date,p.availability,
	    p.VID,p.AID,p.image_url 
        from product as p LEFT JOIN vendor as v ON p.VID=v.VID LEFT JOIN users AS u ON v.email = u.email
        WHERE (p.title LIKE :Searched OR p.description like :Searched OR u.name like :Searched)"""
        
        params = {'Searched':f'%{searchedItem}%'}
        
        if CategoryChoice and CategoryChoice != '':
            Query+=' AND p.category = :category'
            params['category']=CategoryChoice
            
        if InvChoice and InvChoice != '':
            Query+=' AND p.availability = :availability'
            params['availability']=InvChoice
            
        
        if PriceMin is not None  or PriceMax is not None:
            Query += """ AND (CASE
                WHEN p.discount_date > curdate() 
                THEN (p.price - (p.price * p.discount)) BETWEEN :PriceMin AND :PriceMax
                WHEN p.discount_date < curdate() 
                THEN p.price BETWEEN :PriceMin AND :PriceMax
                END)"""
                
                # Updates Parameters
            params.update({
                'PriceMin':PriceMin,
                'PriceMax':PriceMax
            })
            
        Results = conn.execute(text(Query),params).mappings().fetchall()
        
        ResultAmount= len(Results)
        
        Page = render_template('search.html',ResultAmount=ResultAmount, products = Results,SearchedItem=currentSearch,max=currentMax,min=currentMin,CategoryChoice=currentCategory,InvChoice=currentInv, CurDate=CurDate)
        
        session.pop('SearchedTerm',None)
        session.pop('PriceMin',None)
        session.pop('PriceMax',None)
        
        
        return Page
    except Exception as e:
        print(f'Error : {e}')
        return render_template('search.html',ResultAmount=ResultAmount,products = [],CategoryChoice=currentCategory,InvChoice=currentInv,CurDate=CurDate)
        