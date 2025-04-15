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

@login_bp.route('/Login',methods = ["POST"])
def Signin():
    message = None
    # Creates dictionary view of all users,customer, vendor and admin
    
    result = conn.execute(text(
        """ SELECT u.username,c.email, 'customer' AS role FROM customer as c Natural JOIN users as u
            WHERE c.email = :email
            UNION
            SELECT u.username, a.email, 'admin' AS role FROM admin as a Natural JOIN users as u
            WHERE a.email = :email
            UNION
            SELECT u.username, v.email,'vendor' AS role FROM vendor as v Natural JOIN users as u
            WHERE v.email = :email"""
    ),{'email':request.form.get('Email')}).mappings().fetchone()
    
    role = result['role']
    session['User'] = {'Name':result['username'],'Role':role}
    g.User = session['User']
    
    
    try:

        if role=='customer': # * Looks through all customers and see if any match with the email
            
            print('INTO Customer')
            return redirect(url_for('login_bp.customer_bp.CustomerHomePage')) # * Takes you to Customer page
        
        elif role=='admin':
            

            print('INTO Admin')
            
            return redirect(url_for('login_bp.admin.AdminHomePage')) # * Takes you to admin page
        
        elif role=='vendor': # * Looks through all Vendors and see if any match with the email
            
            print('INTO VENDOR')
            return redirect(url_for('login_bp.vendor_bp.VendorHomePage')) # * Takes you to vendor page
        
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