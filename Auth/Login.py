from flask import Blueprint
from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template, request
# from Auth.Register import register_wh

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth', template_folder='templates', static_folder='static', static_url_path='/static')
conn = Connecttodb()

@login_bp.route('/Login',methods=["GET"])
def Login():
    return render_template('login.html')

@login_bp.route('/Login',methods=["POST"])
def Signin():
    try:
        # Fetch all users, customers and admins
        Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
        Allcustomer = conn.execute(text('Select * from customer')).mappings().fetchall()
        AllAdmins = conn.execute(text('Select * from admin')).mappings().fetchall()
        
        # email from the form
        email = request.form.get('Email')
        
        if email in [customer['email'] for customer in Allcustomer]:
            return "CUSTOMER"

        if email in [admin['email'] for admin in AllAdmins]:
            return "Admin"
        else:
            # If not found in customers or admins, assume it's a vendor
            return"Vendor"
    except Exception as e:
        print(e)

@login_bp.route('/Logout')
def Logout():
    return 'logout'