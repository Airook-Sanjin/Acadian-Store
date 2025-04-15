from flask import Blueprint

from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request
from Auth.Register import register_who
from User.Admin import admin

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth',template_folder='templates',static_folder='static',static_url_path='/static')
login_bp.register_blueprint(admin)

conn = Connecttodb()

@login_bp.route('/Login',methods = ["GET"])
def Login():
    print('in LOgin')
    return render_template('login.html')

@login_bp.route('/Login',methods = ["POST"])
def Signin():

    # Creates dictionary view of all users,customer, vendor and admin
    Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    Allcustomers = conn.execute(text('Select * from customer')).mappings().fetchall()
    AllAdmins = conn.execute(text('Select * from admin')).mappings().fetchall()
    AllVendors = conn.execute(text('Select * from vendor')).mappings().fetchall()
    print(Allusers)
    email = request.form.get('Email')
    
    try:
        if any(customer['email'] == email for customer in Allcustomers ):
            print('INTO EMAIL')
            return redirect(url_for('login_bp.admin.AdminHomePage'))
        elif any(admin['email'] == email for admin in AllAdmins ):
            login_bp.add_url_rule('/admin/Home', view_func=admin.AdminHomePage, endpoint='Admin')
            print('INTO Admin')
            return redirect(url_for('login_bp.Admin'))
        elif any(vendor['email'] == email for vendor in AllVendors ):
            print('INTO VENDOR')
            return 'Vendor'
        else:
            print('Not a User')
            return"Not A USER"
        
    except Exception as e:
        print(e)

@login_bp.route('/Logout')
def Logout():
    return 'logout'