from flask import Blueprint, render_template, request, redirect, url_for, session, g
from werkzeug.security import check_password_hash
from globals import Connecttodb, text

login_bp = Blueprint('login_bp', __name__, url_prefix='/auth', template_folder='templates', static_folder='static')

conn = Connecttodb()

@login_bp.route('/Login', methods=["GET"])
def Login():
    conn.commit()
    return render_template('login.html')

@login_bp.route('/Login', methods=["POST"])
def Signin():
    email = request.form.get('Email')
    password_input = request.form.get('Pass')

    try:
        user_data = conn.execute(text("""
            SELECT u.username, u.email, u.password,
                CASE 
                    WHEN c.email IS NOT NULL THEN 'customer'
                    WHEN a.email IS NOT NULL THEN 'admin'
                    WHEN v.email IS NOT NULL THEN 'vendor'
                END AS role,
                c.CID AS customer_id,
                a.AID AS admin_id,
                v.VID AS vendor_id
            FROM users u
            LEFT JOIN customer c ON u.email = c.email
            LEFT JOIN admin a ON u.email = a.email
            LEFT JOIN vendor v ON u.email = v.email
            WHERE u.email = :email
        """), {'email': email}).mappings().fetchone()

        if not user_data:
            return render_template('login.html', message="Email not found.")

        if not check_password_hash(user_data['password'], password_input):
            return render_template('login.html', message="Incorrect password.")

        role = user_data['role']
        user_id = user_data['customer_id'] or user_data['admin_id'] or user_data['vendor_id']

        session['User'] = {
            'Name': user_data['username'],
            'Role': role,
            'ID': user_id,
            'Email': user_data['email']
        }
        g.User = session['User']

        if role == 'customer':
            return redirect(url_for('customer_bp.CustomerHomePage'))

        elif role == 'admin':
            authorized = conn.execute(text("SELECT * FROM admin WHERE AID = :ID AND Authorization = 'granted'"),
                                      {'ID': user_id}).mappings().fetchone()
            if authorized:
                return redirect(url_for('admin_bp.AdminHomePage'))
            else:
                return render_template('login.html', message="You are not authorized as an admin.")

        elif role == 'vendor':
            authorized = conn.execute(text("SELECT * FROM vendor WHERE VID = :ID AND Authorization = 'granted'"),
                                      {'ID': user_id}).mappings().fetchone()
            if authorized:
                return redirect(url_for('vendor_bp.VendorHomePage'))
            else:
                return render_template('login.html', message="You are not authorized as a vendor.")

        return render_template('login.html', message="Invalid user role.")
    except Exception as e:
        print(f"Login error: {e}")
        return render_template('login.html', message="An error occurred during login.")

@login_bp.route('/Logout')
def Logout():
    session.pop('User', None)
    return redirect(url_for('login_bp.Login'))
