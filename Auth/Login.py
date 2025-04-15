from flask import Blueprint

from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request
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
    Allusers = conn.execute(text('Select * from users')).mappings().fetchall()
    Allcustomers = conn.execute(text('Select * from customer')).mappings().fetchall()
    AllAdmins = conn.execute(text('Select * from admin')).mappings().fetchall()
    AllVendors = conn.execute(text('Select * from vendor')).mappings().fetchall()
    print(Allusers)
    email = request.form.get('Email')
    
    try:
        if any(customer['email'] == email for customer in Allcustomers ): # * Looks through all customers and see if any match with the email
            print('INTO Customer')
            return redirect(url_for('login_bp.customer_bp.CustomerHomePage')) # * Takes you to Customer page
        
        elif any(admin['email'] == email for admin in AllAdmins ):
            print('INTO Admin')
            return redirect(url_for('login_bp.admin.AdminHomePage')) # * Takes you to admin page
        
        elif any(vendor['email'] == email for vendor in AllVendors ): # * Looks through all Vendors and see if any match with the email
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