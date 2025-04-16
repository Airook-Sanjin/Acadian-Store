from flask import Blueprint

from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request,session,g
from Auth.Register import register_who
from User.Admin.Admin import admin
from User.Customer.Customer import customer_bp
from User.Vendor.Vendor import vendor_bp

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth',template_folder='templates',static_folder='static',static_url_path='/static')
login_bp.register_blueprint(admin)
login_bp.register_blueprint(customer_bp)
login_bp.register_blueprint(vendor_bp)

conn = Connecttodb()

@login_bp.route('/Login',methods = ["GET"])
def Login():
    print('in LOgin')
    return render_template('login.html')

@login_bp.route('/Login', methods=["POST"])
def Signin():
    message = None
    result = conn.execute(text(""" SELECT u.username, c.email, c.CID AS ID, 'customer' AS role FROM customer AS c NATURAL JOIN users AS u
        WHERE c.email = :email UNION SELECT u.username, a.email, a.AID AS ID, 'admin' AS role FROM admin AS a NATURAL JOIN users AS u
        WHERE a.email = :email UNION SELECT u.username, v.email, v.VID AS ID, 'vendor' AS role FROM vendor AS v NATURAL JOIN users AS u
        WHERE v.email = :email"""), {'email': request.form.get('Email')}).mappings().fetchone()

    if not result:
        message = "Email not found."
        return render_template('login.html', message=message)

    role = result['role']
    session['User'] = {'Name': result['username'], 'Role': role, 'ID': result['ID']}
    g.User = session['User']

    try:
        if role == 'customer':
            print('INTO Customer')
            return redirect(url_for('login_bp.customer_bp.CustomerHomePage'))
        elif role == 'admin':
            print('INTO Admin')
            return redirect(url_for('login_bp.admin.AdminHomePage'))
        elif role == 'vendor':
            print('INTO Vendor')
            return redirect(url_for('login_bp.vendor_bp.VendorHomePage'))
        else:
            message = "Email not found."
            return render_template('login.html', message=message)
    except Exception as e:
        print(e)
        message = "An error occurred during login."
        return render_template('login.html', message=message)

@login_bp.route('/Logout')
def Logout():
    return 'logout'