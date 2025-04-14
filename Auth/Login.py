from flask import Blueprint
from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request
from Auth.Register import register_who

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth',template_folder='templates',static_folder='static',static_url_path='/static')
conn = Connecttodb()

@login_bp.route('/Login',methods=["GET"])
def Login():
    print('in LOgin')
    return render_template('login.html')

@login_bp.route('/Login',methods=["POST"])
def Signin():
    
    Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    Allcustomers = conn.execute(text('Select * from customer')).mappings().fetchall()
    AllAdmins = conn.execute(text('Select * from admin')).mappings().fetchall()
    print(Allusers)
    email = request.form.get('Email')
    try:
        if any(customer['email'] == email for customer in Allcustomers ):
            print('INTO EMAIL')
            return "CUSTOMER"
        elif any(admin['email'] == email for admin in AllAdmins ):
            print('INTO Admin')
            return "Admin"
        else:
            print('INTO Vendor')
            return"Vendor"
        
    except Exception as e:
        print(e)

@login_bp.route('/Logout')
def Logout():
    return 'logout'

login_bp.add_url_rule('/register', view_func=register_who, endpoint='register')

@login_bp.route('/register')
def redirect_to_register_view():
    return redirect(url_for('register_who'))





