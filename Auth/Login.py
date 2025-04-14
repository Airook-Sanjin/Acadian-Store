from flask import Blueprint
from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request
from Auth.Register import register_who

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth',template_folder='templates')
conn = Connecttodb()

@login_bp.route('/Login',methods=["GET"])
def Login():
    return render_template('login.html')

@login_bp.route('/Login',methods=["POST"])
def Signin():
    
    Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    Allcustomer = conn.execute(text('Select * from customer')).mappings().fetchall()
    AllAdmins = conn.execute(text('Select * from admin')).mappings().fetchall()
    try:
        if request.form('Email') in Allcustomer['email']:
                return "CUSTOMER"
        if request.form('Email') in AllAdmins['email']:
                return "Admin"
        else:
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





