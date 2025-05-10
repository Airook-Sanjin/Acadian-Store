from flask import Blueprint

from globals import Flask, secrets, redirect, url_for, Connecttodb, text ,render_template,request,session,g
from Auth.Register import register_who
from User.Admin.Admin import admin_bp
from User.Customer.Customer import customer_bp
from User.Vendor.Vendor import vendor_bp

login_bp = Blueprint('login_bp',__name__,url_prefix='/auth',template_folder='templates',static_folder='static',static_url_path='/static')


conn = Connecttodb()

@login_bp.route('/Login',methods = ["GET"])
def Login():
    print('in Login')
    return render_template('login.html')

@login_bp.route('/Login', methods=["POST"])
def Signin():
    message = None
    # Creates dictionary view of all users,customer, vendor and admin
    try:
        result = conn.execute(text(
        """ SELECT u.username,c.email as email, 'customer' AS role, CID as ID FROM customer as c Natural JOIN users as u
            WHERE c.email = :email and u.password = :password
            UNION
            SELECT u.username, a.email as email, 'admin' AS role, AID as ID FROM admin as a Natural JOIN users as u
            WHERE a.email = :email and u.password = :password
            UNION
            SELECT u.username, v.email as email,'vendor' AS role, VID as ID FROM vendor as v Natural JOIN users as u
            WHERE v.email = :email and u.password = :password """
        ),{'email':request.form.get('Email'),'password':request.form.get('Pass')}).mappings().fetchone()
        
        role = result['role']
        ID= result['ID']
        session['User'] = {'Name':result['username'],'Role':role,'ID': ID,'Email':result['email']}
        g.User = session['User']
        if role=='customer': # * Looks through all customers and see if any match with the email
            print('INTO Customer')
            return redirect(url_for('customer_bp.CustomerHomePage')) # * Takes you to Customer page
        
        
        elif role=='admin':
            Authorized = conn.execute(text("""SELECT * FROM admin WHERE AID = :ID AND Authorization = 'granted'"""),{'ID':ID}).mappings().fetchone()
            if Authorized:
                print('INTO Admin')
                return redirect(url_for('admin_bp.AdminHomePage')) # * Takes you to admin page
            else:
                message = "You have not been authorized to access this page."
                return render_template('login.html', message=message)
        
        elif role=='vendor': # * Looks through all Vendors and see if any match with the email
            Authorized = conn.execute(text("""SELECT * FROM vendor WHERE VID = :ID AND Authorization = 'granted'"""),{'ID':ID}).mappings().fetchone()
            if Authorized:
                print('INTO VENDOR')
                return redirect(url_for('vendor_bp.VendorHomePage')) # * Takes you to vendor page
            else:
                message = "You have not been authorized to access this page."
                return render_template('login.html', message=message)

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