from flask import Blueprint,render_template,g,session


admin=Blueprint('admin',__name__, url_prefix='/admin',template_folder='templates',static_folder='static',static_url_path='/static') # * init blueprint

@admin.before_request # Before each request it will look for the values below
def load_user():
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None

@admin.route('/Home')
def AdminHomePage():
    return render_template('AdminHomepage.html')